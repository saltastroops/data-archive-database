import logging
import os
import traceback
from datetime import date, datetime, timedelta
from typing import Callable, List, Optional, Set, Tuple

import click
import dsnparse
import sentry_sdk

from ssda.database.sdb import SaltDatabaseService
from ssda.database.ssda import SSDADatabaseService
from ssda.util import types
from ssda.util.errors import get_salt_data_to_log
from ssda.util.fits import fits_file_paths, set_fits_base_dir, get_night_date
from ssda.util.types import Instrument, DateRange
from ssda.database.services import DatabaseServices
from ssda.repository import insert
from ssda.observation_properties import observation_properties
from ssda.util.fits import StandardFitsFile

# Log with Sentry
from ssda.util.warnings import clear_warnings, get_warnings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s]: %(message)s",
    datefmt="%Y/%m/%d %H:%M:%S",
)

if os.environ.get("SENTRY_DSN"):
    sentry_sdk.init(os.environ.get("SENTRY_DSN"))  # type: ignore


def execute_database_insert(
        fits_path: str,
        database_services: DatabaseServices,
) -> None:
    # If the FITS file already exists in the database, do nothing.
    if database_services.ssda.file_exists(fits_path):
        return

    # Get the observation properties.
    fits_file = StandardFitsFile(fits_path)
    try:
        _observation_properties = observation_properties(
            fits_file, database_services
        )

        # Check if the FITS file is to be ignored
        if _observation_properties.ignore_observation():
            clear_warnings()
            return
    except Exception as e:
        propid_header_value = fits_file.header_value("PROPID")
        proposal_id = (
            propid_header_value.upper()
            if propid_header_value
            else ""
        )

        # If the FITS file is Junk, Unknown, ENG or CAL_GAIN, do not store the observation.
        if proposal_id in ("JUNK", "UNKNOWN", "NONE", "ENG", "CAL_GAIN"):
            return
        # Do not store engineering data.
        if "ENG_" in proposal_id or "ENG-" in proposal_id:
            return
        raise e

    # Execute the database insert
    insert(
        observation_properties=_observation_properties,
        ssda_database_service=database_services.ssda,
    )


def parse_date(value: str, now: Callable[[], datetime]) -> date:
    """
    Parse a date string.

    The value must be a date of the form yyyy-mm-dd. Alternatively, you can use the
    keywords today and yesterday.

    Parameters
    ----------
    value : str
         Date string
    now : func
         Function returning the current datetime.

    """

    if value == "today":
        return now().date()
    if value == "yesterday":
        return (now() - timedelta(days=1)).date()
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        raise click.UsageError(
            f"{value} is neither a valid date of the form yyyy-mm-dd, nor the string "
            f"yesterday, nor the string today."
        )


def validate_options(
        start: Optional[date],
        end: Optional[date],
        fits_base_dir: Optional[str],
) -> None:
    """
    Validate the command line options.

    An exception is raised if either of the following is true.

    * The start date or end date is missing.
    * The start date is later than the end date.
    * A future date is specified.

    Parameters
    ----------
    start : datetime
        Start date.
    end : datetime
        End date.
    fits_base_dir: str
        The base directory to data files
    """

    if start and start < date(2011, 9, 1):
        raise ValueError("The start date must be 2011-09-01 or later.")

    if not fits_base_dir:
        fits_base_dir = os.environ.get("FITS_BASE_DIR")
    if not fits_base_dir:
        raise ValueError(
            "You must specify the base directory for the FITS files "
            "(either with the --fits-base-dir option or by setting an environment "
            "variable FITS_BASE_DIR)."
        )

    # Either a date range or a FITS file must be specified
    if not (start and end):
        raise click.UsageError(
            "You must specify a date range (with the --start/--end options)."
        )

    # The start date must be earlier than the end date
    if start and end and start >= end:
        raise click.UsageError("The start date must be earlier than the end date.")


def populate_ssda(start: Optional[str],
                  end: Optional[str],
                  instruments: Tuple[str],
                  file: Optional[str],
                  fits_base_dir: Optional[str],
                  skip_errors: bool,
                  verbosity: Optional[str],
                  ) -> int:
    logging.basicConfig(level=logging.INFO)
    logging.error("SALT is always assumed to be the telescope.")

    verbosity_level = 2 if not verbosity else int(verbosity)

    if not os.environ.get("SENTRY_DSN"):
        logging.warning(
            "Environment variable SENTRY_DSN for logging with Sentry not " "set."
        )

    # convert options as required and validate them
    now = datetime.now
    start_date = parse_date(start, now) if start else None
    end_date = parse_date(end, now) if end else None
    if len(instruments):
        instruments_set = set(
            Instrument.for_name(instrument) for instrument in instruments
        )
    else:
        instruments_set = set(instrument for instrument in Instrument)
    validate_options(
        start=start_date,
        end=end_date,
        fits_base_dir=fits_base_dir
    )

    # Off we go!
    start_msg = "Inserting data "
    if start_date and end_date:
        start_msg += (
            f"for the nights from {start_date.isoformat()} to {end_date.isoformat()}"
        )
    if file:
        start_msg += f"from {file}"
    if verbosity_level >= 1:
        logging.info(start_msg)

    # store the base directory
    if fits_base_dir:
        set_fits_base_dir(fits_base_dir)

    # get the FITS file paths
    if start_date and end_date and fits_base_dir:
        paths = fits_file_paths(
            nights=DateRange(start_date, end_date),
            instruments=instruments_set,
            base_dir=fits_base_dir,
        )
    elif file:
        paths = iter([file])
    else:
        raise click.UsageError(
            "The command line options do not allow the FITS file paths to be found."
        )

    # database access
    ssda_db_config = dsnparse.parse_environ("SSDA_DSN")
    ssda_db_config = types.DatabaseConfiguration(
        username=ssda_db_config.user,
        password=ssda_db_config.secret,
        host=ssda_db_config.host,
        port=ssda_db_config.port,
        database=ssda_db_config.database,
    )
    sdb_db_config = dsnparse.parse_environ("SDB_DSN")
    sdb_db_config = types.DatabaseConfiguration(
        username=sdb_db_config.user,
        password=sdb_db_config.secret,
        host=sdb_db_config.host,
        port=3306,
        database=sdb_db_config.database,
    )
    ssda_database_service = SSDADatabaseService(ssda_db_config)
    sdb_database_service = SaltDatabaseService(sdb_db_config)

    database_services = DatabaseServices(
        ssda=ssda_database_service, sdb=sdb_database_service
    )
    ssda_connection = database_services.ssda.connection()

    daytime_errors: List[str] = list()
    nighttime_errors: List[str] = list()
    warnings: List[str] = list()
    night_date = ""
    # execute the requested task
    for path in paths:
        try:
            if verbosity_level >= 1 and night_date != get_night_date(path):
                night_date = get_night_date(path)
                click.echo(f"Mapping files for {get_night_date(path)}")
            clear_warnings()
            execute_database_insert(
                fits_path=path,
                database_services=database_services,
            )
            if get_warnings():
                handle_exception(
                    e=get_warnings()[0],
                    daytime_errors=daytime_errors,
                    nighttime_errors=nighttime_errors,
                    warnings=warnings,
                    verbosity_level=verbosity_level,
                    path=path,
                )
        except BaseException as e:
            handle_exception(
                e=e,
                daytime_errors=daytime_errors,
                nighttime_errors=nighttime_errors,
                warnings=warnings,
                verbosity_level=verbosity_level,
                path=path,
            )

            if not skip_errors:
                ssda_connection.close()
                return -1

    ssda_connection.close()

    if verbosity_level >= 1:
        msg = ""
        msg += "NIGHTTIME ERRORS:\n"
        msg += "-----------------\n"
        if verbosity_level == 1:
            msg += "\n"
        if nighttime_errors:
            for error in nighttime_errors:
                if verbosity_level > 1:
                    msg += "\n"
                msg += f"{error}\n"
        else:
            if verbosity_level > 1:
                msg += "\n"
            msg += "There are no nighttime errors.\n\n"

        msg += "\n"
        msg += "DAYTIME ERRORS:\n"
        msg += "---------------\n"
        if verbosity_level == 1:
            msg += "\n"
        if daytime_errors:
            if verbosity_level > 1:
                msg += "\n"
            for error in daytime_errors:
                msg += f"{error}\n"
        else:
            if verbosity_level > 1:
                msg += "\n"
            msg += "There are no daytime errors.\n\n"

        msg += "\n"
        msg += "WARNINGS:\n"
        msg += "---------\n"
        if verbosity_level == 1:
            msg += "\n"
        if warnings:
            for warning in warnings:
                if verbosity_level > 1:
                    msg += "\n"
                msg += f"{warning}\n"
        else:
            if verbosity_level > 1:
                msg += "\n"
            msg += "There are no warnings.\n\n"

        msg = f"""
Total number of nighttime errors: {len(nighttime_errors)}
Total number of daytime errors: {len(daytime_errors)}
Total number of warnings: {len(warnings)}
"""
        logging.info(msg)

    # Success!
    return 0


def handle_exception(
    e: BaseException,
    daytime_errors: List[str],
    nighttime_errors: List[str],
    warnings: List[str],
    verbosity_level: int,
    path: str,
):
    """
    Handle an exception.

    Parameters
    ----------
    e : Exception
        Exception.
    daytime_errors : List[str]
        Daytime error messages.
    nighttime_errors : List[str]
        Nighttime error messages.
    warnings : List[str]
        Warning messages.
    verbosity_level : int
        Verbosity level.
    path : str
        Path of the FITS File.

    """

    data_to_log = get_salt_data_to_log(path)
    error_msg = str(e)
    is_warning = isinstance(e, Warning)
    msg = ""
    if verbosity_level == 0:
        # don't output anything
        pass
    if verbosity_level == 1:
        filename, lineno = error_location(e)
        msg += f"[{filename}, line {lineno}] {error_msg}"
        if data_to_log.is_daytime_observation():
            msg += " [DAYTIME]"
        msg += f" [{path}]"
        if not data_to_log.is_daytime_observation():
            if not is_warning:
                logging.error(msg)
            else:
                logging.warning(msg)
    if verbosity_level == 2 or verbosity_level == 3:
        # TODO Please note that data_to_log is only for SALT need to be updated in the future
        # output the FITS file path and the error message.
        if is_warning:
            msg = """Warning
-------
"""
        else:
            msg = """Error message
-------------
"""
        msg += f"""{error_msg}
    
FITS file details
------------------
File path: {data_to_log.path}
Proposal code: {data_to_log.proposal_code}
Object: {data_to_log.object}
Block visit id: {data_to_log.block_visit_id}
Observation type: {data_to_log.observation_type}
Observation mode: {data_to_log.observation_mode}
Observation time: {data_to_log.observation_time}{" *** DAYTIME ***" if data_to_log.is_daytime_observation() else ""}"""

        if verbosity_level == 3:
            msg += f"""
        Stack trace
        -----------
        """
            msg += """_________________________________________________________________________________________________
        """
            # output the FITS file path and error stacktrace.
            if not is_warning:
                logging.error(msg, exc_info=verbosity_level == 3)
            else:
                logging.warning(msg, exc_info=verbosity_level == 3)

    if is_warning:
        warnings.append(msg)
    elif data_to_log.is_daytime_observation():
        daytime_errors.append(msg)
    else:
        nighttime_errors.append(msg)


def error_location(e: BaseException) -> Tuple[str, int]:
    """
    Get the name od the file and the line number where an exception was raised.

    Parameters
    ----------
    e : BaseException
        Exception.

    Returns
    -------
    tuple
        A tuple of the file name and line number.

    """

    stack_frames = traceback.extract_tb(e.__traceback__)
    if len(stack_frames) > 0:
        filename = os.path.basename(stack_frames[-1].filename)
        lineno = stack_frames[-1].lineno
        return filename, lineno
    else:
        return "?", 0
