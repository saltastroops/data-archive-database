from ssda.database.sdb import SaltDatabaseService
from ssda.util import types
from ssda.util.energy_cal import rss_energy_properties
from ssda.util.salt_observation import SALTObservation
from ssda.util.fits import FitsFile
from typing import Optional, List


class RssObservationProperties:

    def __init__(self, fits_file: FitsFile, salt_database_service: SaltDatabaseService):
        """
        :param fits_file:
        """
        self.header_value = fits_file.header_value
        self.file_path = fits_file.file_path
        self.database_service = salt_database_service
        self.salt_observation = SALTObservation(
            fits_file=fits_file,
            database_service=salt_database_service
        )

    def artifact(self, plane_id: int) -> types.Artifact:
        return self.salt_observation.artifact(plane_id)

    def energy(self, plane_id: int) -> Optional[types.Energy]:
        if self.salt_observation.is_calibration():
            return None
        slit_barcode = self.header_value("MASKID").strip()

        if self.database_service.is_mos(slit_barcode=slit_barcode):
            return None
        return rss_energy_properties(header_value=self.header_value, plane_id=plane_id)

    def instrument_keyword_values(self, observation_id: int) -> List[types.InstrumentKeywordValue]:
        return []  # TODO Needs to be implemented

    def instrument_setup(self,  observation_id: int) -> types.InstrumentSetup:
        sql = """
        WITH fpm (id) AS (
            SELECT rss_fabry_perot_mode_id FROM rss_fabry_perot_mode WHERE fabry_perot_mode=%(fabry_perot_mode)s
        ),
             rg (id) AS (
                 SELECT rss_grating_id FROM rss_grating WHERE grating=%(grating)s
             )
        INSERT INTO rss_setup (instrument_setup_id, rss_fabry_perot_mode_id, rss_grating_id)
        VALUES (%(instrument_setup_id)s, (SELECT id FROM fpm), (SELECT id FROM rg))
        """

        fabry_perot_mode = self.header_value("OBSMODE").strip()

        grating_value = self.header_value("GRATING").strip()
        grating = None if grating_value == "N/A" else grating_value

        parameters = dict(fabry_perot_mode=fabry_perot_mode, grating=grating)
        queries = [types.SQLQuery(sql=sql, parameters=parameters)]

        detector_mode = None
        for dm in types.DetectorMode:
            if self.header_value("DETMODE").strip() == dm.value:
                detector_mode = dm

        filter = None
        for fi in types.Filter:
            if self.header_value("FILTER").strip() == fi.value:
                filter = fi

        instrument_mode = which_instrument_mode_rss(self.header_value, self.database_service)

        return types.InstrumentSetup(
            additional_queries=queries,
            detector_mode=detector_mode,
            filter=filter,
            instrument_mode=instrument_mode,
            observation_id=observation_id,
        )

    def observation(self, observation_group_id: Optional[int], proposal_id: Optional[int]) -> types.Observation:
        return self.salt_observation.observation(observation_group_id=observation_group_id,
                                                 proposal_id=proposal_id,
                                                 instrument=types.Instrument.RSS)

    def observation_group(self) -> Optional[types.ObservationGroup]:
        return self.salt_observation.observation_group()

    def observation_time(self, plane_id: int) -> types.ObservationTime:
        return self.salt_observation.observation_time(plane_id)

    def plane(self, observation_id: int) -> types.Plane:
        observation_mode = self.header_value("OBSMODE").strip().upper()
        data_product_type = types.DataProductType.IMAGE \
            if observation_mode == "IMAGING" \
            or observation_mode == "FABRY-PEROT" \
            else types.DataProductType.SPECTRUM
        return types.Plane(observation_id, data_product_type=data_product_type)

    @staticmethod
    def get_pattern(pattern: str) -> types.PolarizationMode:
        # if pattern.upper() == "NONE" or not pattern:  # TODO can we have a None if polarization_config is NOT Open
        #     return None
        if pattern.upper() == "LINEAR":
            return types.PolarizationMode.LINEAR
        elif pattern.upper() == "LINEAR-HI":
            return types.PolarizationMode.LINEAR_HI
        elif pattern.upper() == "CIRCULAR":
            return types.PolarizationMode.CIRCULAR
        elif pattern.upper() == "ALL-STOKES":
            return types.PolarizationMode.ALL_STOKES
        else:
            return types.PolarizationMode.OTHER

    def polarization(self, plane_id: int) -> Optional[types.Polarization]:
        polarization_config = self.header_value("POLCONF").strip()
        pattern: str = self.header_value("WPPATERN").strip().upper()
        if polarization_config.upper() == "OPEN":
            return None

        return types.Polarization(
            plane_id=plane_id,
            polarization_mode=self.get_pattern(pattern=pattern)
        )

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


def which_instrument_mode_rss(header_value, database_service) -> types.InstrumentMode:
    slit_barcode = header_value("MASKID").strip()

    mode = header_value("OBSMODE").strip().upper()
    if mode == "FABRY-PEROT":
        return types.InstrumentMode.FABRY_PEROT
    if mode == "SPECTROSCOPY":
        return types.InstrumentMode.SPECTROSCOPY
    if mode == "IMAGING":
        return types.InstrumentMode.IMAGING

    if database_service.is_mos(slit_barcode=slit_barcode):
        return types.InstrumentMode.MOS

    # TODO how to find these  POLARIMETRIC_IMAGING, SPECTROPOLARIMETRY, STREAMING
    raise ValueError("Some modes are not considered there are still in todo")
