from typing import Optional

from ssda.util import types


class DatabaseService:
    """
    Access to the database.

    """

    def __init__(self, database_config: types.DatabaseConfiguration):
        pass

    def begin_transaction(self):
        raise NotImplementedError

    def commit_transaction(self):
        raise NotImplementedError

    def find_observation_id(self, artifact_name: str):
        raise NotImplementedError

    def find_proposal_id(self, proposal_code: str, institution: types.Institution) -> Optional[int]:
        raise NotImplementedError

    def insert_artifact(self, artifact: types.Artifact) -> int:
        raise NotImplementedError

    def insert_energy(self, energy: types.Energy) -> int:
        raise NotImplementedError

    def insert_instrument_keyword_value(self, instrument_keyword_value: types.InstrumentKeywordValue) -> int:
        raise NotImplementedError

    def insert_observation(self, observation: types.Observation) -> int:
        raise NotImplementedError

    def insert_observation_time(self, observation_time: types.ObservationTime):
        raise NotImplementedError

    def insert_polarization(self, polarization: types.Polarization) -> int:
        raise NotImplementedError

    def insert_plane(self, plane: types.Plane):
        raise NotImplementedError

    def insert_position(self, position: types.Position) -> int:
        raise NotImplementedError

    def insert_proposal(self, proposal: types.Proposal) -> int:
        raise NotImplementedError

    def insert_proposal_investigator(self, proposal_investigator: types.ProposalInvestigator) -> int:
        raise NotImplementedError

    def insert_target(self, target: types.Target) -> int:
        raise NotImplementedError

    def rollback_transaction(self):
        raise NotImplementedError

