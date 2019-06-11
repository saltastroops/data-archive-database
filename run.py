"""
    this script should run a night update for all telescopes
"""
import pandas as pd
from datetime import date

from connection import ssda_connect, sdb_connect
from telescope import Telescope
from rss_fits_data import RssFitsData
from populate import populate

conn = ssda_connect()
cursor = conn.cursor()
get_sql = """SELECT * from TargetSubType;"""

insert_sql = "INSERT INTO TargetType (numericValue, explanation) VALUES "

get_results = pd.read_sql(get_sql, sdb_connect())
for i, row in get_results.iterrows():
    insert_sql += '("{numericValue}", "{explanation}"),\n' \
        .format(numericValue=row["NumericCode"], explanation=row["TargetSubType"])

cursor.execute(insert_sql[:-2] + ";")
conn.commit()

populate(date(2019, 4, 3), date(2019, 4, 4))

def update_scam(date):
    return date


def update_rss(date):
    return date


def update_hrs(date):
    return date


def update_bvit(date):
    return date


def update_salt(date):
    """
        This is the method that will update all the the instruments of salt but giving it only the date you want to
        update
        :param date :-
                A date to update
    """
    update_scam(date)
    update_bvit(date)
    update_hrs(date)
    update_rss(date)
