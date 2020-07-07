from typing import Callable
from datetime import timedelta, datetime, date

import click


def parse_date(value: str, now: Callable[[], datetime]) -> date:
    """
    Parse a date string.
    The value must be a date of the form yyyy-mm-dd. Alternatively, you can use the
    keywords today and yesterday.
    Parameters
    ----------
    value : str
         Date string
    now : func
         Function returning the current datetime.
    """

    if value == "today":
        return now().date()
    if value == "yesterday":
        return (now() - timedelta(days=1)).date()
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        raise click.UsageError(
            f"{value} is neither a valid date of the form yyyy-mm-dd, nor the string "
            f"yesterday, nor the string today."
        )
