import os
import MySQLdb
import smtplib
import psycopg2
import psycopg2.extras
import datetime
import click
from prettytable import PrettyTable


def sdb_database_connection():
    database_host = os.environ.get("SDB_HOST")
    database_user = os.environ.get("SDB_DATABASE_USER")
    database_password = os.environ.get("SDB_DATABASE_PASSWORD")
    database_name = os.environ.get("SDB_DATABASE_NAME")

    sdb_connection = MySQLdb.connect(
        host=database_host,
        user=database_user,
        password=database_password,
        database=database_name,
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
        ssda_query_results = {proposal["proposal_code"]: proposal["data_release"] for proposal in results}
        return ssda_query_results


# We get all PIs and their proposals from sdb
def all_pi_and_proposals(proposals):
    sdb_query_results = {}
    with sdb_database_connection().cursor(
            MySQLdb.cursors.DictCursor
    ) as database_connection:
        pi_query = """SELECT Proposal_Code, Email, CONCAT(FirstName," ", Surname) AS fullname
                      FROM ProposalContact AS propCon
                      JOIN ProposalCode ON ProposalCode.ProposalCode_Id = propCon.ProposalCode_Id
                      JOIN Investigator ON Investigator.Investigator_Id = propCon.Leader_Id
                      WHERE Proposal_Code IN %(proposals)s"""
        database_connection.execute(pi_query, dict(proposals=proposals))
        results = database_connection.fetchall()
        for result in results:
            sdb_query_results[result["Proposal_Code"]] = {
                "email": result["Email"],
                "fullname": result["fullname"]
            }
        return sdb_query_results


# We create a dictionary of every PI with each of their proposals and release dates fro each proposal
def all_release_dates_and_proposals():
    ssda_query_results = proposal_release_dates()
    sdb_query_results = all_pi_and_proposals(list(ssda_query_results.keys()))

    all_data = {}
    for proposal_code in ssda_query_results:
        if proposal_code not in sdb_query_results:
            raise ValueError("... some appropriate error message...")
        email = sdb_query_results[proposal_code]['email']
        full_name = sdb_query_results[proposal_code]['fullname']
        release_date = ssda_query_results[proposal_code]

        if email not in all_data:
            all_data[email] = {
                "proposal": [],
                "fullname": full_name,
            }
        all_data[email]["proposal"].append({"proposal_code": proposal_code, "release_date": release_date})
    return all_data


# pprint.PrettyPrinter(indent=4).pprint(all_release_dates_and_proposals())


def text_formatting(proposal):
    if not proposal:
        return ""
    elif len(proposal) == 1:
        return proposal[0]
    else:
        return ", ".join(proposal[:-1]) + ", and " + proposal[-1]


def sending_email(receiver, information):
    message = """
Subject: Release of data
To: {receiver}
From: {sender}

{data_sent} 
"""

    sender = "salthelp@salt.ac.za"
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
                data_sent=information
            ),
        )
    return "Email has been sent"


def log_to_file(email_receiver, proposals, release_dates):
    with open("logging.txt", 'a') as log_file:
        file_information = [email_receiver + " " + proposals + " " + release_dates]
        log_file.writelines("%s\n" % line for line in file_information)


def read_log_file():
    with open("logging.txt", "r") as file_content:
        file_data = [data.replace("\n", "") for data in file_content.readlines()]
        return file_data


@click.command()
@click.option("--public-within", type=int, help="Number of days until release of proposal data")
def send_email(public_within):
    """
    We loop through the dictionary of all the PIs and their release dates of each
    proposal and then we send an email to the PI to tell them that their data will
    be public on the release date in the dictionary for their proposal
    :param public_within: The number of days until the proposal goes public
    :return:
    """
    for email, details in all_release_dates_and_proposals().items():
        x = [prop["proposal_code"] for prop in details["proposal"]]
        table = PrettyTable()
        table.field_names = ["Proposal", "Data becomes public"]
        if len(details["proposal"]) > 1:
            more_proposals = [proposal["proposal_code"] for proposal in details["proposal"]]
            more_release_date = [datetime.datetime.strftime(release_date["release_date"], "%Y-%m-%d")
                                 for release_date in details["proposal"]]
            for i in range(1, len(more_proposals)):
                table.add_row([more_proposals[i], more_release_date[i]])

        proposals = details["proposal"][0]["proposal_code"]
        release_date = details["proposal"][0]["release_date"]
        table.add_row([proposals, release_date])
        file_content = email + " " + proposals + " " + datetime.datetime.strftime(release_date, "%Y-%m-%d")
        if file_content not in read_log_file():
            pass
            # print(file_content)
            # sending_email(email, table)
            # log_to_file(email, proposals, datetime.datetime.strftime(release_date, "%Y-%m-%d"))
    return "Email Sent"


send_email()
