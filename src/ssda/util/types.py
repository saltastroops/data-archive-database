from __future__ import annotations
import os
import uuid
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, NamedTuple, Optional, Set

import astropy.units as u
from astropy.units import def_unit, Quantity

from ssda.util.warnings import record_warning

byte = def_unit("byte")


class SQLQuery(NamedTuple):
    """
    An SQL query.

    Query parameters must be included in the form %(name)s in SQL statement, and their
    value must be provided in the parameters dictionary.

    For example, the query

    INSERT INTO target (ra, dec) VALUES (42.8, -16.4)

    would be represented by

    sql = "INSERT INTO target (ra, dec) VALUES (%(ra)s, %(dec)s)

    and

    parameters = dict(ra=42.8, dec=-16.4)

    Parameters
    ----------
    parameters : Dict[str, any]
        Query parameters and their values.
    sql : str
        SQL statement. Query parameters must be included in the form $(name)s.

    """

    parameters: Dict[str, Any]
    sql: str


@dataclass
class CalibrationLevelPaths:
    """
    Data file paths for different calibration levels.

    Parameters
    ----------
    raw : Path
        The path for the raw data file.
    reduced : Path
        The path for the reduced data file.

    """

    raw: Path
    reduced: Optional[Path]


class AccessRule(Enum):
    """
    Enumeration of the available data access rules.

    The enum values must be the same as the values of the access_rule column in the
    access_rule table.

    """

    PUBLIC_DATA_OR_INSTITUTION_MEMBER = "Public Data or Institution Member"
    PUBLIC_DATA_OR_INVESTIGATOR = "Public Data or Investigator"


class Artifact:
    """
    An artifact, usually a FITS file.

    Parameters
    ----------
    content_checksum : str
        MD5 checksum for the file content.
    content_length : Quantity
        File size.
    identifier : str
        A unique identifier for the artifact.
    name : str
        Artifact name.
    paths : CalibrationLevelPaths
        File paths for the data at different calibration levels.
    plane_id : int
        Database id of the plane which the artifact belongs to.
    product_type : ProductType
        Product type of the artifact.

    """

    def __init__(
        self,
        content_checksum: str,
        content_length: Quantity,
        identifier: uuid.UUID,
        name: str,
        plane_id: int,
        paths: CalibrationLevelPaths,
        product_type: ProductType,
    ):
        if len(content_checksum) > 32:
            raise ValueError("The content checksum must have at most 32 characters.")
        try:
            content_length.to(byte)
        except u.UnitConversionError:
            raise ValueError("The content length must have a file size unit.")
        if content_length.to_value(byte) <= 0:
            raise ValueError("The content length must be positive.")
        if len(name) > 200:
            raise ValueError("The artifact name must have at most 200 characters.")
        if paths.raw is None and paths.reduced is None:
            raise ValueError("At least one of the paths must be non-None.")

        self._content_checksum = content_checksum
        self._content_length = content_length
        self._identifier = identifier
        self._name = name
        self._paths = paths
        self._plane_id = plane_id
        self._product_type = product_type

    @property
    def content_checksum(self) -> str:
        return self._content_checksum

    @property
    def content_length(self) -> Quantity:
        return self._content_length

    @property
    def identifier(self) -> uuid.UUID:
        return self._identifier

    @property
    def name(self) -> str:
        return self._name

    @property
    def paths(self) -> CalibrationLevelPaths:
        return self._paths

    @property
    def plane_id(self) -> int:
        return self._plane_id

    @property
    def product_type(self) -> ProductType:
        return self._product_type


class DatabaseConfiguration:
    """
    A database configuration.

    Parameters
    ----------
    host : str
        Domain of the host server (such as 127.0.0.1 or db.your.host)
    username : str
        Username of the database user.
    password : str
        Password of the database user.
    database : str
        Name of the database.
    port : int
        Port number.

    """

    def __init__(
        self, host: str, username: str, password: str, database: str, port: int
    ) -> None:
        if port <= 0:
            raise ValueError("The port number must be positive.")

        self._host = host
        self._username = username
        self._password = password
        self._database = database
        self._port = port

    def host(self) -> str:
        """
        The domain of the host server.

        Returns
        -------
        str
            The host server.

        """

        return self._host

    def username(self) -> str:
        """
        The username of the database user.

        Returns
        -------
        str
            The database user.

        """

        return self._username

    def password(self) -> str:
        """
        The password of the database user.

        Returns
        -------
        str
            The password.

        """

        return self._password

    def database(self) -> str:
        """
        The name of the database.

        Returns
        -------
        str
            The name of the database.

        """

        return self._database

    def port(self) -> int:
        """
        The port number.

        Returns
        -------
        int
            The port number.

        """

        return self._port

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DatabaseConfiguration):
            return NotImplemented
        return (
            self.host() == other.host()
            and self.username() == other.username()
            and self.password() == other.password()
            and self.database() == other.database()
            and self.port() == other.port()
        )


class DataProductType(Enum):
    """
    Enumeration of the available data product types.

    The enum values must be the same as the values of the product_type column in the
    data_product_type table.

    """

    IMAGE = "Image"
    SPECTRUM = "Spectrum"

    @staticmethod
    def for_name(name: str) -> DataProductType:
        """
        The data product type for a case-insensitive name.

        Parameters
        ----------
        name : str
            Data product type name.

        Returns
        -------
        DataProductType :
            DataProductType.

        """

        for data_product_type in DataProductType:
            if name and name.lower() == str(data_product_type.value).lower():
                return data_product_type

        raise ValueError(f"Unknown data product type: '{name}'")


class DateRange:
    """
    A date range.

    The start date is inclusive, the end date exclusive. So, for example, if the start
    date is 1 January 2019 and the end date 4 January 2019, the date range contains
    1 January, 2 January and 3 January, but not 4 January 2019.

    The start date must be earlier than the end date.

    Parameters
    ----------
    start : date
        Start date.
    end : date
         End date.

    Raises
    ------
    ValueError
        If the start date is equal to or later than the start date.

    """

    def __init__(self, start: date, end: date) -> None:
        if start >= end:
            raise ValueError("The start date must be earlier than the end date.")

        self._start = start
        self._end = end

    @property
    def start(self) -> date:
        """
        The start date.

        Returns
        -------
        date
            The start date.

        """

        return self._start

    @property
    def end(self) -> date:
        """
        The end date.

        Returns
        -------
        date
            The end date.

        """

        return self._end


class DetectorMode(Enum):
    """
    Enumeration of the available detector (readout) modes.

    The enum values must be the same as the values of the detector_mode column in the
    detector_mode table.

    """

    DRIFT_SCAN = "Drift Scan"
    FRAME_TRANSFER = "Frame Transfer"
    NORMAL = "Normal"
    SHUFFLE = "Shuffle"
    SLOT_MODE = "Slot Mode"

    @staticmethod
    def for_name(name: str) -> DetectorMode:
        """The detector mode for a case-insensitive name.

        Parameters
        ----------
        name : str
            Detector mode name.

        Returns
        -------
        DetectorMode :
            DetectorMode.

        """

        if name and name.lower() == "slot":
            name = "Slot Mode"
        if name and name.lower() == "ft":
            name = "Frame Transfer"

        for detector_mode in DetectorMode:
            if (
                name
                and name.replace(" ", "").lower()
                == str(detector_mode.value).replace(" ", "").lower()
            ):
                return detector_mode

        raise ValueError(f"Unknown detector mode: '{name}'")


class Energy:
    """
    Spectral details for a plane.

    Parameters
    ----------
    dimension : int
        Number of wavelength measurements (i.e. detector pixels).
    max_wavelength : Quantity
        Maximum wavelength.
    min_wavelength : Quantity
        Minimum  wavelength.
    plane_id : int
        Database id of the plane to which the spectral details refer.
    resolving_power : float
        Resolving power for the wavelength.
    sample_size : Quantity
        Size of the wavelength interval per pixel.

    """

    def __init__(
        self,
        dimension: int,
        max_wavelength: Quantity,
        min_wavelength: Quantity,
        plane_id: int,
        resolving_power: float,
        sample_size: Quantity,
    ):
        if dimension <= 0:
            raise ValueError("The dimension must be positive.")
        if max_wavelength.value <= 0:
            raise ValueError("The maximum wavelength must be positive.")
        try:
            max_wavelength.to(u.meter)
        except u.UnitConversionError:
            raise ValueError("The maximum wavelength must have a length unit.")
        if min_wavelength.value <= 0:
            raise ValueError("The minimum wavelength must be positive.")
        try:
            min_wavelength.to(u.meter)
        except u.UnitConversionError:
            raise ValueError("The minimum wavelength must have a length unit.")
        if max_wavelength <= min_wavelength:
            raise ValueError(
                "The maximum wavelength must be greater than the minimum " "wavelength."
            )
        if resolving_power < 0:
            raise ValueError("The resolving power must be non-negative.")
        try:
            sample_size.to(u.meter)
        except u.UnitConversionError:
            raise ValueError("The sample size must have a length unit.")
        if sample_size < 0:
            raise ValueError("The sample size must be non-negative.")

        self._dimension = dimension
        self._max_wavelength = max_wavelength
        self._min_wavelength = min_wavelength
        self._plane_id = plane_id
        self._resolving_power = resolving_power
        self._sample_size = sample_size

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def max_wavelength(self) -> Quantity:
        return self._max_wavelength

    @property
    def min_wavelength(self) -> Quantity:
        return self._min_wavelength

    @property
    def plane_id(self) -> int:
        return self._plane_id

    @property
    def resolving_power(self) -> float:
        return self._resolving_power

    @property
    def sample_size(self) -> Quantity:
        return self._sample_size


class FilePath:
    """
    A file path of an existing regular file.

    Parameters
    ----------
    path : str
        File path.

    Raises
    ------
    ValueError
        If the file path does not exist or is not a regular file.

    """

    def __init__(self, path: str) -> None:
        if not os.path.isfile(path):
            raise ValueError("Not a regular file: ")

        self._path = path

    @property
    def path(self) -> str:
        """
        The file path.

        Returns
        -------
        str
            The file path.

        """

        return self._path


class Filter(Enum):
    """
    Enumeration of the filters.

    The enum values must be the same as the values of the name column in the filter
    table.

    """

    Cousins_I = "Cousins I"
    Cousins_R = "Cousins R"
    FUSED_SILICA_CLEAR = "Fused silica clear"
    FWHM_340_35 = "340nm 35nm FWHM"
    FWHM_380_40 = "380nm 40nm FWHM"
    H_ALPHA = "H-alpha"
    H_BETA_NARROW = "H-beta narrow"
    H_BETA_WIDE = "H-beta wide"
    JOHNSON_B = "Johnson B"
    JOHNSON_I = "Johnson I"
    JOHNSON_R = "Johnson R"
    JOHNSON_U = "Johnson U"
    JOHNSON_V = "Johnson V"
    OPEN = "Open"
    SDSS_G = "SDSS g'"
    SDSS_I = "SDSS i'"
    SDSS_R = "SDSS r'"
    SDSS_U = "SDSS u'"
    SDSS_z = "SDSS z'"
    SRE_1 = "SRE 1"
    SRE_2 = "SRE 2"
    SRE_3 = "SRE 3"
    SRE_4 = "SRE 4"
    STROEMGREN_B = "Stroemgren b"
    STROEMGREN_U = "Stroemgren u"
    STROEMGREN_V = "Stroemgren v"
    STROEMGREN_Y = "Stroemgren y"
    PC00000 = "pc00000"
    PC03200 = "pc03200"
    PC03400 = "pc03400"
    PC03850 = "pc03850"
    PC04600 = "pc04600"
    PI04340 = "pi04340"
    PI04400 = "pi04400"
    PI04465 = "pi04465"
    PI04530 = "pi04530"
    PI04600 = "pi04600"
    PI04670 = "pi04670"
    PI04740 = "pi04740"
    PI04820 = "pi04820"
    PI04895 = "pi04895"
    PI04975 = "pi04975"
    PI05060 = "pi05060"
    PI05145 = "pi05145"
    PI05235 = "pi05235"
    PI05325 = "pi05325"
    PI05420 = "pi05420"
    PI05520 = "pi05520"
    PI05620 = "pi05620"
    PI05725 = "pi05725"
    PI05830 = "pi05830"
    PI05945 = "pi05945"
    PI06055 = "pi06055"
    PI06170 = "pi06170"
    PI06290 = "pi06290"
    PI06410 = "pi06410"
    PI06530 = "pi06530"
    PI06645 = "pi06645"
    PI06765 = "pi06765"
    PI06885 = "pi06885"
    PI07005 = "pi07005"
    PI07130 = "pi07130"
    PI07260 = "pi07260"
    PI07390 = "pi07390"
    PI07535 = "pi07535"
    PI07685 = "pi07685"
    PI07840 = "pi07840"
    PI08005 = "pi08005"
    PI08175 = "pi08175"
    PI08350 = "pi08350"
    PI08535 = "pi08535"
    PI08730 = "pi08730"

    @staticmethod
    def for_name(name: str) -> Optional[Filter]:
        """The filter for a case-insensitive name.

        Parameters
        ----------
        name : str
            Filter name.

        Returns
        -------
        Filter :
            Filter.

        """

        if not name:
            return None

        replacements = {
            "SBn-S1": "Stroemgren b",
            "SDSSI": "SDSS i'",
            "SDSSU": "SDSS u'",
            "EMPTY": "OPEN",
        }

        for old_value, new_value in replacements.items():
            if name.lower() == old_value.lower():
                record_warning(
                    Warning(f"Filter name: {name} is assumed to be {new_value}")
                )
                name = new_value

        for filter in Filter:
            if name.lower() == str(filter.value).lower():
                return filter

        # Maybe the name is one of the filter name aliases?
        aliases: Dict[Filter, List[str]] = {
            Filter.JOHNSON_U: ["U-S1", "Johnson U", "SCAM-U"],
            Filter.JOHNSON_B: ["B-S1", "Johnson B", "SCAM-B"],
            Filter.JOHNSON_V: ["V-S1", "Johnson V", "SCAM-V"],
            Filter.Cousins_R: ["R-S1", "Cousins R", "SCAM-R"],
            Filter.Cousins_I: ["I-S1", "Cousins I", "SCAM-I"],
            Filter.FWHM_380_40: ["380-40", "380nm 40nm FWHM", "SCAM380-40"],
            Filter.FWHM_340_35: ["340-35", "340nm 35nm FWHM", "SCAM340-35"],
            Filter.FUSED_SILICA_CLEAR: ["CLR-S1", "Fused silica clear", "PC00000"],
            Filter.SDSS_U: ["SDSSu-S1", "SDSS u'", "S-SDSS-u"],
            Filter.SDSS_G: ["SDSSg-S1", "SDSS g'", "S-SDSS-g"],
            Filter.SDSS_R: ["SDSSr-S1", "SDSS r'", "S-SDSS-r", "SDSS-r'"],
            Filter.SDSS_I: ["SDSSi-S1", "SDSS i'", "S-SDSS-i"],
            Filter.SDSS_z: ["SDSSz-S1", "SDSS z'", "S-SDSS-z"],
            Filter.STROEMGREN_U: ["Su-S1", "Stroemgren u", "Su-S1"],
            Filter.STROEMGREN_B: ["Sb-S1", "Stroemgren b", "Sb-S1"],
            Filter.STROEMGREN_V: ["Sv-S1", "Stroemgren v", "Sv-S1"],
            Filter.STROEMGREN_Y: ["Sy-S1", "Stroemgren y", "Sy-S1"],
            Filter.H_ALPHA: ["Halpha-S1", "H-alpha", "Halpha-S1"],
            Filter.H_BETA_WIDE: ["Hbw-S1", "H-beta wide", "Hbw-S1"],
            Filter.H_BETA_NARROW: ["Hbn-S1", "H-beta narrow", "Hbn-S1"],
            Filter.SRE_1: ["SR613-21", "SRE 1", "SR613-21"],
            Filter.SRE_2: ["SR708-25", "SRE 2", "SR708-25"],
            Filter.SRE_3: ["SR815-29", "SRE 3", "SR815-29"],
            Filter.SRE_4: ["SR862-32", "SRE 4", "SR862-32"],
        }

        for key in aliases:
            for alias in aliases[key]:
                if name.lower() == alias.lower():
                    if name.lower() == "sbn-s1":
                        record_warning(
                            Warning(f"Filter name: {name} is assumed to be {key.value}")
                        )
                    return key

        raise ValueError(f"Unknown filter name: {name}")


class HRSArm(Enum):
    RED = "Red"
    BLUE = "Blue"


class HRSMode(Enum):
    """
    Enumeration of the HRS (resolution) modes.

    The enum values must be the same as the values of the hrs_mode column in the
    hrs_mode table.

    """

    HIGH_RESOLUTION = "High Resolution"
    HIGH_STABILITY = "High Stability"
    INT_CAL_FIBRE = "Int Cal Fibre"
    LOW_RESOLUTION = "Low Resolution"
    MEDIUM_RESOLUTION = "Medium Resolution"


class Institution(Enum):
    """
    Enumeration of the institutions.

    The enum values must be the same as the values of the name column in the institution
    table.

    """

    SAAO = "South African Astronomical Observatory"
    SALT = "Southern African Large Telescope"


@dataclass(frozen=True)
class InstitutionMembership:
    """
    Details for the membership in an institution.

    Parameters
    ----------
    membership_end : date
        Date when the membership has ended or will end.
    membership_start : date
        Date when the membership has started.

    """

    membership_end: date
    membership_start: date

    def __lt__(self, other: InstitutionMembership):
        return (self.membership_start, self.membership_end) < (
            other.membership_start,
            other.membership_end,
        )


class Instrument(Enum):
    """
    Enumeration of the instruments.

    The enum values must be the same as the values of the name column in the instrument
    table.

    """

    RSS = "RSS"
    HRS = "HRS"
    SALTICAM = "Salticam"
    BCAM = "BCAM"

    @staticmethod
    def for_name(name: str) -> Instrument:
        """The instrument for a case-insensitive name.

        Parameters
        ----------
        name : str
            Instrument name.

        Returns
        -------
        Instrument :
            Instrument.

        """

        for instrument in Instrument:
            if name.lower() == str(instrument.value).lower():
                return instrument

        raise ValueError(f"Unknown instrument name: {name}")

    @staticmethod
    def instruments(telescope: Telescope):
        """
        Return the instruments used by a telescope.

        Parameters
        ----------
        telescope : Telescope
            Telescope.

        Returns
        -------
        Set[Instrument]
            The instruments used by the telescope.

        """

        if telescope == Telescope.SALT:
            return {
                Instrument.BCAM,
                Instrument.HRS,
                Instrument.RSS,
                Instrument.SALTICAM,
            }
        raise ValueError(f"Unknown telescope {telescope}")


class InstrumentKeyword(Enum):
    """
    Enumeration of the available instrument keywords.

    """

    EXPOSURE_TIME = "Exposure time"
    FILTER = "Filter"
    GRATING = "Grating"


class InstrumentKeywordValue:
    """
    The value for an instrument keyword and observation.

    Parameters
    ----------
    instrument : Instrument
        Instrument to which the value applies.
    instrument_keyword : InstrumentKeyword
        Instrument keyword.
    observation_id : int
        Database id of the observation to which the keyword value refers.
    value : str
        Value.

    """

    def __init__(
        self,
        instrument: Instrument,
        instrument_keyword: InstrumentKeyword,
        observation_id: int,
        value: str,
    ):
        if len(value) > 200:
            raise ValueError("The values must have at most 200 characters.")

        self._instrument = instrument
        self._instrument_keyword = instrument_keyword
        self._observation_id = observation_id
        self._value = value

    @property
    def instrument(self) -> Instrument:
        return self._instrument

    @property
    def instrument_keyword(self) -> InstrumentKeyword:
        return self._instrument_keyword

    @property
    def observation_id(self) -> int:
        return self._observation_id

    @property
    def value(self) -> str:
        return self._value


class InstrumentMode(Enum):
    """
    An enumeration of the instrument modes such as "Imaging" or "Spectroscopy".

    The enum values must be the same as the values of the instrument_mode column in the
    instrument table.

    """

    FABRY_PEROT = "Fabry Perot"
    IMAGING = "Imaging"
    MOS = "MOS"
    POLARIMETRIC_IMAGING = "Polarimetric Imaging"
    SPECTROPOLARIMETRY = "Spectropolarimetry"
    SPECTROSCOPY = "Spectroscopy"
    STREAMING = "Streaming"

    @staticmethod
    def for_name(name: str) -> InstrumentMode:
        """
        The instrument mode for a case-insensitive name.

        Parameters
        ----------
        name : str
            Instrument mode name.

        Returns
        -------
        InstrumentMode :
            InstrumentMode.

        """

        for instrument_mode in InstrumentMode:
            if name and name.lower() == str(instrument_mode.value).lower():
                return instrument_mode

        raise ValueError(f"Unknown instrument mode: '{name}'")


class InstrumentSetup:
    """
    Additional details about an instrument setup.

    The additional_queries allows the insertion of instrument-specific content, such as
    a grating or a resolution mode. Each query consists of the SQL (with parameters of
    the form %(name)s) and a dictionary of parameter names and values.

    If an additional query requires the instrument setup id as a parameter, it should be
    included as %(instrument_setup_id)s. The id will automatically be included in the
    dictionary of parameters.

    Parameters
    ----------
    additional_queries : List[SQLQuery]
        Additional queries for instrument specific content.
    detector_mode : DetectorMode
        Detector (readout) mode.
    filter : Optional[Filter]
        Bandpass filter
    instrument_mode : InstrumentMode
        Instrument mode, such imaging or spectroscopy.
    observation_id : int
        Database id of the observation to which this instrument setup belongs.

    """

    def __init__(
        self,
        additional_queries: List[SQLQuery],
        detector_mode: DetectorMode,
        filter: Optional[Filter],
        instrument_mode: InstrumentMode,
        observation_id: int,
    ):
        self._additional_queries = additional_queries
        self._detector_mode = detector_mode
        self._filter = filter
        self._instrument_mode = instrument_mode
        self._observation_id = observation_id

    @property
    def additional_queries(self) -> List[SQLQuery]:
        return self._additional_queries

    @property
    def detector_mode(self) -> DetectorMode:
        return self._detector_mode

    @property
    def filter(self) -> Optional[Filter]:
        return self._filter

    @property
    def instrument_mode(self) -> InstrumentMode:
        return self._instrument_mode

    @property
    def observation_id(self) -> int:
        return self._observation_id


class Intent(Enum):
    """
    Enumeration of the available intent values.

    The enum values must be the same as the values of the intent column in the intent
    table.

    """

    CALIBRATION = "Calibration"
    SCIENCE = "Science"

    @staticmethod
    def for_name(name: str) -> Intent:
        """
        The intent for a case-insensitive name.

        Parameters
        ----------
        name : str
            Intent name.

        Returns
        -------
        Intent :
            Intent.

        """

        for intent in Intent:
            if name and name.lower() == str(intent.value).lower():
                return intent

        raise ValueError(f"Unknown intent: '{name}'")


class Observation:
    """
    An observation.

    Parameters
    ----------
    data_release : date
        Date when the data for this observation becomes public.
    instrument : Instrument
        Instrument used for obtaining the observation data.
    intent : Intent
        Intent of the observation.
    meta_release : date
        Date when the metadata for this observation becomes public.
    observation_group_id : int
        Identifier of the observation group to which the observation belongs.
        Observation type.
    proposal_id : int
        Database id of the proposal to which this observation belongs.
    status : Status
        Status (accepted or rejected) of the observation.
    telescope : Telescope
        Telescope used for the observation.

    """

    def __init__(
        self,
        data_release: date,
        instrument: Instrument,
        intent: Intent,
        meta_release: date,
        observation_group_id: Optional[int],
        proposal_id: Optional[int],
        status: Status,
        telescope: Telescope,
    ):
        if data_release < meta_release:
            raise ValueError(
                "The data release cannot be earlier than the metadata " "release."
            )

        self._data_release = data_release
        self._instrument = instrument
        self._intent = intent
        self._meta_release = meta_release
        self._observation_group_id = observation_group_id
        self._proposal_id = proposal_id
        self._status = status
        self._telescope = telescope

    @property
    def data_release(self) -> date:
        return self._data_release

    @property
    def instrument(self) -> Instrument:
        return self._instrument

    @property
    def intent(self) -> Intent:
        return self._intent

    @property
    def meta_release(self) -> date:
        return self._meta_release

    @property
    def observation_group_id(self) -> Optional[int]:
        return self._observation_group_id

    @property
    def proposal_id(self) -> Optional[int]:
        return self._proposal_id

    @property
    def status(self) -> Status:
        return self._status

    @property
    def telescope(self) -> Telescope:
        return self._telescope


class ObservationGroup:
    """
    A logical group of observations, such as a block visit for SALT.

    Parameters
    ----------
    group_identifier : str
        Identifier for the group, which must be unique within the groups belonging to
        the same telescope.
    name : str
        Name of the observation group.

    """

    def __init__(self, group_identifier: str, name: str):
        if group_identifier and len(group_identifier) > 40:
            raise ValueError("The group identifier must have at most 40 characters.")
        if name and len(name) > 40:
            raise ValueError("The name must have at most 40 characters.")

        self._group_identifier = group_identifier
        self._name = name

    @property
    def group_identifier(self) -> Optional[str]:
        return self._group_identifier

    @property
    def name(self) -> str:
        return self._name


class ObservationTime:
    """
    The time (and duration) for an observation (or, more precisely, plane).

    Parameters
    ----------
    end_time : datetime
        Time when the observation ended.
    exposure_time : Quantity
        Duration of the exposure.
    plane_id : int
        Database id of the plane with this observation time.
    resolution : Quantity
        Time resolution.
    start_time : datetime
        Time when the observation started.

    """

    def __init__(
        self,
        end_time: datetime,
        exposure_time: Quantity,
        plane_id: int,
        resolution: Quantity,
        start_time: datetime,
    ):
        if start_time.tzinfo is None:
            raise ValueError("The start time must be timezone-aware.")
        if end_time.tzinfo is None:
            raise ValueError("The end time must be timezone-aware.")
        if start_time > end_time:
            raise ValueError("The start time must not be later than the end time.")
        if exposure_time.value < 0:
            raise ValueError("The exposure time must be non-negative.")
        try:
            exposure_time.to(u.second)
        except u.UnitConversionError:
            raise ValueError("The exposure time must have a time unit.")
        if resolution.value < 0:
            raise ValueError("The resolution must be non-negative.")
        try:
            resolution.to(u.second)
        except u.UnitConversionError:
            raise ValueError("The time resolution must have a time unit.")

        self._end_time = end_time
        self._exposure_time = exposure_time
        self._plane_id = plane_id
        self._resolution = resolution
        self._start_time = start_time

    @property
    def end_time(self) -> datetime:
        return self._end_time

    @property
    def exposure_time(self) -> Quantity:
        return self._exposure_time

    @property
    def plane_id(self) -> int:
        return self._plane_id

    @property
    def resolution(self) -> Quantity:
        return self._resolution

    @property
    def start_time(self) -> datetime:
        return self._start_time


class Plane:
    """
    A plane.

    Parameters
    ----------
    observation_id : int
        Database id of the observation to which this plane belongs.
    data_product_type : DataProductType
        Data product type.

    """

    def __init__(self, observation_id: int, data_product_type: DataProductType):
        self._observation_id = observation_id
        self._data_product_type = data_product_type

    @property
    def observation_id(self) -> int:
        return self._observation_id

    @property
    def data_product_type(self) -> DataProductType:
        return self._data_product_type


class PolarizationMode(Enum):
    """
    Enumeration of the available polarization modes.

    The enum values must be the same as the values of the name column in the
    polarization_mode table.

    """

    ALL_STOKES = "All Stokes"
    CIRCULAR = "Circular"
    LINEAR = "Linear"
    LINEAR_HI = "Linear Hi"
    OTHER = "Other"

    @staticmethod
    def polarization_mode(polarization_mode: str) -> PolarizationMode:
        if polarization_mode.upper() == "LINEAR":
            return PolarizationMode.LINEAR
        elif (
            polarization_mode.upper() == "LINEAR-HI"
            or polarization_mode.upper() == "LINEAR HI"
        ):
            return PolarizationMode.LINEAR_HI
        elif polarization_mode.upper() == "CIRCULAR":
            return PolarizationMode.CIRCULAR
        elif (
            polarization_mode.upper() == "ALL-STOKES"
            or polarization_mode.upper() == "ALL STOKES"
        ):
            return PolarizationMode.ALL_STOKES
        elif polarization_mode.upper() == "OTHER":
            return PolarizationMode.OTHER
        else:
            raise ValueError(f"Polarization mode {polarization_mode} is not known")


class Polarization:
    """
    Polarization for an observation.

    Parameters
    ----------
    plane_id : int
        Database id of the plane with the polarization.
    polarization_mode : PolarizationMode
        Polarization mode.

    """

    def __init__(self, plane_id: int, polarization_mode: PolarizationMode):
        self._plane_id = plane_id
        self._polarization_mode = polarization_mode

    @property
    def plane_id(self) -> int:
        return self._plane_id

    @property
    def polarization_mode(self) -> PolarizationMode:
        return self._polarization_mode


class Position:
    """
    A target position.

    Parameters
    ----------
    dec : Quantity
        Declination, as an angle between -90 and 90 degrees (both inclusive).
    equinox : float
        Equinox.
    plane_id : int
        Database id of the plane to which this position belongs.
    ra : Quantity
        Right ascension, as an angle between 0 degrees (inclusive) and 360 degrees
        (exclusive).

    """

    def __init__(self, dec: Quantity, equinox: float, plane_id: int, ra: Quantity):
        try:
            dec.to(u.degree)
        except u.UnitConversionError:
            raise ValueError("The declination must have an angular unit.")
        if dec.to_value(u.degree) < -90 or dec.to_value(u.degree) > 90:
            raise ValueError("The declination must be between -90 and 90 degrees.")
        if 199.9 < equinox < 200.1:
            equinox = 2000
        if equinox < 1900:
            raise ValueError("The equinox must be 1900 or later.")
        try:
            ra.to(u.degree)
        except u.UnitConversionError:
            raise ValueError("The right ascension must have an angular unit.")
        if ra.to_value(u.degree) < 0 or ra.to_value(u.degree) >= 360:
            raise ValueError(
                "The right ascension must have a value between 0 degress "
                "(inclusive) and 360 degrees (exclusive)."
            )

        self._dec = dec
        self._equinox = equinox
        self._plane_id = plane_id
        self._ra = ra

    @property
    def dec(self) -> Quantity:
        return self._dec

    @property
    def equinox(self) -> float:
        return self._equinox

    @property
    def plane_id(self) -> int:
        return self._plane_id

    @property
    def ra(self) -> Quantity:
        return self._ra


class ProductCategory(Enum):
    """
    Enumeration of the available product category.

    The enum values must be the same as the values of the product_category column in the
    product_category table.

    """

    ARC = "Arc"
    BIAS = "Bias"
    DARK = "Dark"
    FLAT = "Flat"
    SCIENCE = "Science"
    STANDARD = "Standard"

    @staticmethod
    def for_name(name: str) -> ProductCategory:
        """
        The product category for a case-insensitive name.

        Parameters
        ----------
        name : str
            Product category name.

        Returns
        -------
        ProductCategory :
            ProductCategory.

        """

        for product_category in ProductCategory:
            if name and name.lower() == str(product_category.value).lower():
                return product_category

        raise ValueError(f"Unknown product category: '{name}'")


class ProductType(Enum):
    """
    Enumeration of the available product types.

    The enum values must be the same as the values of the product_type column in the
    product_type table.

    """

    ARC_CALSYS = "Arc - Calsys"
    ARC_INTERNAL = "Arc - Internal"
    BIAS = "Bias"
    DARK = "Dark"
    IMAGING_FLAT_LAMP = "Imaging Flat - Lamp"
    IMAGING_FLAT_TWILIGHT = "Imaging Flat - Twilight"
    SPECTROSCOPIC_FLAT_LAMP = "Spectroscopic Flat - Lamp"
    SPECTROSCOPIC_FLAT_TWILIGHT = "Spectroscopic Flat - Twilight"
    SCIENCE = "Science"
    STANDARD_CIRCULAR_POLARIMETRIC = "Standard - Circular Polarimetric"
    STANDARD_LICK = "Standard - Lick"
    STANDARD_LINEAR_POLARIMETRIC = "Standard - Linear Polarimetric"
    STANDARD_PHOTOMETRIC = "Standard - Photometric"
    STANDARD_RADIAL_VELOCITY = "Standard - Radial Velocity"
    STANDARD_SMOOTH_SPECTRUM = "Standard - Smooth Spectrum"
    STANDARD_SPECTROPHOTOMETRIC = "Standard - Spectrophotometric"
    STANDARD_SPECTROSCOPIC = "Standard - Spectroscopic"
    STANDARD_TELLURIC = "Standard - Telluric"
    STANDARD_UNPOLARISED = "Standard - Unpolarised"

    @staticmethod
    def for_name(name: str) -> ProductType:
        """
        The product type for a case-insensitive name.

        Parameters
        ----------
        name : str
            Product type name.

        Returns
        -------
        ProductType :
            ProductType.

        """

        for product_type in ProductType:
            if name.lower() == str(product_type.value).lower():
                return product_type

        raise ValueError(f"Unknown product type: '{name}'")


class Proposal:
    """
    A proposal.

    Parameters
    ----------
    institution : Institution
        Institution.
    pi : str
        Principal Investigator.
    proposal_code : str
        Proposal identifier, which is unique within an institution.
    proposal_type : ProposalType
        Proposal type.
    title : str
        Proposal title.

    """

    def __init__(
        self,
        institution: Institution,
        pi: str,
        proposal_code: str,
        proposal_type: ProposalType,
        title: str,
    ):
        if len(pi) > 100:
            raise ValueError("The PI must have at most 100 characters.")
        if len(proposal_code) > 50:
            raise ValueError("The proposal code must have at most 50 characters.")
        if len(title) > 200:
            raise ValueError("The title must have at most 200 characters.")

        self._institution = institution
        self._pi = pi
        self._proposal_code = proposal_code
        self.proposal_type = proposal_type
        self._title = title

    @property
    def institution(self) -> Institution:
        return self._institution

    @property
    def pi(self) -> str:
        return self._pi

    @property
    def proposal_code(self) -> str:
        return self._proposal_code

    @property
    def title(self) -> str:
        return self._title


class ProposalInvestigator:
    """
    An investigator on a proposal.

    Parameters
    ----------
    proposal_id : int
        Database id of the proposal.
    institution : Institution
            Institution to which the proposal was submitted.
    institution_memberships: List[InstitutionMembership]
            Institution memberships.
    investigator_id : str
        The unique id of the investigator, as determined by the institution to which the
        proposal was submitted.

    """

    def __init__(
        self,
        proposal_id: int,
        investigator_id: str,
        institution: Institution,
        institution_memberships: List[InstitutionMembership],
    ):
        if len(investigator_id) > 50:
            raise ValueError("The investigator id must have at most 30 characters.")

        self._proposal_id = proposal_id
        self._institution = institution
        self._institution_memberships = institution_memberships
        self._investigator_id = investigator_id

    @property
    def proposal_id(self) -> int:
        return self._proposal_id

    @property
    def institution(self) -> Institution:
        return self._institution

    @property
    def institution_memberships(self) -> List[InstitutionMembership]:
        return self._institution_memberships

    @property
    def investigator_id(self) -> str:
        return self._investigator_id


class ProposalType(Enum):
    """
    Enumeration of the available proposal type.

    The enum values must be the same as the values of the proposal_type column in the
    proposal_type table.

    """

    COMMISSIONING = "Commissioning"
    ENGINEERING = "Engineering"
    SCIENCE = "Science"
    SCIENCE_VERIFICATION = "Science Verification"


@dataclass
class ReleaseDates:
    meta_release: date
    data_release: date


class RSSFabryPerotMode(Enum):
    """
    Enumeration of the RSS Fabry-Perot modes.

    The enum values must be the same as the values of the fabry_perot_mode column in the
    rss_fabry_perot_mode table.

    """

    HIGH_RESOLUTION = "High Resolution"
    LOW_RESOLUTION = "Low Resolution"
    MEDIUM_RESOLUTION = "Medium Resolution"
    TUNABLE_FILTER = "Tunable Filter"

    @staticmethod
    def parse_fp_mode(fp_mode_abbr: str) -> RSSFabryPerotMode:
        if fp_mode_abbr.upper() == "LR":
            return RSSFabryPerotMode.LOW_RESOLUTION
        if fp_mode_abbr.upper() == "MR":
            return RSSFabryPerotMode.MEDIUM_RESOLUTION
        if fp_mode_abbr.upper() == "HR":
            return RSSFabryPerotMode.HIGH_RESOLUTION
        if fp_mode_abbr.upper() == "TF":
            return RSSFabryPerotMode.TUNABLE_FILTER
        raise ValueError(f"Mode {fp_mode_abbr} is not known.")


class RSSGrating(Enum):
    """
    Enumeration of the RSS gratings.

    The enum values must be the same as the values of the grating column in the
    rss_grating table.

    """

    OPEN = "Open"
    PG0300 = "PG0300"
    PG0900 = "PG0900"
    PG1300 = "PG1300"
    PG1800 = "PG1800"
    PG2300 = "PG2300"
    PG3000 = "PG3000"


class SALTObservationGroup:
    def __init__(self, status: Status, group_identifier: str):
        self.status = status
        self.group_identifier = group_identifier

    def __eq__(self, other):
        return (
            self.__class__ == other.__class__
            and self.status.value == other.status.value
            and self.group_identifier == other.group_identifier
        )


class SALTProposalDetails:
    def __init__(
        self,
        proposal_code: str,
        institution: Institution,
        meta_release: date,
        data_release: date,
        pi: str,
        title: str,
        investigators: List[str],
    ):
        self.proposal_code = proposal_code
        self.institution = institution
        self.meta_release = meta_release
        self.data_release = data_release
        self.pi = pi
        self.title = title
        self.investigators = investigators

    def __eq__(self, other):
        return (
            self.__class__ == other.__class__
            and self.proposal_code == other.proposal_code
            and self.institution == other.institution
            and self.meta_release == other.meta_release
            and self.data_release == other.data_release
            and self.pi == other.pi
            and self.investigators.sort() == other.investigators.sort()
        )


class Status(Enum):
    """
    Enumeration of the available status values.

    The enum values must be the same as the values of the status column in the status
    table.

    """

    ACCEPTED = "Accepted"
    DELETED = "Deleted"
    IN_QUEUE = "In queue"
    REJECTED = "Rejected"

    @staticmethod
    def for_value(value: str) -> Status:
        """The status for a case-insensitive status value.

        Parameters
        ----------
        value : str
            Status value.

        Returns
        -------
        Status :
            Status.

        """

        for status in Status:
            if value.lower() == str(status.value).lower():
                return status

        raise ValueError(f"Unknown status: {value}")


class StokesParameter(Enum):
    """
    Enumeration of the Stokes parameters.

    The enum values must be the same as the values of the stokesParameter column in the
    stokes_parameter table.

    """

    I = "I"
    Q = "Q"
    U = "U"
    V = "V"


class Target:
    """
    A target.

    Parameters
    ----------
    name : str
        Target name.
    observation_id : int
        Database id of the observation during which the target was observed.
    standard : bool
        Whether the targetv is used as a standard.
    target_type : str
        Numeric code for the target type, such as "15.15.02.02".

    """

    def __init__(
        self, name: str, observation_id: int, standard: bool, target_type: str
    ):
        if name and len(name) > 50:
            raise ValueError("The target name must have at most 50 characters.")

        self._name = name
        self._observation_id = observation_id
        self._standard = standard
        self._target_type = target_type

    @property
    def name(self) -> str:
        return self._name

    @property
    def observation_id(self) -> int:
        return self._observation_id

    @property
    def standard(self) -> bool:
        return self._standard

    @property
    def target_type(self) -> str:
        return self._target_type


class Telescope(Enum):
    """
    Enumeration of the telescopes included in the SSDA.

    The enum values must be the same as the telescope names in the Telescope table.

    """

    LESEDI = "LESEDI"
    ONE_DOT_NINE = "1.9 m"
    SALT = "SALT"
