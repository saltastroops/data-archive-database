import click
from datetime import datetime
import dsnparse

from ssda.cli import parse_date
from ssda.database.sdb import SaltDatabaseService
from ssda.database.services import DatabaseServices
from ssda.database.ssda import SSDADatabaseService

from ssda.util import types

@click.command()
@click.option('--start', type=str, help='Start date of the last night to consider.')
@click.option('--end', type=str, help='Start date of the last night to consider.')

def main(start, end):
    """Simple program that greets NAME for a total of COUNT times."""

    # convert options as required and validate them
    now = datetime.now
    start_date = parse_date(start, now) if start else None
    end_date = parse_date(end, now) if end else None

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

    proposals_to_update = ssda_database_service.find_proposals_to_update(start_date, end_date)
    # Compare proposal and update
    for proposal in proposals_to_update:
        ssda_database_service.begin_transaction()

        # Proposal id
        proposal_id = proposal.proposal_id
        # Proposal code
        proposal_code = proposal.proposal_code
        # Proposal title
        sdb_title = sdb_database_service.find_proposal_title(proposal_code=proposal_code)

        if proposal.title != sdb_title:
            ssda_database_service.update_title(proposal_id=proposal_id, title=sdb_title)

        # compare proposal PI
        sdb_pi = sdb_database_service.find_pi(proposal_code=proposal_code)
        if proposal.pi != sdb_pi:
            ssda_database_service.update_pi(proposal_id=proposal_id, pi=sdb_pi)

        # compare proposal date release
        sdb_date_release = sdb_database_service.find_release_date(proposal_code)
        if proposal.date_release != sdb_date_release[0] or proposal.meta_release != sdb_date_release[1]:
            ssda_database_service.update_release_date(
                proposal_code=proposal_code,
                release_date=sdb_date_release[0],
                meta_release_date=sdb_date_release[1]
            )

        # compare proposal proposal investigators
        proposal_investigators = ssda_database_service.find_proposal_investigators(proposal_code=proposal_code)
        sdb_proposal_investigators = sdb_database_service.find_proposal_investigators(proposal_code=proposal_code)

        if not (sorted(proposal_investigators) == sorted(sdb_proposal_investigators)):
            ssda_database_service.update_investigators(
                proposal_id=proposal.proposal_id,
                proposal_investigators=sdb_proposal_investigators
            )
        ssda_database_service.commit_transaction()
    observations_to_update = ssda_database_service.find_observations(start_date, end_date)

    for observation in observations_to_update:
        sdb_observation_status = sdb_database_service.find_observation_status(observation.group_identifier)
        if observation.status != sdb_observation_status.value:
            ssda_database_service.update_status(
                status=observation.status,
                observation_id=observation.observation_id
            )

    ssda_connection.close()