from pymysql import connect, Connection, cursors
import os

ssda_config = {
    "user": os.environ["SSDA_USER"],
    "host": os.environ["SSDA_HOST"],
    "password": os.getenv("SSDA_PASSWORD"),
    "db": os.getenv("SSDA_DATABASE"),
    "charset": "utf8",
    "cursorclass": cursors.DictCursor,
}

sdb_config = {
    "user": os.environ["SDB_USER"],
    "host": os.environ["SDB_HOST"],
    "password": os.getenv("SDB_PASSWORD"),
    "db": os.getenv("SDB_DATABASE"),
    "charset": "utf8",
    "cursorclass": cursors.DictCursor,
}


def sdb_connect() -> Connection:
    return connect(**sdb_config)


def ssda_connect() -> Connection:
    return connect(**ssda_config)
