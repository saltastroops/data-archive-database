from abc import ABC
from typing import List, Optional

from ssda.util import types


class ObservationProperties(ABC):
    """
    Properties of an observation.

    The methods of this class return objects that correspond to database tables to be
    populated.

    """

    def artifact(self, plane_id: int) -> types.Artifact:
        raise NotImplemented

    def energy(self, plane_id: int) -> types.Energy:
        raise NotImplemented

    def instrument_keyword_values(self, observation_id) -> List[types.InstrumentKeywordValue]:
        raise NotImplemented

    def observation(self, proposal_id: Optional[int]) -> types.Observation:
        raise NotImplemented

    def observation_time(self, plane_id: int) -> types.ObservationTime:
        raise NotImplemented

    def plane(self, observation_id: int) -> types.Plane:
        raise NotImplemented

    def polarizations(self, plane_id: int) -> List[types.Polarization]:
        raise NotImplemented

    def position(self, plane_id: int) -> types.Position:
        raise NotImplemented

    def proposal(self) -> Optional[types.Proposal]:
        raise NotImplemented

    def target(self) -> types.Target:
        raise NotImplemented



class StandardObservationProperties(ObservationProperties):
    pass


class DummyObservationProperties(ObservationProperties):
    pass
