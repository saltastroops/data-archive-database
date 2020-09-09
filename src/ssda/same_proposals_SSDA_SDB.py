import dsnparse
import pymysql
import psycopg2
from ssda.util.types import DatabaseConfiguration


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


def sdb_proposals():
    with sdb_database_connection().cursor() as cursor:
        mysql = """SELECT Proposal_Code from  ProposalCode"""
        cursor.execute(mysql)
        result = cursor.fetchall()
        return result


def ssda_proposals():
    with ssda_database_connection().cursor() as cursor:
        mysql = """SELECT proposal_code from observations.proposal"""
        cursor.execute(mysql)
        result = cursor.fetchall()
        return result


ssda = ssda_proposals()
sdb = sdb_proposals()
for proposal in ssda:
    if proposal not in sdb:
        print("These following proposals are in ssda but not in sdb", proposal)
