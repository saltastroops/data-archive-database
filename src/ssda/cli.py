from typing import Optional,Tuple
import click
from ssda.ssda_populate import populate
from ssda.ssda_delete import delete
from ssda.util.ssda_sync import sync


@click.command()
@click.option("--end", type=str, help="Start date of the last night to consider.")
@click.option(
    "--file",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="FITS file to map to the database."
)
@click.option(
    "--instrument",
    "instruments",
    type=click.Choice(["BCAM", "HRS", "RSS", "Salticam"], case_sensitive=False),
    multiple=True,
    help="Instrument to consider.",
)
@click.option(
    "--mode",
    type=click.Choice(["dummy", "production"], case_sensitive=False),
    required=True,
    help="Task execution mode.",
)
@click.option(
    "--skip-errors", is_flag=True, help="Do not terminate if there is an error"
)
@click.option("--start", type=str, help="Start date of the last night to consider.")
@click.option("--task",
              type=click.Choice(["delete", "insert"]),
              required=True,
              help="Task to perform.",
              )
@click.option(
    "--verbosity", type=click.Choice(["0", "1", "2", "3"]), help="Log more details."
)
def main(
        task: str,
        start: Optional[str],
        end: Optional[str],
        instruments: Tuple[str],
        file: Optional[str],
        fits_base_dir: Optional[str],
        mode: str,
        skip_errors: bool,
        verbosity: Optional[str],
):
    if task == "populate":
        populate(start, end, instruments, file, fits_base_dir, mode, skip_errors, verbosity)

    if task == "sync":
        sync(start, end)

    if task == "delete":
        delete(file, start, end, instruments)
