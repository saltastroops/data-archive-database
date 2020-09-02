from email.mime.text import MIMEText
import os
import smtplib
from typing import Union


def sendmail(from_addr: str, to_addr: str, message: Union[str, bytes], **kwargs):
    """
    Send an email.

    The following environment variables must have been set.

    MAIL_PASSWORD: Password of the mail server account
    MAIL_PORT:     Port to use
    MAIL_SERVER:   Mail server address
    MAIL_USER:     Username of the mail server account

    For testing, you can start a local SMTP debugging server by running

    python -m smtpd -c DebuggingServer -n localhost:1025

    You then have to set the environment variables as follows.

    MAIL_PASSWORD: must not be set
    MAIL_PORT: 1025
    MAIL_SERVER: localhost
    MAIL_USER: must not be set

    The MAIL_USER and MAIL_PASSWORD environment variables must not be set in this case
    as the debugging server does not support authentication.

    The debugging SMTP server outputs the email content to stdout. It does not send an
    emails.

    Parameters
    ----------
    from_addr : str
        Email address from which the email is sent.
    to_addr : str
        Email address to which the email is sent.
    message : str or bytes
        Text body for the email.
    **kwargs
        Other keyword arguments understood by SMTP.sendmail.

    """

    password = os.environ.get("MAIL_PASSWORD")
    port = os.environ.get("MAIL_PORT")
    server = os.environ.get("MAIL_SERVER")
    username = os.environ.get("MAIL_USER")

    with smtplib.SMTP(server, port) as server:
        if username:
            server.login(username, password)
        server.sendmail(from_addr, to_addr, message, **kwargs)
