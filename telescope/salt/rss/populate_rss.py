from glob import iglob
import os

from astropy.io import fits
from dateutil import parser

from util.get_information import *
from util.map_csv import create_column_value_pair_from_headers, create_insert_sql
from util.util import handle_missing_header, dms_degree, hms_degree


def populate_rss(date):
    # setting up a directory for rss from given date
    date = parser.parse(date)
    conn = ssda_connect()
    cursor = conn.cursor()
    data_directory = '/salt/data/{year}/{month_day}/rss/raw'.format(year=date.strftime('%Y'), month_day=date.strftime('%m%d'))

    for filename in iglob(data_directory + "**/**/raw/*.fits", recursive=True):

        # Opening current fits file
        with fits.open(filename) as header_data_unit_list:
            headers = header_data_unit_list[0].header
            # Obtain the file sie
            file_size = os.path.getsize(filename)

            if handle_missing_header(headers, 'INSTRUME') == 'RSS':

                # Observation-------------------------------------------------------------------Start
                observation_id = handle_missing_header(headers, 'BVISITID')
                telescope_observation_id = get_telescope_observation_id(observation_id)
                observation_date = handle_missing_header(headers, "DATE-OBS")

                create_observation(
                    telescope="SALT",
                    telescope_observation_id=telescope_observation_id,
                    observation_status_id=789665
                )
                # Observation -------------------------------------------------------------------End

                # Target ------------------------------------------------------------------------Start
                create_target(
                    target_name=handle_missing_header(headers, 'OBJECT'),
                    right_ascension=hms_degree(handle_missing_header(headers, 'RA')),
                    declination=dms_degree(handle_missing_header(headers, 'DEC')),
                    block_id=handle_missing_header(headers, 'BLOCKID'))
                # Target ------------------------------------------------------------------------End

                # Data File ---------------------------------------------------------------------Start

                get_ssda_observation_id(2, None)
                create_data_file(
                    data_category_id=1,
                    observation_date=parser.parse(observation_date),
                    filename=filename,
                    target_id=2,
                    observation_id=4,
                    file_size=file_size
                )
                data_file_id = get_data_file_id(filename=filename)
                # Data File ---------------------------------------------------------------------End

                # Data File Preview -------------------------------------------------------------Start

                create_data_preview(
                    name=filename,
                    datafile_id=data_file_id,
                    order="DESC"
                )
                # Data File Preview -------------------------------------------------------------End

                # Main Rss input ----------------------------------------------------------------Start
                rss_data = create_column_value_pair_from_headers(headers, data_file_id=data_file_id)

                # Main Rss input ----------------------------------------------------------------End
                cursor.execute(create_insert_sql(rss_data))
                conn.commit()


populate_rss("2019-05-10")

# populate_target_type()
