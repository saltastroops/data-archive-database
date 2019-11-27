from ssda.database.sdb import SaltDatabaseService
from ssda.util import types
from ssda.util.energy_cal import hrs_spectral_properties
from ssda.util.salt_observation import SALTObservation
from ssda.util.fits import FitsFile
from typing import Optional, List


class HrsObservationProperties:

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

        filename = str(os.path.basename(self.file_path))
        arm = types.HRSArm.RED if filename[0] == "R" else types.HRSArm.BLUE if filename[0] == "H" else None
        if not arm:
            raise ValueError("Unknown arm.")
        resolution = self._mode()
        return hrs_spectral_properties(plane_id, arm, resolution)

    def instrument_keyword_values(self, observation_id: int) -> List[types.InstrumentKeywordValue]:
        return []  # TODO Needs to be implemented

    def instrument_setup(self,  observation_id: int) -> types.InstrumentSetup:
        hrs_mode = self._mode()

        sql = """
        WITH hm (id) AS (
            SELECT hrs_mode_id FROM hrs_mode WHERE hrs_mode.hrs_mode=%(hrs_mode)s
        )
        INSERT INTO hrs_setup (instrument_setup_id, hrs_mode_id)
        VALUES (%(instrument_setup_id)s, (SELECT id FROM hm))
        """
        parameters = dict(hrs_mode=hrs_mode.value)
        queries = [types.SQLQuery(sql=sql, parameters=parameters)]

        detector_mode = None
        for dm in types.DetectorMode:
            if self.header_value("DETMODE").strip() == dm.value:
                detector_mode = dm
        if not detector_mode:
            raise ValueError(f"Detector mode of file {self.file_path} is not recognised")

        return types.InstrumentSetup(
            additional_queries=queries,
            detector_mode=detector_mode,
            filter=None,
            instrument_mode=types.InstrumentMode.SPECTROSCOPY,
            observation_id=observation_id
        )

    def observation(self, observation_group_id: Optional[int], proposal_id: Optional[int]) -> types.Observation:
        return self.salt_observation.observation(observation_group_id=observation_group_id,
                                                 proposal_id=proposal_id,
                                                 instrument=types.Instrument.HRS)

    def observation_group(self) -> Optional[types.ObservationGroup]:
        return self.salt_observation.observation_group()

    def observation_time(self, plane_id: int) -> types.ObservationTime:
        return self.salt_observation.observation_time(plane_id)

    def plane(self, observation_id: int) -> types.Plane:
        return types.Plane(observation_id, data_product_type=types.DataProductType.SPECTRUM)

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

    def _mode(self) -> types.HRSMode:
        observation_mode = self.header_value("OBSMODE")
        if observation_mode == "LOW RESOLUTION":
            return types.HRSMode.LOW_RESOLUTION
        if observation_mode == "MEDIUM RESOLUTION":
            return types.HRSMode.MEDIUM_RESOLUTION
        if observation_mode == "HIGH RESOLUTION":
            return types.HRSMode.HIGH_RESOLUTION
        if observation_mode == "HIGH STABILITY":
            return types.HRSMode.HIGH_STABILITY
        raise ValueError(f"Unknown resolution {resolution.value}")
