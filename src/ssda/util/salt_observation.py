import uuid
from pathlib import Path
from typing import Optional, List
from datetime import timedelta, datetime, date, timezone
from astropy.coordinates import Angle

import astropy.units as u
from ssda.database.sdb import SaltDatabaseService
from ssda.util.fits import FitsFile, get_fits_base_dir

from ssda.util import types


class SALTObservation:
    def __init__(self, fits_file: FitsFile, database_service: SaltDatabaseService):
        self.headers = fits_file.headers
        self.header_value = fits_file.header_value
        self.size = fits_file.size()
        self.checksum = fits_file.checksum
        self.fits_file = fits_file
        self.file_path = fits_file.file_path
        self.database_service = database_service
        self.block_visit_id = (
            None
            if not fits_file.header_value("BVISITID")
            else int(fits_file.header_value("BVISITID"))
        )

    def artifact(self, plane_id: int) -> types.Artifact:
        # Creates a file path of the reduced calibration level mapping a raw calibration level.
        def create_reduced_path(path: Path) -> Path:
            reduced_dir = Path.joinpath(path.parent.parent, "product")

            reduced_paths = reduced_dir.glob("*.fits")

            _reduced_path = ""

            for _path in reduced_paths:
                if _path.name.endswith(path.name):
                    _reduced_path = _path
            return _reduced_path

        raw_path = self.fits_file.file_path()
        reduced_path = create_reduced_path(Path(raw_path))

        identifier = uuid.uuid4()

        return types.Artifact(
            content_checksum=self.fits_file.checksum(),
            content_length=self.fits_file.size(),
            identifier=identifier,
            name=Path(raw_path).name,
            plane_id=plane_id,
            paths=types.CalibrationLevelPaths(
                raw=Path(raw_path).relative_to(get_fits_base_dir()),
                reduced=None
                if not reduced_path
                else Path(reduced_path).relative_to(get_fits_base_dir()),
            ),
            product_type=self._product_type(),
        )

    def observation(
        self,
        observation_group_id: Optional[int],
        proposal_id: Optional[int],
        instrument: types.Instrument,
    ) -> types.Observation:

        if not self.block_visit_id:
            observation_date = datetime.strptime(
                self.header_value("DATE-OBS"), "%Y-%m-%d"
            ).date()
            release_date = date(
                year=observation_date.year,
                month=observation_date.month,
                day=observation_date.day,
            )
            status = types.Status.ACCEPTED
        else:
            release_date = self.database_service.find_release_date(self.block_visit_id)
            status = self.database_service.find_observation_status(self.block_visit_id)
        return types.Observation(
            data_release=release_date,
            instrument=instrument,
            intent=self._intent(),
            meta_release=release_date,
            observation_group_id=observation_group_id,
            observation_type=types.ObservationType.OBJECT,
            proposal_id=proposal_id,
            status=status,
            telescope=types.Telescope.SALT,
        )

    def observation_group(self) -> Optional[types.ObservationGroup]:
        if not self.header_value("BVISITID"):
            return None
        return types.ObservationGroup(
            group_identifier=self.header_value("BVISITID"),
            name="SALT-" + self.header_value("BVISITID"),
        )

    def observation_time(self, plane_id: int) -> types.ObservationTime:
        start_date_time_str = (
            self.header_value("DATE-OBS") + " " + self.header_value("TIME-OBS")
        )
        start_date_time = datetime.strptime(start_date_time_str, "%Y-%m-%d %H:%M:%S.%f")
        start_time_tz = datetime(
            year=start_date_time.year,
            month=start_date_time.month,
            day=start_date_time.day,
            hour=start_date_time.hour,
            minute=start_date_time.minute,
            second=start_date_time.second,
            tzinfo=timezone.utc,
        )

        exposure_time = float(self.header_value("EXPTIME"))
        return types.ObservationTime(
            end_time=start_time_tz + timedelta(seconds=exposure_time),
            exposure_time=exposure_time * u.second,
            plane_id=plane_id,
            resolution=exposure_time * u.second,
            start_time=start_time_tz,
        )

    def position(self, plane_id: int) -> Optional[types.Position]:
        ra_header_value = self.header_value("RA")
        dec_header_value = self.header_value("DEC")
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
        ra = Angle("{} hours".format(ra_header_value)).degree * u.deg
        dec = Angle("{} degrees".format(dec_header_value)).degree * u.deg
        if ra.value == 0 and dec.value == 0:
            return None
        equinox = float(self.header_value("EQUINOX"))
        if equinox == 0:  # TODO check if it is cal and use it instead
            return None
        return types.Position(dec=dec, equinox=equinox, plane_id=plane_id, ra=ra)

    def proposal(self) -> Optional[types.Proposal]:
        if not self.fits_file.header_value("BVISITID"):
            return None

        return types.Proposal(
            institution=types.Institution.SALT,
            pi=self.database_service.find_pi(self.block_visit_id),
            proposal_code=self.database_service.find_proposal_code(self.block_visit_id),
            title=self.database_service.find_proposal_title(self.block_visit_id),
        )

    def proposal_investigators(
        self, proposal_id: int
    ) -> List[types.ProposalInvestigator]:
        investigators = self.database_service.find_proposal_investigators(
            self.block_visit_id
        )
        return [
            types.ProposalInvestigator(
                proposal_id=proposal_id, investigator_id=str(investigator)
            )
            for investigator in investigators
        ]

    def target(self, observation_id: int) -> Optional[types.Target]:
        object_name = self.header_value("OBJECT").upper()
        product_category = self._product_category()

        if (
            product_category == types.ProductType.ARC_CALSYS
            or product_category == types.ProductType.ARC_INTERNAL
            or product_category == types.ProductType.BIAS
            or product_category == types.ProductType.IMAGING_FLAT_LAMP
            or product_category == types.ProductType.IMAGING_FLAT_TWILIGHT
            or product_category == types.ProductType.SPECTROSCOPIC_FLAT_LAMP
            or product_category == types.ProductType.SPECTROSCOPIC_FLAT_TWILIGHT
            or product_category == types.ProductType.DARK
            or not self.block_visit_id
        ):
            return None
        is_standard = False
        if (
            # TODO ADD MORE WHEN ROS CONFIRMS STANDARD MAPPING
            product_category == types.ProductType.STANDARD_CIRCULAR_POLARIMETRIC
            or product_category == types.ProductType.STANDARD_LICK
            or product_category == types.ProductType.STANDARD_PHOTOMETRIC
            or product_category == types.ProductType.STANDARD_RADIAL_VELOCITY
            or product_category == types.ProductType.STANDARD_SPECTROPHOTOMETRIC
            or product_category == types.ProductType.STANDARD_UNPOLARISED
        ):
            is_standard = True

        return types.Target(
            name=object_name,
            observation_id=observation_id,
            standard=is_standard,
            target_type=self.database_service.find_target_type(self.block_visit_id),
        )

    def _product_category(self):
        observation_object = self.header_value("OBJECT").upper()
        product_type = self.header_value("OBSTYPE").upper()
        product_type_unknown = not product_type or product_type == "ZERO"

        if "ARC" in product_type or (
            product_type_unknown
            and (observation_object == "ARC" or "_ARC" in observation_object)
        ):
            return types.ProductCategory.ARC
        if "BIAS" in product_type or (
            product_type_unknown
            and (observation_object == "BIAS" or "_BIAS" in observation_object)
        ):
            return types.ProductCategory.BIAS
        if "FLAT" in product_type or (
            product_type_unknown
            and (observation_object == "FLAT" or "_FLAT" in observation_object)
        ):
            return types.ProductCategory.FLAT
        if "DARK" in product_type or (
            product_type_unknown
            and (observation_object == "DARK" or "_DARK" in observation_object)
        ):
            return types.ProductCategory.DARK
        if "STANDARD" in product_type or (
            product_type_unknown
            and (observation_object == "STANDARD" or "_STANDARD" in observation_object)
        ):
            return types.ProductCategory.STANDARD
        if product_type == "OBJECT" or product_type == "SCIENCE":
            return types.ProductCategory.SCIENCE
        else:
            raise ValueError(
                f"Product category of file ${self.fits_file.file_path()} could not be determined"
            )

    def _product_type(self) -> types.ProductType:
        obs_mode = self.header_value("OBSMODE").upper()
        instrument = self.header_value("INSTRUME").upper()
        proposal_id = self.header_value("PROPID").upper()
        product_category = self._product_category()

        if (
            proposal_id != "CAL_STABLE"
            and product_category == types.ProductCategory.ARC
        ):
            return types.ProductType.ARC_CALSYS
        if (
            proposal_id == "CAL_STABLE"
            and product_category == types.ProductCategory.ARC
        ):
            return types.ProductType.ARC_INTERNAL
        if proposal_id == "CAL_BIAS" and product_category == types.ProductCategory.BIAS:
            return types.ProductType.BIAS
        if (
            (instrument == "SALTICAM" or instrument == "BCAM")
            and proposal_id == "CAL_SKYFLAT"
            and product_category == types.ProductCategory.FLAT
        ):
            return types.ProductType.IMAGING_FLAT_TWILIGHT
        if (
            (instrument == "SALTICAM" or instrument == "BCAM")
            and proposal_id != "CAL_SKYFLAT"
            and product_category == types.ProductCategory.FLAT
        ):
            return types.ProductType.IMAGING_FLAT_LAMP
        if (
            instrument == "HRS"
            and proposal_id == "CAL_SKYFLAT"
            and product_category == types.ProductCategory.FLAT
        ):
            return types.ProductType.IMAGING_FLAT_TWILIGHT
        if (
            instrument == "HRS"
            and proposal_id != "CAL_SKYFLAT"
            and product_category == types.ProductCategory.FLAT
        ):
            return types.ProductType.IMAGING_FLAT_LAMP
        if (
            instrument == "RSS"
            and (obs_mode == "IMAGING" or obs_mode == "FABRY-PEROT")
            and proposal_id == "CAL_SKYFLAT"
            and product_category == types.ProductCategory.FLAT
        ):
            return types.ProductType.IMAGING_FLAT_TWILIGHT
        if (
            instrument == "RSS"
            and (obs_mode == "IMAGING" or obs_mode == "FABRY-PEROT")
            and proposal_id != "CAL_SKYFLAT"
            and product_category == types.ProductCategory.FLAT
        ):
            return types.ProductType.IMAGING_FLAT_LAMP
        if product_category == types.ProductCategory.DARK:
            return types.ProductType.DARK
        # TODO ADD MORE WHEN ROS CONFIRMS STANDARD MAPPING
        if (
            proposal_id == "CAL_POLST"
            and product_category == types.ProductCategory.STANDARD
        ):
            return types.ProductType.STANDARD_CIRCULAR_POLARIMETRIC
        if (
            proposal_id == "CAL_LICKST"
            and product_category == types.ProductCategory.STANDARD
        ):
            return types.ProductType.STANDARD_LICK
        if (
            proposal_id == "CAL_PHOTST"
            and product_category == types.ProductCategory.STANDARD
        ):
            return types.ProductType.STANDARD_PHOTOMETRIC
        if (
            proposal_id == "CAL_RVST"
            and product_category == types.ProductCategory.STANDARD
        ):
            return types.ProductType.STANDARD_RADIAL_VELOCITY
        if (
            proposal_id == "CAL_SPST"
            and product_category == types.ProductCategory.STANDARD
        ):
            return types.ProductType.STANDARD_SPECTROPHOTOMETRIC
        if (
            proposal_id == "CAL_UNPOLST"
            and product_category == types.ProductCategory.STANDARD
        ):
            return types.ProductType.STANDARD_UNPOLARISED
        if product_category == types.ProductCategory.SCIENCE:
            return types.ProductType.SCIENCE
        else:
            raise ValueError(
                f"Product type of file ${self.fits_file.file_path()} could not be determined"
            )

    def _intent(self) -> types.Intent:
        product_category = self._product_category()

        if (
            product_category == types.ProductCategory.ARC
            or product_category == types.ProductCategory.BIAS
            or product_category == types.ProductCategory.FLAT
            or product_category == types.ProductCategory.DARK
            or product_category == types.ProductCategory.STANDARD
        ):
            return types.Intent.CALIBRATION
        elif product_category == types.ProductCategory.SCIENCE:
            return types.Intent.SCIENCE
        raise ValueError(f"Intent for file {self.file_path()} could not be determined")

    def is_calibration(self):
        return "CAL_" in self.header_value("PROPID")
