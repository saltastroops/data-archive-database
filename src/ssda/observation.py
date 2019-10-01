from abc import ABC
from typing import List, Optional

from ssda.instrument.hrs_observation_properties import HrsObservationProperties
from ssda.instrument.instrument import Instrument
from ssda.instrument.rss_observation_properties import RssObservationProperties
from ssda.instrument.salticam_observation_properties import SalticamObservationProperties
from ssda.util import types
from ssda.util.fits import FitsFile
from ssda.util.salt_observation import SaltDatabaseService


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

    def observation(self, proposal_id: Optional[int]):
        raise NotImplementedError

    def observation_time(self, plane_id: int) -> types.ObservationTime:
        raise NotImplementedError

    def plane(self, observation_id: int) -> types.Plane:
        raise NotImplementedError

    def polarizations(self, plane_id: int) -> List[types.Polarization]:
        raise NotImplementedError

    def position(self, plane_id: int) -> types.Position:
        raise NotImplementedError

    def proposal(self) -> Optional[types.Proposal]:
        raise NotImplementedError

    def proposal_investigators(
        self, proposal_id: int
    ) -> List[types.ProposalInvestigator]:
        raise NotImplementedError

    def target(self, observation_id: int) -> types.Target:
        raise NotImplementedError


class StandardObservationProperties(ObservationProperties):
    def __init__(self, fits_file: FitsFile):
        if fits_file.instrument() == Instrument.RSS:
            self.salt_database_service = SaltDatabaseService(None)
            self._observation_properties = RssObservationProperties(fits_file, self.salt_database_service)

        if fits_file.instrument() == Instrument.HRS:
            self.salt_database_service = SaltDatabaseService(None)
            self._observation_properties = HrsObservationProperties(fits_file, self.salt_database_service)

        if fits_file.instrument() == Instrument.SALTICAM:
            self.salt_database_service = SaltDatabaseService(None)
            self._observation_properties = SalticamObservationProperties(fits_file, self.salt_database_service)

    def artifact(self, plane_id: int) -> types.Artifact:
        return self._observation_properties.artifact(plane_id)

    def energy(self, plane_id: int) -> Optional[types.Energy]:
        return self._observation_properties.energy(plane_id)

    def instrument_keyword_values(
            self, observation_id: int
    ) -> List[types.InstrumentKeywordValue]:
        return self._observation_properties.instrument_keyword_values(observation_id)

    def observation(self, proposal_id: Optional[int]):
        return self._observation_properties.observation(proposal_id)

    def observation_time(self, plane_id: int) -> types.ObservationTime:
        return self._observation_properties.observation_time(plane_id)

    def plane(self, observation_id: int) -> types.Plane:
        return self._observation_properties.plane(observation_id)

    def polarizations(self, plane_id: int) -> List[types.Polarization]:
        return self._observation_properties.polarizations(plane_id)

    def position(self, plane_id: int) -> types.Position:
        return self._observation_properties.position(plane_id)

    def proposal(self) -> Optional[types.Proposal]:
        return self._observation_properties.proposal()

    def proposal_investigators(
            self, proposal_id: int
    ) -> List[types.ProposalInvestigator]:
        return self._observation_properties.proposal_investigators(proposal_id)

    def target(self, observation_id: int) -> types.Target:
        return self._observation_properties.target(observation_id)


class DummyObservationProperties(ObservationProperties):
    pass
