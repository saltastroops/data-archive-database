from ssda.database.sdb import SaltDatabaseService
# from ssda.observation import ObservationProperties
from ssda.util import types
from ssda.util.energy_cal import salticam_spectral_properties
from ssda.util.salt_observation import SALTObservation
from ssda.util.fits import FitsFile
from typing import Optional, List


class SalticamObservationProperties:
    """
    The Salticam Observation Properties.
    This class should be implementing ObservationProperties but it doesn't need all the methods.
    """

    def __init__(self, fits_file: FitsFile, database_service: SaltDatabaseService):
        """
        :param fits_file:
        """
        self.header_value = fits_file.header_value
        self.file_path = fits_file.file_path()
        self.database_service = database_service
        self.salt_observation = SALTObservation(
            fits_file=fits_file,
            database_service=database_service
        )

    def artifact(self, plane_id: int) -> types.Artifact:
        return self.salt_observation.artifact(plane_id)

    def energy(self, plane_id: int) -> Optional[types.Energy]:
        if self.salt_observation.is_calibration():
            return None
        filter_name = self.header_value("FILTER")
        return salticam_spectral_properties(plane_id, filter_name)

    def instrument_keyword_values(self, observation_id: int) -> List[types.InstrumentKeywordValue]:
        return []  # TODO Needs to be implemented

    def instrument_setup(self,  observation_id: int) -> types.InstrumentSetup:
        queries = []

        detector_mode = None
        for dm in types.DetectorMode:
            if self.header_value("DETMODE").upper() == dm.value.upper():
                detector_mode = dm
        if self.header_value("DETMODE").upper() == "SLOT":
            detector_mode = types.DetectorMode.SLOT_MODE
        filter = None
        for fi in types.Filter:
            if self.header_value("FILTER") == fi.value:
                filter = fi

        return types.InstrumentSetup(
            additional_queries=queries,
            detector_mode=detector_mode,
            filter=filter,
            instrument_mode=types.InstrumentMode.IMAGING,
            observation_id=observation_id
        )

    def observation(self,  observation_group_id: Optional[int], proposal_id: Optional[int]) -> types.Observation:
        return self.salt_observation.observation(
            observation_group_id=observation_group_id,
            proposal_id=proposal_id,
            instrument=types.Instrument.SALTICAM)

    def observation_group(self) -> Optional[types.ObservationGroup]:
        return self.salt_observation.observation_group()

    def observation_time(self, plane_id: int) -> types.ObservationTime:
        return self.salt_observation.observation_time(plane_id)

    def plane(self, observation_id: int) -> types.Plane:
        return types.Plane(observation_id, data_product_type=types.DataProductType.IMAGE)

    def polarization(self, plane_id: int) -> Optional[types.Polarization]:
        return None

    def position(self, plane_id: int) -> Optional[types.Position]:
        return self.salt_observation.position(plane_id=plane_id)

    def proposal(self) -> Optional[types.Proposal]:
        return self.salt_observation.proposal()

    def proposal_investigators(
            self, proposal_id: int
    ) -> List[types.ProposalInvestigator]:
        return self.salt_observation.proposal_investigators(proposal_id=proposal_id)

    def target(self, observation_id: int) -> Optional[types.Target]:
        proposal_id = self.header_value("PROPID")
        if proposal_id.upper() == "CAL_BIAS" or \
                proposal_id.upper() == "CAL_FLAT" or \
                proposal_id.upper() == "CAL_ARC":
            return None
        return self.salt_observation.target(observation_id=observation_id)
