import logging
from datetime import date, datetime
from typing import Optional
import dsnparse

from ssda.database.ssda import SSDADatabaseService
from ssda.ssda_populate import parse_date
from ssda.util import types
from ssda.util.types import DateRange

logging.basicConfig(
    level=logging.INFO, format="%(levelname)s %(asctime)s: %(message)s",
)


def validate_options(
    fits: Optional[str] = None,
    out: Optional[str] = None,
    start: Optional[date] = None,
    end: Optional[date] = None,
):
    if not fits and not start and not end:
        raise ValueError("You must provide either the FITS file path or a date range.")
    if fits and (start or end):
        raise ValueError("You cannot provide provide both the FITS file path and a date range.")
    if not out and (start or end):
        raise ValueError("The --out option must be used with the --start and --end option.")
    if fits and out:
        raise ValueError("The --fits and --out options cannot be used together.")
    if (start and not end) or (not start and end):
        raise ValueError(
            "You cannot provide a start_date without an end_date date, or an end_date date without a "
            "start_date date."
        )


def delete_in_ssda(fits: Optional[str], start: Optional[str], end: Optional[str], out: Optional[str]):
    validate_options(fits=fits, start=start, end=end, out=out)

    # database access
    ssda_db_config = dsnparse.parse_environ("SSDA_DSN")
    ssda_db_config = types.DatabaseConfiguration(
        username=ssda_db_config.user,
        password=ssda_db_config.secret,
        host=ssda_db_config.host,
        port=ssda_db_config.port,
        database=ssda_db_config.database,
    )
    ssda_database_service = SSDADatabaseService(ssda_db_config)

    ssda_database_service.begin_transaction()

    try:
        if fits:
            observation_id = ssda_database_service.find_observation_id(artifact_path=fits)
            if observation_id is None:
                raise ValueError(f"No observation id found for {fits}")
            ssda_database_service.delete_observation(
                observation_id=observation_id
            )
            ssda_database_service.commit_transaction()
            logging.info(msg=f"\nSuccessfully deleted observation for {fits}")
        else:
            if start is None:
                raise ValueError("The start date must not be None.")
            if end is None:
                raise ValueError("The end date must not be None.")
            now = datetime.now
            observation_paths = ssda_database_service.find_file_paths(
                nights=DateRange(parse_date(start, now), parse_date(end, now))
            )
            with open(f"{out}", "w") as f:
                for obs_path in observation_paths:
                    f.write("ssda delete -fits " + obs_path + "\n")
            logging.info(msg=f""
                             f"The delete command does not support deleting files for a date range, as there might be "
                             f"cases where this leads to unexpected results.Your chosen date range covers the following "
                             f"file paths. Please check the list and call the delete command with the --file-path option"
                             f" for every path you want to delete.")
    except BaseException as e:
        ssda_database_service.rollback_transaction()
        logging.error(msg="Failed to delete data.", exc_info=True)
        logging.error(e)
