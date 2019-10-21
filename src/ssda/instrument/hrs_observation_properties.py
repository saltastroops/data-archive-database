from astropy.units import Quantity
from ssda.database.sdb import SaltDatabaseService
from ssda.observation import ObservationProperties
from ssda.util import types
from ssda.util.energy_cal import hrs_interval, hrs_energy_cal
from ssda.util.salt_observation import SALTObservation
from ssda.util.fits import FitsFile
from typing import Optional, List


class HrsObservationProperties(ObservationProperties):

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
        if "CAL_" in self.header_value("PROPID"):
            return None

        filename = str(self.file_path.split()[-1])
        arm = "red" if filename[0] == "R" else "blue" if filename[0] == "H" else None
        if not arm:
            raise ValueError("Unknown arm.")
        resolution = self.header_value("OBSMODE")
        return hrs_energy_cal(plane_id, arm, resolution)

    def instrument_keyword_values(self, observation_id: int) -> List[types.InstrumentKeywordValue]:
        return [
            types.InstrumentKeywordValue(
                instrument=types.Instrument.HRS,
                instrument_keyword=types.InstrumentKeyword.FILTER,
                observation_id=observation_id,
                value=self.header_value("FILTER")
            ),
            types.InstrumentKeywordValue(
                instrument=types.Instrument.HRS,
                instrument_keyword=types.InstrumentKeyword.EXPOSURE_TIME,
                observation_id=observation_id,
                value=self.header_value("EXPTIME")
            )
        ]  # TODO check if there is more keywords

    def observation(self, observation_group_id: Optional[int], proposal_id: Optional[int]) -> types.Observation:
        return self.salt_observation.observation(observation_group_id=observation_group_id,
                                                 proposal_id=proposal_id,
                                                 instrument=types.Instrument.HRS)

    def observation_time(self, plane_id: int) -> types.ObservationTime:
        return self.salt_observation.observation_time(plane_id)

    @staticmethod
    def plane(observation_id: int) -> types.Plane:
        return types.Plane(observation_id)

    def polarizations(self, plane_id: int) -> List[types.Polarization]:  # TODO find out why is this an array
        polarization_config = self.header_value("POLCONF").strip()
        if polarization_config.upper() == "OPEN":
            return []

        return [
            types.Polarization(
                plane_id=plane_id,
                stokes_parameter=stoke
            )
            for stoke in self.salt_observation.stokes_parameter
        ]

    def position(self, plane_id: int) -> Optional[types.Position]:
        return self.salt_observation.position(plane_id=plane_id)

    def proposal(self) -> Optional[types.Proposal]:
        """
        SALT proposal

        Parameters
        ----------

        Returns
        -------
        Proposal
            A proposal for the file.
        """
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
