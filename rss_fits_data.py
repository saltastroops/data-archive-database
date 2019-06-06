from datetime import date, timedelta
from dateutil import parser
import glob
import os
import pandas as pd
from typing import List

from connection import sdb_connect, ssda_connect
from instrument_fits_data import InstrumentFitsData
from observation_status import ObservationStatus
from telescope import Telescope


class RssFitsData(InstrumentFitsData):
    def __init__(self, fits_file: str):
        InstrumentFitsData.__init__(self, fits_file)

    @staticmethod
    def fits_files(night: date) -> List[str]:
        data_directory = '{base_dir}/{year}/{monthday}/rss/raw'.format(base_dir=os.environ['SALT_FITS_BASE_DIR'],
                                                                       year=night.strftime('%Y'), monthday=night.strftime('%m%d'))

        return sorted(glob.iglob(os.path.join(data_directory, '*.fits')))

    def night(self) -> date:
        return parser.parse(self.header.get('DATE-OBS')).date()

    def observation_status(self) -> ObservationStatus:
        block_visit_id = self.telescope_observation_id()
        if block_visit_id is None:
            return ObservationStatus.ACCEPTED

        sql = """
        SELECT BlockVisitStatus FROM BlockVisitStatus JOIN BlockVisit WHERE BlockVisit_Id=%s
        """
        df = pd.read_sql(sql, con=sdb_connect(), params=(block_visit_id,))

        return ObservationStatus(df['BlockVisitStatus'][0])

    def telescope(self) -> Telescope:
        return Telescope.SALT

    def telescope_observation_id(self) -> str:
        return self.header.get('BVISITID') or None


