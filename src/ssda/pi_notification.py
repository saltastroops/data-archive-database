from typing import Dict, List, Optional
from dataclasses import dataclass
import os
import pymysql
import psycopg2
from prettytable import PrettyTable
from psycopg2 import extras
import smtplib
from datetime import datetime, timedelta
import dsnparse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date
import click
from emailedbefore import SentEmails


@dataclass
class Proposal:
    code: str
    release_date: date
    title: Optional[str]


@dataclass
class Astronomer:
    fullname: str
    email: str
    proposals: List[Proposal]


class DatabaseConfiguration:
    """
    A database configuration.

    Parameters
    ----------
    host : str
        Domain of the host server (such as 127.0.0.1 or db.your.host)
    username : str
        Username of the database user.
    password : str
        Password of the database user.
    database : str
        Name of the database.
    port : int
        Port number.
    """

    def __init__(
            self, host: str, username: str, password: str, database: str, port: int
    ) -> None:
        if port <= 0:
            raise ValueError("The port number must be positive.")

        self._host = host
        self._username = username
        self._password = password
        self._database = database
        self._port = port

    def host(self) -> str:
        """
        The domain of the host server.
        Returns
        -------
        str
            The host server.
        """

        return self._host

    def username(self) -> str:
        """
        The username of the database user.
        Returns
        -------
        str
            The database user.
        """

        return self._username

    def password(self) -> str:
        """
        The password of the database user.
        Returns
        -------
        str
            The password.
        """

        return self._password

    def database(self) -> str:
        """
        The name of the database.
        Returns
        -------
        str
            The name of the database.
        """

        return self._database

    def port(self) -> int:
        """
        The port number.
        Returns
        -------
        int
            The port number.
        """

        return self._port

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DatabaseConfiguration):
            return NotImplemented
        return (
                self.host() == other.host()
                and self.username() == other.username()
                and self.password() == other.password()
                and self.database() == other.database()
                and self.port() == other.port()
        )


def sdb_database_connection():
    sdb_db_config = dsnparse.parse_environ("SDB_DSN")
    sdb_db_config = DatabaseConfiguration(
        username=sdb_db_config.user,
        password=sdb_db_config.secret,
        host=sdb_db_config.host,
        port=3306,
        database=sdb_db_config.database,
    )
    sdb_connection = pymysql.connect(
        database=sdb_db_config.database(),
        host=sdb_db_config.host(),
        user=sdb_db_config.username(),
        passwd=sdb_db_config.password()
    )
    return sdb_connection


def ssda_database_connection():
    ssda_db_config = dsnparse.parse_environ("SSDA_DSN")
    ssda_db_config = DatabaseConfiguration(
        username=ssda_db_config.user,
        password=ssda_db_config.secret,
        host=ssda_db_config.host,
        port=ssda_db_config.port,
        database=ssda_db_config.database,
    )
    ssda_connection = psycopg2.connect(
        database=ssda_db_config.database(),
        host=ssda_db_config.host(),
        user=ssda_db_config.username(),
        password=ssda_db_config.password(),
    )
    return ssda_connection


# getting the release dates for the proposals in ssda
def proposal_release_dates(days):
    with ssda_database_connection().cursor(
            cursor_factory=psycopg2.extras.DictCursor
    ) as ssda_cursor:
        psql_query = """SELECT DISTINCT proposal_code, data_release
                        FROM observations.proposal proposal
                        JOIN observations.observation obs on proposal.proposal_id=obs.proposal_id
                        JOIN observations.telescope telescope on obs.telescope_id=telescope.telescope_id
                        WHERE name='SALT' and data_release - CURRENT_DATE BETWEEN 1 and %(days)s"""
        ssda_cursor.execute(psql_query, dict(days=days))
        results = ssda_cursor.fetchall()
        ssda_query_results = {
            pi_proposal["proposal_code"]: pi_proposal["data_release"]
            for pi_proposal in results
        }
        return ssda_query_results


# Return a nested dictionary of the PI and PC email and full name for a list of proposal
# codes.
def _astronomers_details(proposal_codes):
    if not len(proposal_codes):
        return {}

    sdb_query_results = {}
    with sdb_database_connection().cursor(
            pymysql.cursors.DictCursor
    ) as database_connection:
        pi_query = """
SELECT Proposal_Code,
       pi.Email AS pi_email,
       CONCAT(pi.FirstName, ' ', pi.Surname) AS pi_fullname,
       pc.Email AS pc_email,
       CONCAT(pc.FirstName, ' ', pc.Surname) AS pc_fullname
FROM ProposalContact
JOIN ProposalCode ON ProposalCode.ProposalCode_Id = ProposalContact.ProposalCode_Id
JOIN Investigator pi ON pi.Investigator_Id = ProposalContact.Leader_Id
JOIN Investigator pc ON pc.Investigator_Id = ProposalContact.Contact_Id
WHERE Proposal_Code IN %(proposal_codes)s
        """
        database_connection.execute(pi_query, dict(proposal_codes=proposal_codes))
        results = database_connection.fetchall()
        for result in results:
            astronomers = []
            astronomers.append({"email": result["pi_email"], "fullname": result["pi_fullname"]})
            if result["pc_fullname"] != result["pi_fullname"]:
                astronomers.append({"email": result["pc_email"], "fullname": result["pc_fullname"]})
            sdb_query_results[result["Proposal_Code"]] = astronomers
        return sdb_query_results


def _proposal_titles(proposal_codes: List[str]) -> Dict[str, str]:
    if not len(proposal_codes):
        return {}

    sdb_query_results: Dict[str, str] = {}
    with sdb_database_connection().cursor(
            pymysql.cursors.DictCursor
    ) as database_connection:
        title_query = """SELECT Proposal_Code, Title
                     FROM ProposalText
                     JOIN ProposalCode ON ProposalText.ProposalCode_Id=ProposalCode.ProposalCode_Id
                     WHERE Proposal_Code IN %(proposal_codes)s"""
        database_connection.execute(title_query, dict(proposal_codes=proposal_codes))
        results = database_connection.fetchall()
        for result in results:
            sdb_query_results[result["Proposal_Code"]] = str(result["Title"])
        return sdb_query_results


def astronomers_details(days):
    proposals_and_release_dates = proposal_release_dates(days)
    proposal_titles = _proposal_titles(list(proposals_and_release_dates.keys()))
    proposal_and_pi_information = _astronomers_details(list(proposals_and_release_dates.keys()))

    all_data = {}
    for proposal_code in proposals_and_release_dates:
        if proposal_code not in proposal_and_pi_information:
            raise ValueError("invalid proposal code.")
        for astronomer in proposal_and_pi_information[proposal_code]:
            email = astronomer['email']
            fullname = astronomer['fullname']
            proposal_release_date = proposals_and_release_dates[proposal_code]

            if email not in all_data:
                all_data[email] = {
                    "proposals": [],
                    "fullname": fullname,
                }
            all_data[email]["proposals"].append({"proposal_code": proposal_code, "release_date": proposal_release_date})

    astronomers = []
    for key, astronomer in all_data.items():
        proposals = []
        for proposal in sorted(astronomer["proposals"], key=lambda i: i["proposal_code"]):
            proposals.append(
                Proposal(
                    code=proposal["proposal_code"],
                    release_date=proposal["release_date"],
                    title=proposal_titles[proposal["proposal_code"]]
                )
            )
        astronomers.append(Astronomer(
            fullname=astronomer["fullname"],
            email=key,
            proposals=proposals
        ))
    return astronomers


def plain_text_email_content(table, pi_name):
    message = f"""
Dear {pi_name},

Please note that the observation data of your following proposals will become public soon.

{table}

You may request an extension on the proposal's page in the Web Manager.

Kind regards,

SALT Astronomy Operations"""
    return message


def html_email_content(table):
    message = f"""
Please note that the observation data of your following proposals will become public soon.<br><br>

{table}<br>

You may request an extension on the proposal's page in the Web Manager.<br><br>

Kind regards,<br><br>

SALT Astronomy Operations"""
    return message


def sending_email(receiver, pi_name, plain_table, styled_table):
    sender = "salthelp@salt.ac.za"
    message = MIMEMultipart("alternative")
    message["Subject"] = "Your SALT proposal data will become public"
    message["From"] = sender
    message["To"] = receiver

    # write the plain text part
    text = f"""{plain_text_email_content(plain_table, pi_name)} """

    # write the html part
    html = f"""
<html>
  <body>
   <p> Dear {pi_name},<br><br>
      
      {html_email_content(styled_table)}
  
  </body>
</html>
 """
    # convert both the parts to MIMEText objects and add them to the MIMEMultipart message
    part1 = MIMEText(text, "plain")

    part2 = MIMEText(html, "html")
    message.attach(part1)
    message.attach(part2)

    # now we send the email
    mail_port = os.environ.get("MAIL_PORT")
    mail_server = os.environ.get("MAIL_SERVER")
    mail_username = os.environ.get("MAIL_USER")
    mail_password = os.environ.get("MAIL_PASSWORD")

    with smtplib.SMTP(mail_server, mail_port) as server:
        if mail_username:
            server.starttls()
            server.login(mail_username, mail_password)
        server.sendmail(
            sender,
            receiver,
            message.as_string()
        )
        return "Email has been sent"


def log_to_database(email_receiver, proposal_code):
    now = datetime.now()
    sent_emails = SentEmails(os.environ["SENT_EMAILS_DB"])
    sent_emails.register(email_receiver, _email_topic(proposal_code), now)


def email_sent_at(email_receiver: str, proposal_code: str) -> datetime:
    return SentEmails.last_sent_at(SentEmails(os.environ["SENT_EMAILS_DB"]), email_receiver, _email_topic(proposal_code))


def _email_topic(proposal_code: str) -> str:
    return f'Release date for {proposal_code}'


def plain_text_table(proposals):
    table = PrettyTable()
    table.field_names = ["Proposal", "Title", "Release Date"]
    table.align["Proposal"] = "l"
    table.align["Title"] = "l"
    table.align["Release Date"] = "l"
    for proposal in proposals:
        table.add_row([proposal.code, proposal.title, proposal.release_date])
    return table


def html_table(proposals):
    table = """

    <style>
     table {
     font-family: arial, sans-serif;
     border-collapse: collapse;
     }
     th, td {
     border: 1px solid #dddddd;
     padding: 8px;
     text-align:left;
     }
     
    </style>

    <body>
     <table>
       <tr>
         <th>Proposal</th>
         <th>Title</th>
         <th>Release Date</th>
       </tr>
       """

    for pi_proposal in proposals:
        table += f"""
                  <tr>
                    <td><a href="https://www.salt.ac.za/wm/proposal/{pi_proposal.code}">{pi_proposal.code}</a></td>
                    <td>{pi_proposal.title}</td>
                    <td>{pi_proposal.release_date}</td>
                   </tr>"""
    table += '</table>'
    return table


def proposals_to_send(pi_proposals, email):
    info = []
    for proposal in pi_proposals:
        sent_at = email_sent_at(email, proposal.code)
        if not sent_at or datetime.now() - sent_at > timedelta(days=14):
            info.append(proposal)
    return info


def adding_each_proposal_to_db(pi_proposals, email):
    for proposal in pi_proposals:
        log_to_database(email, proposal.code)
    return None


def handle_pi(pi_information):
    proposals = proposals_to_send(pi_information.proposals, pi_information.email)
    if len(proposals) > 0:
        sending_email(pi_information.email, pi_information.fullname, plain_text_table(proposals), html_table(proposals))
        adding_each_proposal_to_db(pi_information.proposals, pi_information.email)
    return None


def notify(days):
    p = astronomers_details(days)
    for pi_information in p:
        handle_pi(pi_information)
    return None
