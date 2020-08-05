import logging
from datetime import date, datetime
from typing import Optional
import dsnparse
import click

from ssda.cli import parse_date
from ssda.database.ssda import SSDADatabaseService
from ssda.util import types
from ssda.util.types import DateRange

logging.basicConfig(
    level=logging.INFO, format="%(levelname)s %(asctime)s: %(message)s",
)


def validate_options(
    file_path: Optional[str] = None,
    start: Optional[date] = None,
    end: Optional[date] = None,
):
    if not file_path and not start and not end:
        raise ValueError("You must provide either a file path or a date range.")
    if file_path and (start or end):
        raise ValueError("You cannot provide provide both a file path and a date range.")
    if (start and not end) or (not start and end):
        raise ValueError(
            "You cannot provide a start_date without an end_date date, or an end_date date without a "
            "start_date date."
        )


@click.command()
@click.option("--end", type=str, help="Start date of the last night to consider.")
@click.option(
    "--file_path", help="FITS file whose data to remove from the database.",
)
@click.option("--start", type=str, help="Start date of the last night to consider.")
def main(file_path: Optional[str], start: Optional[str], end: Optional[str]):
    validate_options(file_path=file_path, start=start, end=end)

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
        if file_path:
            observation_id = ssda_database_service.find_observation_id(artifact_path=file_path)
            if observation_id is None:
                raise ValueError(f"No observation id found for file path: {file_path}")
            ssda_database_service.delete_observation(
                observation_id=observation_id
            )
            ssda_database_service.commit_transaction()
            logging.info(msg="\nSuccessfully deleted observation(s)")
        else:
            if start is None:
                raise ValueError("The start date is None.")
            if end is None:
                raise ValueError("The end date is None.")
            now = datetime.now
            observation_ids = ssda_database_service.find_observation_ids(
                nights=DateRange(parse_date(start, now), parse_date(end, now))
            )
            files_affected = open(f"files to delete from {start} to {end}.log", "w")
            for obs_id in observation_ids:
                files_affected.writelines(str(obs_id) + "\n")
            logging.info(msg=f"\nDate range can not be deleted please look at log: "
                             f"files to delete from {start} to {end}.log for files that can be deleted")
    except BaseException as e:
        ssda_database_service.rollback_transaction()
        logging.error(msg="Failed to delete data.", exc_info=True)
        logging.error(e)
