from collections import defaultdict
from typing import Dict, List, Optional, cast, Set, DefaultDict
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


@dataclass(frozen=True)
class Proposal:
    code: str
    pi: str
    release_date: date
    title: Optional[str]


@dataclass
class Astronomer:
    fullname: str
    email: str
    proposals: List[Proposal]


@dataclass(frozen=True)
class TACMember:
    fullname: str
    email: str


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
def proposal_release_dates(days: int) -> Dict[str, date]:
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
def _astronomers_details(proposal_codes: List[str]) -> Dict[str, List[Dict[str, str]]]:
    if not len(proposal_codes):
        return {}

    sdb_query_results: Dict[str, List[Dict[str, str]]] = {}
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
            astronomers: List[Dict[str, str]] = [
                {"email": result["pi_email"], "fullname": result["pi_fullname"]}]
            if result["pc_fullname"] != result["pi_fullname"]:
                astronomers.append({"email": result["pc_email"], "fullname": result["pc_fullname"]})
            sdb_query_results[cast(str, result["Proposal_Code"])] = astronomers
        return sdb_query_results


def _proposal_details(proposals_and_release_dates: Dict[str, date]) -> Dict[str, Proposal]:
    if not len(proposals_and_release_dates):
        return {}

    sdb_query_results: Dict[str, Proposal] = {}
    with sdb_database_connection().cursor(
            pymysql.cursors.DictCursor
    ) as database_connection:
        details_query = """SELECT Proposal_Code, Title, FirstName, Surname, Email
FROM ProposalText
JOIN ProposalCode ON ProposalText.ProposalCode_Id=ProposalCode.ProposalCode_Id
JOIN ProposalContact ON ProposalCode.ProposalCode_Id = ProposalContact.ProposalCode_Id
JOIN Investigator ON ProposalContact.Leader_Id=Investigator.Investigator_Id
WHERE Proposal_Code IN %(proposal_codes)s"""
        database_connection.execute(details_query, dict(proposal_codes=list(proposals_and_release_dates.keys())))
        results = database_connection.fetchall()
        for result in results:
            sdb_query_results[result["Proposal_Code"]] = Proposal(
                code=result["Proposal_Code"],
                pi=f"{result['FirstName']} {result['Surname']}",
                release_date=proposals_and_release_dates[result["Proposal_Code"]],
                title=result["Title"])
        return sdb_query_results


def astronomers_details(days):
    proposals_and_release_dates = proposal_release_dates(days)
    proposal_and_pi_information = _astronomers_details(list(proposals_and_release_dates.keys()))
    proposal_details = _proposal_details(proposals_and_release_dates)

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

    astronomers: List[Astronomer] = []
    for key, astronomer in all_data.items():
        proposals: List[Proposal] = []
        for proposal in sorted(astronomer["proposals"], key=lambda i: i["proposal_code"]):
            proposal_code = proposal["proposal_code"]
            proposals.append(proposal_details[proposal_code])
        astronomers.append(Astronomer(
            fullname=astronomer["fullname"],
            email=key,
            proposals=proposals
        ))
    return astronomers


def _tac_proposal_codes(proposal_codes: List[str]) -> Dict[str, Set[str]]:
    """
    Proposals for the TACs.

    A dictionary of partner codes (such as "IUCAA") and set of proposal codes for which
    the partner TAC has allocated time is returned. A proposal code is ony included if
    it is in the supplied list of proposal codes.
    """

    query = '''
SELECT DISTINCT Proposal_Code, Partner_Code
FROM PriorityAlloc
JOIN MultiPartner ON PriorityAlloc.MultiPartner_Id=MultiPartner.MultiPartner_Id
JOIN ProposalCode ON MultiPartner.ProposalCode_Id = ProposalCode.ProposalCode_Id
JOIN Partner ON MultiPartner.Partner_Id = Partner.Partner_Id
WHERE TimeAlloc>0 AND Proposal_Code IN %(proposal_codes)s
'''
    with sdb_database_connection().cursor(pymysql.cursors.DictCursor) as cursor:
        cursor.execute(query, dict(proposal_codes=proposal_codes))
        results = cursor.fetchall()
        partner_proposals: DefaultDict[str, Set[str]] = defaultdict(set)
        for result in results:
            partner_proposals[result["Partner_Code"]].add(result["Proposal_Code"])

    return partner_proposals


def tac_proposals(days: int) -> Dict[str, Set[Proposal]]:
    proposals_and_release_dates = proposal_release_dates(days)
    proposal_details = _proposal_details(proposals_and_release_dates)
    proposal_codes = _tac_proposal_codes(list(proposals_and_release_dates.keys()))
    proposals: DefaultDict[str, Set[Proposal]] = defaultdict(set)
    for partner_code, partner_proposal_codes in proposal_codes.items():
        partner_proposals = set(
            Proposal(
                code=proposal_code,
                pi=proposal_details[proposal_code].pi,
                title=proposal_details[proposal_code].title,
                release_date=proposal_details[proposal_code].release_date
            )
            for proposal_code in partner_proposal_codes
        )
        proposals[partner_code] = partner_proposals

    return proposals


def tac_members(partner_code: str) -> Set[TACMember]:
    """
    Return a dictionary of partner codes abd corresponding TAC members.

    The TAC members include the chair(s) of the TAC.
    """

    query = '''
SELECT CONCAT(FirstName, ' ', Surname) AS FullName, Email
FROM Investigator
JOIN PiptUser ON Investigator.Investigator_Id = PiptUser.Investigator_Id
JOIN PiptUserTAC ON PiptUser.PiptUser_Id = PiptUserTAC.PiptUser_Id
JOIN Partner ON PiptUserTAC.Partner_Id = Partner.Partner_Id
WHERE Partner_Code=%(partner_code)s;
    '''

    with sdb_database_connection().cursor(pymysql.cursors.DictCursor) as cursor:
        cursor.execute(query, dict(partner_code=partner_code))
        results = cursor.fetchall()
        return set(
            TACMember(fullname=result["FullName"], email=result["Email"])
            for result in results
        )


def plain_text_email_content(table: PrettyTable, recipient_name: str, for_tac: bool) -> str:
    if for_tac:
        main_content = f"""\
This email is sent for your information only; no action on your part is required.

Your TAC has allocated time to the following SALT proposals. Their data will become public soon, unless their PIs request an extension of the proprietary period.

{table}
"""
    else:
        main_content = f"""\
Please note that the observation data of your following proposals will become public soon.

{table}

You may request an extension on the proposal's page in the Web Manager."""

    message = f"""
Dear {recipient_name},

{main_content}

Kind regards,

SALT Astronomy Operations"""
    return message


def html_email_content(table: str, recipient_name: str, for_tac: bool) -> str:
    if for_tac:
        main_content = f"""
This email is sent for your information only; no action on your part is required.<br><br>

Your TAC has allocated time to the following SALT proposals. Their data will become public soon, unless their PIs request an extension of the proprietary period.<br><br>

{table}<br>
        """
    else:
        main_content = f"""
Please note that the observation data of your following proposals will become public soon.<br><br>

{table}<br>

You may request an extension on the proposal's page in the Web Manager.
    """
    message = f"""
<html>
  <body>
Dear {recipient_name},<br><br>
      
{main_content}<br><br>

Kind regards,<br><br>

SALT Astronomy Operations"""
    return message


def sending_email(receiver: str, pi_name: str, plain_table: PrettyTable, styled_table: str, for_tac=False) -> None:
    sender = "salthelp@salt.ac.za"
    message = MIMEMultipart("alternative")
    if for_tac:
        message["Subject"] = "Some SALT proposal data will become public"
    else:
        message["Subject"] = "Your SALT proposal data will become public"
    message["From"] = sender
    message["To"] = receiver

    # write the plain text part
    recipent_name = 'TAC Member' if for_tac else pi_name
    text = plain_text_email_content(plain_table, recipent_name, for_tac=for_tac)

    # write the html part
    html = html_email_content(styled_table, recipent_name, for_tac=for_tac)

    # convert both the parts to MIMEText objects and add them to the MIMEMultipart message
    part1 = MIMEText(text, "plain")

    part2 = MIMEText(html, "html")
    message.attach(part1)
    message.attach(part2)

    # now we send the email
    mail_port = int(os.environ["MAIL_PORT"])
    mail_server = os.environ["MAIL_SERVER"]
    mail_username = os.environ["MAIL_USER"]
    mail_password = os.environ["MAIL_PASSWORD"]

    with smtplib.SMTP(mail_server, mail_port) as server:
        if mail_username:
            server.starttls()
            server.login(mail_username, mail_password)
        server.sendmail(
            sender,
            receiver,
            message.as_string()
        )


def log_to_database(email_receiver, proposal_code):
    now = datetime.now()
    sent_emails = SentEmails(os.environ["SENT_EMAILS_DB"])
    sent_emails.register(email_receiver, _email_topic(proposal_code), now)


def email_sent_at(email_receiver: str, proposal_code: str) -> Optional[datetime]:
    return SentEmails.last_sent_at(SentEmails(os.environ["SENT_EMAILS_DB"]), email_receiver, _email_topic(proposal_code))


def _email_topic(proposal_code: str) -> str:
    return f'Release date for {proposal_code}'


def plain_text_table(proposals: List[Proposal], include_pi=False):
    table = PrettyTable()
    if include_pi:
        table.field_names = ["Proposal", "PI", "Title", "Release Date"]
    else:
        table.field_names = ["Proposal", "Title", "Release Date"]
    table.align["Proposal"] = "l"
    if include_pi:
        table.align["PI"] = "l"
    table.align["Title"] = "l"
    table.align["Release Date"] = "l"
    for proposal in proposals:
        if include_pi:
            table.add_row([proposal.code, proposal.pi, proposal.title, proposal.release_date])
        else:
            table.add_row([proposal.code, proposal.title, proposal.release_date])
    return table


def html_table(proposals, include_pi=False):
    pi_header = '<th>PI</th>' if include_pi else ''
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
         """ + pi_header + """
         <th>Title</th>
         <th>Release Date</th>
       </tr>
       """

    for pi_proposal in proposals:
        pi_field = f'<td>{pi_proposal.pi}</td>' if include_pi else ''
        table += f"""
                  <tr>
                    <td><a href="https://www.salt.ac.za/wm/proposal/{pi_proposal.code}">{pi_proposal.code}</a></td>
                    {pi_field}
                    <td>{pi_proposal.title}</td>
                    <td>{pi_proposal.release_date}</td>
                   </tr>"""
    table += '</table>'
    return table


def proposals_to_send(pi_proposals, email, for_tac=False):
    info = []
    for proposal in pi_proposals:
        topic = proposal.code
        if for_tac:
            topic += '-tac'
        sent_at = email_sent_at(email, topic)
        if not sent_at or datetime.now() - sent_at > timedelta(days=14):
            info.append(proposal)
    return info


def adding_each_proposal_to_db(pi_proposals, email, for_tac=False):
    for proposal in pi_proposals:
        topic = proposal.code
        if for_tac:
            topic += '-tac'
        log_to_database(email, topic)
    return None


def handle_pi(pi_information) -> None:
    proposals = proposals_to_send(pi_information.proposals, pi_information.email)
    if len(proposals) > 0:
        sending_email(pi_information.email, pi_information.fullname, plain_text_table(proposals), html_table(proposals))
        adding_each_proposal_to_db(pi_information.proposals, pi_information.email)


def handle_tacs(days: int) -> None:
    _tac_proposals = tac_proposals(days)
    for partner_code, proposals in _tac_proposals.items():
        _tac_members = tac_members(partner_code)
        for member in _tac_members:
            handle_tac_member(member, proposals)


def handle_tac_member(tac_member: TACMember, proposals: Set[Proposal]) -> None:
    sorted_proposals = list(proposals)
    sorted_proposals.sort(key=lambda p: p.title)
    sorted_proposals = proposals_to_send(sorted_proposals, tac_member.email, for_tac=True)
    if len(sorted_proposals) > 0:
        sending_email(tac_member.email, tac_member.fullname, plain_text_table(sorted_proposals, include_pi=True), html_table(sorted_proposals, include_pi=True), for_tac=True)
        adding_each_proposal_to_db(sorted_proposals, tac_member.email, for_tac=True)


def notify(days):
    p = astronomers_details(days)
    for pi_information in p:
       handle_pi(pi_information)
    handle_tacs(days)
    return None
