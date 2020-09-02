import os

from ssda.database.sdb import SaltDatabaseService
from ssda.observation import ObservationProperties
from ssda.util import types
from ssda.util.salt_energy_calculation import hrs_spectral_properties
from ssda.util.salt_observation import SALTObservation
from ssda.util.fits import FitsFile
from typing import Optional, List


class HrsObservationProperties(ObservationProperties):
    def __init__(self, fits_file: FitsFile, database_service: SaltDatabaseService):
        self.header_value = fits_file.header_value
        self.file_path = fits_file.file_path()
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

        filename = str(os.path.basename(self.file_path))
        arm = (
            types.HRSArm.RED
            if filename[0] == "R"
            else types.HRSArm.BLUE
            if filename[0] == "H"
            else None
        )
        if not arm:
            raise ValueError("Unknown arm.")
        hrs_mode = self._mode()
        return hrs_spectral_properties(plane_id, arm, hrs_mode)

    def ignore_observation(self) -> bool:
        return self.salt_observation.ignore_observation()

    def instrument_keyword_values(
        self, observation_id: int
    ) -> List[types.InstrumentKeywordValue]:
        return []  # TODO Needs to be implemented

    def instrument_setup(self, observation_id: int) -> types.InstrumentSetup:
        hrs_mode = self._mode()

        sql = """
        WITH hm (id) AS (
            SELECT hrs_mode_id FROM observations.hrs_mode
                   WHERE hrs_mode.hrs_mode=%(hrs_mode)s
        )
        INSERT INTO observations.hrs_setup (instrument_setup_id, hrs_mode_id)
        VALUES (%(instrument_setup_id)s, (SELECT id FROM hm))
        """
        parameters = dict(hrs_mode=hrs_mode.value)
        queries = [types.SQLQuery(sql=sql, parameters=parameters)]

        detmode_header_value = self.header_value("DETMODE")
        detector_mode = types.DetectorMode.for_name(
            detmode_header_value if detmode_header_value else ""
        )

        return types.InstrumentSetup(
            additional_queries=queries,
            detector_mode=detector_mode,
            filter=None,
            instrument_mode=types.InstrumentMode.SPECTROSCOPY,
            observation_id=observation_id,
        )

    def observation(
        self, observation_group_id: Optional[int], proposal_id: Optional[int]
    ) -> types.Observation:
        return self.salt_observation.observation(
            observation_group_id=observation_group_id,
            proposal_id=proposal_id,
            instrument=types.Instrument.HRS,
        )

    def observation_group(self) -> Optional[types.ObservationGroup]:
        return self.salt_observation.observation_group()

    def observation_time(self, plane_id: int) -> types.ObservationTime:
        return self.salt_observation.observation_time(plane_id)

    def plane(self, observation_id: int) -> types.Plane:
        return types.Plane(
            observation_id, data_product_type=types.DataProductType.SPECTRUM
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

    def _mode(self) -> types.HRSMode:
        obsmode_header_value = self.header_value("OBSMODE")
        hrs_mode = obsmode_header_value.upper() if obsmode_header_value else ""
        if hrs_mode == "LOW RESOLUTION":
            return types.HRSMode.LOW_RESOLUTION
        if hrs_mode == "MEDIUM RESOLUTION":
            return types.HRSMode.MEDIUM_RESOLUTION
        if hrs_mode == "HIGH RESOLUTION":
            return types.HRSMode.HIGH_RESOLUTION
        if hrs_mode == "HIGH STABILITY":
            return types.HRSMode.HIGH_STABILITY
        if hrs_mode == "INT CAL FIBRE":
            return types.HRSMode.INT_CAL_FIBRE
        raise ValueError(f"Unknown HRS mode {hrs_mode} for file {self.file_path}")
