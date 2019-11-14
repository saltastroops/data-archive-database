import datetime
import pandas as pd
from dateutil.parser import parse
from typing import Optional, List
# import mysql.connector
from pymysql import connect

from ssda.util import types


class SaltDatabaseService:
    def __init__(self, database_config: types.DatabaseConfiguration):
        self._connection = connect(
            database=database_config.database(),
            host=database_config.host(),
            user=database_config.username(),
            passwd=database_config.password()
        )
        self._cursor = self._connection.cursor()

    def find_pi(self, block_visit_id: int) -> str:
        sql = """
SELECT FirstName, Surname FROM  BlockVisit
    JOIN `Block` USING(Block_Id)
    JOIN Proposal ON `Block`.Proposal_Id = Proposal.Proposal_Id
    JOIN ProposalCode ON Proposal.ProposalCode_Id = ProposalCode.ProposalCode_Id
    JOIN ProposalContact ON ProposalCode.ProposalCode_Id = ProposalContact.ProposalCode_Id
    JOIN Investigator ON ProposalContact.Leader_Id = Investigator.Investigator_Id
WHERE BlockVisit_Id = %s;
        """
        pi = pd.read_sql(sql, self._connection, params=(block_visit_id,)).iloc[0]
        print(pi['Surname'])
        if pi['Surname']:
            return f"{pi['Surname']} {pi['FirstName']}"
        raise ValueError("Observation have no Principal investigator")

    def find_proposal_code(self, block_visit_id: int) -> str:
        sql = """
SELECT Proposal_Code FROM  BlockVisit
    JOIN `Block` USING(Block_Id)
    JOIN Proposal ON `Block`.Proposal_Id = Proposal.Proposal_Id
    JOIN ProposalCode ON Proposal.ProposalCode_Id = ProposalCode.ProposalCode_Id
WHERE BlockVisit_Id = %s;
        """
        pc = pd.read_sql(sql, self._connection, params=(block_visit_id,)).iloc[0]
        if pc['Proposal_Code']:
            return f"{pc['Proposal_Code']}"
        raise ValueError("Observation have proposal/program code")

    def find_proposal_title(self, block_visit_id: int) -> str:
        sql = """
SELECT Title FROM  BlockVisit
	JOIN `Block` USING(Block_Id)
    JOIN Proposal ON `Block`.Proposal_Id = Proposal.Proposal_Id
    JOIN ProposalText ON Proposal.ProposalCode_Id = ProposalText.ProposalCode_Id
		AND Proposal.Semester_Id = ProposalText.Semester_Id
WHERE BlockVisit_Id = %s;
        """
        pt = pd.read_sql(sql, self._connection, params=(block_visit_id,)).iloc[0]
        if pt['Title']:
            return f"{pt['Title']}"
        raise ValueError("Observation have no title")

    def find_observation_status(self, block_visit_id: int) -> types.Status:
        sql = '''
SELECT BlockVisitStatus FROM BlockVisit JOIN BlockVisitStatus USING(BlockVisitStatus_Id) WHERE BlockVisit_Id =%s
        '''
        status = pd.read_sql(sql, self._connection, params=(block_visit_id,)).iloc[0]

        if status['BlockVisitStatus'].lower() == "accepted":
            return types.Status.ACCEPTED
        if status['BlockVisitStatus'].lower() == "rejected":
            return types.Status.REJECTED
        raise ValueError("Observation have unknown status.")

    def find_release_date(self, block_visit_id: int) -> datetime.datetime:
        sql = """
SELECT ReleaseDate FROM  BlockVisit
    JOIN `Block` USING(Block_Id)
    JOIN Proposal ON `Block`.Proposal_Id = Proposal.Proposal_Id
    JOIN ProposalGeneralInfo ON Proposal.ProposalCode_Id = ProposalGeneralInfo.ProposalCode_Id
WHERE BlockVisit_Id = %s;
        """
        release_date = pd.read_sql(sql, self._connection, params=(block_visit_id,)).iloc[0]
        if release_date['ReleaseDate']:
            return release_date['ReleaseDate']
        raise ValueError("Observation have no release date.")

    def find_meta_release_date(self, block_visit_id: int) -> datetime.datetime:
        return self.find_release_date(block_visit_id)

    def find_proposal_investigators(self, block_visit_id: int) -> List[str]:
        sql = """
SELECT FirstName, Surname FROM  BlockVisit
    JOIN `Block` USING(Block_Id)
    JOIN Proposal ON `Block`.Proposal_Id = Proposal.Proposal_Id
    JOIN ProposalInvestigator ON Proposal.ProposalCode_Id = ProposalInvestigator.ProposalCode_Id
    JOIN Investigator ON ProposalInvestigator.Investigator_Id = Investigator.Investigator_Id
WHERE BlockVisit_Id = %s;
        """
        pis = pd.read_sql(sql, self._connection, params=(block_visit_id,))
        if len(pis):
            ps = []
            for index, row in pis.iterrows():
                ps.append(f"{row['Surname']} {row['FirstName']}")
            return ps
        raise ValueError("Observation have no Investigators")

    def find_target_type(self, block_visit_id: int) -> Optional[str]:
        sql = """
SELECT TargetType.TargetType as TargetType FROM BlockVisit
    JOIN `Block` ON BlockVisit.Block_Id = `Block`.Block_Id
    JOIN Pointing ON `Block`.Block_Id = Pointing.Block_Id
    JOIN Observation ON Pointing.Pointing_Id = Observation.Pointing_Id
    JOIN Target ON Observation.Target_Id = Target.Target_Id
    JOIN TargetSubType ON Target.TargetSubType_Id = TargetSubType.TargetSubType_Id
    JOIN TargetType ON TargetType.TargetType_Id = TargetSubType.TargetType_Id
WHERE BlockVisit.BlockVisit_Id = %s
        """
        target_type = pd.read_sql(sql, self._connection, params=(block_visit_id,)).iloc[0]
        if target_type['TargetType']:
            return target_type['TargetType']
        return 'Unknown'


    def is_mos(self, slit_barcode: str) -> bool:

        sql = '''
SELECT RssMaskType FROM RssMask JOIN RssMaskType USING(RssMaskType_Id)  WHERE Barcode=%s
        '''
        mos = pd.read_sql(sql, self._connection, params=(slit_barcode,)).iloc[0]
        if mos['RssMaskType']:
            if mos['RssMaskType'] == 'MOS':
                return True
        return False

    def find_block_code(self, block_visit_id) -> Optional[str]:
        sql = """
SELECT BlockCode FROM  BlockCode
    JOIN `Block` USING(BlockCode_Id)
    JOIN BlockVisit ON `Block`.Block_Id = BlockVisit.Block_Id
WHERE BlockVisit_Id = %s;
        """
        block_code = pd.read_sql(sql, self._connection, params=(block_visit_id,)).iloc[0]
        if block_code['BlockCode']:
            return block_code['BlockCode']
        return None
