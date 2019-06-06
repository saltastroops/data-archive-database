from datetime import date, timedelta
import pandas as pd

from connection import ssda_connect
from instrument_fits_data import InstrumentFitsData
from rss_fits_data import RssFitsData
from telescope import Telescope


def populate(start_date: date, end_date: date) -> None:
    # get FITS files
    # loop over all dates
    if start_date >= end_date:
        raise ValueError('The start date must be earlier than the end date.')
    dt = timedelta(days=1)
    night = start_date
    files = []
    while night <= end_date:
        files += sorted(RssFitsData.fits_files(night))
        night += dt

    for f in files:
        print('FILE: ' + f)
        populate_with_data(RssFitsData(f))


def populate_with_data(fits_data: InstrumentFitsData) -> None:
    print(fits_data.header.get('OBSTYPE'), fits_data.header.get('OBJECT'), fits_data.header.get('BVISITID'))
    print(insert_observation(fits_data))


def insert_observation(fits_data: InstrumentFitsData) -> int:
    # Collect the query parameters
    telescope_id = fits_data.telescope().id()
    telescope_observation_id = fits_data.telescope_observation_id()
    night = fits_data.night()
    observation_status_id = fits_data.observation_status().id()

    # Maybe the observation exists already?
    if telescope_id and telescope_observation_id:
        select_sql = """
        SELECT observationId FROM Observation
               WHERE telescopeId=%(telescope_id)s
                     AND telescopeObservationId=%(telescope_observation_id)s
        """
        select_params = dict(telescope_id=telescope_id,
                             telescope_observation_id=telescope_observation_id)
        select_df = pd.read_sql(select_sql, con=ssda_connect(), params=select_params)
        if len(select_df) > 0:
            return int(select_df['observationId'][0])

    # Create and execute the query
    conn = ssda_connect()
    cursor = conn.cursor()
    insert_sql = """
    INSERT INTO Observation(
                            telescopeId,
                            telescopeObservationId,
                            night,
                            observationStatusId
                           )
                VALUES (%(telescope_id)s,
                        %(telescope_observation_id)s,
                        %(night)s,
                        %(observation_status_id)s)
    """
    insert_params = dict(telescope_id=telescope_id,
                         telescope_observation_id=telescope_observation_id,
                         night=night,
                         observation_status_id=observation_status_id)
    cursor.execute(insert_sql, insert_params)
    conn.commit()

    # Get the observation id
    id_sql = """SELECT LAST_INSERT_ID() AS lastId"""
    id_df = pd.read_sql(id_sql, con=conn)
    if len(id_df) == 0 or not id_df['lastId'][0]:
        raise ValueError('The id of the newly added Observation entry could not be retrieved')

    return int(id_df['lastId'])
