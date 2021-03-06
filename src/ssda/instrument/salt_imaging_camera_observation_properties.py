from ssda.database.sdb import SaltDatabaseService
from ssda.observation import ObservationProperties
from ssda.util import types
from ssda.util.salt_energy_calculation import salt_imaging_camera_spectral_properties
from ssda.util.salt_observation import SALTObservation
from ssda.util.fits import FitsFile
from typing import Optional, List


class SaltImagingCameraObservationProperties(ObservationProperties):
    def __init__(self, fits_file: FitsFile, database_service: SaltDatabaseService):
        self.file_path = fits_file.file_path()
        self.header_value = fits_file.header_value
        self.instrument = fits_file.instrument()
        self.database_service = database_service
        self.salt_observation = SALTObservation(
            fits_file=fits_file, database_service=database_service
        )

    def access_rule(self) -> Optional[types.AccessRule]:
        return self.salt_observation.access_rule()

    def artifact(self, plane_id: int) -> types.Artifact:
        return self.salt_observation.artifact(plane_id)

    def energy(self, plane_id: int) -> Optional[types.Energy]:
        if self.salt_observation.is_calibration():
            return None
        filter_header_value = self.header_value("FILTER")
        filter_name = filter_header_value if filter_header_value else ""
        return salt_imaging_camera_spectral_properties(
            plane_id, filter_name, self.instrument
        )

    def ignore_observation(self) -> bool:
        return self.salt_observation.ignore_observation()

    def instrument_keyword_values(
        self, observation_id: int
    ) -> List[types.InstrumentKeywordValue]:
        return []  # TODO Needs to be implemented

    def instrument_setup(self, observation_id: int) -> types.InstrumentSetup:
        queries: List[types.SQLQuery] = []

        detmode_header_value = self.header_value("DETMODE")
        detector_mode = types.DetectorMode.for_name(
            detmode_header_value if detmode_header_value else ""
        )

        filter_header_value = self.header_value("FILTER")
        filter = types.Filter.for_name(
            filter_header_value if filter_header_value else ""
        )

        return types.InstrumentSetup(
            additional_queries=queries,
            detector_mode=detector_mode,
            filter=filter,
            instrument_mode=types.InstrumentMode.IMAGING,
            observation_id=observation_id,
        )

    def observation(
        self, observation_group_id: Optional[int], proposal_id: Optional[int]
    ) -> types.Observation:
        raise NotImplementedError

    def observation_group(self) -> Optional[types.ObservationGroup]:
        return self.salt_observation.observation_group()

    def observation_time(self, plane_id: int) -> types.ObservationTime:
        return self.salt_observation.observation_time(plane_id)

    def plane(self, observation_id: int) -> types.Plane:
        return types.Plane(
            observation_id, data_product_type=types.DataProductType.IMAGE
        )

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
        return self.salt_observation.target(observation_id=observation_id)
