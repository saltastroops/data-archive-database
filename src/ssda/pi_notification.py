import os
import MySQLdb
import smtplib
import psycopg2
import psycopg2.extras
import datetime
import click

mail_port = os.environ.get("MAIL_PORT")
mail_server = os.environ.get("MAIL_SERVER")
mail_username = os.environ.get("MAIL_USER")
mail_password = os.environ.get("MAIL_PASSWORD")


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


date_today = datetime.datetime.now().date()


# We get all PIs and their proposals from sdb
def all_pi_and_proposals_sdb():
    with sdb_database_connection().cursor(
        MySQLdb.cursors.DictCursor
    ) as database_connection:
        pi_query = """SELECT Proposal_Code, Email, CONCAT(FirstName," ", Surname) AS FullName
                      FROM ProposalContact AS propCon
                      JOIN ProposalCode ON ProposalCode.ProposalCode_Id = propCon.ProposalCode_Id
                      JOIN Investigator ON Investigator.Investigator_Id = propCon.Leader_Id"""
        database_connection.execute(pi_query)
        results = database_connection.fetchall()
        return results


# getting the release dates for the proposals in ssda
def proposal_release_dates():
    with ssda_database_connection().cursor(
        cursor_factory=psycopg2.extras.DictCursor
    ) as ssda_cursor:
        psql_query = """SELECT DISTINCT (proposal_code), data_release
                        FROM observations.proposal prop
                        JOIN observations.observation obs on prop.proposal_id=obs.proposal_id
                        WHERE telescope_id=%(telescope_id)s"""
        ssda_cursor.execute(psql_query, dict(telescope_id=3))
        results = ssda_cursor.fetchall()
        return results


# We create a dictionary of every PI with each of their proposals and release dates fro each proposal
def all_release_dates_and_proposals():
    ssda_query_results = proposal_release_dates()
    sdb_query_results = all_pi_and_proposals_sdb()
    all_data = dict()
    for pi in sdb_query_results:
        for data in ssda_query_results:
            if pi["Proposal_Code"] == data["proposal_code"]:
                if pi["Email"] not in all_data:
                    all_data[pi["Email"]] = {
                        "proposals": {},
                        "FullName": pi["FullName"],
                    }
                all_data[pi["Email"]]["proposals"].update(
                    {pi["Proposal_Code"]: data["data_release"]}
                )
    return all_data


def text_formatting(proposal):
    if not proposal:
        return ""
    elif len(proposal) == 1:
        return proposal[0]
    else:
        return ", ".join(proposal[:-1]) + ", and " + proposal[-1]


message = """
Subject: Release of data
To: {receiver}
From: {sender}
The release date for {proposal_code} is {release_date}.
Please let us know if you wish to extend the release date. """

sender = "Salt help<salthelp@saao.ac.za>"


def email_to_be_sent(receiver, proposal, release_date):
    with smtplib.SMTP(mail_server, mail_port) as server:
        server.login(mail_username, mail_password)
        server.sendmail(
            sender,
            receiver,
            message.format(
                receiver=receiver,
                sender=sender,
                proposal_code=proposal,
                release_date=release_date,
            ),
        )


@click.command()
@click.option(
    "--public-within", type=int, help="Number of days until release of proposal"
)
def send_email(public_within):
    """
    We loop through the dictionary of all the PIs and their release dates of each
    proposal and then we send an email to the PI to tell them that their data will
    be public on the release date in the dictionary for their proposal
    :param public_within: The number of days until the proposal goes public
    :return:
    """
    proposals_to_include = {}
    for key, value in all_release_dates_and_proposals().items():
        for proposal, release_date in value["proposals"].items():
            time_difference = release_date - date_today
            if (
                datetime.timedelta(0)
                <= time_difference
                <= datetime.timedelta(public_within)
            ):
                if key not in proposals_to_include:
                    proposals_to_include[key] = {proposal: release_date}
                else:
                    proposals_to_include[key].update({proposal: release_date})

    for email, all_info in proposals_to_include.items():
        all_dates = text_formatting(
            [datetime.datetime.strftime(d, "%Y-%m-%d") for d in list(all_info.values())]
        )
        email_to_be_sent(email, text_formatting(list(all_info.keys())), all_dates)
