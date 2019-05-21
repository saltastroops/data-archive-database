from pymysql import connect
import os

db_config = {
    'user': os.environ["SSDA_USER"],
    'host': os.environ["SSDA_HOST"],
    'passwd': os.getenv("SSDA_PASSWORD"),
    'db': os.getenv("SSDA_DATABASE"),
    'charset': 'utf8'
}

sdb_config = {
        'user': os.environ["SDB_USER"],
        'host': os.environ["SDB_HOST"],
        'passwd': os.getenv("SDB_PASSWORD"),
        'db': os.getenv("SDB_DATABASE"),
        'charset': 'utf8'
    }


def sdb_connect():
    return connect(**sdb_config)


def ssda_connect():
    return connect(**db_config)

