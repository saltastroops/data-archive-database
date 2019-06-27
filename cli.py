import click
from datetime import date, datetime, timedelta
import logging
from typing import Generator, Optional, Set, Tuple

import ssda.database_update
from ssda.instrument.instrument import Instrument
from ssda.instrument.instrument_fits_data import InstrumentFitsData
from ssda.database_update import UpdateAction, fits_data_from_date_range_gen, \
    fits_data_from_file_gen

INSTRUMENTS = [instrument.value for instrument in Instrument]


def validate_options(start: Optional[datetime], end: Optional[datetime], file: Optional[str], instruments: Set[str]):
    """
    Validate the command line options.

    An exception is raised if either of the following is true.

    * A start date but no end date is given.
    * An end date but no start date is given.
    * Both a date range abd a FITS file are specified.
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
    instruments : set of str
        Set of instruments.

    """

    # A start date requires an end date, and vice versa
    if start and not end:
        raise Exception('You must also use the --end option if you use the --start option.')
    if end and not start:
        raise Exception('You must also use the --start option if you use the --end option.')

    # Date ranges and the --file option are mutually exclusive
    if start and file:
        raise Exception('The --start/--end and --file options are mutually exclusive.')

    # Either a date range or a FITS file must be specified
    if not start and not end:
        raise Exception('You must either specify a date range (with the --start/--end options) or a FITS file (with the --file option).')

    # Exactly one instrument must be specified if the --file option is used
    if file and len(set(instruments)) != 1:
        raise Exception('The --instrument option must be used exactly once if you use the --file option.')

    # The start date must not be later than the end date
    if start and end and start.date() > end.date():
        raise Exception('The start date must not be later than the end date.')

    # No future dates are allowed
    if end.date() > datetime.now().date():
        raise Exception('The --start and --end options do not allow future dates.')


def update_database(action: UpdateAction, start: datetime, end: datetime, file: str, instruments: Tuple[str], verbose: bool):
    """
    Update the database by inserting, updating or deleting entries.

    See the insert, update and delete functions for the rules regarding the
    parameters.

    Parameters
    ----------
    action : UpdateAction
        Action to perform (insert, update or delete).
    start : datetime
        Start date of the first night to consider.
    end : datetime
        Start date of the last night to consider.
    file : str
        File path of the FITS file to consider.
    instruments : tuple of str
        Instruments to consider.
    verbose : bool
        Whether to run in verbose mode.

    Returns
    -------
    status : int
        Error status. 0 means success, any other value means an error.

    """

    # Function for converting instrument names to instruments
    def instrument_from_name(name: str) -> Instrument:
        for instrument in Instrument:
            if name.lower() == str(instrument.value).lower():
                return instrument

        raise ValueError('No instrument found for name: {}'.format(name))

    try:
        # Convert instrument names to instruments
        instruments = set(instrument_from_name(name) for name in instruments)

        # Create a generator for the FITS data
        if start and end:
            fits_data_gen = fits_data_from_date_range_gen(start_date=start.date(),
                                                          end_date=end.date(),
                                                          instruments=set(instruments))
        elif file:
            fits_data_gen = fits_data_from_file_gen(fits_file=file,
                                                    instrument=list(instruments)[0])
        else:
            raise ValueError('Neither a date range nor a FITS file have been given.')

        # Perform the database update for every FITS file
        for fits_data in fits_data_gen:
            ssda.database_update.update_database(action, fits_data, verbose)

    except Exception as e:
        logging.critical('Exception occurred', exc_info=True)
        click.echo(click.style(str(e), fg='red', blink=True, bold=True))
        return -1

    # Success!
    return 0


@click.group()
def cli():
    """
    Update the database for the SAAO/SALT Data Archive.

    """

    pass


@cli.command()
@click.option('--end',
              type=click.DateTime(formats=['%Y-%m-%d']),
              help='Start date of the last night to consider.')
@click.option('--file',
              type=click.Path(exists=True, file_okay=True),
              help='FITS file to map to the database.')
@click.option('--instrument', 'instruments',
              type=click.Choice(INSTRUMENTS, case_sensitive=False),
              multiple=True,
              help='Instrument to consider.')
@click.option('--start',
              type=click.DateTime(formats=['%Y-%m-%d']),
              help='Start date of the last night to consider.')
@click.option('--verbose',
              is_flag=True,
              help='Run in verbose mode.')
def insert(end: datetime, file: str, instruments: Tuple[str], start: datetime, verbose: bool):
    """
    Insert entries into the data archive database.

    The entries are generated from the FITS files in a date range (if the --start and
    --end options are used), or from a single FITS file (if the --file option is used).
    By default all instruments are considered, but you may restrict insertion to an
    instrument with the --instrument option. This option may be used multiple times in
    case you want to restrict insertion to a set of instruments.

    If you specify a FITS file with the --file option you also need to specify the
    instrument which took the data by using the --instrument option exactly once.

    You cannot specify a date range and a file at the same time.

    Already existing database entries will not be modified; use the update command if
    you need to update database entries.

    Parameters
    ----------
    end : datetime
        Start date of the last night to consider.
    file : str
        FITS file to consider.
    force
    instruments : set of str
        Instruments to consider.
    start : datetime
        Start date of the first night to consider
    verbose : bool
        Whether to run in verbose mode.

    Returns
    -------
    status : int
        Error status. 0 means success, any other value means an error.

    """

    return update_database(UpdateAction.INSERT, start, end, file, instruments, verbose)


@cli.command()
@click.option('--end',
              type=click.DateTime(formats=['%Y-%m-%d']),
              help='Start date of the last night to consider.')
@click.option('--file',
              type=click.Path(exists=True, file_okay=True),
              help='FITS file to map to the database.')
@click.option('--instrument', 'instruments',
              type=click.Choice(INSTRUMENTS, case_sensitive=False),
              multiple=True,
              help='Instrument to consider.')
@click.option('--start',
              type=click.DateTime(formats=['%Y-%m-%d']),
              help='Start date of the last night to consider.')
@click.option('--verbose',
              is_flag=True,
              help='Run in verbose mode.')
def update(end: datetime, file: str, instruments: Tuple[str], start: datetime, verbose: bool):
    """
    Update entries in the data archive database.

    The entries are updated from the FITS files in a date range (if the --start and
    --end options are used), or from a single FITS file (if the --file option is used).
    By default all instruments are considered, but you may restrict updating to an
    instrument with the --instrument option. This option may be used multiple times in
    case you want to restrict updating to a set of instruments.

    If you specify a FITS file with the --file option you also need to specify the
    instrument which took the data by using the --instrument option exactly once.

    You cannot specify a date range and a file at the same time.

    The command fails if you try to update an entry which does not exist already.

    Parameters
    ----------
    end : datetime
        Start date of the last night to consider.
    file : str
        FITS file to consider.
    instruments : set of str
        Instruments to consider.
    start : datetime
        Start date of the first night to consider
    verbose : bool
        Whether to run in verbose mode.

    Returns
    -------
    status : int
        Error status. 0 means success, any other value means an error.

    """

    return update_database(UpdateAction.UPDATE, start, end, file, instruments, verbose)


@cli.command()
@click.option('--end',
              type=click.DateTime(formats=['%Y-%m-%d']),
              help='Start date of the last night to consider.')
@click.option('--file',
              type=click.Path(exists=True, file_okay=True),
              help='FITS file to map to the database.')
@click.option('--force',
              is_flag=True,
              help='Do not ask for confirmation before deleting.')
@click.option('--instrument', 'instruments',
              type=click.Choice(INSTRUMENTS, case_sensitive=False),
              multiple=True,
              help='Instrument to consider.')
@click.option('--start',
              type=click.DateTime(formats=['%Y-%m-%d']),
              help='Start date of the last night to consider.')
@click.option('--verbose',
              is_flag=True,
              help='Run in verbose mode.')
def delete(end: datetime, file: str, force: bool, instruments: Tuple[str], start: datetime, verbose: bool):
    """
    Delete entries from the data archive database.

    The entries to delete are gathered from the FITS files in a date range (if the
    --start and --end options are used), or from a single FITS file (if the --file
    option is used). By default all instruments are considered, but you may restrict
    deleting to an instrument with the --instrument option. This option may be used
    multiple times in case you want to restrict insertion to a set of instruments.

    If you specify a FITS file with the --file option you also need to specify the
    instrument which took the data by using the --instrument option exactly once.

    You cannot specify a date range and a file at the same time.

    No error is raised if you try to delete database entries which do not exist.

    By default you are prompted to confirm that you really want to delete the database
    entries. You may avoid this by adding the --force flag.

    Parameters
    ----------
    end : datetime
        Start date of the last night to consider.
    file : str
        FITS file to consider.
    force : bool
        Whether to skip the confirmation prompt.
    instruments : set of str
        Instruments to consider.
    start : datetime
        Start date of the first night to consider
    verbose : bool
        Whether to run in verbose mode.

    Returns
    -------
    status : int
        Error status. 0 means success, any other value means an error.

    """

    if not force and not click.confirm('Do you really want to delete database entries?'):
        click.echo('No entries have been deleted.')
        return 0

    return update_database(UpdateAction.DELETE, start, end, file, instruments, verbose)


if __name__ == '__main__':
    cli()