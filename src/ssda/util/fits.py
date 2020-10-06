from __future__ import annotations
import os
import random
import hashlib
import re
import string
from abc import ABC, abstractmethod
from datetime import date, timedelta
from pathlib import Path
from typing import Iterator, List, Set, Optional
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


def get_night_date(path: str) -> str:
    """
    Extract the night start date from the FITS file path.

    Parameters
    ----------
    path : str
        Path of the FITS file.

    Returns
    -------
    str
        The night date.

    """

    # search for the night date
    date_search = re.search(r"(\d{4})/(\d{2})(\d{2})", path)
    if not date_search:
        raise ValueError(f"Invalid date format: {date_search}")
    # format the date as "yyyy-mm-dd"
    night_date = f"{date_search.group(1)}-{date_search.group(2)}-{date_search.group(3)}"

    return night_date


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
    def telescope(self) -> types.Telescope:
        """
        The telescope used.

        Returns
        -------
        telescope: Telescope
            The telescope.

        """

        raise NotImplementedError

    @abstractmethod
    def header_value(self, keyword: str) -> Optional[str]:
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
        paths: List[Path] = []
        for instrument in instruments:
            paths.extend(
                Path(fits_file_dir(night, instrument, base_dir)).glob("*.fits")
            )
        # Different instruments, such as Salticam and BCAM, may have the same file
        # paths, hence we use set() to eliminate duplicate values.
        for path in sorted(set(paths)):
            if "tmp" in path.name:
                continue
            yield str(path)
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
    elif instrument == types.Instrument.SALTICAM or instrument == types.Instrument.BCAM:
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
        header_value = self.header_value("INSTRUME")
        instrument_value = header_value.upper() if header_value else None
        if instrument_value == "RSS":
            return types.Instrument.RSS
        elif instrument_value == "HRS":
            return types.Instrument.HRS
        elif instrument_value == "SALTICAM":
            return types.Instrument.SALTICAM
        elif instrument_value == "BCAM":
            return types.Instrument.BCAM
        else:
            # There are some HRS files missing the INSTRUME keyword. We rely on the
            # filename together with an HRS-specific header keyword instead. (As that
            # keyword is for a temperature it should never be 0.)
            filename = os.path.basename(self.file_path())
            if (
                filename.startswith("H2") or filename.startswith("R2")
            ) and self.header_value("TEM-RMIR"):
                return types.Instrument.HRS
            # There are some BCAM files missing the INSTRUME keyword.
            # For these files we rely on the file name to contain the word "bcam".
            if "bcam" in filename.lower():
                return types.Instrument.BCAM
            raise ValueError(
                f"Unknown instrument in file {self.path}: {instrument_value}"
            )

    def telescope(self) -> types.Telescope:
        # TODO UPDATE
        return types.Telescope.SALT
        # telescope_value = (
        #     self.header_value("OBSERVAT")
        #     if not self.header_value("OBSERVAT")
        #     else self.header_value("OBSERVAT").upper()
        # )
        #
        # if telescope_value == "SALT":
        #     return types.Telescope.SALT
        # else:
        #     raise ValueError(
        #         f"Unknown telescope in file {self.path}: {telescope_value}"
        #     )

    def file_path(self) -> str:
        return self.path

    def checksum(self) -> str:
        # Open,close, read file and calculate MD5 on its contents
        with open(self.file_path(), "rb") as f:
            # read contents of the file
            data = f.read()
            # pipe contents of the file through
            md5_returned = hashlib.md5(data).hexdigest()
        return md5_returned

    def header_value(self, keyword: str) -> Optional[str]:
        try:
            header_value = self.headers[keyword]
            if header_value is None:
                return None
            value = str(header_value).strip()
            return None if value.upper() == "NONE" else value
        except KeyError:
            return None


class DummyFitsFile(FitsFile):
    def __init__(self, path: str) -> None:
        self.path = path

    def checksum(self) -> str:
        letters = string.ascii_lowercase
        return "".join(random.choice(letters) for _ in range(50))

    def file_path(self) -> str:
        return "some/file/path"

    def header_value(self, keyword: str) -> Optional[str]:
        letters = string.ascii_lowercase
        return "".join(random.choice(letters) for _ in range(random.randint(1, 10)))

    def instrument(self) -> types.Instrument:
        return types.Instrument.RSS

    def size(self) -> Quantity:
        return random.randint(1000, 100000000) * types.byte

    def telescope(self) -> types.Telescope:
        return types.Telescope.SALT
