import uuid
from dateutil.tz import tz
import os
from typing import Optional, List, Iterable
from dateutil.parser import parse
from datetime import timedelta, datetime
from astropy.coordinates import Angle

import astropy.units as u
from ssda.database.sdb import SaltDatabaseService
from ssda.util.fits import FitsFile

from ssda.util import types


class SALTObservation:
    def __init__(self, fits_file: FitsFile, database_service:  SaltDatabaseService):
        """
        :param fits_file:
        """
        self.headers = fits_file.headers
        self.header_value = fits_file.header_value
        self.size = fits_file.size()
        self.checksum = fits_file.checksum
        self.fits_file = fits_file
        self.file_path = fits_file.file_path
        self.database_service = database_service

    def artifact(self, plane_id: int) -> types.Artifact:

        path = self.fits_file.file_path()
        identifier = uuid.uuid4()

        return types.Artifact(
            content_checksum=self.fits_file.checksum(),
            content_length=self.fits_file.size(),
            identifier=identifier,
            name=path.split("/")[-1],
            plane_id=plane_id,
            path=path,
            product_type=self._product_type()
        )

    def observation(self,
                    observation_group_id: Optional[int],
                    proposal_id: Optional[int],
                    instrument: types.Instrument
                    ) -> types.Observation:

        if not self.header_value("BVISITID"):
            today = datetime.now()
            release_date_tz = \
                datetime(year=today.year,
                         month=today.month,
                         day=today.day,
                         hour=today.hour,
                         minute=today.minute,
                         second=today.second,
                         tzinfo=tz.gettz("Africa/Johannesburg"))
            status = types.Status.ACCEPTED
        else:
            release_date_tz = self.database_service.find_release_date(int(self.header_value("BVISITID")))
            status = self.database_service.find_observation_status(int(self.header_value("BVISITID")))
        return types.Observation(
            data_release=release_date_tz,
            instrument=instrument,
            intent=self._intent(),
            meta_release=release_date_tz,
            observation_group_id=observation_group_id,
            observation_type=types.ObservationType.OBJECT,
            proposal_id=proposal_id,
            status=status,
            telescope=types.Telescope.SALT
        )

    def observation_group(self) -> Optional[types.ObservationGroup]:
        if not self.header_value("BVISITID"):
            return None
        return types.ObservationGroup(
            group_identifier=self.header_value("BVISITID"),
            name=self.header_value("BVISITID")  # Todo block name
        )

    def observation_time(self, plane_id: int) -> types.ObservationTime:
        start_time = parse(self.header_value("TIME-OBS"))
        start_time_tz = \
            datetime(year=start_time.year,
                     month=start_time.month,
                     day=start_time.day,
                     hour=start_time.hour,
                     minute=start_time.minute,
                     second=start_time.second,
                     tzinfo=tz.gettz("Africa/Johannesburg"))
        exposure_time = float(self.header_value("EXPTIME"))
        return types.ObservationTime(
            end_time=start_time_tz + timedelta(seconds=exposure_time),
            exposure_time=exposure_time * u.second,
            plane_id=plane_id,
            resolution=exposure_time * u.second,
            start_time=start_time_tz
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
        equinox = float(self.header_value("EQUINOX"))
        if equinox == 0:
            return None
        return types.Position(
            dec=dec,
            equinox=equinox,
            plane_id=plane_id,
            ra=ra
        )

    def proposal(self) -> Optional[types.Proposal]:
        if not self.fits_file.header_value("BVISITID"):
            return None

        return types.Proposal(
            institution=types.Institution.SALT,
            pi=self.database_service.find_pi(int(self.fits_file.header_value("BVISITID"))),
            proposal_code=self.database_service.find_proposal_code(int(self.header_value("BVISITID"))),
            title=self.database_service.find_proposal_title(int(self.header_value("BVISITID")))
        )

    def proposal_investigators(self, proposal_id: int) -> List[types.ProposalInvestigator]:
        investigators = self.database_service.find_proposal_investigators(int(self.header_value("BVISITID")))
        return [
            types.ProposalInvestigator(
                proposal_id=proposal_id,
                investigator_id=str(investigator)
            ) for investigator in investigators
        ]

    def target(self, observation_id: int) -> types.Target:
        proposal_id = self.header_value("PROPID")
        object_name = self.header_value("OBJECT").strip()
        block_visit_id = self.header_value("BVISITID")
        if object_name == types.ProductType.ARC or \
           object_name == types.ProductType.BIAS or \
           object_name == types.ProductType.FLAT:
            raise ValueError("Calibrations (Arcs, Bias and Flats) doesn't have a target")
        is_standard = False
        if proposal_id.upper() == "CAL_SPST" or \
                proposal_id.upper() == "CAL_LICKST" or\
                proposal_id.upper() == "CAL_RVST" or\
                proposal_id.upper() == "CAL_SPST":
            is_standard = True
        return types.Target(
            name=object_name,
            observation_id=observation_id,
            standard=is_standard,
            target_type='Unknown' if not block_visit_id else
            self.database_service.find_target_type(int(block_visit_id))
        )

    def _product_type(self) -> types.ProductType:
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

    def _intent(self) -> types.Intent:
        observation_object: str = self.header_value("OBJECT")
        product_type: str = self.header_value("OBSTYPE")
        if observation_object.upper() == "ARC" or \
                observation_object.upper() == "BIAS" or \
                observation_object.upper() == "FLAT" or \
                observation_object.upper() == "STANDARDS":
            return types.Intent.CALIBRATION
        elif product_type.upper() == "OBJECT" or product_type.upper() == "SCIENCE":
            return types.Intent.SCIENCE
        raise ValueError(f"unknown intent for file {self.file_path}")

    def is_calibration(self):
        return "CAL_" in self.header_value("PROPID")
