import click
from datetime import datetime
import dsnparse
import logging

from ssda.database.sdb import SaltDatabaseService
from ssda.database.services import DatabaseServices
from ssda.database.ssda import SSDADatabaseService

from ssda.util import types
from ssda.util.parse_date import parse_date


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

    salt_proposals = sdb_database_service.find_submitted_proposals(start_date, end_date)


    # Compare proposal and update
    for sdb_proposal in salt_proposals:
        ssda_database_service.begin_transaction()
        institution = types.Institution.SALT
        try:
            # Proposal to compare
            ssda_proposal = ssda_database_service.find_proposal(
                proposal_code=sdb_proposal.proposal_code,
                institution=institution
            )
            if not ssda_proposal:
                continue

            # Compare proposal title
            if sdb_proposal.title != ssda_proposal.title:
                ssda_database_service.update_title(
                    proposal_code=ssda_proposal.proposal_code,
                    institution=institution,
                    title=sdb_proposal.title
                )

            # Compare proposal PI
            if sdb_proposal.pi != ssda_proposal.pi:
                ssda_database_service.update_pi(
                    proposal_code=ssda_proposal.proposal_code,
                    institution=institution,
                    pi=sdb_proposal.pi
                )

            # compare proposal investigators
            sdb_proposal_investigators = sdb_database_service.find_proposal_investigator_user_ids(proposal_code=sdb_proposal.proposal_code)

            ssda_database_service.update_investigators(
                proposal_code=ssda_proposal.proposal_code,
                institution=institution,
                proposal_investigators=sdb_proposal_investigators
            )
            salt_observations = sdb_database_service.find_proposal_observations(
                proposal_code=sdb_proposal.proposal_code
            )
            observations = ssda_database_service.find_proposal_observations(
                proposal_code=sdb_proposal.proposal_code,
                telescope=types.Telescope.SALT
            )

            # compare observation status.
            for salt_obs in salt_observations:
                for obs in observations:
                    group_identifier = ssda_database_service.find_observation_group(
                        observation_group_id=obs.observation_group_id
                    )
                    release_date = sdb_database_service.find_release_date(sdb_proposal.proposal_code)
                    if group_identifier.group_identifier == salt_obs.group_identifier:
                        ssda_database_service.update_observation(
                            group_identifier=salt_obs.group_identifier,
                            data_release_date=release_date,
                            meta_release_date=release_date,
                            status=salt_obs.status
                        )
                        break

            ssda_database_service.commit_transaction()
        except AttributeError as e:
            ssda_database_service.rollback_transaction()

    ssda_connection.close()

    # Success!
    return 0