from datetime import date, datetime

from astropy.coordinates import Angle
from dateutil import parser
import glob
import os
import pandas as pd
from typing import List, Optional

from connection import sdb_connect, ssda_connect
from instrument_fits_data import InstrumentFitsData, PrincipalInvestigator, Target, \
    DataCategory
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

    def data_category(self) -> DataCategory:
        # TODO: What about standards?
        object_name = self.header.get('OBJECT').upper()
        if object_name == 'ARC':
            return DataCategory.ARC
        elif object_name == 'BIAS':
            return DataCategory.BIAS
        elif object_name == 'FLAT':
            return DataCategory.FLAT
        else:
            return DataCategory.SCIENCE

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

    def principal_investigator(self) -> Optional[PrincipalInvestigator]:
        proposal_code = self.proposal_code()
        if not proposal_code:
            return None

        sql = """
        SELECT FirstName, Surname
               FROM Investigator
               JOIN ProposalInvestigator ON Investigator.Investigator_Id=ProposalInvestigator.Investigator_Id
               JOIN ProposalContact ON ProposalInvestigator.Investigator_Id=ProposalContact.Leader_Id
               JOIN ProposalCode ON ProposalContact.ProposalCode_Id=ProposalCode.ProposalCode_Id
        WHERE Proposal_Code=%s
        """
        df = pd.read_sql(sql, con=sdb_connect(), params=(proposal_code,))
        if len(df) == 0:
            raise ValueError('No Principal Investigator was found for the proposal {}'
                             .format(proposal_code))

        return PrincipalInvestigator(family_name=df['Surname'][0],
                                     given_name=df['FirstName'][0])

    def proposal_code(self) -> Optional[str]:
        code = self.header.get('PROPID') or None
        if not code:
            return None

        # Is this a valid proposal code (rather than a fake one such as 'CAL_BIAS')?
        if code[:2] == '20':
            return code
        else:
            return None

    def proposal_title(self) -> Optional[str]:
        proposal_code = self.proposal_code()
        if not proposal_code:
            return None

        sql = """
        SELECT Title
               FROM ProposalText
               JOIN ProposalCode USING (ProposalCode_Id)
        WHERE Proposal_Code=%s
        """
        df = pd.read_sql(sql, con=sdb_connect(), params=(proposal_code,))

        return df['Title'][0]

    def start_time(self) -> datetime:
        return parser.parse(self.header['DATE-OBS'] + ' ' + self.header['TIME-OBS'])

    def target(self) -> Optional[Target]:
        # Get the target position
        ra_header_value = self.header.get('RA')
        dec_header_value = self.header.get('DEC')
        if ra_header_value and not dec_header_value:
            raise ValueError('There is a right ascension header value, but no declination header value.')
        if not ra_header_value and dec_header_value:
            raise ValueError('There is a declination header value, but no right ascension header value.')
        if not ra_header_value and not dec_header_value:
            return None
        ra = Angle('{} hours'.format(ra_header_value)).degree
        dec = Angle('{} degrees'.format(dec_header_value)).degree

        # Get the target name
        name = self.header.get('OBJECT', '')

        # Calibrations don't have a target
        if name.upper() in ['ARC', 'BIAS', 'FLAT']:
            return None

        # Get the target type
        _target_type = target_type(self.header.get('BVISITID'))

        return Target(name=name, ra=ra, dec=dec, target_type=_target_type)

    def telescope(self) -> Telescope:
        return Telescope.SALT

    def telescope_observation_id(self) -> str:
        return self.header.get('BVISITID') or None


def target_type(block_visit_id: Optional[str]) -> Optional[str]:
    # No target type can be determined if there is no observation linked to the target
    if block_visit_id is None:
        return None

    # Get the target type from the SDB
    sdb_target_type_query = """
    SELECT NumericCode
           FROM Pointing
           JOIN Observation USING(Pointing_Id)
           JOIN Target USING(Target_Id)
           JOIN TargetSubType USING(TargetSubType_Id)
    WHERE Block_Id = %s
    """
    numeric_code_df = pd.read_sql(sql=sdb_target_type_query, con=sdb_connect(), params=(block_visit_id,))
    if numeric_code_df.empty:
        return None

    return numeric_code_df['NumericCode'][0]

