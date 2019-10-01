import os
import random
import string
from typing import Optional, List
from dateutil.parser import parse
from datetime import timedelta
from astropy.coordinates import Angle

import astropy.units as u
from astropy.units import Quantity
from ssda.database import SaltDatabaseService
from ssda.filter_wavelength_files.reader import energy_calculation_image, fp_fwhm_cal, get_wavelength, \
    get_grating_frequency, get_wavelength_resolution, slit_width_from_barcode, hrs_interval
from ssda.util.fits import FitsFile
from ssda.database import DatabaseService as SsdaDB

from ssda.util.types import Proposal, Institution, Energy
from ssda.util import types


class SALTObservation:
    def __init__(self, fits_file: FitsFile, database_service:  SaltDatabaseService):
        """
        :param fits_file:
        """
        self.headers = fits_file.headers
        self.header_value = fits_file.header_value
        self.size = fits_file.size()
        self.checksum = fits_file.checksum()
        self.fits_file = fits_file
        self.file_path = fits_file.file_path()
        self.database_service = database_service

    def artifact(self, plane_id: int) -> types.Artifact:

        path = self.fits_file.file_path()
        letters = string.ascii_lowercase
        identifier = "".join(random.choice(letters) for _ in range(10))
        while SsdaDB.find_identifier(identifier) is not None:
            identifier = "".join(random.choice(letters) for _ in range(10))

        return types.Artifact(
            content_checksum=self.fits_file.checksum(),
            content_length=self.fits_file.size(),
            identifier=identifier,
            name=path.split("/")[-1],
            plane_id=plane_id,
            path=path,
            product_type=self.__product_type(),
        )

    def energy(self, plane_id: int, instrument: types.Instrument) -> Optional[types.Energy]:

        proposal_id = self.header_value("PROPID")
        obs_mode = self.header_value("OBSMODE").strip().upper()
        slit_barcode = self.header_value("MASKID").strip()
        if "CAL_" in proposal_id.upper():
            return
        if instrument == types.Instrument.RSS and self.database_service.is_mos(slit_barcode=slit_barcode):  # TODO know MOS Fits
            return
        if instrument == types.Instrument.RSS or instrument == types.Instrument.SALTICAM:
            if obs_mode == "IMAGING" or instrument == types.Instrument.SALTICAM:
                filter_name = self.header_value("FILTER").strip()
                fwhm_points = energy_calculation_image(filter_name, instrument)
                lambda1, lambda2 = fwhm_points["lambda1"], fwhm_points["lambda2"]
                resolving_power = lambda1[1] * (lambda1[0] + lambda2[0]) / (lambda2[0] - lambda1[0])
                return types.Energy(
                    dimension=1,
                    max_wavelength=Quantity(
                        value=lambda2[0],
                        unit=types.meter
                    ),
                    min_wavelength=Quantity(
                        value=lambda1[0],
                        unit=types.meter
                    ),
                    plane_id=plane_id,
                    resolving_power=resolving_power,
                    sample_size=Quantity(
                        value=abs(lambda2[0]-lambda1[0]),
                        unit=types.meter
                    )
                )

            if obs_mode == "SPECTROSCOPY":
                grating_angle = float(self.header_value("GR-ANGLE").strip())
                camera_angle = float(self.header_value("AR-ANGLE").strip())
                slit_barcode = self.header_value("MASKID").strip()
                spectral_binning = int(self.header_value("CCDSUM").strip().split()[0])
                grating_frequency = get_grating_frequency(self.header_value("GRATING").strip())
                energy_interval = (
                    get_wavelength(3162, grating_angle, camera_angle, grating_frequency=grating_frequency),
                    get_wavelength(-3162, grating_angle, camera_angle, grating_frequency=grating_frequency)
                )
                dimension = 6096 / spectral_binning  # TODO this is a float
                sample_size = get_wavelength(spectral_binning, grating_angle, camera_angle, grating_frequency) - \
                    get_wavelength(0, grating_angle, camera_angle, grating_frequency)
                return types.Energy(
                    dimension=dimension,
                    max_wavelength=Quantity(
                        value=energy_interval[0],
                        unit=types.meter
                    ),
                    min_wavelength=Quantity(
                        value=energy_interval[1],
                        unit=types.meter
                    ),
                    plane_id=plane_id,
                    resolving_power=get_wavelength_resolution(
                        grating_angle,
                        camera_angle,
                        grating_frequency,
                        slit_width=slit_width_from_barcode(slit_barcode)),
                    sample_size=Quantity(
                        value=abs(sample_size),
                        unit=types.meter
                    )
                )

            if obs_mode == "FABRY-PEROT":
                etalon_state = self.header_value("ET-STATE")
                if etalon_state.strip().lower() == "s1 - etalon open":
                    return

                if etalon_state.strip().lower() == "s3 - etalon 2":
                    resolution = self.header_value("ET2MODE").strip().upper()  # TODO CHECK with encarni which one use ET2/1
                    lambda1 = float(self.header_value("ET2WAVE0"))
                elif etalon_state.strip().lower() == "s2 - etalon 1" or etalon_state.strip().lower() == "s4 - etalon 1 & 2":
                    resolution = self.header_value("ET1MODE").strip().upper()  # TODO CHECK with encarni which one use ET2/1
                    lambda1 = float(self.header_value("ET1WAVE0"))
                else:
                    raise ValueError("Unknown Etelo state for  FP")

                fwhm = fp_fwhm_cal(resolution=resolution, wavelength=lambda1)
                energy_intervals = ((lambda1 - fwhm) / 2, (lambda1 + fwhm) / 2)
                return types.Energy(
                    dimension=1,
                    max_wavelength=Quantity(
                        value=energy_intervals[1],
                        unit=types.meter
                    ),
                    min_wavelength=Quantity(
                        value=energy_intervals[0],
                        unit=types.meter
                    ),
                    plane_id=plane_id,
                    resolving_power=lambda1/fwhm,
                    sample_size=Quantity(
                        value=fwhm,
                        unit=types.meter
                    )
                )

        if instrument == types.Instrument.HRS:
            filename = str(self.file_path.split()[-1])
            arm = "red" if filename[0] == "R" else "blue" if filename[0] == "H" else None
            resolution = self.header_value("OBSMODE")

            interval = hrs_interval(arm, resolution)
            return types.Energy(
                dimension=1,
                max_wavelength=Quantity(
                    value=max(interval["interval"]),
                    unit=types.meter
                ),
                min_wavelength=Quantity(
                    value=min(interval["interval"]),
                    unit=types.meter
                ),
                plane_id=plane_id,
                resolving_power=interval["power"],
                sample_size=Quantity(
                    value=abs(interval["interval"][0]-interval["interval"][1]),
                    unit=types.meter
                )
            )

    def observation(self, proposal_id: int, instrument: types.Instrument) -> types.Observation:
        return types.Observation(
            data_release=self.database_service.find_release_date(self.header_value("BVISITID")),
            instrument=instrument,
            intent=self.__intent(),
            meta_release=self.database_service.find_meta_release_date(self.header_value("BVISITID")),
            observation_group=self.header_value("BVISITID"),
            observation_type=types.ObservationType.OBJECT,
            proposal_id=proposal_id,
            status=self.database_service.find_observation_status(self.header_value("BVISITID")),
            telescope=types.Telescope.SALT
        )

    def observation_time(self, plane_id: int) -> types.ObservationTime:
        start_time = parse(self.header_value("TIME-OBS"))
        exposure_time = float(self.header_value("EXPTIME"))
        return types.ObservationTime(
            end_time=start_time + timedelta(seconds=exposure_time),
            exposure_time=exposure_time * u.second,
            plane_id=plane_id,
            resolution=exposure_time * u.pixel,
            start_time=start_time
        )

    def position(self, plane_id: int) -> types.Position:
        ra_header_value = self.header_value("RA")
        dec_header_value = self.header_value("DEC")
        equinox = float(self.header_value("EQUINOX"))
        if ra_header_value and not dec_header_value:
            raise ValueError(
                "There is a right ascension header value, but no declination header value."
            )
        if not ra_header_value and dec_header_value:
            raise ValueError(
                "There is a declination header value, but no right ascension header value."
            )
        if not ra_header_value and not dec_header_value:
            return None
        ra = Angle("{} hours".format(ra_header_value)).degree
        dec = Angle("{} degrees".format(dec_header_value)).degree

        return types.Position(
            dec=dec,
            equinox=equinox,
            plane_id=plane_id,
            ra=ra
        )

    def proposal(self) -> Optional[types.Proposal]:
        return Proposal(
            institution=Institution.SALT,
            pi=self.database_service.find_pi(self.fits_file.header_value("BVISITID")),
            proposal_code=self.database_service.find_proposal_code(self.header_value("BVISITID")),
            title=self.database_service.find_proposal_title(self.header_value("BVISITID"))
        )

    def proposal_investigators(self, proposal_id: int) -> List[types.ProposalInvestigator]:
        investigators = self.database_service.find_proposal_investigators(self.header_value("BVISITID"))
        return [
            types.ProposalInvestigator(
                proposal_id=proposal_id,
                investigator_id=str(investigator)
            ) for investigator in investigators
        ]

    def target(self, observation_id: int) -> Optional[types.Target]:
        proposal_id = self.header_value("PROPID")
        object_name = self.header_value("OBJECT")
        name = object_name if self.__product_type().isinstance(types.ProductType.SCIENCE) else None
        is_standard = False
        if proposal_id.upper() == "CAL_SPST" or \
                proposal_id.upper() == "CAL_LICKST" or\
                proposal_id.upper() == "CAL_RVST" or\
                proposal_id.upper() == "CAL_SPST":
            is_standard = True
        return types.Target(
            name=name,
            observation_id=observation_id,
            standard=is_standard,
            target_type=""  # TODO how to get target type
        )

    def __product_type(self) -> types.ProductType:
        observation_object = self.header_value("OBJECT")
        product_type = self.header_value("OBSTYPE")
        if observation_object.upper() == "ARC":
            return types.ProductType.ARC
        elif observation_object.upper() == "BIAS":
            return types.ProductType.BIAS
        elif observation_object.upper() == "FLAT":
            return types.ProductType.FLAT
        elif product_type.upper() == "OBJECT" or product_type.upper() == "SCIENCE":
            # TODO Check if there is any other product type for SALT instruments
            return types.ProductType.SCIENCE
        else:
            raise ValueError(f'Product type of file ${self.fits_file.file_path()} not found')

    def __intent(self) -> types.Intent:
        observation_object: str = self.header_value("OBJECT")
        product_type: str = self.header_value("OBSTYPE")
        if observation_object.upper() == "ARC" or \
                observation_object.upper() == "BIAS" or \
                observation_object.upper() == "FLAT":
            return types.Intent.CALIBRATION
        elif product_type.upper() =="OBJECT" or product_type.upper() == "SCIENCE":
            # TODO Check if there is any other product type for SALT instruments
            return types.Intent.SCIENCE

    @property
    def stokes_parameter(self) -> Optional[List[types.StokesParameter]]:
        pattern: str = self.header_value("WPPATERN")

        if pattern.upper() == "NONE" or not pattern:
            return None
        elif pattern.upper() == "LINEAR":
            return [types.StokesParameter.Q, types.StokesParameter.U]
        elif pattern.upper() == "LINEAR-HI":
            return [types.StokesParameter.Q, types.StokesParameter.U]
        elif pattern.upper() == "CIRCULAR":
            return [types.StokesParameter.V]
        elif pattern.upper() == "CIRCULAR-HI":
            return [types.StokesParameter.V]
        elif pattern.upper() == "ALL-STOKES":
            return [types.StokesParameter.Q, types.StokesParameter.U, types.StokesParameter.V]
        elif pattern.upper() == "OLD-ALL-STOKES":
            raise ValueError(f"Strokes for filename ${self.file_path} are OLD-ALL-STOKES don't know what to return")
        elif pattern.upper() == "USER-DEFINED":
            raise ValueError(f"Strokes for filename ${self.file_path} are USER-DEFINED don't know what to return")
        else:
            raise ValueError(f"Strokes for filename ${self.file_path} not found")

