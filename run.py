"""
    this script should run a night update for all telescopes
"""

from datetime import date
from telescope import Telescope
from rss_fits_data import RssFitsData
from populate import populate

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
