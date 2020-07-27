import click
from dataclasses import dataclass
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import io
import os
from pathlib import Path
import re
import shutil
from ssda.util.databases import ssda_configuration
from ssda.util.email import sendmail
import subprocess
import tempfile


@dataclass(frozen=True)
class CompletedDump:
    # There is no stdout property as the database content is output to stdout.
    return_code: int
    stderr: str


@dataclass
class CompletedPopulation:
    daytime_errors: int
    nighttime_errors: int
    return_code: int
    stderr: str
    stdout: str
    warnings: int

    def __init__(self, completed_process: subprocess.CompletedProcess):
        stderr = completed_process.stderr
        properties = ['daytime errors', 'nighttime errors', 'warnings']
        metadata = {}
        for p in properties:
            m = re.findall(r'Total number of ' + p + r':\s*(\d+)', stderr)
            if len(m) == 0:
                message = f"""\
The error output does not include the number of {p}.

The error output is:

{completed_process.stderr}
"""
                raise ValueError(message)
            metadata[p] = int(m[0])

        self.daytime_errors=metadata["daytime errors"]
        self.nighttime_errors=metadata['nighttime errors']
        self.return_code=completed_process.returncode
        self.stderr=stderr
        self.stdout=completed_process.stdout
        self.warnings=metadata['warnings']


@dataclass(frozen=True)
class CompletedSynchronisation:
    return_code: int
    stderr: str
    stdout: str


def dump_database(dump_file: Path):
    """
    Dump the ssda database.

    Parameters
    ----------
    dump_file

    Returns
    -------

    """
    if dump_file.exists() and not dump_file.is_file():
        raise ValueError(f"{dump_file} is not a file.")

    database_config = ssda_configuration()

    with tempfile.TemporaryFile(mode="w+t") as t:
        # Dump the database into a temporary file...
        command = [
            "pg_dump",
            "--host",
            database_config.host(),
            "--port",
            str(database_config.port()),
            "--dbname",
            database_config.database(),
            "--username",
            database_config.username(),
            "--password"
        ]
        stderr = io.StringIO()
        completed_process = subprocess.run(command, input=database_config.password() + "\n", stderr=stderr, stdout=t, text=True)
        completed_dump = CompletedDump(return_code=completed_process.returncode, stderr=completed_process.stderr)

        if completed_process.returncode:
            # The database could not be dumped, so we better stop.
            return completed_dump

    # ... and copy the temporary file to the database dump file.
        t.seek(0)
        with open(dump_file, 'w') as f:
            for line in t:
                f.write(line)

        return completed_dump


def backup(path: Path, num_backups: int = 10):
    """
    Backup a file, keeping a number of previous versions.

    Backups have a running number as suffix. For example, from latest to oldest, the
    backups of a file dump.sql would be named dump.sql.1, dump.sql.2, dump.sql.3, ...

    When a new backup is made, existing backups are "shifted", i.e. (again using
    dump.sql as an example) dump.sql.1 becomes dump.sql.2, dump.sql.2 becomes dump.sql.3
    and so forth. If there exist num_backups backups already, the oldest backup is
    deleted.

    Parameters
    ----------
    path : Path
       File to backup.
    num_backups : int
       Number of backups to keep.

    Returns
    -------

    """
    if num_backups < 1:
        raise ValueError("num_backups must be a positive integer.")

    if not path.exists():
        return

    for i in range(num_backups - 1, -1, -1):
        source = (path.parent / path.name).with_suffix(path.suffix + (f".{i}" if i != 0 else ""))
        target = (path.parent / path.name).with_suffix(path.suffix + f".{i + 1}")
        if source.exists():
            shutil.copy(str(source), str(target))


def populate_database():
    # TODO: Check whether pipeline has run successfully
    start_date = datetime.now().date() - timedelta(days=30)
    end_date = datetime.now().date() - timedelta(days=7)

    command = [
        'ssda',
        '--task',
        'insert',
        '--mode',
        'production',
        '--start',
        start_date.strftime("%Y-%m-%d"),
        '--end',
        end_date.strftime("%Y-%m-%d"),
        '--fits-base-dir',
        os.environ['FITS_BASE_DIR'],
        '--verbosity',
        '2',
        '--skip-errors'
    ]
    completed_process = subprocess.run(command, capture_output=True, text=True)

    return CompletedPopulation(completed_process)


def synchronise_database():
    command = ['ssda_sync']
    completed_process = subprocess.run(command, capture_output=True, text=True)

    return CompletedSynchronisation(return_code=completed_process.returncode, stderr=completed_process.stderr, stdout=completed_process.stdout)


def send_email_notification(subject: str, body: str):
    """
    Send an email notification.

    The email is sent to the address defined by the MAIL_SUMMARY_ADDRESS environment
    variable.

    Parameters
    ----------
    subject : str
        Subject,
    body : str
        Text body.

    """

    message = MIMEMultipart()
    message['From'] = 'SSDA Daily Maintenance <no-reply@ssda.saao.c.za>'
    message['To'] = f"SSDA Daily Maintenance <{os.environ['MAIL_SUMMARY_ADDRESS']}>"
    message['Subject'] = subject

    part = MIMEText(body, "plain")
    message.attach(part)

    sendmail(from_addr='no-reply@ssda.saao.c.za', to_addr=os.environ['MAIL_SUMMARY_ADDRESS'], message=message.as_string())


def check_environment_variables():
    """
    Check whether all required and optional environment variables are defined.

    """

    required_variables = ['MAIL_SUMMARY_ADDRESS', 'FITS_BASE_DIR', 'MAIL_PORT', 'MAIL_SERVER', 'SDB_DSN', 'SSDA_DSN',]
    optional_variables = ['MAIL_PASSWORD', 'MAIL_USERNAME']
    missing_required_variables = []
    missing_optional_variables = []
    for variable in required_variables:
        if variable not in os.environ:
            missing_required_variables.append(variable)
    for variable in optional_variables:
        if variable not in os.environ:
            missing_optional_variables.append(variable)

    if len(missing_optional_variables):
        click.echo(click.style(f"You may have to define the following environment "
                               f"variables: {', '.join(missing_optional_variables)}.",
                               fg="yellow"))
    if len(missing_required_variables):
        raise ValueError(f"The following environment variable(s) need to be defined: "
                         f"{', '.join(missing_required_variables)}.")


def database_dump_message(completed_dump: CompletedDump) -> str:
    return f"""\
=============
Database dump
=============

Status: {"Success" if not completed_dump.return_code else "FAILURE"}

Output to stderr
----------------
{completed_dump.stderr}
"""


def database_population_message(completed_population: CompletedPopulation) -> str:
    return f"""\
===================
Database population
===================

Status: {"Success" if not completed_population.return_code else "FAILURE"}

Number of nighttime errors: {completed_population.nighttime_errors}
Number of daytime errors:   {completed_population.daytime_errors}
Number of warnings:         {completed_population.warnings}

Output to stdout
----------------
{completed_population.stdout}

Output to stderr
----------------
{completed_population.stderr}
"""


def database_synchronisation_message(completed_synchronisation: CompletedSynchronisation) -> str:
    return f"""\
========================
Database synchronisation
========================

Status: {"Success" if not completed_synchronisation.return_code else "FAILURE"}

Output to stdout
----------------
{completed_synchronisation.stdout}

Output to stderr
----------------
{completed_synchronisation.stderr}
"""


@click.command()
def main():
    """
    Perform daily maintenance work for the SAAO/SALT Data Archive.

    The maintenance includes:

    * Dumping the database. The latest previous dumps are retained.
    * Populating the database for the last few nights.
    * Synchronising the database with other databases.

    A summary of the run of the script is sent by email.

    The following environment variables need to be defined for this script.

    * FITS_BASE_DIR: Base directory for the FITS files.
    * MAIL_PORT: Port of the mail server for sending the summary email.
    * MAIL_SERVER: Address of the mail server.
    * MAIL_SUMMARY_ADDRESS: Email address to which the summary email should be sent.
    * SDB_DSN: Data source name (DSN) for the DSALT Science Database.
    * SSDA_DSN: Data source name (DSN) for the SAAO/SALT Data Archive database.

    In production you probably have to set the following environment variables as well.

    * MAIL_PASSWORD: Password for accessing the mail server.
    * MAIL_USERNAME: Username for accessing the mail server,

    """

    message = ""
    failed = False
    try:
        check_environment_variables()
        database_dump_file = Path(os.environ['DATABASE_DUMP_FILE'])
        backup(database_dump_file)
        completed_dump = dump_database(database_dump_file)
        message += database_dump_message(completed_dump)
        message += "\n"
        completed_population = populate_database()
        message += database_population_message(completed_population)
        message += "\n"
        completed_synchronisation = synchronise_database()
        message += database_synchronisation_message(completed_synchronisation)
        message = f"The daily SSDA update has completed.\n\n" + message
    except Exception as e:
        failed = True
        message = f"The daily SSDA update failed with an error:\n\n{e}\n\n" + message

    subject = ("FAILED: " if failed else "") + "Daily SSDA maintenance for "
    send_email_notification(subject, message)
