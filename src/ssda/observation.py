from abc import ABC
from typing import List, Optional

from ssda.util import types
from ssda.util.fits import FitsFile


class ObservationProperties(ABC):
    """
    Properties of an observation.

    The methods of this class return objects that correspond to database tables to be
    populated.

    """

    def artifact(self, plane_id: int) -> types.Artifact:
        raise NotImplementedError

    def energy(self, plane_id: int) -> Optional[types.Energy]:
        raise NotImplementedError

    def instrument_keyword_values(
        self, observation_id: int
    ) -> List[types.InstrumentKeywordValue]:
        raise NotImplementedError

    def observation(self, proposal_id: Optional[int]) -> types.Observation:
        raise NotImplementedError

    def observation_time(self, plane_id: int) -> types.ObservationTime:
        raise NotImplementedError

    def plane(self, observation_id: int) -> types.Plane:
        raise NotImplementedError

    def polarizations(self, plane_id: int) -> List[types.Polarization]:
        raise NotImplementedError

    def position(self, plane_id: int) -> Optional[types.Position]:
        raise NotImplementedError

    def proposal(self) -> Optional[types.Proposal]:
        raise NotImplementedError

    def proposal_investigators(
        self, proposal_id: int
    ) -> List[types.ProposalInvestigator]:
        raise NotImplementedError

    def target(self, observation_id: int) -> Optional[types.Target]:
        raise NotImplementedError


class StandardObservationProperties(ObservationProperties):
    def __init__(self, fits_file: FitsFile):
        pass
