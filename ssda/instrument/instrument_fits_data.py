import os
import pandas as pd
from abc import ABC, abstractmethod
from astropy.io import fits
from datetime import date, datetime
from enum import Enum
from typing import Any, List, NamedTuple, Optional, Tuple

from astropy.io.fits import ImageHDU, PrimaryHDU
from ssda.connection import ssda_connect
from ssda.institution import Institution
from ssda.observation_status import ObservationStatus
from ssda.telescope import Telescope


class DataCategory(Enum):
    """
    Enumeration of the data categories.

    The values must be the same as those of the dataCategory column in the DataCategory
    table.

    """

    ARC = "Arc"
    BIAS = "Bias"
    FLAT = "Flat"
    SCIENCE = "Science"

    def id(self) -> int:
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
            raise ValueError(
                "The data category {} is not included in the DataCategory table.".format(
                    self.value
                )
            )

        return int(df["dataCategoryId"][0])


class DataPreviewType(Enum):
    """
    Enumeration of the data preview types.

    The values must be the same as those of the dataPreviewType column in the
    DataPreviewType table.

    """

    HEADER = 'Header'
    IMAGE = "Image"

    def id(self) -> int:
        """
        The id of this data preview type.

        Returns
        -------
        id : int
            The id.

        """

        sql = """
        SELECT dataPreviewTypeId FROM DataPreviewType WHERE dataPreviewType=%s
        """
        df = pd.read_sql(sql, con=ssda_connect(), params=(self.value,))
        if len(df) == 0:
            raise ValueError('There is no database entry for the preview type {}'.format(self.value))
        return int(df['dataPreviewTypeId'])


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
        with fits.open(fits_file) as hdul:
            # Only use keywords and values from the primary header
            self.header = hdul[0].header

    @property
    def header_text(self) -> str:
        """
        The primary header content as a properly formatted string. The final END line
        and any subsequent empty lines are not included.

        Returns
        -------
        header : str
            The primary header content.

        """

        # Split the header into lines of 80 characters
        content = str(self.header)
        lines = [content[i:i + 80] for i in range(0, len(content), 80)]

        # Only include content up to the END line
        end_index = [line.strip() for line in lines].index("END")
        return "\n".join(lines[:end_index])

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
    def create_preview_files(self) -> List[Tuple[str, DataPreviewType]]:
        """
        Create the preview files for the FITS file.

        Returns
        -------
        paths: list of str
            The list of file paths of the created preview files.

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
    def institution(self) -> Institution:
        """
        The institution (such as SALT or SAAO) operating the telescope with which the
        data was taken.

        Returns
        -------
        institution : Institution
            The institution.

        """

        raise NotImplementedError

    @abstractmethod
    def instrument_details_file(self) -> str:
        """
        The path of the file containing FITS header keywords and corresponding columns
        of the instrument table.

        The format of the file content must be as follows:

        - Lines starting with a '#' are comments.
        - Lines containing only whitespace are comments.
        - Any non-comment line has a FITS header keyword and a datavase column,
          separated by whitespace.

        For example:

        # First column is for FITS header keywords
        # Second column is for table columns

        AMPSEC         amplifierSection
        AMPTEM         amplifierTemperature
        ATM1_1         amplifierReadoutX
        ATM1_2         amplifierReadoutY

        Returns
        -------
        path : str
            The file path.

        """

        raise NotImplementedError

    @abstractmethod
    def instrument_id_column(self) -> str:
        """
        The name of the column containing the id (i.e. the primary key) in the table
        containing the instrument details for the instrument that took the data.

        Returns
        -------
        column : str
            The column name.

        """

        raise NotImplementedError

    @abstractmethod
    def instrument_table(self) -> str:
        """
        The name of the table containing the instrument details for the instrument that
        took the data.

        Returns
        -------
        table : str
            The name of the instrument details table.

        """

        raise NotImplementedError

    @abstractmethod
    def investigator_ids(self) -> List[int]:
        """
        The list of ids of users who are an investigator on the proposal for the FITS
        file.

        The ids are those assigned by the institution (such as SALT or the SAAO) which
        received the proposal. These may differ from ids used by the data archive.

        An empty list is returned if the FITS file is not linked to a proposal.

        Returns
        -------
        ids : list of id
            The list of user ids.

        """

        raise NotImplementedError

    @abstractmethod
    def is_proprietary(self) -> bool:
        """
        Indicate whether the data for the FITS file is proprietary.

        Returns
        -------
        proprietary : bool
            Whether the data is proprietary.

        """

        raise NotImplementedError

    @abstractmethod
    def available_from_date(self) -> date:
        """
        Indicate whether the data for the FITS file is proprietary.

        Returns
        -------
        proprietary : bool
            Whether the data is proprietary.

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

    @abstractmethod
    def preprocess_header_value(self, keyword: str, value: str) -> Any:
        """
        Preprocess a FITS header value for use in the database.

        Parameters
        ----------
        keyword : str
            FITs header keyword
        value : str
            FITS header value

        Returns
        -------
        preprocessed : Any
            The preprocessed value.

        """

        raise NotImplementedError

    def principal_investigator(self) -> Optional[PrincipalInvestigator]:
        """
        The principal investigator for the proposal to which this file belongs.
        If the FITS file is not linked to any observation, the status is assumed to be
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
        The telescope used for observing the data in the FITS file.

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
