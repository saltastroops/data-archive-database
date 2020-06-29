import click
from datetime import datetime, date
import dsnparse
import logging
from sentry_sdk import capture_exception

from ssda.database.sdb import SaltDatabaseService
from ssda.database.services import DatabaseServices
from ssda.database.ssda import SSDADatabaseService

from ssda.util import types
from ssda.util.setup_logger import setup_logger
from ssda.util.parse_date import parse_date


logging.root.setLevel(logging.INFO)

info_log = setup_logger('info_logger', 'ssda_sync_info.log', logging.Formatter('%(asctime)s %(levelname)s - %(message)s'))
error_log = setup_logger('error_logger', 'ssda_sync_error.log', logging.Formatter('%(asctime)s %(levelname)s\n%(message)s'))


@click.command()
@click.option('--start', type=str, required=True, help='Start date of the last night to consider. The date is inclusive.')
@click.option('--end', type=str, required=True, help='Start date of the last night to consider. The date is inclusive.')
def main(start, end) -> int:
    """
    Synchronise the SSDA database with telescope databases such as the SALT Science Database.
    """
    logging.basicConfig(level=logging.INFO)
    logging.error("SALT is always assumed to be the telescope.")
    # convert options as required and validate them
    now = datetime.now
    start_date = parse_date(start, now)
    end_date = parse_date(end, now)

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

    salt_proposals = sdb_database_service.find_submitted_proposals_details(start_date, end_date)

    # Compare proposal and update
    for sdb_proposal in salt_proposals:
        ssda_database_service.begin_transaction()
        try:
            # Proposal to compare
            ssda_proposal = ssda_database_service.find_salt_proposal_details(
                proposal_code=sdb_proposal.proposal_code
            )
            if not ssda_proposal:
                continue

            if sdb_proposal != ssda_proposal:
                ssda_database_service.update_salt_proposal(proposal=sdb_proposal)

            # Compare observation group status.
            salt_observation_groups = sdb_database_service.find_proposal_observation_groups(
                proposal_code=sdb_proposal.proposal_code
            )
            for salt_obs_group in salt_observation_groups:
                ssda_obs_group = ssda_database_service.find_salt_observation_group(
                    group_identifier=salt_obs_group.group_identifier
                )
                if salt_obs_group != ssda_obs_group and ssda_obs_group is not None:
                    ssda_database_service.update_observation_group_status(
                        group_identifier=salt_obs_group.group_identifier,
                        telescope=salt_obs_group.telescope,
                        status=salt_obs_group.status
                    )
            ssda_database_service.commit_transaction()

            info_log.info(msg=f"Proposal: {sdb_proposal.proposal_code} was sucessfully updated.")
        except AttributeError as e:
            ssda_database_service.rollback_transaction()

            capture_exception(e)
            error_log.error(
                """____________________________________________________________________________________________________________
            """, exc_info=True)
    ssda_connection.close()

    # Success!
    return 0
