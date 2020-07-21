import click
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from pathlib import Path
import shutil
from ssda.util.email import sendmail
import subprocess
import tempfile


def dump_database(dump_file: Path):
    """
    Dump the ssda database.

    The database must be on localhost, must be named ssda and must be accessible by the
    user running the script.

    Parameters
    ----------
    dump_file

    Returns
    -------

    """
    if dump_file.exists() and not dump_file.is_file():
        raise ValueError(f"{dump_file} is not a file.")

    with tempfile.TemporaryFile(mode="w+t") as t:
        subprocess.run(["pg_dump", "ssda"], stdout=t)
        t.seek(0)
        with open(dump_file, 'w') as f:
            for line in t:
                f.write(line)


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


def send_email_notification(subject: str, body: str):
    """
    Send an email notification.

    The email is sent to the address defined by the CRONJOB_TO_ADDRESS environment
    variable.

    Parameters
    ----------
    subject : str
        Subject,
    body : str
        Text body.

    """

    message = MIMEMultipart()
    message['From'] = 'SSDA Daily Cronjob <no-reply@ssda.saao.c.za>'
    message['To'] = f"SSDA Daily Cronjob <{os.environ['CRONJOB_TO_ADDRESS']}>"
    message['Subject'] = subject

    part = MIMEText(body, "plain")
    message.attach(part)

    sendmail(from_addr='no-reply@ssda.saao.c.za', to_addr=os.environ['CRONJOB_TO_ADDRESS'], message=message.as_string())


@click.command()
def main():
    dump_database(Path("/Users/christian/IdeaProjects/DataArchiveDatabase/DUMPS/A/dump.sql"))
