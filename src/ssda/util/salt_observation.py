import random
import string
from typing import Optional, List, Iterable
from dateutil.parser import parse
from datetime import timedelta
from astropy.coordinates import Angle

import astropy.units as u
from ssda.database.sdb import SaltDatabaseService
from ssda.util.fits import FitsFile
from ssda.database.ssda import DatabaseService as SsdaDB

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
            product_type=self.__product_type()
        )

    def observation(self, proposal_id: Optional[int], instrument: types.Instrument) -> types.Observation:
        return types.Observation(
            data_release=self.database_service.find_release_date(int(self.header_value("BVISITID"))),
            instrument=instrument,
            intent=self.__intent(),
            meta_release=self.database_service.find_meta_release_date(int(self.header_value("BVISITID"))),
            observation_group=int(self.header_value("BVISITID")),  # TODO parse a group ot just an id
            observation_type=types.ObservationType.OBJECT,
            proposal_id=proposal_id,
            status=self.database_service.find_observation_status(int(self.header_value("BVISITID"))),
            telescope=types.Telescope.SALT
        )

    def observation_time(self, plane_id: int) -> types.ObservationTime:
        start_time = parse(self.header_value("TIME-OBS"))
        exposure_time = float(self.header_value("EXPTIME"))
        return types.ObservationTime(
            end_time=start_time + timedelta(seconds=exposure_time),
            exposure_time=exposure_time * u.second,
            plane_id=plane_id,
            resolution=exposure_time * u.second,
            start_time=start_time
        )

    def position(self, plane_id: int) -> Optional[types.Position]:
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
        return types.Proposal(
            institution=types.Institution.SALT,
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

    def target(self, observation_id: int) -> types.Target:
        proposal_id = self.header_value("PROPID")
        object_name = self.header_value("OBJECT").strip()
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
        raise ValueError(f"unknown intent for file {self.file_path}")

    @property
    def stokes_parameter(self) -> Iterable[types.StokesParameter]:
        pattern: str = self.header_value("WPPATERN")

        if pattern.upper() == "NONE" or not pattern:
            return []
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

