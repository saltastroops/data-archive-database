import glob
import uuid
import os
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
        def create_reduced_path(path: str) -> str:
            reduced_dir = os.path.join(os.path.dirname(Path(path).parent), "product/*.fits")

            reduced_paths = glob.glob(reduced_dir)

            _reduced_path = ""

            for _path in reduced_paths:
                if _path.endswith(os.path.basename(path)):
                    _reduced_path = _path

            return _reduced_path

        raw_path = self.fits_file.file_path()
        reduced_path = create_reduced_path(raw_path)

        identifier = uuid.uuid4()

        return types.Artifact(
            content_checksum=self.fits_file.checksum(),
            content_length=self.fits_file.size(),
            identifier=identifier,
            name=os.path.basename(raw_path),
            plane_id=plane_id,
            paths=types.CalibrationLevel(
                raw=os.path.relpath(raw_path, get_fits_base_dir()),
                reduced=os.path.relpath(reduced_path, get_fits_base_dir())
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
        start_date_time_str = self.header_value("DATE-OBS") + " " + self.header_value("TIME-OBS")
        start_date_time = datetime.strptime(start_date_time_str, '%Y-%m-%d %H:%M:%S.%f')
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
        proposal_id = self.header_value("PROPID")
        object_name = self.header_value("OBJECT")
        if (
            object_name.upper() == "ARC"
            or object_name.upper() == "BIAS"
            or object_name.upper() == "FLAT"
            or not self.block_visit_id
        ):
            return None
        is_standard = False
        if (
            proposal_id.upper() == "CAL_SPST"
            or proposal_id.upper() == "CAL_LICKST"
            or proposal_id.upper() == "CAL_RVST"
        ):
            is_standard = True

        return types.Target(
            name=object_name,
            observation_id=observation_id,
            standard=is_standard,
            target_type=self.database_service.find_target_type(self.block_visit_id),
        )

    def _product_type(self) -> types.ProductType:
        observation_object = self.header_value("OBJECT")
        product_type = self.header_value("OBSTYPE")
        if observation_object.upper() == "ARC" or product_type.upper() == "ARC":
            return types.ProductType.ARC
        elif observation_object.upper() == "BIAS" or product_type.upper() == "BIAS":
            return types.ProductType.BIAS
        elif observation_object.upper() == "FLAT" or product_type.upper() == "FLAT" or observation_object.upper() == "FLAT FIELD" or product_type.upper() == "FLAT FIELD":
            return types.ProductType.FLAT
        elif observation_object.upper() == "DARK" or product_type.upper() == "DARK":
            return types.ProductType.DARK
        elif product_type.upper() == "OBJECT" or product_type.upper() == "SCIENCE":
            # TODO Check if there is any other product type for SALT instruments
            return types.ProductType.SCIENCE
        else:
            raise ValueError(
                f"Product type of file ${self.fits_file.file_path()} could not be determined"
            )

    def _intent(self) -> types.Intent:
        observation_object = self.header_value("OBJECT")
        product_type = self.header_value("OBSTYPE")
        if (
            observation_object.upper() == "ARC"
            or product_type.upper() == "ARC"
            or observation_object.upper() == "BIAS"
            or product_type.upper() == "BIAS"
            or observation_object.upper() == "FLAT"
            or product_type.upper() == "FLAT"
            or observation_object.upper() == "FLAT FIELD"
            or product_type.upper() == "FLAT FIELD"
            or observation_object.upper() == "STANDARDS"
            or product_type.upper() == "STANDARDS"
            or observation_object.upper() == "DARK"
            or product_type.upper() == "DARK"
        ):
            return types.Intent.CALIBRATION
        elif product_type.upper() == "OBJECT" or product_type.upper() == "SCIENCE":
            return types.Intent.SCIENCE
        raise ValueError(f"Intent for file {self.file_path()} could not be determined")

    def is_calibration(self):
        return "CAL_" in self.header_value("PROPID")
