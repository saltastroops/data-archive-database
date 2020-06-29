from datetime import datetime, timezone
from typing import Any, Optional

from ssda.util import types


def parse_start_datetime(start_date: str, start_time: str):
    """
    Combine start dare and time from a SALT FITS file into a UTC datetime.

    Parameters
    ----------
    start_date : str
        Start date.
    start_time L: str
        Start time.

    Returns
    -------
    datetime
        The start datetime (as UTC).

    """

    start_date_time_str = start_date + " " + start_time
    try:
        start_date_time = datetime.strptime(start_date_time_str, "%Y-%m-%d %H:%M:%S.%f")
    except ValueError:
        # support legacy format
        start_date_time = datetime.strptime(start_date_time_str, "%Y-%m-%d %H:%M:%S")
    start_time_tz = datetime(
        year=start_date_time.year,
        month=start_date_time.month,
        day=start_date_time.day,
        hour=start_date_time.hour,
        minute=start_date_time.minute,
        second=start_date_time.second,
        tzinfo=timezone.utc,
    )

    return start_time_tz


def find_fabry_perot_mode(header_value: Any) -> Optional[types.RSSFabryPerotMode]:
    etalon_state = header_value("ET-STATE")
    if etalon_state.lower() == "s1 - etalon open":
        return None

    if etalon_state.lower() == "s3 - etalon 2":
        fabry_perot_mode = types.RSSFabryPerotMode.parse_fp_mode(
            header_value("ET2MODE").upper()
        )
    elif (
            etalon_state.lower() == "s2 - etalon 1"
            or etalon_state.lower() == "s4 - etalon 1 & 2"
    ):
        fabry_perot_mode = types.RSSFabryPerotMode.parse_fp_mode(header_value("ET1MODE").upper())
    else:
        raise ValueError("Unknown etalon state: '{etalon_state}")
    return fabry_perot_mode
