import click
from datetime import date, datetime
import logging
from sentry_sdk import capture_exception
from ssda.database.sdb import SaltDatabaseService
from ssda.database.ssda import SSDADatabaseService

from ssda.util.databases import database_services as db_services
from ssda.util import types
from ssda.util.setup_logger import setup_logger


logging.root.setLevel(logging.INFO)

info_log = setup_logger('info_logger', 'ssda_sync_info.log', logging.Formatter('%(asctime)s %(levelname)s - %(message)s'))
error_log = setup_logger('error_logger', 'ssda_sync_error.log', logging.Formatter('%(asctime)s %(levelname)s\n%(message)s'))


@click.command()
def main() -> int:
    """
    Synchronise the SSDA database with telescope databases such as the SALT Science Database.
    """
    logging.basicConfig(level=logging.INFO)
    logging.error("SALT is always assumed to be the telescope.")
    # convert options as required and validate them

    # database access
    database_services = db_services()
    ssda_database_service = database_services.ssda
    sdb_database_service = database_services.sdb

    sdb_proposals = sdb_database_service.find_mapped_submitted_proposals()
    ssda_proposals = ssda_database_service.find_salt_proposal_details()

    # Compare proposal and update
    for proposal_code, ssda_proposal in ssda_proposals.items():
        ssda_database_service.begin_transaction()
        try:
            sdb_proposal = sdb_proposals[proposal_code]
            update_salt_proposal(old_proposal=ssda_proposal, new_proposal=sdb_proposal, ssda_database_service=ssda_database_service, sdb_database_service=sdb_database_service)
            ssda_database_service.commit_transaction()
        except BaseException as e:
            ssda_database_service.rollback_transaction()
            capture_exception(e)
            error_log.error(
                """____________________________________________________________________________________________________________
            """, exc_info=True)
    info_log.info(msg=f'SSDA sync script ran.')
    # Success!
    return 0


def update_salt_proposal(old_proposal: types.SALTProposalDetails, new_proposal: types.SALTProposalDetails, ssda_database_service: SSDADatabaseService, sdb_database_service: SaltDatabaseService):
    update_salt_proposal_pi(old_proposal, new_proposal, ssda_database_service)
    update_salt_proposal_title(old_proposal, new_proposal, ssda_database_service)
    update_salt_release_dates(old_proposal, new_proposal, ssda_database_service)
    update_salt_proposal_investigators(old_proposal, new_proposal, ssda_database_service, sdb_database_service)
    update_salt_position_owner_ids(new_proposal, ssda_database_service)
    update_salt_observation_group_status_values(old_proposal, new_proposal, ssda_database_service, sdb_database_service)


def update_salt_proposal_pi(old_proposal: types.SALTProposalDetails, new_proposal: types.SALTProposalDetails, ssda_database_service: SSDADatabaseService) -> None:
    check_proposal_code_consistency(old_proposal, new_proposal)
    if new_proposal.pi != old_proposal.pi:
        proposal_id = ssda_database_service.find_proposal_id(
            proposal_code=old_proposal.proposal_code,
            institution=types.Institution.SALT
        )
        ssda_database_service.update_pi(proposal_id=proposal_id, pi=new_proposal.pi)
        info_log.info(msg=f'The PI of {old_proposal.proposal_code} has been changed from "{old_proposal.pi}" to "{new_proposal.pi}".')


def update_salt_proposal_title(old_proposal: types.SALTProposalDetails, new_proposal: types.SALTProposalDetails, ssda_database_service: SSDADatabaseService):
    check_proposal_code_consistency(old_proposal, new_proposal)
    if new_proposal.title != old_proposal.title:
        proposal_id = ssda_database_service.find_proposal_id(
            proposal_code=old_proposal.proposal_code,
            institution=types.Institution.SALT
        )
        ssda_database_service.update_proposal_title(proposal_id=proposal_id, title=new_proposal.title)
        info_log.info(msg=f'The title of {old_proposal.proposal_code} has been changed from "{old_proposal.title}" to "{new_proposal.title}".')


def update_salt_release_dates(old_proposal: types.SALTProposalDetails, new_proposal: types.SALTProposalDetails, ssda_database_service: SSDADatabaseService) -> None:
    check_proposal_code_consistency(old_proposal, new_proposal)
    if (
            old_proposal.data_release != new_proposal.data_release or
            old_proposal.meta_release != new_proposal.meta_release
    ):
        proposal_id = ssda_database_service.find_proposal_id(
            proposal_code=old_proposal.proposal_code,
            institution=types.Institution.SALT
        )
        ssda_database_service.update_proposal_release_date(
            proposal_id=proposal_id,
            release_dates=types.ReleaseDates(
                meta_release=new_proposal.meta_release, data_release=new_proposal.data_release
            )
        )
        info_log.info(msg=f"The data release date of {old_proposal.proposal_code} has been changed from {old_proposal.data_release.strftime('%Y-%m-%d')} to {new_proposal.data_release.strftime('%Y-%m-%d')}")
        info_log.info(msg=f"The metadata release date of {old_proposal.proposal_code} has been changed from {old_proposal.meta_release.strftime('%Y-%m-%d')} to {new_proposal.meta_release.strftime('%Y-%m-%d')}")


def update_salt_proposal_investigators(old_proposal: types.SALTProposalDetails, new_proposal: types.SALTProposalDetails, ssda_database_service: SSDADatabaseService, sdb_database_service: SaltDatabaseService) -> None:
    check_proposal_code_consistency(old_proposal, new_proposal)
    if new_proposal.investigators != old_proposal.investigators:
        proposal_id = ssda_database_service.find_proposal_id(
            proposal_code=old_proposal.proposal_code,
            institution=types.Institution.SALT
        )
        ssda_database_service.update_investigators(
            proposal_code=new_proposal.proposal_code,
            institution=new_proposal.institution,
            proposal_investigators=[
                types.ProposalInvestigator(
                    proposal_id=proposal_id,
                    investigator_id=str(investigator),
                    institution=types.Institution.SALT,
                    institution_memberships=sdb_database_service.institution_memberships(
                        int(investigator)
                    )
                )
                for investigator in new_proposal.investigators
            ],
        )
        info_log.info(msg=f"The proposal investigators of {old_proposal.proposal_code} have been updated. There were {len(old_proposal.investigators)} investigators before, and there are {len(new_proposal.investigators)} now.")


def update_salt_position_owner_ids(new_proposal: types.SALTProposalDetails, ssda_database_service: SSDADatabaseService) -> None:
    proposal_id = ssda_database_service.find_proposal_id(
        proposal_code=new_proposal.proposal_code,
        institution=types.Institution.SALT
    )
    owner_ids = find_salt_position_owner_ids(proposal_id, new_proposal.data_release, ssda_database_service)

    sql = """
    WITH plane_ids (id) AS (
         SELECT pln.plane_id
         FROM plane pln
         JOIN observation obs ON pln.observation_id = obs.observation_id
         WHERE obs.proposal_id='%(proposal_id)s'
    )
    UPDATE position SET owner_institution_user_ids=%(owner_ids)s
    WHERE plane_id IN (SELECT * FROM plane_ids)
    """

    with ssda_database_service.connection().cursor() as cur:
        cur.execute(sql, dict(proposal_id=proposal_id, owner_ids=owner_ids))
        info_log.info(msg=f"{cur.rowcount} positions of {new_proposal.proposal_code} have been updated to have {len(owner_ids) if owner_ids else 'no'} owner ids.")


def update_salt_observation_group_status_values(old_proposal: types.SALTProposalDetails, new_proposal: types.SALTProposalDetails, ssda_database_service: SSDADatabaseService, sdb_database_service: SaltDatabaseService) -> None:
    check_proposal_code_consistency(old_proposal, new_proposal)
    new_observation_groups = sdb_database_service.find_proposal_observation_groups(
        proposal_code=old_proposal.proposal_code
    )
    old_observation_groups = ssda_database_service.find_salt_observation_group(old_proposal.proposal_code)
    for group_identifier, old_observation_group in old_observation_groups.items():
        if group_identifier not in new_observation_groups:
            continue
        new_observation_group = new_observation_groups[group_identifier]
        if new_observation_group != old_observation_group:
            ssda_database_service.update_observation_group_status(
                group_identifier=group_identifier,
                telescope=types.Telescope.SALT,
                status=new_observation_group.status
            )
            info_log.info(msg=f'The status of the observation group with group identifier {group_identifier} has been updated from '
                              f'{old_observation_group.status.value} to {new_observation_group.status.value}.')


def check_proposal_code_consistency(proposal1: types.SALTProposalDetails, proposal2: types.SALTProposalDetails):
    if not proposal1.proposal_code:
        raise ValueError("Proposal 1 has no proposal code.")
    if proposal1.proposal_code != proposal2.proposal_code:
        raise ValueError(f'The proposal codes differ ("{proposal1.proposal_code}"; "{proposal2.proposal_code}").')


def find_salt_position_owner_ids(proposal_id: int, release_date: date, ssda_database_service: SSDADatabaseService) -> List[int]:
    if release_date < datetime.now().date():
        return None

    sql = """
    SELECT array_agg(pi.institution_user_id)
    FROM proposal_investigator pi
    WHERE proposal_id=%(proposal_id)s
    """
    with ssda_database_service.connection().cursor() as cur:
        cur.execute(sql, dict(proposal_id=proposal_id))
        return cur.fetchone()[0]
