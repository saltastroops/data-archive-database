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
    Synchronise the SSDA database with telescope databases such as the SALT Science Database

    Parameters
    ----------
    start: date
        The Start date
    end: date
        The end date
    Returns
    -------
        0 on successful synchronising

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

    proposals_to_update = sdb_database_service.find_proposals_to_update(start_date, end_date)


    # Compare proposal and update
    for proposal in proposals_to_update:
        ssda_database_service.begin_transaction()
        try:
            # Proposal to compare
            proposal_ = ssda_database_service.find_proposal(
                proposal_code=proposal.proposal_code,
                institution=types.Institution.SALT
            )
            if not proposal_:
                continue
            # Proposal id
            proposal_id = proposal_.proposal_id

            # Compare proposal title
            if proposal.title != proposal_.title:
                ssda_database_service.update_title(proposal_id=proposal_id, title=proposal.title)

            # Compare proposal PI
            if proposal.pi != proposal_.pi:
                ssda_database_service.update_pi(proposal_id=proposal_id, pi=proposal.pi)

            # compare proposal investigators
            proposal_investigators = ssda_database_service.find_proposal_investigators(proposal_code=proposal.proposal_code)
            sdb_proposal_investigators = sdb_database_service.find_proposal_investigators(proposal_code=proposal.proposal_code)

            if not (sorted(proposal_investigators) == sorted(sdb_proposal_investigators)):
                ssda_database_service.update_investigators(
                    proposal_id=proposal.proposal_id,
                    proposal_investigator_ids=sdb_proposal_investigators
                )
            observations_to_update = sdb_database_service.find_proposal_observations(
                proposal_code=proposal.proposal_code
            )
            observations_to_compare = ssda_database_service.find_proposal_observations(
                proposal_code=proposal.proposal_code,
                telescope=types.Telescope.SALT
            )

            # compare observation status.
            for obs in observations_to_update:
                for c in observations_to_compare:
                    if c.group_identifier == obs.group_identifier:
                        if proposal.meta_release != c.meta_release or \
                           proposal.data_release != c.data_release or \
                           obs.status != c.status:
                            ssda_database_service.update_release_date(
                                group_identifier=obs.group_identifier,
                                data_release_date=proposal.date_release,
                                meta_release_date=proposal.meta_release,
                                status=obs.status
                            )
                        break

            ssda_database_service.commit_transaction()
        except AttributeError as e:
            ssda_database_service.rollback_transaction()

    ssda_connection.close()

    # Success!
    return 0