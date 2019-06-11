import os
import pandas as pd
from abc import ABC, abstractmethod
from astropy.io import fits
from datetime import date, datetime
from enum import Enum
from typing import List, NamedTuple, Optional

from connection import ssda_connect
from observation_status import ObservationStatus
from telescope import Telescope


class DataCategory(Enum):
    """
    Enumeration of the data categories.

    The values must be the same as those of the dataCategory column in the DataCategory
    table.

    """

    ARC = 'Arc'
    BIAS = 'Bias'
    FLAT = 'Flat'
    SCIENCE = 'Science'

    def id(self):
        """
        Return the primary key of the DataCategory entry for this data category.

        Returns
        -------
        id : int
            The primary key.

        """
        sql = """
        SELECT dataCategoryId from DataCategory where dataCategory=%s
        """
        df = pd.read_sql(sql, con=ssda_connect(), params=(self.value,))
        if len(df) == 0:
            raise ValueError('The data category {} is not included in the DataCategory table.'.format(self.value))

        return int(df['dataCategoryId'])


class PrincipalInvestigator(NamedTuple):
    """
    A Principal Investigator (PI).

    """

    family_name: str
    """The PI's family name (last name)."""

    given_name: str
    """The PI's given name (first name)."""


class Target(NamedTuple):
    """
    A target.

    """

    name: str
    """The target name."""

    ra: float
    """The right ascension, in degrees."""

    dec: float
    """The declination, in degrees."""

    target_type: Optional[str]
    """The target type, as a numerical SIMBAD Code."""


class InstrumentFitsData(ABC):
    """
    Data obtained from an instrument FITS file.

    This is an abstract base class, which needs to be extended for the various
    instruments. Its constructor sets two properties:

    * The FITS header with FITS keywords and values.
    * The size of the FITS file.

    Parameters
    ----------
    fits_file : str
        Path of the FITS file.

    Attributes
    ----------
    file_path : str
        Absolute path of the FITS file.
    file_size : int
        Size of the FITS file, in bytes.
    header : Header
        FITS header.

    """

    def __init__(self, fits_file: str):
        self.file_path = os.path.abspath(fits_file)
        self.file_size = os.path.getsize(fits_file)
        with fits.open(fits_file) as header_data_unit_list:
            self.header = header_data_unit_list[0].header

    @staticmethod
    @abstractmethod
    def fits_files(night: date) -> List[str]:
        """
        The list of FITS files generated for the instrument during a night.

        Parameters
        ----------
        night : date
            Start date of the night for which the FITS files are returned.

        Returns
        -------
        files : list of str
            The list of file paths.

        """

        raise NotImplementedError

    @abstractmethod
    def data_category(self) -> DataCategory:
        """
        The category (such as science or arc) of the data contained in the FITS file.

        Returns
        -------
        category : DataCategory
            The data category.

        """

        raise NotImplementedError

    @abstractmethod
    def night(self) -> date:
        """
        The night when the data was taken.

        Returns
        -------
        night : date
            The date of the night when the data was taken.

        """

        raise NotImplementedError

    def observation_status(self) -> ObservationStatus:
        """
        The status (such as Accepted) for the observation to which the FITS file
        belongs.

        If the FIS file is not linked to any observation, the status is assumed to be
        Accepted.

        Returns
        -------
        status : ObservationStatus
            The observation status.

        """

        raise NotImplementedError

    def principal_investigator(self) -> Optional[PrincipalInvestigator]:
        """

        The principal investigator for the proposal to which this File belonhs.
        If the FIS file is not linked to any observation, the status is assumed to be
        Accepted.

        Returns
        -------
        pi : PrincipalInvestigator
            The principal investigator for the proposal.

        """

        pass

    @abstractmethod
    def proposal_code(self) -> Optional[str]:
        """
        The unique identifier of the proposal to which the FITS file belongs.

        The identifier is the identifier that would be used whe referring to the
        proposal communication between the Principal Investigator and another
        astronomer. For example, an identifier for a SALT proposal might look like
        2019-1-SCI-042.

        None is returned if the FITS file is not linked to a proposal.

        Returns
        -------
        code : str
            The proposal code.

        """

        raise NotImplementedError

    @abstractmethod
    def proposal_title(self) -> Optional[str]:
        """
        The proposal title of the proposal to which the FITS file belongs.

        None is returned if the FITS file is not linked to a proposal.

        Returns
        -------
        title : str
            The proposal title.

        """

        raise NotImplementedError

    @abstractmethod
    def start_time(self) -> datetime:
        """
        The start time, i.e. the time when taking data for the FITS file began.

        Returns
        -------
        time : datetime
            The start time.

        """

        raise NotImplementedError

    @abstractmethod
    def target(self) -> Optional[Target]:
        """
        The target specified in the FITS file.

        None is returned if no target is specified, i.e. if no target position is
        defined.

        Returns
        -------

        """

        raise NotImplementedError

    @abstractmethod
    def telescope(self) -> Telescope:
        """
        The telescope used for generating the data in the FITS file.

        Returns
        -------
        telescope : Telescope
            The telescope.

        """

        raise NotImplementedError

    @abstractmethod
    def telescope_observation_id(self) -> str:
        """
        The id used by the telescope for the observation.

        If the FITS file was taken as part of an observation, this method returns the
        unique id used by the telescope for identifying this observation.

        If the FITS file was not taken as part of an observation (for example because it
        refers to a standard), this method returns None.

        Returns
        -------
        id : str
            The unique id used by the telescope for identifying the observation.

        """

        raise NotImplementedError
