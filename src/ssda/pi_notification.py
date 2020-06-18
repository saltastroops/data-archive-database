from typing import List
from dataclasses import dataclass
import os
import pymysql
import psycopg2
import pprint
import operator
from prettytable import PrettyTable
from psycopg2 import extras
import smtplib
import datetime
import dsnparse
from ssda.util import types
from ssda.database.ssda import SSDADatabaseService
from ssda.database.sdb import SaltDatabaseService
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date
import click


@dataclass
class Proposal:
    code: str
    release_date: date


@dataclass
class PI:
    fullname: str
    email: str
    proposals: List[Proposal]


PIs = []


def sdb_database_connection():
    sdb_db_config = dsnparse.parse_environ("SDB_DSN")
    sdb_db_config = types.DatabaseConfiguration(
        username=sdb_db_config.user,
        password=sdb_db_config.secret,
        host=sdb_db_config.host,
        port=3306,
        database=sdb_db_config.database,
    )
    sdb_database_service = SaltDatabaseService(sdb_db_config)
    sdb_connection = sdb_database_service.connection()
    return sdb_connection


def ssda_database_connection():
    ssda_db_config = dsnparse.parse_environ("SSDA_DSN")
    ssda_db_config = types.DatabaseConfiguration(
        username=ssda_db_config.user,
        password=ssda_db_config.secret,
        host=ssda_db_config.host,
        port=ssda_db_config.port,
        database=ssda_db_config.database,
    )
    ssda_database_service = SSDADatabaseService(ssda_db_config)
    ssda_connection = ssda_database_service.connection()
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


# We get the PI full names, proposals and email addresses for a list proposal codes, we then return
# a nested dictionary of the pi email and full name
def pi_details(proposal_codes):
    sdb_query_results = {}
    with sdb_database_connection().cursor(
            pymysql.cursors.DictCursor
    ) as database_connection:
        pi_query = """SELECT Proposal_Code, Email, CONCAT(FirstName," ", Surname) AS fullname
                      FROM ProposalContact
                      JOIN ProposalCode ON ProposalCode.ProposalCode_Id = ProposalContact.ProposalCode_Id
                      JOIN Investigator ON Investigator.Investigator_Id = ProposalContact.Leader_Id
                      WHERE Proposal_Code IN %(proposals)s"""
        database_connection.execute(pi_query, dict(proposals=proposal_codes))
        results = database_connection.fetchall()
        for result in results:
            sdb_query_results[result["Proposal_Code"]] = {
                "email": result["Email"],
                "fullname": result["fullname"],
            }
        return sdb_query_results


# We make a dictionary where the PI email is key and the values are the PI name and the proposals to be released in
# the given time period
def release_dates_and_proposals(days):
    proposals_and_release_dates = proposal_release_dates(days)
    proposal_and_pi_information = pi_details(list(proposals_and_release_dates.keys()))

    all_data = {}
    for proposal_code in proposals_and_release_dates:
        if proposal_code not in proposal_and_pi_information:
            raise ValueError("invalid proposal code.")
        pi_email = proposal_and_pi_information[proposal_code]['email']
        fullname = proposal_and_pi_information[proposal_code]['fullname']
        proposal_release_date = proposals_and_release_dates[proposal_code]

        if pi_email not in all_data:
            all_data[pi_email] = {
                "proposals": [],
                "fullname": fullname,
            }
        all_data[pi_email]["proposals"].append({"proposal_code": proposal_code, "release_date": proposal_release_date})
    return all_data


def pi_information_to_be_sent(days):
    for key, pi in release_dates_and_proposals(days).items():
        proposals = []
        for proposal in sorted(pi["proposals"], key=lambda i: i["proposal_code"]):
            proposals.append(
                Proposal(
                    code=proposal["proposal_code"],
                    release_date=proposal["release_date"]
                )
            )
        PIs.append(PI(
            fullname=pi["fullname"],
            email=key,
            proposals=proposals
        ))
    return PIs


def email_content(table):
    message = f"""
Please note that the observation data of your following proposals will become public soon.

{table}

You may request an extension on the proposal's page in the Web Manager.

Kind regards,

SALT Astronomy Operations"""
    return message


def sending_email(receiver, pi_name, table):
    sender = "salthelp@salt.ac.za"
    message = MIMEMultipart("alternative")
    message["Subject"] = "Your SALT proposal data will become public"
    message["From"] = sender
    message["To"] = receiver

# write the plain text part
    text = f"""
To: {receiver}
From: {sender}

Dear {pi_name}

 {email_content(table)} """

# write the html part
    html = f"""
<html>
  <body>
   <p> Dear {pi_name}<br><br>
      
      {email_content(table)}
  
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
        server.login(mail_username, mail_password)
        server.sendmail(
            sender,
            receiver,
            message.as_string()
        )
        return "Email has been sent"


def log_to_file(email_receiver, pi_proposal, release_date):
    with open("logging.txt", 'a') as log_file:
        file_information = email_receiver + " " + pi_proposal + " " + release_date
        log_file.write("%s\n" % file_information)


def read_log_file():
    with open("logging.txt", "r") as file_content:
        file_data = [data.strip("\n") for data in file_content.readlines()]
        return file_data


def plain_text_table(proposals):
    table = PrettyTable()
    table.field_names = ["Proposals", "Release Date"]
    table.align["Proposals"] = "l"
    table.align["Release Date"] = "l"
    for proposal in proposals:
        table.add_row([proposal.code, proposal.release_date])
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
         <th>Release Date</th>
       </tr>
       """

    for pi_proposal in proposals:
        table += f"""
                  <tr>
                    <td><a href="https://www.salt.ac.za/wm/proposal/{pi_proposal.code}">{pi_proposal.code}</a></td>
                    <td>{pi_proposal.release_date}</td>
                   </tr>"""
    table += '</table>'
    return table


def proposals_to_send(pi_proposals, email):
    info = []
    for proposal in pi_proposals:
        file_content = email + " " + proposal.code + " " + datetime.datetime.strftime(proposal.release_date, "%d %b %Y")
        if file_content not in read_log_file():
            info.append(proposal)
    return info


def log_proposal_information(pi_proposals, email):
    for proposal in pi_proposals:
        log_to_file(email, proposal.code, datetime.datetime.strftime(proposal.release_date, "%d %b %Y"))
    return None


def handle_pi(pi_information):
    proposals = proposals_to_send(pi_information.proposals, pi_information.email)
    if len(proposals) > 0:
        sending_email("lonwabo@saao.ac.za", pi_information.fullname, html_table(proposals))
        log_proposal_information(pi_information.proposals, pi_information.email)
    return None


def run_code(days):
    for pi_information in pi_information_to_be_sent(days):
        handle_pi(pi_information)
    return None


@click.command()
@click.argument("days", nargs=1, type=int)
def main(days):
    run_code(days)


main()
