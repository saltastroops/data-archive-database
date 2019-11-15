from __future__ import annotations
import glob
import os
import random
import string
from abc import ABC, abstractmethod
from datetime import date, timedelta
from typing import Iterator, Set, Dict, Any, Optional
from astropy.units import Quantity
from astropy.io import fits
from ssda.util import types
from ssda.util.types import DateRange, Instrument


# The path of the base directory where all FITS files are stored.
_fits_base_dir: str = ''


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
    def instrument(self) -> Instrument:
        """
        The instrument a file belongs too.

        Returns
        -------
        str :
            The Instrument.

        """

        raise NotImplementedError

    @abstractmethod
    def headers(self) -> Dict[str, Any]:
        """
        The FITS header value for a keyword.

        Returns
        -------
        dict
            FITS headers key value pair.
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
    nights: DateRange, instruments: Set[Instrument], base_dir: str
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


def fits_file_dir(night: date, instrument: Instrument, base_dir: str) -> str:
    """
    The directory containing the FITs file for a night and instrument.

    Parameters
    ----------
    night : date
        Start date of the night.
    instrument : Instrument
        Instrument.
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

    if instrument == Instrument.HRS:
        return f"{base_dir}/salt/data/{year}/{month}{day}/hrs/raw"
    elif instrument == Instrument.RSS:
        return f"{base_dir}/salt/data/{year}/{month}{day}/rss/raw"
    elif instrument == Instrument.SALTICAM:
        return f"{base_dir}/salt/data/{year}/{month}{day}/scam/raw"
    else:
        raise NotImplementedError(f"Not implemented for {instrument}")


class StandardFitsFile(FitsFile):
    def __init__(self, path: str) -> None:
        self.path = path

    def size(self) -> Quantity:
        return random.randint(1000, 1000000000) * types.byte

    def instrument(self) -> Instrument:
        dirs = self.path.split("/")
        instrument_dir = None
        for i, d in enumerate(dirs):
            if d.lower() == "data" and dirs[i - 1].lower() == "salt":
                instrument_dir = dirs[i + 3]
                break
        if not instrument_dir:
            raise ValueError("No selected instrument")
        inst = Instrument.RSS if instrument_dir.lower() == "rss" else \
            Instrument.HRS if instrument_dir.lower() == "hrs" else \
            Instrument.SALTICAM if instrument_dir.lower() == "scam" else None
        if not inst:
            raise ValueError("Unknown instrument")

        return inst

    def file_path(self) -> str:
        return self.path

    def checksum(self) -> str:
        letters = string.ascii_lowercase
        return "".join(random.choice(letters) for _ in range(20))

    def headers(self) -> Dict[str, Any]:
        hdulist = fits.open(self.path)
        return hdulist[0].header

    def header_value(self, keyword: str) -> Optional[str]:
        try:
            return str(self.headers()[keyword])
        except KeyError:
            return None


class DummyFitsFile(FitsFile):
    def __init__(self, path: str) -> None:
        self.path = path

    def size(self) -> Quantity:
        return random.randint(1000, 100000000)

    def checksum(self) -> str:
        letters = string.ascii_lowercase
        return "".join(random.choice(letters) for _ in range(50))

    def header_value(self, keyword: str) -> str:
        letters = string.ascii_lowercase
        return "".join(random.choice(letters) for _ in range(random.randint(1, 10)))
