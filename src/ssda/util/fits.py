from __future__ import annotations
import glob
import os
import random
import hashlib
import string
from abc import ABC, abstractmethod
from datetime import date, timedelta
from typing import Iterator, Set, Optional
from astropy.units import Quantity
from astropy.io import fits
from ssda.util import types


# The path of the base directory where all FITS files are stored.
_fits_base_dir = ""


def set_fits_base_dir(path: str) -> None:
    """
    Set the path of the base directory where all FITS files are stored.

    Parameters
    ----------
    path : str
        Path of the base directory.

    """
    global _fits_base_dir
    _fits_base_dir = path


def get_fits_base_dir():
    """
    Get the path of the base directory where all FITS files are stored.

    Returns
    -------
    str
        The path of the base directory.

    """

    return _fits_base_dir


class FitsFile(ABC):
    """
    A FITS file interface.

    """

    @abstractmethod
    def size(self) -> Quantity:
        """
        The size of the file.

        Returns
        -------
        Quantity:
           The file size.

        """

        raise NotImplementedError

    @abstractmethod
    def checksum(self) -> str:
        """
        The checksum for the file.

        Returns
        -------
        str :
            The checksum.

        """

        raise NotImplementedError

    @abstractmethod
    def instrument(self) -> types.Instrument:
        """
        The instrument a file belongs too.

        Returns
        -------
        instrument: Instrument
            The instrument.

        """

        raise NotImplementedError

    @abstractmethod
    def telescope(self) -> types.Instrument:
        """
        The telescope used.

        Returns
        -------
        telescope: Telescope
            The telescope.

        """

        raise NotImplementedError

    @abstractmethod
    def header_value(self, keyword: str) -> str:
        """
        The FITS header value for a keyword.

        A ValueError is raised if the keyword does not exist in the FITS header.

        Parameters
        ----------
        keyword : str
            Header keyword.

        Returns
        -------
        str
            The value for the keyword.

        Raises
        ------
        ValueError
            If the keyword does not exist in the header.

        """

        raise NotImplementedError

    @abstractmethod
    def file_path(self) -> str:
        """
        The FITS header value for a keyword.

        A ValueError is raised if the keyword does not exist in the FITS header.

        Parameters
        ----------
        keyword : str
            Header keyword.

        Returns
        -------
        str
            The value for the keyword.

        Raises
        ------
        ValueError
            If the keyword does not exist in the header.

        """

        raise NotImplementedError


def fits_file_paths(
    nights: types.DateRange, instruments: Set[types.Instrument], base_dir: str
) -> Iterator[str]:
    """
    The paths of the FITS files for a date range and a set of instruments.

    Parameters
    ----------
    nights : DateRange
        Nights.
    instruments : Set[Instrument]
        Instruments.
    base_dir : str
        Base directory containing all the FITS files.

    Returns
    -------
    An iterator with the file paths.

    """

    night = nights.start
    while night < nights.end:
        for instrument in instruments:
            for path in sorted(
                glob.iglob(
                    os.path.join(fits_file_dir(night, instrument, base_dir), "*.fits")
                )
            ):
                yield path
        night += timedelta(days=1)


def fits_file_dir(night: date, instrument: types.Instrument, base_dir: str) -> str:
    """
    The directory containing the FITS file for a night and instrument.

    Parameters
    ----------
    night : date
        Start date of the night.
    instrument : Instrument
        types.Instrument.
    base_dir : str
        Path of the base directory where all the FITS files are located.

    Returns
    -------
    str
        Path of the directory.

    """

    year = night.strftime("%Y")
    month = night.strftime("%m")
    day = night.strftime("%d")

    # avoid a double slash
    if base_dir == "/":
        base_dir = ""

    if instrument == types.Instrument.HRS:
        return f"{base_dir}/salt/data/{year}/{month}{day}/hrs/raw"
    elif instrument == types.Instrument.RSS:
        return f"{base_dir}/salt/data/{year}/{month}{day}/rss/raw"
    elif instrument == types.Instrument.SALTICAM:
        return f"{base_dir}/salt/data/{year}/{month}{day}/scam/raw"
    else:
        raise NotImplementedError(f"Not implemented for {instrument}")


class StandardFitsFile(FitsFile):

    def __init__(self, path: str) -> None:
        hdulist = fits.open(path)
        self.path = path
        self.headers = hdulist[0].header

    def size(self) -> Quantity:
        return os.stat(self.path).st_size * types.byte

    def instrument(self) -> types.Instrument:
        instrument_value = self.header_value("INSTRUME").upper()
        if instrument_value == "RSS":
            return types.Instrument.RSS
        elif instrument_value.upper() == "HRS":
            return types.Instrument.HRS
        elif instrument_value.upper() == "SALTICAM":
            return types.Instrument.SALTICAM
        else:
            raise ValueError(f"Unknown instrument in file {self.path}: {instrument_value}")

    def telescope(self) -> types.Telescope:

        telescope_value = self.header_value("OBSERVAT").upper()
        if telescope_value == "SALT":
            return types.Telescope.SALT
        else:
            raise ValueError(f"Unknown telescope in file {self.path}: {telescope_value}")

    def file_path(self) -> str:
        return self.path

    def checksum(self) -> str:
        letters = string.ascii_lowercase
        result = "".join(random.choice(letters) for _ in range(20))

        # Open,close, read file and calculate MD5 on its contents
        with open(self.file_path(), "rb") as f:
            # read contents of the file
            data = f.read()
            # pipe contents of the file through
            md5_returned = hashlib.md5(data).hexdigest()
        return md5_returned

    def header_value(self, keyword: str) -> Optional[str]:
        try:
            value = str(self.headers[keyword]).strip()
            return None if value.upper() == "NONE" else value
        except KeyError:
            return None


class DummyFitsFile(FitsFile):
    def __init__(self, path: str) -> None:
        self.path = path

    def size(self) -> Quantity:
        return random.randint(1000, 100000000) * types.byte

    def checksum(self) -> str:
        letters = string.ascii_lowercase
        return "".join(random.choice(letters) for _ in range(50))

    def header_value(self, keyword: str) -> str:
        letters = string.ascii_lowercase
        return "".join(random.choice(letters) for _ in range(random.randint(1, 10)))
