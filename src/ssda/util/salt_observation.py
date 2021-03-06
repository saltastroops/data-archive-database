import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, List
from datetime import timedelta, date, datetime
from astropy.coordinates import Angle

import astropy.units as u
from ssda.database.sdb import SaltDatabaseService, FileDataItem
from ssda.util.fits import FitsFile, get_fits_base_dir

from ssda.util import types
from ssda.util.salt_fits import parse_start_datetime
from ssda.util.types import Status
from ssda.util.warnings import record_warning


@dataclass
class FileData:
    data: Dict[str, FileDataItem]
    night: Optional[date]

# Creates a file path of the reduced calibration level mapping a raw calibration level.
def create_reduced_path(raw_path: Path) -> Optional[Path]:
    reduced_dir = Path.joinpath(raw_path.parent.parent, "product")

    reduced_paths = reduced_dir.glob("*.fits")

    reduced_path: Optional[Path] = None

    for _path in reduced_paths:
        if _path.name.endswith(raw_path.name):
            if reduced_path is None or len(_path.name) > len(reduced_path.name):
                reduced_path = _path
    return reduced_path


class SALTObservation:
    file_data = FileData({}, None)

    def __init__(self, fits_file: FitsFile, database_service: SaltDatabaseService):
        self.header_value = fits_file.header_value
        self.size = fits_file.size()
        self.checksum = fits_file.checksum
        self.fits_file = fits_file
        self.file_path = fits_file.file_path
        self.database_service = database_service

    def access_rule(self) -> Optional[types.AccessRule]:
        proposal_code = self._proposal_code()
        if not self.database_service.is_existing_proposal_code(proposal_code):
            return None

        # Gravitational wave event proposals may be accessed by all SALT members
        if (
            self.database_service.sdb_proposal_type(proposal_code)
            != "Gravitational Wave Event"
        ):
            return types.AccessRule.PUBLIC_DATA_OR_INVESTIGATOR
        else:
            return types.AccessRule.PUBLIC_DATA_OR_INSTITUTION_MEMBER

    def artifact(self, plane_id: int) -> types.Artifact:
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

    def _proposal_code(self) -> str:
        propid_header_value = self.header_value("PROPID")
        propid = propid_header_value.upper() if propid_header_value else ""

        # Some FITS files have proposal codes which have been renamed in the database.
        existing = self.database_service.is_existing_proposal_code(propid)
        if not existing and propid.startswith("20"):
            raise ValueError("The proposal code {propid} does not exist in the SDB.")

        if propid and existing:
            return propid
        else:
            return ""

    def _block_visit_id(self) -> Optional[str]:
        # The block visit id from the FITS header...
        bvid_from_fits: Optional[str] = self.fits_file.header_value("BVISITID")

        # ... must be discarded if this observation is not part of a proposal
        proposal_code = self._proposal_code()
        if not proposal_code:
            bvid_from_fits = None

        # Get the block visit id from the database
        # As reading FITS headers takes a while, we first try reading information from
        # the database only...
        filename = Path(self.fits_file.file_path()).name
        night = (self.observation_start_time() - timedelta(hours=12)).date()
        if SALTObservation.file_data.night != night:
            SALTObservation.file_data = FileData(
                self.database_service.find_block_visit_ids(night, False), night
            )

        # ... but if this doesn't get details for the file, we try again, this time
        # including FITS headers.
        if filename not in SALTObservation.file_data.data:
            SALTObservation.file_data = FileData(
                self.database_service.find_block_visit_ids(night, True), night
            )

        if filename in SALTObservation.file_data.data:
            bvid_from_db = SALTObservation.file_data.data[filename].block_visit_id
        else:
            bvid_from_db = None

        # If the FITS file has a block visit id, it must be the same as that from
        # the database, unless the block visit belongs to another night and has
        # been replaced with a random value by the database search.
        if (bvid_from_fits and str(bvid_from_fits) != str(bvid_from_db)) and not (
            type(bvid_from_db) == str
            and not self.database_service.is_block_visit_in_night(
                int(bvid_from_fits), night
            )
        ):
            record_warning(
                Warning(
                    f"The block visit ids from the FITS header ({bvid_from_fits}) and the database ({bvid_from_db}) are different."
                )
            )

        # Some block visit ids don't exist in the FITS header but can be inferred
        # from the database. Also, if the two differ, the database inferred one is the
        # more conservative (and hence safer) bet.
        return str(bvid_from_db) if bvid_from_db is not None else ""

    def observation(
        self,
        observation_group_id: Optional[int],
        proposal_id: Optional[int],
        instrument: types.Instrument,
    ) -> types.Observation:
        proposal_code = self._proposal_code()
        if proposal_code:
            data_release_dates = self.database_service.find_release_date(proposal_code)
        else:
            data_release_dates = (
                self.observation_start_time().date(),
                self.observation_start_time().date(),
            )
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
        name = "SALT-" + str(bv_id)
        if len(name) > 40:
            name = name[:40]
        return types.ObservationGroup(group_identifier=str(bv_id), name=name)

    def observation_start_time(self) -> datetime:
        start_date = self.header_value("DATE-OBS")
        if not start_date:
            raise ValueError("Missing DATE-OBS header value.")
        start_time = self.header_value("TIME-OBS")
        if not start_time:
            raise ValueError("Missing TIME-OBS header value.")

        return parse_start_datetime(start_date, start_time)

    def observation_time(self, plane_id: int) -> types.ObservationTime:
        exposure_time_string = self.header_value("EXPTIME")
        if exposure_time_string:
            exposure_time = float(exposure_time_string)
            resolution = exposure_time
        else:
            record_warning(
                RuntimeWarning(
                    "No exposure time found. A value of 0 seconds is assumed."
                )
            )
            exposure_time = 0
            resolution = 100000
        return types.ObservationTime(
            end_time=self.observation_start_time() + timedelta(seconds=exposure_time),
            exposure_time=exposure_time * u.second,
            plane_id=plane_id,
            resolution=resolution * u.second,
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
        equinox_header_value = self.header_value("EQUINOX")
        equinox = float(equinox_header_value if equinox_header_value else "")
        if equinox == 0:  # TODO check if it is cal and use it instead
            return None
        return types.Position(dec=dec, equinox=equinox, plane_id=plane_id, ra=ra)

    def proposal(self) -> Optional[types.Proposal]:
        bv_id = self._block_visit_id()
        if bv_id is None:
            return None

        proposal_code = self._proposal_code()
        if not proposal_code:
            return None

        return types.Proposal(
            institution=types.Institution.SALT,
            pi=self.database_service.find_pi(proposal_code),
            proposal_code=proposal_code,
            proposal_type=self.database_service.find_proposal_type(proposal_code),
            title=self.database_service.find_proposal_title(proposal_code),
        )

    def proposal_investigators(
        self, proposal_id: int
    ) -> List[types.ProposalInvestigator]:
        proposal_code = self._proposal_code()
        investigators = self.database_service.find_proposal_investigators(proposal_code)
        return [
            types.ProposalInvestigator(
                proposal_id=proposal_id,
                investigator_id=str(investigator),
                institution=types.Institution.SALT,
                institution_memberships=self.database_service.institution_memberships(
                    int(investigator)
                ),
            )
            for investigator in investigators
        ]

    def target(self, observation_id: int) -> Optional[types.Target]:
        object_name = self.header_value("OBJECT")

        if object_name is None:
            return None

        if self.is_calibration() and not self.is_standard():
            return None

        return types.Target(
            name=object_name,
            observation_id=observation_id,
            standard=self.is_standard(),
            target_type=self.database_service.find_target_type(self._block_visit_id()),
        )

    def _obs_type(self):
        obs_type = (
            self.header_value("OBSTYPE").upper() if self.header_value("OBSTYPE") else ""
        )

        # CCDTYPE is a copy of OBSTYPE
        if not obs_type:
            obs_type = (
                self.header_value("CCDTYPE").upper()
                if self.header_value("CCDTYPE")
                else ""
            )

        return obs_type

    def _product_category(self):
        observation_object = (
            self.header_value("OBJECT").upper() if self.header_value("OBJECT") else ""
        )
        obs_type = self._obs_type()
        proposal_id = (
            self.header_value("PROPID").upper() if self.header_value("PROPID") else ""
        )

        obs_type_unknown = not obs_type or obs_type == "ZERO"

        if (
            proposal_id in ["CAL_ARC", "CAL_STABLE"]
            or "ARC" in obs_type
            or (
                obs_type_unknown
                and (observation_object == "ARC" or "_ARC" in observation_object)
            )
        ):
            return types.ProductCategory.ARC
        if (
            proposal_id == "CAL_BIAS"
            or "BIAS" in obs_type
            or (
                obs_type_unknown
                and (observation_object == "BIAS" or "_BIAS" in observation_object)
            )
        ):
            return types.ProductCategory.BIAS
        if (
            proposal_id in ["CAL_FLAT", "CAL_SKYFLAT"]
            or "FLAT" in obs_type
            or (
                obs_type_unknown
                and (observation_object == "FLAT" or "_FLAT" in observation_object)
            )
        ):
            return types.ProductCategory.FLAT
        if "DARK" in obs_type or (
            obs_type_unknown
            and (observation_object == "DARK" or "_DARK" in observation_object)
        ):
            return types.ProductCategory.DARK
        if (
            proposal_id.startswith("CAL_")
            or "STANDARD" in obs_type
            or (
                obs_type_unknown
                and (
                    observation_object == "STANDARD"
                    or "_STANDARD" in observation_object
                )
            )
        ):
            return types.ProductCategory.STANDARD
        if obs_type == "OBJECT" or obs_type == "SCIENCE":
            # Science files with no block visit id are not populated
            if self._block_visit_id() is None:
                raise ValueError(
                    f"The observation is marked as science but has no block visit id. "
                    f"The proposal code is '{proposal_id}'."
                )
            return types.ProductCategory.SCIENCE

        header_values = {
            "CCDTYPE": self.header_value("CCDTYPE"),
            "OBJECT": self.header_value("OBJECT"),
            "OBSTYPE": self.header_value("OBSTYPE"),
            "PROPID": self.header_value("PROPID"),
        }
        raise ValueError(
            f"The product category could not be determined. (Observation type: {obs_type}, FITS header values: {header_values})"
        )

    def _product_type(self) -> types.ProductType:
        obsmode_header_value = self.header_value("OBSMODE")
        obs_mode = obsmode_header_value.upper() if obsmode_header_value else ""
        instrume_header_value = self.header_value("INSTRUME")
        instrument = instrume_header_value.upper() if instrume_header_value else ""
        propid_header_value = self.header_value("PROPID")
        proposal_id = propid_header_value.upper() if propid_header_value else ""
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

        header_values = {
            "INSTRUME": instrume_header_value,
            "OBSMODE": obsmode_header_value,
            "PROPID": propid_header_value,
        }
        raise ValueError(
            f"The product type could not be determined. (Product Category: {product_category}, observation mode: {obs_mode}, instrument: {instrument}, FITS header values: {header_values})"
        )

    def _intent(self) -> types.Intent:
        product_category = self._product_category()

        if self.is_calibration():
            return types.Intent.CALIBRATION
        elif product_category == types.ProductCategory.SCIENCE:
            return types.Intent.SCIENCE

        raise ValueError(
            f"The intent could not be determined. (Product category: {product_category})"
        )

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
        propid_header_value = self.fits_file.header_value("PROPID")
        proposal_id = propid_header_value.upper() if propid_header_value else ""
        # If the FITS file is Junk, Unknown, ENG or CAL_GAIN, do not store the observation.
        if proposal_id in ("JUNK", "UNKNOWN", "NONE", "ENG", "CAL_GAIN", "TEST"):
            return True
        # Do not store engineering data.
        # Proposal ids referring to an actual proposal will always start with a "2" (as in 2020-1-SCI-014).
        if not proposal_id.startswith("2") and (
            "ENG_" in proposal_id or "ENG-" in proposal_id
        ):
            return True

        object_header_value = self.header_value("OBJECT")
        observation_object = object_header_value.upper() if object_header_value else ""
        # Do not store commissioning data that pretends to be science.
        if "COM-" in proposal_id or "COM_" in proposal_id:
            if observation_object == "DUMMY":
                return True

        # If the FITS header does not include the observation date and time, do not
        # store its data.
        observation_date = self.fits_file.header_value("DATE-OBS")
        observation_time = self.fits_file.header_value("TIME-OBS")
        if not observation_date or not observation_time:
            return True

        # Ignore calibrations unless they are part of a proposal.
        proposal_id = self.header_value("PROPID") or ""
        is_standard = self.is_standard()
        try:
            # Checking whether the proposal code exists might result in an exception.
            # But in this case we should not ignore the file.
            if (
                not self.database_service.is_existing_proposal_code(proposal_id)
                and not is_standard
            ):
                return True
        except:
            pass

        # Ignore "science" proposals without a proposal code and block visit id
        product_type = self._obs_type()
        is_science = (
            product_type == "OBJECT" or product_type == "SCIENCE"
        ) and not is_standard
        if is_science and not self._block_visit_id():
            return True

        # Ignore deleted and in queue blocks
        if self._block_visit_id() and self.database_service.find_observation_status(
            self._block_visit_id()
        ) in [Status.DELETED, Status.IN_QUEUE]:
            return True

        return False
