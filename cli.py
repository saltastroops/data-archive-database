import os
import traceback

import click
from datetime import datetime, timedelta
import logging
from typing import Optional, Set, Tuple
import sentry_sdk

import ssda.database_update
from ssda.instrument.instrument import Instrument
from ssda.database_update import UpdateAction, fits_data_from_date_range_gen, \
    fits_data_from_file_gen

INSTRUMENTS = [instrument.value for instrument in Instrument]

TABLES = ['Observation', 'Proposal']
if os.environ.get('SENTRY_DSN'):
    sentry_sdk.init(os.environ.get('SENTRY_DSN'))


class DateWithKeywordsParamType(click.ParamType):
    """
    Parameter type for dates.

    The value must be a date of the form yyyy-mm-dd, the string yesterday or the string
    last-year.

    yesterday is converted to yesterday's date; last-night is converted to the date 365
    days ago.

    """

    name = "date"

    def convert(self, value: str, param, ctx):
        value = value.lower()

        if value == 'yesterday':
            return (datetime.now() - timedelta(days=1)).date()
        if value == 'last-year':
            return (datetime.now() - timedelta(days=365)).date()
        try:
            return datetime.strptime(value, '%Y-%m-%d').date()
        except ValueError:
            self.fail(f'{value} is neither a date of the form yyyy-mm-dd, nor the string yesterday, nor the '
                      f'string last-year.')


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
        raise Exception('You must either specify a date range (with the --start/--end options) or '
                        'a FITS file (with the --file option).')

    # Exactly one instrument must be specified if the --file option is used
    if file and len(set(instruments)) != 1:
        raise Exception('The --instrument option must be used exactly once if you use the --file option.')

    # The start date must not be later than the end date
    if start and end and start.date() > end.date():
        raise Exception('The start date must not be later than the end date.')

    # No future dates are allowed
    if end.date() > datetime.now().date():
        raise Exception('The --start and --end options do not allow future dates.')


def update_database(action: UpdateAction, start: datetime, end: datetime, file: str, instruments: Tuple[str],
                    tables: Tuple[str] = None):
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
    tables : str
        Which tables to update. All tables are updated if an empty set is passed. This
        argument is ignored when inserting or deleting.

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
        # Clean up table values.
        tables = set(tables or ())

        # Convert instrument names to instruments
        instruments = set(instrument_from_name(name) for name in instruments)

        # Create a generator for the FITS data
        if start and end:
            logging.info('Files from {start} to {end} are considered.'.format(start=start.strftime('%d %b %Y'),
                                                                              end=end.strftime('%d %b %Y')))
            fits_data_gen = fits_data_from_date_range_gen(start_date=start,
                                                          end_date=end,
                                                          instruments=set(instruments))
        elif file:
            fits_data_gen = fits_data_from_file_gen(fits_file=file,
                                                    instrument=list(instruments)[0])
        else:
            raise ValueError('Neither a date range nor a FITS file have been given.')

        # Perform the database update for every FITS file
        for fits_data in fits_data_gen:
            ssda.database_update.update_database(action, fits_data, tables)

    except Exception as e:
        logging.critical('Exception occurred', exc_info=True)
        click.echo(click.style(str(e), fg='red', blink=True, bold=True))
        return -1

    # Success!
    return 0


@click.group()
@click.option('--verbose',
              is_flag=True,
              help='Log in verbose mode.')
def cli(verbose):
    """
    Update the database for the SAAO/SALT Data Archive.

    """

    if verbose:
        logging.basicConfig(level=logging.INFO)


@cli.command()
@click.option('--end',
              type=DateWithKeywordsParamType(),
              help='Start date of the last night to consider.')
@click.option('--file',
              type=click.Path(exists=True, file_okay=True),
              help='FITS file to map to the database.')
@click.option('--instrument', 'instruments',
              type=click.Choice(INSTRUMENTS, case_sensitive=False),
              multiple=True,
              help='Instrument to consider.')
@click.option('--start',
              type=DateWithKeywordsParamType(),
              help='Start date of the last night to consider.')
def insert(end: datetime, file: str, instruments: Tuple[str], start: datetime):
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
    instruments : tuple of str
        Instruments to consider.
    start : datetime
        Start date of the first night to consider

    Returns
    -------
    status : int
        Error status. 0 means success, any other value means an error.

    """

    return update_database(UpdateAction.INSERT, start, end, file, instruments)


@cli.command()
@click.option('--end',
              type=DateWithKeywordsParamType(),
              help='Start date of the last night to consider.')
@click.option('--file',
              type=click.Path(exists=True, file_okay=True),
              help='FITS file to map to the database.')
@click.option('--instrument', 'instruments',
              type=click.Choice(INSTRUMENTS, case_sensitive=False),
              multiple=True,
              help='Instrument to consider.')
@click.option('--start',
              type=DateWithKeywordsParamType(),
              help='Start date of the last night to consider.')
@click.option('--table', 'tables',
              type=click.Choice(TABLES, case_sensitive=False),
              multiple=True,
              help='What information to update.')
def update(end: datetime, file: str, instruments: Tuple[str], start: datetime, tables: Tuple[str]):
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
    instruments : tuple of str
        Instruments to consider.
    start : datetime
        Start date of the first night to consider
    tables :

    Returns
    -------
    status : int
        Error status. 0 means success, any other value means an error.

    """

    return update_database(UpdateAction.UPDATE, start, end, file, instruments, tables)


@cli.command()
@click.option('--end',
              type=DateWithKeywordsParamType(),
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
              type=DateWithKeywordsParamType(),
              help='Start date of the last night to consider.')
def delete(end: datetime, file: str, force: bool, instruments: Tuple[str], start: datetime):
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
    instruments : tuple of str
        Instruments to consider.
    start : datetime
        Start date of the first night to consider

    Returns
    -------
    status : int
        Error status. 0 means success, any other value means an error.

    """

    if not force and not click.confirm('Do you really want to delete database entries?'):
        click.echo('No entries have been deleted.')
        return 0

    return update_database(UpdateAction.DELETE, start, end, file, instruments)


if __name__ == '__main__':
    cli()
