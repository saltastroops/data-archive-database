import datetime
from typing import Optional, List

from ssda.util import types


class DatabaseService:
    """
    Access to the database.

    """

    def __init__(self, database_config: types.DatabaseConfiguration):
        pass

    def begin_transaction(self) -> None:
        """
        Start a transaction.

        """

        raise NotImplementedError

    def commit_transaction(self) -> None:
        """
        Commit the current transaction.

        """

        raise NotImplementedError

    def find_observation_id(self, artifact_name: str) -> Optional[int]:
        """
        Find the database id of an observation.

        Parameters
        ----------
        artifact_name : str
            Name of an artifact for the observation.

        Returns
        -------
        Optional[int]
            The database id of the observation, or None if there is no observation for
            the artifact name.

        """

        raise NotImplementedError

    def find_proposal_id(
        self, proposal_code: str, institution: types.Institution
    ) -> Optional[int]:
        """
        Find the database id of a proposal.

        Parameters
        ----------
        proposal_code : str
            Proposal code.
        institution
            Institution to which the proposal was submitted.

        Returns
        -------
        Optional[int]
            The database id of the proposal, or None if there is no proposal for the
            proposal code abd institution.

        """

        raise NotImplementedError

    @staticmethod
    def find_identifier(identifier: str) -> Optional[str]:
        # Todo search data base if Identifier exist
        return None

    def insert_artifact(self, artifact: types.Artifact) -> int:
        """
        Insert an artifact.

        Parameters
        ----------
        artifact : Artifact
            Artifact.

        Returns
        -------
        int
            Database id of the inserted artifact.

        """

        raise NotImplementedError

    def insert_energy(self, energy: Optional[types.Energy]) -> Optional[int]:
        """
        Insert spectral details.

        Nothing is done and None is returned if None is passed as the energy argument.

        Parameters
        ----------
        energy : Optional[Energy]
            Spectral details.

        Returns
        -------
        Optional[int]
            Database id of the inserted spectral details, or None if None is passed as
            energy argument.

        """

        raise NotImplementedError

    def insert_instrument_keyword_value(
        self, instrument_keyword_value: types.InstrumentKeywordValue
    ) -> int:
        """
        Insert an instrument keyword value.

        Parameters
        ----------
        instrument_keyword_value : InstrumentKeywordValue
            Instrument keyword value.

        Returns
        -------
        int
            Database id of the inserted instrument keyword value.

        """

        raise NotImplementedError

    def insert_observation(self, observation: types.Observation) -> int:
        """
        Insert an observation.

        Parameters
        ----------
        observation : Observation
            Observation.

        Returns
        -------
        int
            The database id of the inserted observation.

        """

        raise NotImplementedError

    def insert_observation_time(self, observation_time: types.ObservationTime) -> int:
        """
        Insert an observation time.

        Parameters
        ----------
        observation_time : ObservationTime
            Observation time.

        Returns
        -------
        The database id of the inserted observation time.

        """

        raise NotImplementedError

    def insert_polarization(self, polarization: types.Polarization) -> int:
        """
        Insert a polarization.

        Parameters
        ----------
        polarization : Polarization
            Polarization.

        Returns
        -------
        The database id of the inserted polarization.

        """

        raise NotImplementedError

    def insert_plane(self, plane: types.Plane) -> int:
        """
        Insert a plane.

        Parameters
        ----------
        plane : Plane
            Plane.

        Returns
        -------
        int
            The database id of the inserted plane.

        """

        raise NotImplementedError

    def insert_position(self, position: types.Position) -> int:
        """
        Inert a position.

        Parameters
        ----------
        position : Position
            Position.

        Returns
        -------
        int
            The database id of the inserted position.

        """

        raise NotImplementedError

    def insert_proposal(self, proposal: types.Proposal) -> int:
        """
        Insert a proposal.

        Parameters
        ----------
        proposal : proposal
            Proposal.

        Returns
        -------
        int
            The database id of the inserted proposal.

        """

        raise NotImplementedError

    def insert_proposal_investigator(
        self, proposal_investigator: types.ProposalInvestigator
    ) -> int:
        """
        Insert a proposal investigator.

        Parameters
        ----------
        proposal_investigator : ProposalInvestigator
            Proposal investigator.

        Returns
        -------
        int
            The database id of the inserted proposal investigator.

        """

        raise NotImplementedError

    def insert_target(self, target: types.Target) -> int:
        """
        Insert a target.

        Parameters
        ----------
        target : Target
            Target.

        Returns
        -------
        int
            The database id of the inserted target.

        """

        raise NotImplementedError

    def rollback_transaction(self) -> None:
        """
        Roll back the changes made during the current transaction.

        """

        raise NotImplementedError


class SaltDatabaseService:
    def __init__(self, database_config: types.DatabaseConfiguration):
        pass

    def find_pi(self, block_visit: str) -> Optional[str]:
        return

    def find_proposal_code(self, block_visit: str) -> Optional[str]:
        return

    def find_proposal_title(self, block_visit: str) -> Optional[str]:
        return

    def find_observation_status(self, block_visit_id: str) -> types.Status:
        obs_status = block_visit_id

        if obs_status == "":
            return types.Status.ACCEPTED
        else:
            return types.Status.REJECTED

    def find_release_date(self, block_visit_id: str) -> datetime.datetime:
        # Todo search data base if Identifier exist
        return datetime.datetime.now()

    def find_meta_release_date(self, block_visit_id: str) -> datetime.datetime:
        # Todo search data base if Identifier exist
        return datetime.datetime.now()

    def find_proposal_investigators(self, block_visit_id: str) -> List[int]:
        # Todo search data base if Identifier exist
        return [1]
