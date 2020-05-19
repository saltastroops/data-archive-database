from datetime import date
from typing import List
from dataclasses import dataclass
import os
import pymysql
import psycopg2
from psycopg2 import extras
from prettytable import PrettyTable
import smtplib
import datetime


@dataclass
class Proposal:
    code: str
    release_date: date


@dataclass
class PI:
    name: str
    email: str
    proposals: List[Proposal]


PIs = []


def sdb_database_connection():
    database_host = os.environ.get("SDB_HOST")
    database_user = os.environ.get("SDB_DATABASE_USER")
    database_password = os.environ.get("SDB_DATABASE_PASSWORD")
    database_name = os.environ.get("SDB_DATABASE_NAME")

    sdb_connection = pymysql.connect(
        host=database_host,
        user=database_user,
        passwd=database_password,
        database=database_name,
        cursorclass=pymysql.cursors.DictCursor
    )
    return sdb_connection


def ssda_database_connection():
    psql_database_host = os.environ.get("PSQL_HOST")
    psql_database_user = os.environ.get("PSQL_USER")
    psql_database_password = os.environ.get("PSQL_PASSWORD")
    psql_database_name = os.environ.get("PSQL_DATABASE")

    ssda_connection = psycopg2.connect(
        host=psql_database_host,
        user=psql_database_user,
        password=psql_database_password,
        database=psql_database_name,
    )
    return ssda_connection


# getting the release dates for the proposals in ssda
def proposal_release_dates():
    with ssda_database_connection().cursor(
            cursor_factory=psycopg2.extras.DictCursor
    ) as ssda_cursor:
        psql_query = """SELECT DISTINCT proposal_code, data_release
                        FROM observations.proposal proposal
                        JOIN observations.observation obs on proposal.proposal_id=obs.proposal_id
                        JOIN observations.telescope telescope on obs.telescope_id=telescope.telescope_id
                        WHERE name=%(telescope_name)s and data_release - CURRENT_DATE BETWEEN 1 and %(days)s"""
        ssda_cursor.execute(psql_query, dict(telescope_name='SALT', days=189))
        results = ssda_cursor.fetchall()
        ssda_query_results = {pi_proposal["proposal_code"]: pi_proposal["data_release"] for pi_proposal in results}
        return ssda_query_results


# We get all PIs and their proposals from sdb
def all_pi_and_proposals(pi_proposals):
    sdb_query_results = {}
    with sdb_database_connection().cursor(
    ) as database_connection:
        pi_query = """SELECT Proposal_Code, Email, CONCAT(FirstName," ", Surname) AS fullname
                      FROM ProposalContact AS propCon
                      JOIN ProposalCode ON ProposalCode.ProposalCode_Id = propCon.ProposalCode_Id
                      JOIN Investigator ON Investigator.Investigator_Id = propCon.Leader_Id
                      WHERE Proposal_Code IN %(proposals)s"""
        database_connection.execute(pi_query, dict(proposals=pi_proposals))
        results = database_connection.fetchall()
        for result in results:
            sdb_query_results[result["Proposal_Code"]] = {
                "email": result["Email"],
                "fullname": result["fullname"]
            }
        return sdb_query_results


def all_release_dates_and_proposals():
    ssda_query_results = proposal_release_dates()
    sdb_query_results = all_pi_and_proposals(list(ssda_query_results.keys()))

    all_data = {}
    for proposal_code in ssda_query_results:
        if proposal_code not in sdb_query_results:
            raise ValueError("Invalid Proposal code.")
        pi_email = sdb_query_results[proposal_code]['email']
        full_name = sdb_query_results[proposal_code]['fullname']
        proposal_release_date = ssda_query_results[proposal_code]

        if pi_email not in all_data:
            all_data[pi_email] = {
                "proposal": [],
                "fullname": full_name,
            }
        all_data[pi_email]["proposal"].append({"proposal_code": proposal_code, "release_date": proposal_release_date})
    return all_data


for key, pi in all_release_dates_and_proposals().items():  # all_pi_proposal.items is the dict with email as keys
    proposals = []
    for proposal in pi["proposal"]:
        proposals.append(
            Proposal(
                code=proposal["proposal_code"],
                release_date=proposal["release_date"]
            )
        )
    PIs.append(PI(
        name=pi["fullname"],
        email=key,
        proposals=proposals
    ))


def sending_email(receiver, pi_name, table):
    sender = "salthelp@salt.ac.za"

    message = f"""\
        
Subject: Release of data
To: {receiver}
From: {sender}

Hi {pi_name}

Please note that the below proposal will be public soon.

{table}

Your friendly SALT assistance. """

    mail_port = os.environ.get("MAIL_PORT")
    mail_server = os.environ.get("MAIL_SERVER")
    mail_username = os.environ.get("MAIL_USER")
    mail_password = os.environ.get("MAIL_PASSWORD")

    with smtplib.SMTP(mail_server, mail_port) as server:
        server.login(mail_username, mail_password)
        server.sendmail(
            sender,
            receiver,
            message.format(
                receiver=receiver,
                sender=sender,
                pi=pi_name,
                table=table
            )
        )
        return "Email has been sent"


def log_to_file(email_receiver, pi_proposal, release_dates):
    with open("logging.txt", 'a') as log_file:
        file_information = [email_receiver + " " + pi_proposal + " " + release_dates]
        log_file.writelines("%s\n" % line for line in file_information)


def read_log_file():
    with open("logging.txt", "r") as file_content:
        file_data = [data.replace("\n", "") for data in file_content.readlines()]
        return file_data


def send_message(pi, proposals):
    # before send check if proposals are not yet included in a log if there is one send email with just that one
    # if not do not send email.
    table = PrettyTable()
    table.field_names = ["Proposal", "Data to be released"]
    proposal_to_send = []
    proposals_in_log = read_log_file()
    for proposal in proposals:
        file_content = pi.email + " " + proposal.code+" "+datetime.datetime.strftime(proposal.release_date, "%Y-%m-%d")
        if file_content not in proposals_in_log:
            proposal_to_send.append(proposal)
        table.add_row([proposal.code, proposal.release_date])
    if len(proposal_to_send) > 0:
        sending_email(pi.email, pi.name, table)
        for prop in proposal_to_send:
            log_to_file(pi.email, prop.code, datetime.datetime.strftime(prop.release_date, "%Y-%m-%d"))
    return "Email has been sent to".format(pi.name)


def run_code():
    for pi in PIs:  # PIs is the list of all PIs like you have above
        public_soon = []
        for proposal in pi.proposals:
            public_soon.append(proposal)
        if len(public_soon) > 0:
            send_message(pi, public_soon)
    return ""


run_code()
