import click
from datetime import date, datetime
import logging
from sentry_sdk import capture_exception
from ssda.database.sdb import SaltDatabaseService
from ssda.database.ssda import SSDADatabaseService
from ssda.util.databases import database_services as db_services
from ssda.util import types
from ssda.util.setup_logger import setup_logger
from typing import Dict, List, Optional


logging.root.setLevel(logging.INFO)

info_log = setup_logger(
    "info_logger",
    "ssda_sync_info.log",
    logging.Formatter("%(asctime)s %(levelname)s - %(message)s"),
)
error_log = setup_logger(
    "error_logger",
    "ssda_sync_error.log",
    logging.Formatter("%(asctime)s %(levelname)s\n%(message)s"),
)


@click.command()
def sync() -> int:
    """
    Synchronise the SSDA database with telescope databases such as the SALT Science
    Database.

    """

    logging.basicConfig(level=logging.INFO)
    logging.error("SALT is always assumed to be the telescope.")

    database_services = db_services()
    ssda_database_service = database_services.ssda
    sdb_database_service = database_services.sdb

    # Compare proposal and update
    update_salt_proposals(ssda_database_service, sdb_database_service)

    info_log.info(msg=f"SSDA sync script ran.")
    # Success!
    return 0


def update_salt_proposals(ssda_database_service: SSDADatabaseService, sdb_database_service: SaltDatabaseService):
    """
    Update the SALT proposals in the Data Archive.

    The updates for an individual proposal are done within a database transaction, so
    for an individual proposal either no or all updates are made. However, the failure
    to update a proposal does not lead to a rollback of the updates for other proposals.

    Parameters
    ----------
    ssda_database_service : SSDADatabaseService
        SSDA database service.
    sdb_database_service : SaltDatabaseService
        SDB database service.

    """

    sdb_proposals = sdb_database_service.find_phase2_proposals(date(2010, 1, 1))
    ssda_proposals = ssda_database_service.find_salt_proposal_details()

    sanitize_gwe_proposal_release_dates(ssda_proposals, sdb_proposals)

    proposal_synchronisation = SaltProposalSynchronisation(ssda_database_service, sdb_database_service)
    for proposal_code, ssda_proposal in ssda_proposals.items():
        ssda_database_service.begin_transaction()
        try:
            sdb_proposal = sdb_proposals[proposal_code]
            proposal_synchronisation.update_proposal(
                old_proposal=ssda_proposal,
                new_proposal=sdb_proposal
            )
            ssda_database_service.commit_transaction()
        except BaseException as e:
            ssda_database_service.rollback_transaction()
            capture_exception(e)
            error_log.error(
                """____________________________________________________________________________________________________________
            """,
                exc_info=True,
            )


def sanitize_gwe_proposal_release_dates(old_proposals: Dict[str, types.SALTProposalDetails], new_proposals: Dict[str, types.SALTProposalDetails]):
    """
    Sanitize the metadata release dates of gravitational wave proposals.

    The metadata release date of gravitational wave proposals is set to the current
    date and should not be updated.

    Parameters
    ----------
    old_proposals : Dict[str, types.SALTProposalDetails]
        Old proposal details.
    new_proposals L Dict[str, types.SALTProposalDetails]
        New proposal details.

    """

    for proposal_code in new_proposals:
        if proposal_code in old_proposals:
            if 'GWE' in proposal_code:
                new_proposals[proposal_code].meta_release = old_proposals[proposal_code].meta_release


class SaltProposalSynchronisation:
    """
    Synchronise proposal details between the SALT Science Database and the data archive
    database.

    Parameters
    ----------
    ssda_database_service : SSDADatabaseService
        SSDA database service.
    sdb_database_service : SaltDatabaseService
        SDB database service.

    """

    def __init__(self, ssda_database_service: SSDADatabaseService, sdb_database_service: SaltDatabaseService):
        self.ssda_database_service = ssda_database_service
        self.sdb_database_service = sdb_database_service

    def update_proposal(
        self,
        old_proposal: types.SALTProposalDetails,
        new_proposal: types.SALTProposalDetails
    ):
        """
        Update the details for a proposal.

        Parameters
        ----------
        old_proposal : SALTProposalDetails
            Old proposal details.
        new_proposal : SALTProposalDetails
            New proposal details.

        """

        self._update_proposal_pi(old_proposal, new_proposal)
        self._update_proposal_title(old_proposal, new_proposal)
        self._update_release_dates(old_proposal, new_proposal)
        self._update_proposal_investigators(old_proposal, new_proposal)
        self._update_position_owner_ids(old_proposal, new_proposal)
        self._update_observation_groups(old_proposal, new_proposal)

    def _update_proposal_pi(
            self,
        old_proposal: types.SALTProposalDetails,
        new_proposal: types.SALTProposalDetails,
    ) -> None:
        """
        Update the Principal Investigator of a proposal.

        Parameters
        ----------
        old_proposal : SALTProposalDetails
            Old proposal details.
        new_proposal : SALTProposalDetails
            New proposal details.

        """

        self.check_proposal_code_consistency(old_proposal, new_proposal)
        proposal_code = old_proposal.proposal_code
        if new_proposal.pi != old_proposal.pi:
            proposal_id = self.ssda_database_service.find_proposal_id(
                proposal_code=proposal_code, institution=types.Institution.SALT
            )
            self.ssda_database_service.update_pi(proposal_id=proposal_id, pi=new_proposal.pi)
            info_log.info(
                msg=f'The PI of {proposal_code} has been changed from "{old_proposal.pi}" to "{new_proposal.pi}".'
            )

    def _update_proposal_title(
            self,
        old_proposal: types.SALTProposalDetails,
        new_proposal: types.SALTProposalDetails,
    ):
        """
        Update the proposal title.

        Parameters
        ----------
        old_proposal : SALTProposalDetails
            Old proposal details.
        new_proposal : SALTProposalDetails
            New proposal details.

        """

        self.check_proposal_code_consistency(old_proposal, new_proposal)
        proposal_code = old_proposal.proposal_code
        if new_proposal.title != old_proposal.title:
            proposal_id = self.ssda_database_service.find_proposal_id(
                proposal_code=proposal_code, institution=types.Institution.SALT
            )
            self.ssda_database_service.update_proposal_title(
                proposal_id=proposal_id, title=new_proposal.title
            )
            info_log.info(
                msg=f'The title of {proposal_code} has been changed from "{old_proposal.title}" to "{new_proposal.title}".'
            )

    def _update_release_dates(
            self,
        old_proposal: types.SALTProposalDetails,
        new_proposal: types.SALTProposalDetails,
    ) -> None:
        """
        Update the data and metadata release date.

        Parameters
        ----------
        old_proposal : SALTProposalDetails
            Old proposal details.
        new_proposal : SALTProposalDetails
            New proposal details.

        """

        self.check_proposal_code_consistency(old_proposal, new_proposal)
        proposal_code = old_proposal.proposal_code
        if (
            old_proposal.data_release != new_proposal.data_release
            or old_proposal.meta_release != new_proposal.meta_release
        ):
            proposal_id = self.ssda_database_service.find_proposal_id(
                proposal_code=proposal_code, institution=types.Institution.SALT
            )
            self.ssda_database_service.update_proposal_release_date(
                proposal_id=proposal_id,
                release_dates=types.ReleaseDates(
                    meta_release=new_proposal.meta_release,
                    data_release=new_proposal.data_release,
                ),
            )
            info_log.info(
                msg=f"The data release date of {proposal_code} has been changed from {old_proposal.data_release.strftime('%Y-%m-%d')} to {new_proposal.data_release.strftime('%Y-%m-%d')}"
            )
            info_log.info(
                msg=f"The metadata release date of {proposal_code} has been changed from {old_proposal.meta_release.strftime('%Y-%m-%d')} to {new_proposal.meta_release.strftime('%Y-%m-%d')}"
            )

    def _update_proposal_investigators(
            self,
        old_proposal: types.SALTProposalDetails,
        new_proposal: types.SALTProposalDetails,
    ) -> None:
        """
        Update the proposal investigators.

        Parameters
        ----------
        old_proposal : SALTProposalDetails
            Old proposal details.
        new_proposal : SALTProposalDetails
            New proposal details.

        """

        self.check_proposal_code_consistency(old_proposal, new_proposal)
        proposal_code = old_proposal.proposal_code
        if set(new_proposal.investigators) != set(old_proposal.investigators):
            proposal_id = self.ssda_database_service.find_proposal_id(
                proposal_code=proposal_code, institution=types.Institution.SALT
            )
            self.ssda_database_service.update_investigators(
                proposal_code=proposal_code,
                institution=new_proposal.institution,
                proposal_investigators=[
                    types.ProposalInvestigator(
                        proposal_id=proposal_id,
                        investigator_id=str(investigator),
                        institution=types.Institution.SALT,
                        institution_memberships=self.sdb_database_service.institution_memberships(
                            int(investigator)
                        ),
                    )
                    for investigator in new_proposal.investigators
                ],
            )
            info_log.info(
                msg=f"The proposal investigators of {proposal_code} have been updated. There were {len(old_proposal.investigators)} investigators before, and there are {len(new_proposal.investigators)} now."
            )

    def _update_position_owner_ids(
            self,
            old_proposal: types.SALTProposalDetails,
            new_proposal: types.SALTProposalDetails
    ) -> None:
        """
        Update the position owner ids.

        Parameters
        ----------
        new_proposal : SALTProposalDetails
            New proposal details.

        """

        self.check_proposal_code_consistency(old_proposal, new_proposal)
        proposal_code = old_proposal.proposal_code

        if old_proposal.data_release != new_proposal.data_release or set(old_proposal.investigators) != set(new_proposal.investigators):
            proposal_id = self.ssda_database_service.find_proposal_id(
                proposal_code=new_proposal.proposal_code, institution=types.Institution.SALT
            )
            owner_ids = self.find_position_owner_ids(
                proposal_id, new_proposal.data_release
            )

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

            with self.ssda_database_service.connection().cursor() as cur:
                cur.execute(sql, dict(proposal_id=proposal_id, owner_ids=owner_ids))
                info_log.info(
                    msg=f"{cur.rowcount} positions of {new_proposal.proposal_code} have been updated to have {len(owner_ids) if owner_ids else 'no'} owner ids."
                )

    def _update_observation_groups(
            self,
        old_proposal: types.SALTProposalDetails,
        new_proposal: types.SALTProposalDetails,
    ) -> None:
        """
        Update the status of the observation groups.

        Parameters
        ----------
        old_proposal : SALTProposalDetails
            Old proposal details.
        new_proposal : SALTProposalDetails
            New proposal details.

        Returns
        -------

        """
        self.check_proposal_code_consistency(old_proposal, new_proposal)
        proposal_code = old_proposal.proposal_code
        new_observation_groups = self.sdb_database_service.find_proposal_observation_groups(
            proposal_code=proposal_code
        )
        old_observation_groups = self.ssda_database_service.find_salt_observation_group(
            proposal_code
        )
        for group_identifier, old_observation_group in old_observation_groups.items():
            if group_identifier not in new_observation_groups:
                continue
            new_observation_group = new_observation_groups[group_identifier]
            self.update_observation_group(old_observation_group,
                                          new_observation_group)

    def update_observation_group(self, old_observation_group: types.SALTObservationGroup, new_observation_group: types.SALTObservationGroup):
        """
        Update the details of an observation group.

        Parameters
        ----------
        old_observation_group : SALTObservationGroup
            Old observation group details.
        new_observation_group : SALTObservationGroup
            New observation group details.

        """

        if old_observation_group.group_identifier is None or old_observation_group.group_identifier != new_observation_group.group_identifier:
            raise ValueError("The old and new observation group must have the same "
                             "group identifier, which must not be None.")
        group_identifier = old_observation_group.group_identifier

        if new_observation_group != old_observation_group:
            self.ssda_database_service.update_observation_group_status(
                group_identifier=group_identifier,
                telescope=types.Telescope.SALT,
                status=new_observation_group.status,
            )
            info_log.info(
                msg=f"The status of the observation group with group identifier {group_identifier} has been updated from "
                    f"{old_observation_group.status.value} to {new_observation_group.status.value}."
            )

    def find_position_owner_ids(
            self,
        proposal_id: int, data_release: date
    ) -> Optional[List[int]]:
        """
        Find the position owner ids.

        Parameters
        ----------
        proposal_id : int
            Proposal id.
        data_release : date
            Data release date.

        """

        # public data has no owner
        if data_release < datetime.now().date():
            return None

        sql = """
        SELECT array_agg(pi.institution_user_id)
        FROM proposal_investigator pi
        WHERE proposal_id=%(proposal_id)s
        """
        with self.ssda_database_service.connection().cursor() as cur:
            cur.execute(sql, dict(proposal_id=proposal_id))
            return cur.fetchone()[0]

    @staticmethod
    def check_proposal_code_consistency(
            proposal1: types.SALTProposalDetails, proposal2: types.SALTProposalDetails
    ):
        """
        Check whether two proposals have the same non-null proposal code, and raise an
        error if they don't.

        Parameters
        ----------
        proposal1 : SALTProposalDetails
            First proposal (details).
        proposal2 : SALTProposalDetails
            Second proposal (details).

        """

        if not proposal1.proposal_code:
            raise ValueError("Proposal 1 has no proposal code.")
        if proposal1.proposal_code != proposal2.proposal_code:
            raise ValueError(
                f'The proposal codes differ ("{proposal1.proposal_code}"; "{proposal2.proposal_code}").'
            )
