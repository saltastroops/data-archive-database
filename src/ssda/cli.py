import click
from datetime import date, datetime, timedelta
from typing import Callable, Optional, Set, Tuple

from ssda.observation import StandardObservationProperties, DummyObservationProperties
from ssda.task import execute_task
from ssda.util.fits import fits_file_paths
from ssda.util.types import (
    Instrument,
    DateRange,
    TaskName,
    DatabaseConfiguration,
    TaskExecutionMode,
)


def parse_date(value: str, now: Callable[[], datetime]) -> date:
    """Parse a date string.

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


def validate_options(
    start: Optional[date],
    end: Optional[date],
    file: Optional[str],
    instruments: Set[Instrument],
    fits_base_dir: Optional[str],
) -> None:
    """
    Validate the command line options.

    An exception is raised if either of the following is true.

    * A start date but no end date is given.
    * An end date but no start date is given.
    * Both a date range and a FITS file are specified.
    * Neither a date range nor a FITS file are specified.
    * Either no instrument or more than one instrument is specified along with
      specifying a FITS file.
    * The start date is later than the end date.
    * A future date is specified.

    Parameters
    ----------
    start : datetime
        Start date.
    end : datetime
        End date.
    file : str
        FITS file (path).
    instruments : set of Instrument
        Set of instruments.

    """

    # A start date requires an end date, and vice versa
    if start and not end:
        raise click.UsageError(
            "You must also use the --end option if you use the --start option."
        )
    if end and not start:
        raise click.UsageError(
            "You must also use the --start option if you use the --end option."
        )

    # Date ranges and the --file option are mutually exclusive
    if start and file:
        raise click.UsageError("The --start/--end and --file options are mutually exclusive.")

    # A date range requires at least one instrument
    if start and not len(instruments):
        raise click.UsageError(
            "You must specify at least one instrument (with the "
            "--instrument option) if you specify a date range."
        )

    # Either a date range or a FITS file must be specified
    if not start and not end and not file:
        raise click.UsageError(
            "You must either specify a date range (with the --start/--end options) or "
            "a FITS file (with the --file option)."
        )

    # A date range requires a base directory
    if start and not fits_base_dir:
        raise click.UsageError(
            "You must specify the base directory for the FITS files (with the"
            "--fits-base-dir option) if you are using a date range."
        )

    # A base directory and a file are mutually exclusive
    if file and fits_base_dir:
        raise click.UsageError(
            "The --file and --fits-base-dir options are mutually exclusive."
        )

    # The start date must be earlier than the end date
    if start and end and start >= end:
        raise click.UsageError("The start date must be earlier than the end date.")


@click.command()
@click.option("--end", type=str, help="Start date of the last night to consider.")
@click.option(
    "--file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
    help="FITS file to map to the database.",
)
@click.option(
    "--fits-base-dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Base directory containing all the FITS files.",
)
@click.option(
    "--instrument",
    "instruments",
    type=click.Choice(["HRS", "RSS", "Salticam"], case_sensitive=False),
    multiple=True,
    help="Instrument to consider.",
)
@click.option(
    "--mode",
    type=click.Choice(["dummy", "production"], case_sensitive=False),
    required=True,
    help="Task execution mode.",
)
@click.option("--start", type=str, help="Start date of the last night to consider.")
@click.option(
    "--task",
    type=click.Choice(["delete", "insert"]),
    required=True,
    help="Task to perform.",
)
def main(
    task: str,
    start: Optional[str],
    end: Optional[str],
    instruments: Tuple[str],
    file: Optional[str],
    fits_base_dir: Optional[str],
    mode: str,
) -> None:
    # convert options as required and validate them
    now = datetime.now
    start_date = parse_date(start, now) if start else None
    end_date = parse_date(end, now) if end else None
    instruments_set = set(Instrument.for_name(instrument) for instrument in instruments)
    task_name = TaskName.for_name(task)
    task_mode = TaskExecutionMode.for_mode(mode)
    validate_options(
        start=start_date,
        end=end_date,
        file=file,
        instruments=instruments_set,
        fits_base_dir=fits_base_dir,
    )

    # get the FITS file paths
    if start_date and end_date and fits_base_dir:
        paths = fits_file_paths(
            nights=DateRange(start_date, end_date),
            instruments=instruments_set,
            base_dir=fits_base_dir,
        )
    elif file:
        paths = iter([file])
    else:
        raise click.UsageError(
            "The command line options do not allow the FITS file paths to be found."
        )

    # execute the requested task
    for path in paths:
        execute_task(task_name=task_name, fits_path=path, task_mode=task_mode)