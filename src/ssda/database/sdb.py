import datetime
from dateutil.parser import parse
from typing import Optional, List
from mysql.connector import connect

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
        pi = self._cursor.execute(sql, params=(block_visit_id,)).fetchone()
        if len(pi):
            return f"{pi[1]} {pi[0]}"
        raise ValueError("Observation have no Principal investigator")

    def find_proposal_code(self, block_visit_id: int) -> str:
        sql = """
SELECT Proposal_Code FROM  BlockVisit
	JOIN `Block` USING(Block_Id)
    JOIN Proposal ON `Block`.Proposal_Id = Proposal.Proposal_Id
    JOIN ProposalCode ON Proposal.ProposalCode_Id = ProposalCode.ProposalCode_Id
WHERE BlockVisit_Id = %s;
        """
        pc = self._cursor.execute(sql, params=(block_visit_id,)).fetchone()
        if len(pc):
            return f"{pc[0]}"
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
        pt = self._cursor.execute(sql, params=(block_visit_id,)).fetchone()
        if len(pt):
            return f"{pt[0]}"
        raise ValueError("Observation have no title")

    def find_observation_status(self, block_visit_id: int) -> types.Status:
        sql = '''
SELECT BlockVisitStatus FROM BlockVisit JOIN BlockVisitStatus USING(BlockVisitStatus_Id) WHERE BlockVisit_Id =%s
        '''
        status = self._cursor.execute(sql, params=(block_visit_id,)).fetchone()

        if status[0].lower() == "accepted":
            return types.Status.ACCEPTED
        if status[0].lower() == "rejected":
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
        release_date = self._cursor.execute(sql, params=(block_visit_id,)).fetchone()
        if len(release_date):
            return parse(release_date[0])
        raise ValueError("Observation have no release date.")

    def find_meta_release_date(self, block_visit_id: int) -> datetime.datetime:
        return self.find_release_date(block_visit_id)

    def find_proposal_investigators(self, block_visit_id: int) -> List[str]:
        sql = """
SELECT FirstName, Surname FROM  BlockVisit
	JOIN `Block` USING(Block_Id)
    JOIN Proposal ON `Block`.Proposal_Id = Proposal.Proposal_Id
    JOIN ProposalInvestigator ON Proposal.ProposalCode_Id = ProposalInvestigator.ProposalCode_Id
    JOIN Investigator ON ProposalInvestigator.Investigator_Id = Investigator.Investigator_I
WHERE BlockVisit_Id = %s;
        """
        pis = self._cursor.execute(sql, params=(block_visit_id,)).fetchall()
        if len(pis):
            ps = []
            for pi in pis:
                ps.append(f"{pis[1]} {pi[0]}")
            return ps
        raise ValueError("Observation have no Investigators")

    def is_mos(self, slit_barcode: str) -> bool:

        sql = '''
SELECT RssMaskType FROM RssMask JOIN RssMaskType USING(RssMaskType_Id)  WHERE Barcode=%s
        '''
        mos = self._cursor.execute(sql, params=(slit_barcode,)).fetchone()
        if len(mos):
            if mos[0] == 'MOS':
                return True
        return False
