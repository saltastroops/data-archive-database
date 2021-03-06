from ssda.database.sdb import SaltDatabaseService
from ssda.observation import ObservationProperties
from ssda.util import types
from ssda.util.salt_energy_calculation import rss_spectral_properties
from ssda.util.salt_fits import find_fabry_perot_mode
from ssda.util.salt_observation import SALTObservation
from ssda.util.fits import FitsFile
from typing import Optional, List


class RssObservationProperties(ObservationProperties):
    def __init__(self, fits_file: FitsFile, salt_database_service: SaltDatabaseService):
        self.header_value = fits_file.header_value
        self.file_path = fits_file.file_path
        self.database_service = salt_database_service
        self.salt_observation = SALTObservation(
            fits_file=fits_file, database_service=salt_database_service
        )

    def access_rule(self) -> Optional[types.AccessRule]:
        return self.salt_observation.access_rule()

    def artifact(self, plane_id: int) -> types.Artifact:
        return self.salt_observation.artifact(plane_id)

    def energy(self, plane_id: int) -> Optional[types.Energy]:
        if self.salt_observation.is_calibration():
            return None
        slit_barcode = self.header_value("MASKID")

        if self.is_custom_mask(slit_barcode):
            return None
        return rss_spectral_properties(
            header_value=self.header_value, plane_id=plane_id
        )

    def ignore_observation(self) -> bool:
        return self.salt_observation.ignore_observation()

    def is_custom_mask(self, slit_barcode):
        if self.database_service.is_mos(slit_barcode=slit_barcode):
            return True
        if slit_barcode == "OCKERT":
            return True
        return False

    def instrument_keyword_values(
        self, observation_id: int
    ) -> List[types.InstrumentKeywordValue]:
        return []  # TODO Needs to be implemented

    def instrument_setup(self, observation_id: int) -> types.InstrumentSetup:
        sql = """
        WITH fpm (id) AS (
            SELECT rss_fabry_perot_mode_id FROM observations.rss_fabry_perot_mode
            WHERE fabry_perot_mode=%(fabry_perot_mode)s
        ),
             rg (id) AS (
                 SELECT rss_grating_id FROM observations.rss_grating WHERE grating=%(grating)s
             )
        INSERT INTO observations.rss_setup (instrument_setup_id, rss_fabry_perot_mode_id, rss_grating_id, camera_angle)
        VALUES (%(instrument_setup_id)s, (SELECT id FROM fpm), (SELECT id FROM rg), %(camera_angle)s)
        """

        fabry_perot_mode = find_fabry_perot_mode(self.header_value)

        def normalized_grating_name(grating_name: Optional[str]) -> str:
            if not grating_name:
                return ""
            normalized_name = grating_name.lower()
            if normalized_name == "open":
                normalized_name = "Open"
            return normalized_name

        gr_state_header_value = self.header_value("GR-STATE")
        grating_not_homed = (
            gr_state_header_value and "S1 -" not in gr_state_header_value
        )
        camang_header_value = self.header_value("CAMANG")
        camera_angle = (
            float(camang_header_value) if camang_header_value is not None else None
        )

        if grating_not_homed and camera_angle:
            grating_value = normalized_grating_name(self.header_value("GRATING"))
            grating = None if grating_value == "n/a" else grating_value
        else:
            grating = None

        if fabry_perot_mode and (grating and grating != "Open"):
            raise ValueError("There is both a Fabry-Perot mode and a grating.")

        parameters = dict(
            fabry_perot_mode=fabry_perot_mode.value if fabry_perot_mode else None,
            grating=grating,
            camera_angle=camera_angle,
        )
        queries = [types.SQLQuery(sql=sql, parameters=parameters)]

        detmode_header_value = self.header_value("DETMODE")
        detector_mode = types.DetectorMode.for_name(
            detmode_header_value if detmode_header_value else ""
        )

        filter_header_value = self.header_value("FILTER")
        filter = types.Filter.for_name(
            filter_header_value if filter_header_value else ""
        )

        instrument_mode = rss_instrument_mode(self.header_value, self.database_service)

        return types.InstrumentSetup(
            additional_queries=queries,
            detector_mode=detector_mode,
            filter=filter,
            instrument_mode=instrument_mode,
            observation_id=observation_id,
        )

    def observation(
        self, observation_group_id: Optional[int], proposal_id: Optional[int]
    ) -> types.Observation:
        return self.salt_observation.observation(
            observation_group_id=observation_group_id,
            proposal_id=proposal_id,
            instrument=types.Instrument.RSS,
        )

    def observation_group(self) -> Optional[types.ObservationGroup]:
        return self.salt_observation.observation_group()

    def observation_time(self, plane_id: int) -> types.ObservationTime:
        return self.salt_observation.observation_time(plane_id)

    def plane(self, observation_id: int) -> types.Plane:
        obsmode_header_value = self.header_value("OBSMODE")
        observation_mode = obsmode_header_value.upper() if obsmode_header_value else ""
        if observation_mode:
            data_product_type = (
                types.DataProductType.IMAGE
                if observation_mode == "IMAGING" or observation_mode == "FABRY-PEROT"
                else types.DataProductType.SPECTRUM
            )  # TODO is fp only imaging
        else:
            raise ValueError(f"The OBSMODE FITS header value is missing.")
        return types.Plane(observation_id, data_product_type=data_product_type)

    def polarization(self, plane_id: int) -> Optional[types.Polarization]:
        polconf_header_value = self.header_value("POLCONF")
        polarization_config = polconf_header_value if polconf_header_value else ""
        polarization_mode = self.header_value("WPPATERN")
        if not polarization_mode or polarization_config.upper() == "OPEN":
            return None
        if polarization_mode.upper() not in [
            "ALL-STOKES",
            "LINEAR-HI",
            "LINEAR",
            "CIRCULAR",
        ]:
            polarization_mode = "OTHER"

        return types.Polarization(
            plane_id=plane_id,
            polarization_mode=types.PolarizationMode.polarization_mode(
                polarization_mode=polarization_mode
            ),
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
        return self.salt_observation.target(observation_id=observation_id)


def rss_instrument_mode(header_value, database_service) -> types.InstrumentMode:

    mode = header_value("OBSMODE").upper()
    polarization_mode = header_value("WPPATERN")
    if mode == "IMAGING":
        if polarization_mode:
            return types.InstrumentMode.POLARIMETRIC_IMAGING
        else:
            return types.InstrumentMode.IMAGING

    if mode == "SPECTROSCOPY":
        slit_barcode = header_value("MASKID")
        if slit_barcode == "NOREAD" and header_value("MASKTYPE") == "MOS":
            return types.InstrumentMode.MOS
        if database_service.is_mos(slit_barcode=slit_barcode):
            return types.InstrumentMode.MOS

        if polarization_mode:
            return types.InstrumentMode.SPECTROPOLARIMETRY
        else:
            return types.InstrumentMode.SPECTROSCOPY

    if mode == "FABRY-PEROT":
        return types.InstrumentMode.FABRY_PEROT

    raise ValueError(f"Unsupported mode: {mode}")
