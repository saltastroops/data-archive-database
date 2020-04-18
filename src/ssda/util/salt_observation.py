import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, List
from datetime import timedelta, date, datetime, timezone
from astropy.coordinates import Angle

import astropy.units as u
from ssda.database.sdb import SaltDatabaseService, FileDataItem
from ssda.util.fits import FitsFile, get_fits_base_dir

from ssda.util import types
from ssda.util.types import Status


@dataclass
class FileData:
    data: Dict[str, FileDataItem]
    night: Optional[date]


class SALTObservation:
    def __init__(self, fits_file: FitsFile, database_service: SaltDatabaseService):
        self.header_value = fits_file.header_value
        self.size = fits_file.size()
        self.checksum = fits_file.checksum
        self.fits_file = fits_file
        self.file_path = fits_file.file_path
        self.database_service = database_service
        self.file_data = FileData({}, None)

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

    def _block_visit_id(self) -> Optional[str]:
        night = (self.observation_start_time() - timedelta(hours=12)).date()
        if self.file_data.night != night:
            self.file_data = FileData(self.database_service.find_block_visit_ids(night), night)
        filename = Path(self.fits_file.file_path()).name
        if filename not in self.file_data:
            raise Exception(f"The filename {filename} is not included in the FileData table.")

        return self.file_data.data[filename].block_visit_id

    def observation(
        self,
        observation_group_id: Optional[int],
        proposal_id: Optional[int],
        instrument: types.Instrument,
    ) -> types.Observation:
        proposal_code = self.header_value("PROPID").upper()
        data_release_dates = self.database_service.find_release_date(proposal_code)
        status = self.database_service.find_observation_status(self._block_visit_id())
        return types.Observation(
            data_release=data_release_dates[0],
            instrument=instrument,
            intent=self._intent(),
            meta_release=data_release_dates[1],
            observation_group_id=observation_group_id,
            proposal_id=proposal_id,
            status=status,
            telescope=types.Telescope.SALT,
        )

    def observation_group(self) -> Optional[types.ObservationGroup]:
        bv_id = self._block_visit_id()
        if bv_id is None:
            return None
        return types.ObservationGroup(
            group_identifier=str(bv_id), name="SALT-" + str(bv_id)
        )

    def observation_start_time(self) -> datetime:
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

        return start_time_tz

    def observation_time(self, plane_id: int) -> types.ObservationTime:
        exposure_time = float(self.header_value("EXPTIME"))
        return types.ObservationTime(
            end_time=self.observation_start_time() + timedelta(seconds=exposure_time),
            exposure_time=exposure_time * u.second,
            plane_id=plane_id,
            resolution=exposure_time * u.second,
            start_time=self.observation_start_time(),
        )

    def position(self, plane_id: int) -> Optional[types.Position]:
        if self.is_calibration() and not self.is_standard():
            return None
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
        bv_id = self._block_visit_id()
        if bv_id is None:
            return None

        proposal_code = self.header_value("PROPID").upper()

        return types.Proposal(
                institution=types.Institution.SALT,
                pi=self.database_service.find_pi(proposal_code),
                proposal_code=proposal_code,
                title=self.database_service.find_proposal_title(proposal_code),
            )

    def proposal_investigators(
        self, proposal_id: int
    ) -> List[types.ProposalInvestigator]:
        proposal_code = self.header_value("PROPID").upper()
        investigators = self.database_service.find_proposal_investigators(
            proposal_code
        )
        return [
            types.ProposalInvestigator(
                proposal_id=proposal_id, investigator_id=str(investigator)
            )
            for investigator in investigators
        ]

    def target(self, observation_id: int) -> Optional[types.Target]:
        object_name = self.header_value("OBJECT").upper()

        if self.is_calibration() and not self.is_standard():
            return None

        return types.Target(
            name=object_name,
            observation_id=observation_id,
            standard=self.is_standard(),
            target_type=self.database_service.find_target_type(self._block_visit_id()),
        )

    def _product_category(self):
        observation_object = self.header_value("OBJECT").upper()
        product_type = self.header_value("OBSTYPE").upper()
        proposal_id = self.header_value("PROPID").upper()

        # CCDTYPE is a copy of OBSTYPE
        if not product_type:
            product_type = self.header_value("CCDTYPE").upper()

        product_type_unknown = not product_type or product_type == "ZERO"

        if (
            proposal_id in ["CAL_ARC", "CAL_STABLE"]
            or "ARC" in product_type
            or (
                product_type_unknown
                and (observation_object == "ARC" or "_ARC" in observation_object)
            )
        ):
            return types.ProductCategory.ARC
        if (
            proposal_id == "CAL_BIAS"
            or "BIAS" in product_type
            or (
                product_type_unknown
                and (observation_object == "BIAS" or "_BIAS" in observation_object)
            )
        ):
            return types.ProductCategory.BIAS
        if (
            proposal_id in ["CAL_FLAT", "CAL_SKYFLAT"]
            or "FLAT" in product_type
            or (
                product_type_unknown
                and (observation_object == "FLAT" or "_FLAT" in observation_object)
            )
        ):
            return types.ProductCategory.FLAT
        if "DARK" in product_type or (
            product_type_unknown
            and (observation_object == "DARK" or "_DARK" in observation_object)
        ):
            return types.ProductCategory.DARK
        if (
            proposal_id
            in [
                "CAL_POLST",
                "CAL_LICKST",
                "CAL_PHOTST",
                "CAL_RVST",
                "CAL_SPST",
                "CAL_TELLST",
                "CAL_UNPOLST",
            ]
            or "STANDARD" in product_type
            or (
                product_type_unknown
                and (
                    observation_object == "STANDARD"
                    or "_STANDARD" in observation_object
                )
            )
        ):
            return types.ProductCategory.STANDARD
        if product_type == "OBJECT" or product_type == "SCIENCE":
            # Science file with no block visit id are not populated
            if self._block_visit_id() is None:
                raise ValueError(
                    "The observation is marked as science but has no block visit id."
                )
            return types.ProductCategory.SCIENCE

        raise ValueError(
            f"Product category of file ${self.fits_file.file_path()} could not be determined"
        )

    def _product_type(self) -> types.ProductType:
        obs_mode = self.header_value("OBSMODE").upper()
        instrument = self.header_value("INSTRUME").upper()
        proposal_id = self.header_value("PROPID").upper()
        product_category = self._product_category()

        if product_category == types.ProductCategory.ARC:
            if proposal_id == "CAL_STABLE":
                return types.ProductType.ARC_INTERNAL
            else:
                return types.ProductType.ARC_CALSYS

        if product_category == types.ProductCategory.BIAS:
            return types.ProductType.BIAS

        if product_category == types.ProductCategory.FLAT:
            if instrument == "SALTICAM" or instrument == "BCAM":
                if proposal_id == "CAL_SKYFLAT":
                    return types.ProductType.IMAGING_FLAT_TWILIGHT
                else:
                    return types.ProductType.IMAGING_FLAT_LAMP

            if instrument == "HRS":
                if proposal_id == "CAL_SKYFLAT":
                    return types.ProductType.SPECTROSCOPIC_FLAT_TWILIGHT
                else:
                    return types.ProductType.SPECTROSCOPIC_FLAT_LAMP

            if instrument == "RSS":
                if obs_mode == "IMAGING" or obs_mode == "FABRY-PEROT":
                    if proposal_id == "CAL_SKYFLAT":
                        return types.ProductType.IMAGING_FLAT_TWILIGHT
                    else:
                        return types.ProductType.IMAGING_FLAT_LAMP
                if obs_mode == "SPECTROSCOPY":
                    if proposal_id == "CAL_SKYFLAT":
                        return types.ProductType.SPECTROSCOPIC_FLAT_TWILIGHT
                    else:
                        return types.ProductType.SPECTROSCOPIC_FLAT_LAMP

        if product_category == types.ProductCategory.DARK:
            return types.ProductType.DARK

        if product_category == types.ProductCategory.STANDARD:
            if proposal_id == "CAL_LICKST":
                return types.ProductType.STANDARD_LICK
            if proposal_id == "CAL_PHOTST":
                return types.ProductType.STANDARD_PHOTOMETRIC
            if proposal_id == "CAL_POLST":
                return types.ProductType.STANDARD_LINEAR_POLARIMETRIC
            if proposal_id == "CAL_RVST":
                return types.ProductType.STANDARD_RADIAL_VELOCITY
            if proposal_id == "CAL_SPST":
                return types.ProductType.STANDARD_SPECTROPHOTOMETRIC
            if proposal_id == "CAL_TELLST":
                return types.ProductType.STANDARD_TELLURIC
            if proposal_id == "CAL_UNPOLST":
                return types.ProductType.STANDARD_UNPOLARISED

        if product_category == types.ProductCategory.SCIENCE:
            return types.ProductType.SCIENCE

        raise ValueError(
            f"Product type of file ${self.fits_file.file_path()} could not be determined"
        )

    def _intent(self) -> types.Intent:
        product_category = self._product_category()

        if self.is_calibration():
            return types.Intent.CALIBRATION
        elif product_category == types.ProductCategory.SCIENCE:
            return types.Intent.SCIENCE
        raise ValueError(f"Intent for file {self.file_path()} could not be determined")

    def is_calibration(self):
        product_category = self._product_category()

        return (
            product_category == types.ProductCategory.ARC
            or product_category == types.ProductCategory.BIAS
            or product_category == types.ProductCategory.DARK
            or product_category == types.ProductCategory.FLAT
            or product_category == types.ProductCategory.STANDARD
        )

    def is_standard(self):
        product_category = self._product_category()

        return product_category == types.ProductCategory.STANDARD

    def ignore_observation(self) -> bool:
        proposal_id = (
            self.fits_file.header_value("PROPID").upper()
            if self.fits_file.header_value("PROPID")
            else self.fits_file.header_value("PROPID")
        )
        # If the FITS file is Junk, Unknown, ENG or CAL_GAIN, do not store the observation.
        if proposal_id in ("JUNK", "UNKNOWN", "NONE", "ENG", "CAL_GAIN"):
            return True
        # Do not store engineering data.
        # Proposal ids referring to an actual proposal will always start with a "2" (as in 2020-1-SCI-014).
        if not proposal_id.startswith("2") and (
            "ENG_" in proposal_id or "ENG-" in proposal_id
        ):
            return True

        observation_object = self.header_value("OBJECT").upper()
        # Do not store commissioning data that pretends to be science.
        if "COM-" in proposal_id or "COM_" in proposal_id:
            if observation_object == "DUMMY":
                return True

        observation_date = self.fits_file.header_value("DATE-OBS")
        # If the FITS header does not include the observation date, do not store its data.
        if not observation_date:
            return True

        bv_id = self._block_visit_id()

        status = self.database_service.find_observation_status(bv_id)

        # Do not store deleted or in a queue observation data.
        if status == Status.DELETED or status == Status.INQUEUE:
            return True

        return False
