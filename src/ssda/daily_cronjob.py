import click
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from ssda.util.email import sendmail


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
    send_email_notification("Greetings", "Hello Daily Cronjob!")
