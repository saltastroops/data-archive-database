import glob
import os

from astropy.io import fits
from dateutil import parser

from connection import ssda_connect
from util.get_information import *
from util.map_csv import create_column_value_pair_from_headers, create_insert_sql
from util.util import handle_missing_header, dms_degree, hms_degree


def populate_rss(date):
    # setting up a directory for rss from given date
    date = parser.parse(date)
    conn = ssda_connect()
    cursor = conn.cursor()
    # data_directory = '/salt/data/{year}/{monthday}/rss/raw'.format(year=date.strftime('%Y'), monthday=date.strftime('%m%d'))
    # print("DIR: ", data_directory)
    data_directory = '/home/nhlavu/nhlavu/da/database/data-archive-database/data/test_rss/one_file/'
    for filename in glob.iglob(data_directory + '**/*.fits', recursive=True):

        # Opening current fits file
        with fits.open(filename) as header_data_unit_list:
            headers = header_data_unit_list[0].header
            # Obtain the file sie
            file_size = os.path.getsize(filename)

            if handle_missing_header(headers, 'INSTRUME') == 'RSS':
                dms_degree(handle_missing_header(headers, 'DEC'))
                hms_degree(handle_missing_header(headers, 'RA'))

                # Observation-------------------------------------------------------------------Start
                observation_id = handle_missing_header(headers, 'BLOCKID') # TODO: BlockId is not in RSS
                telescope_id = get_telescope_id("SALT")
                telescope_observation_id = get_telescope_observation_id(observation_id)
                observation_date = handle_missing_header(headers, "DATE-OBS")
                observation_status_id = get_observation_status_id(observation_id)

                observation_sql = """
                                    INSERT INTO Observation(
                                        telescopeId,
                                        telescopeObservationId,
                                        startTime,
                                        observationStatusId
                                    )
                                    VALUES (%s,%s,%s,%s)
                                """
                observation_params = (telescope_id, telescope_observation_id, observation_date, observation_status_id)
                cursor.execute(observation_sql, observation_params)
                conn.commit()

                # Observation -------------------------------------------------------------------End

                # Target ------------------------------------------------------------------------Start
                target_sql = """
                                    INSERT INTO Target(
                                        name,
                                        rightAscension,
                                        declination,
                                        position,
                                        targetTypeId
                                    )
                                    VALUES (%s,%s,%s,%s,%s)
                                """

                target_params = (
                    handle_missing_header(headers, 'OBJECT'),
                    hms_degree((handle_missing_header(headers, 'RA'))),
                    dms_degree((handle_missing_header(headers, 'DEC'))),
                    None,
                    1  # TODO TargetType still need to be defined
                )
                cursor.execute(target_sql, target_params)
                # Target ------------------------------------------------------------------------End

                # Data File ---------------------------------------------------------------------Start
                data_category_id = get_data_category_id(handle_missing_header(headers, 'OBJECT'))
                data_files_sql = """
                                    INSERT INTO DataFile(
                                        dataCategoryId,
                                        startTime,
                                        name,
                                        targetId,
                                        size,
                                        observationId
                                    )
                                    VALUES (%s,%s,%s,%s,%s,%s)
                                """

                data_files_params = (
                    data_category_id,
                    observation_date,
                    filename,
                    get_last_target_id(),
                    file_size,
                    get_last_observation_id()
                )
                cursor.execute(data_files_sql, data_files_params)
                # Data File ---------------------------------------------------------------------End

                # Data File Preview -------------------------------------------------------------Start
                data_preview_sql = """
                                    INSERT INTO DataPreview(
                                        name,
                                        dataFileId,
                                        orders
                                    )
                                    VALUES (%s,%s,%s)
                                """
                data_preview_params = (
                    filename,
                    get_last_data_file_id(),
                    "DESC"
                )
                cursor.execute(data_preview_sql, data_preview_params)
                # Data File Preview -------------------------------------------------------------End
                # Main Rss input ----------------------------------------------------------------Start

                rss_data = create_column_value_pair_from_headers(headers)
                create_insert_sql(rss_data)
                # Main Rss input ----------------------------------------------------------------End
                conn.commit()
                return


populate_rss("2019-05-10")
