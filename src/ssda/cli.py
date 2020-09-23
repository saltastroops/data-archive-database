from typing import Optional, Tuple
import click
from datetime import date
from ssda.ssda_daily_update import daily_update
from ssda.ssda_delete import delete_in_ssda
from ssda.ssda_populate import populate_ssda
from ssda.ssda_sync import sync_ssda


@click.group()
def main():
    pass


@main.command()
@click.option("--end", type=str, help="Start date of the last night to consider.")
@click.option(
    "--fits-base-dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Base directory containing all the FITS files.",
)
@click.option(
    "--file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
    help="FITS file to map to the database.",
)
@click.option(
    "--instrument",
    "instruments",
    type=click.Choice(["BCAM", "HRS", "RSS", "Salticam"], case_sensitive=False),
    multiple=True,
    help="Instrument to consider.",
)
@click.option(
    "--skip-errors", is_flag=True, help="Do not terminate if there is an error"
)
@click.option("--start", type=str, help="Start date of the last night to consider.")
@click.option(
    "--task",
    type=click.Choice(["delete", "insert"]),
    required=True,
    help="Task to perform.",
)
@click.option(
    "--verbosity",
    required=False,
    type=click.Choice(["0", "1", "2", "3"]),
    help="Log more details.",
)
def populate(start: Optional[str],
             end: Optional[str],
             instruments: Tuple[str],
             file: Optional[str],
             fits_base_dir: Optional[str],
             skip_errors: bool,
             verbosity: Optional[str]):
    """Populate the database SSDA"""
    populate_ssda(start, end, instruments, file, fits_base_dir, skip_errors, verbosity)


@main.command()
def sync():
    """Sync SSDA and SDB Databases"""
    sync_ssda()


@main.command()
@click.option("--end", type=str, help="Start date of the last night to consider.")
@click.option("--start", type=str, help="Start date of the last night to consider.")
@click.option(
    "--file",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="FITS file to map to the database.",
)
def delete(file: Optional[str], start: Optional[date], end: Optional[date]):
    """Delete file from database"""
    delete_in_ssda(file, start, end)


@main.command()
def daily():
    """
    Perform the daily database update.

    This includes dumping the current database content, populating the database with
    data (from 7 days ago, plus a few days before) and synchronising the database with
    the SDB.

    """

    daily_update()


if __name__ == "__main__":
    main()
