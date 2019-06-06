import os
from abc import ABC, abstractmethod
from astropy.io import fits
from datetime import date

from observation_status import ObservationStatus
from telescope import Telescope


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
    file_size : int
        Size of the FITS file, in bytes.
    header : Header
        FITS header.

    """

    def __init__(self, fits_file: str):
        self.file_size = os.path.getsize(fits_file)
        with fits.open(fits_file) as header_data_unit_list:
            self.header = header_data_unit_list[0].header

    @staticmethod
    @abstractmethod
    def fits_files(night: date) -> [str]:
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
