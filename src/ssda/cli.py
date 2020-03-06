import logging
import os
from datetime import date, datetime, timedelta
from typing import Callable, Optional, Set, Tuple

import click
import dsnparse
import sentry_sdk

from ssda.database.sdb import SaltDatabaseService
from ssda.database.ssda import SSDADatabaseService
from ssda.database.services import DatabaseServices
from ssda.task import execute_task
from ssda.util import types
from ssda.util.errors import get_salt_data_to_log
from ssda.util.fits import fits_file_paths, set_fits_base_dir, get_night_date
from ssda.util.types import Instrument, DateRange, TaskName, TaskExecutionMode

# Log with Sentry
if os.environ.get("SENTRY_DSN"):
    sentry_sdk.init(os.environ.get("SENTRY_DSN"))  # type: ignore


def parse_date(value: str, now: Callable[[], datetime]) -> date:
    """Parse a date string.

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
    instruments: Set[Instrument],
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
    instruments : set of Instrument
        Set of instruments.
    fits_base_dir: str
        The base directory to data files

    """

    # A start date requires an end date, and vice versa
    if start and not end:
        raise click.UsageError(
            "You must also use the --end option if you use the --start option."
        )
    if end and not start:
        raise click.UsageError(
            "You must also use the --start option if you use the --end option."
        )

    # The instrument is unknown
    if len(instruments) != len([instrument for instrument in Instrument]):
        raise click.UsageError("The --instrument is unknown.")

    # A date range must be specified
    if not start or not end:
        raise click.UsageError(
            "You must specify a date range (with the --start/--end options)."
        )

    # A date range requires a base directory
    if start and not fits_base_dir:
        raise click.UsageError(
            "You must specify the base directory for the FITS files (with the"
            "--fits-base-dir option) if you are using a date range."
        )

    # The start date must be earlier than the end date
    if start and end and start >= end:
        raise click.UsageError("The start date must be earlier than the end date.")


@click.command()
@click.option("--end", type=str, help="Start date of the last night to consider.")
@click.option(
    "--fits-base-dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Base directory containing all the FITS files.",
)
@click.option(
    "--instrument",
    "instruments",
    type=click.Choice(["BCAM", "HRS", "RSS", "Salticam"], case_sensitive=False),
    multiple=True,
    help="Instrument to consider.",
)
@click.option(
    "--mode",
    type=click.Choice(["dummy", "production"], case_sensitive=False),
    required=True,
    help="Task execution mode.",
)
@click.option(
    "--skip-errors", is_flag=True, help="Do not terminate if there is an error"
)
@click.option("--start", type=str, help="Start date of the last night to consider.")
@click.option(
    "--task",
    type=click.Choice(["delete", "insert"]),
    required=True,
    help="Task to perform.",
)
@click.option(
    "--verbosity", type=click.Choice(["0", "1", "2"]), help="Log more details."
)
def main(
    task: str,
    start: Optional[str],
    end: Optional[str],
    instruments: Tuple[str],
    fits_base_dir: Optional[str],
    mode: str,
    skip_errors: bool,
    verbosity: Optional[str],
) -> int:
    logging.basicConfig(level=logging.INFO)

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
    task_name = TaskName.for_name(task)
    task_mode = TaskExecutionMode.for_mode(mode)
    validate_options(
        start=start_date,
        end=end_date,
        instruments=instruments_set,
        fits_base_dir=fits_base_dir,
    )

    # store the base directory
    set_fits_base_dir(fits_base_dir)

    # get the FITS file paths
    if start_date and end_date and fits_base_dir:
        paths = fits_file_paths(
            nights=DateRange(start_date, end_date),
            instruments=instruments_set,
            base_dir=fits_base_dir,
        )
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

    flagged_errors = set()
    night_date = ""
    # execute the requested task
    for path in paths:
        try:
            if verbosity_level >= 1 and night_date != get_night_date(path):
                night_date = get_night_date(path)
                click.echo(f"Mapping files for {get_night_date(path)}")
            execute_task(
                task_name=task_name,
                fits_path=path,
                task_mode=task_mode,
                database_services=database_services,
            )
        except BaseException as e:
            error_msg = str(e)
            if verbosity_level == 0:
                # don't output anything
                pass
            # output the FITS file path and the error message.
            data_to_log = get_salt_data_to_log(path)

            if verbosity_level == 1 and error_msg not in flagged_errors:
                msg = f"""
Error in {path}.
{error_msg}
"""
                # Add error to already flagged errors.
                flagged_errors.add(error_msg)
                logging.error(msg)
            if verbosity_level == 2:
                msg = f"""
Error in {path}.
Proposal code: {data_to_log.proposal_code}
Object: {data_to_log.object}
Block visit id: {data_to_log.block_visit_id}
Observation type: {data_to_log.observation_type}
Observation mode: {data_to_log.observation_mode}
Observation time: {data_to_log.observation_time}
{error_msg}
"""
                # output the FITS file path and error stacktrace.
                logging.error(msg, exc_info=True)
            print("_________________________________________________________________________________________________\n")
            if not skip_errors:
                ssda_connection.close()
                return -1

    ssda_connection.close()

    # Success!
    return 0
