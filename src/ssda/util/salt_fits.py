from datetime import datetime, timezone


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
