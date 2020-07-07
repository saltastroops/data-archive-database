import click
from datetime import datetime
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

    salt_proposals = sdb_database_service.find_mapped_submitted_proposals()
    ssda_proposals = ssda_database_service.find_salt_proposal_details()

    # Compare proposal and update
    for proposal_code, ssda_proposal in ssda_proposals.items():
        ssda_database_service.begin_transaction()
        try:
            salt_proposal = salt_proposals[proposal_code]
            proposal_id = ssda_database_service.find_proposal_id(
                proposal_code=proposal_code,
                institution=types.Institution.SALT
            )

            if (
                ssda_proposal.data_release != salt_proposal.data_release or
                ssda_proposal.meta_release != salt_proposal.meta_release
            ):
                ssda_database_service.update_proposal_release_date(
                    proposal_id=proposal_id,
                    release_dates=types.ReleaseDates(
                        meta_release=salt_proposal.meta_release, data_release=salt_proposal.data_release
                    )
                )

            if salt_proposal.pi != ssda_proposal.pi:
                ssda_database_service.update_pi(proposal_id=proposal_id, pi=salt_proposal.pi)
                info_log.info(msg=f'The PI of {proposal_code} has been changed to be {salt_proposal.pi}.')

            if salt_proposal.title != ssda_proposal.title:
                ssda_database_service.update_proposal_title(proposal_id=proposal_id, title=salt_proposal.title)
                info_log.info(msg=f'The title of {proposal_code} has been changed to be: {salt_proposal.title}.')

            if salt_proposal.investigators != ssda_proposal.investigators:
                ssda_database_service.update_investigators(
                    proposal_code=salt_proposal.proposal_code,
                    institution=salt_proposal.institution,
                    proposal_investigators=[
                        types.ProposalInvestigator(
                            proposal_id=proposal_id, investigator_id=investigator, institution=types.Institution.SALT
                        )
                        for investigator in salt_proposal.investigators
                    ],
                )

            # Compare observation group status.
            salt_observation_groups = sdb_database_service.find_proposal_observation_groups(
                proposal_code=proposal_code
            )
            ssda_observation_groups = ssda_database_service.find_salt_observation_group()
            for group_identifier, ssda_observation_group in ssda_observation_groups.items():
                salt_observation_group = salt_observation_groups[group_identifier]
                if salt_observation_group != ssda_observation_group:
                    ssda_database_service.update_observation_group_status(
                        group_identifier=group_identifier,
                        telescope=types.Telescope.SALT,
                        status=salt_observation_group.status
                    )
                    info_log.info(msg=f'The status of group identifier: {group_identifier} has been changed to'
                                      f'{salt_observation_group.status.value}.')
            ssda_database_service.commit_transaction()

        except AttributeError as e:
            ssda_database_service.rollback_transaction()

            capture_exception(e)
            error_log.error(
                """____________________________________________________________________________________________________________
            """, exc_info=True)
    ssda_connection.close()
    info_log.info(msg=f'SSDA sync script ran.')
    # Success!
    return 0