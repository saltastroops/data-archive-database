import os
import pymysql
import smtplib
import psycopg2
import psycopg2.extras
import datetime
import logging
import click

database_host = os.environ.get("sdb_host")
database_user = os.environ.get("sdb_database_user")
database_password = os.environ.get("sdb_database_password")
database_name = os.environ.get("sdb_database_name")

psql_database_host = os.environ.get("psql_host")
psql_database_user = os.environ.get("psql_user")
psql_database_password = os.environ.get("psql_password")
psql_database_name = os.environ.get("psql_database")

mail_port = os.environ.get("mail_port")
mail_server = os.environ.get("mail_server")
mail_username = os.environ.get("mail_user")
mail_password = os.environ.get("mail_password")

sdb_connection = pymysql.connect(
    host=database_host,
    user=database_user,
    password=database_password,
    database=database_name,
    cursorclass=pymysql.cursors.DictCursor,
)

ssda_connection = psycopg2.connect(
    host=psql_database_host,
    user=psql_database_user,
    password=psql_database_password,
    database=psql_database_name,
)

date_today = datetime.datetime.now().date()


# We get all PIs and their proposals
def all_pi():
    with sdb_connection.cursor() as database_connection:
        pi_query = """SELECT Proposal_Code, Email, CONCAT(FirstName," ", Surname) AS Name
                      FROM ProposalContact AS propCon
                      JOIN ProposalCode ON ProposalCode.ProposalCode_Id = propCon.ProposalCode_Id
                      JOIN ProposalInvestigator ON ProposalInvestigator.ProposalCode_Id=propCon.ProposalCode_Id
                      JOIN Investigator ON Investigator.Investigator_Id = ProposalInvestigator.Investigator_Id"""
        database_connection.execute(pi_query)
        results = database_connection.fetchall()
        return results


# We add the release dates to the all_pi function
def proposal_and_release_dates():
    with ssda_connection.cursor(
            cursor_factory=psycopg2.extras.DictCursor
    ) as ssda_cursor:
        psql_query = """SELECT
                        DISTINCT (proposal_code), data_release
                        FROM observations.proposal prop
                        JOIN observations.observation obs on prop.proposal_id=obs.proposal_id"""
        ssda_cursor.execute(psql_query)
        results = ssda_cursor.fetchall()
        return results


# We create a dictionary of the proposal and release date for each PI
all_data = {}
for pi in all_pi():
    all_data[pi["Name"]] = {
        "proposal code": pi["Proposal_Code"],
        "Email": pi["Email"]
    }

pi_information = {}
for data in proposal_and_release_dates():
    for key, value in all_data.items():
        if value["proposal code"] == data["proposal_code"]:
            pi_information[key] = {
                "proposal code": value["proposal code"],
                "Email": value["Email"],
                "data release": data["data_release"],
            }

message = """
Subject: Release of data
To: {receiver}
From: {sender}
The proposal with proposal code {proposal_code} is due to
be released soon with its release date being {release_date}.
Please let us know if you wish to extend the release date. """

sender = "Salt help<salthelp@saao.ac.za>"
logging.basicConfig(filename="email.log", level=logging.INFO, format="%(message)s")


# read the log file
def read_log_file():
    with open("email.log", "r") as email_log:
        array = []
        endl = os.linesep
        email_content = email_log.readlines()
        for line in email_content:
            array.append(line.strip(endl))
    return array


@click.command()
@click.option("--public-within", type=int, help="Number of days until release of proposal")
def send_email(public_within):
    for user, information in pi_information.items():
        if information['data release'] - public_within <= date_today:
            name_and_proposal = user + " " + information["proposal code"]
            if name_and_proposal not in read_log_file():
                with smtplib.SMTP(mail_server, mail_port) as server:
                    server.login(mail_username, mail_password)
                    server.sendmail(
                        sender,
                        information["Email"],
                        message.format(receiver=information["Email"],
                                       sender=sender,
                                       proposal_code=information["proposal code"],
                                       release_date=information["data release"],
                                       )
                    )
                logging.info(f"{user} {information['proposal code']}")
