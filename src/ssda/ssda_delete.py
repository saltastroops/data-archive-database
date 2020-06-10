import logging
from datetime import date
from typing import Optional
import dsnparse
import click

from ssda.database.ssda import SSDADatabaseService
from ssda.util import types

logging.basicConfig(level=logging.INFO, format='%(levelname)s %(asctime)s: %(message)s',)


def validate_options(
        filename: Optional[str] = None,
        start: Optional[date] = None,
        end: Optional[date] = None
):
    if not filename and not start and not end:
        raise ValueError("You must provide either a filename or a date range.")
    if filename and (start or end):
        raise ValueError("You cannot provide provide both a filename and a date range.")
    if (start and not end) or (not start and end):
        raise ValueError("You cannot provide a start_date without an end_date date, or an end_date date without a "
                         "start_date date.")


@click.command()
@click.option("--end", type=str, help="Start date of the last night to consider.")
@click.option(
    "--file",
    help="FITS file whose data to remove from the database.",
)
@click.option("--start", type=str, help="Start date of the last night to consider.")
def main(
        file: Optional[str],
        start: Optional[date],
        end: Optional[date]
):
    validate_options(
        filename=file,
        start=start,
        end=end)

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
        if file:
            ssda_database_service.delete_observation(
                observation_id=ssda_database_service.find_observation_id(artifact_name=file)
            )
        else:
            observation_ids = ssda_database_service.find_observation_ids(start=start, end=end)
            for obs_id in observation_ids:
                ssda_database_service.delete_observation(observation_id=obs_id)
        ssda_database_service.commit_transaction()
        logging.info(msg="\nSuccessfully deleted observation(s)")
    except BaseException as e:
        ssda_database_service.rollback_transaction()
        logging.error(msg="Failed to delete data.", exc_info=True)
        logging.error(e)

    ssda_database_service.close()