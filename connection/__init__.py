from pymysql import connect
import os

db_config = {
    'user': os.environ["DB_USER"],
    'host': os.environ["DB_HOST"],
    'passwd': os.getenv("DB_PASSWORD"),
    'db': os.getenv("DB_DATABASE"),
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


def db_connect():
    return connect(**db_config)

