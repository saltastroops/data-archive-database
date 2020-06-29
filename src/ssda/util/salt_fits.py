from datetime import datetime, timezone
from typing import Callable, Optional

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


def find_fabry_perot_mode(header_value: Callable[[str], Optional[str]]) -> Optional[types.RSSFabryPerotMode]:
    et_state_header_value = header_value("ET-STATE")
    etalon_state = et_state_header_value.lower() if et_state_header_value else ""
    if etalon_state == "s1 - etalon open":
        return None

    if etalon_state == "s3 - etalon 2":
        et2mode_header_value = header_value("ET2MODE")
        fabry_perot_mode = types.RSSFabryPerotMode.parse_fp_mode(
            et2mode_header_value.upper() if et2mode_header_value else ""
        )
    elif (
            etalon_state == "s2 - etalon 1"
            or etalon_state == "s4 - etalon 1 & 2"
    ):
        et1mode_header_value = header_value("ET1MODE")
        fabry_perot_mode = types.RSSFabryPerotMode.parse_fp_mode(et1mode_header_value.upper() if et1mode_header_value else "")
    else:
        raise ValueError("Unknown etalon state: '{etalon_state}")
    return fabry_perot_mode
