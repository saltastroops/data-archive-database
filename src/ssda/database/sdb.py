import datetime
import pandas as pd
from typing import Optional, List
from pymysql import connect
from ssda.exceptions import IgnoreObservationError
from ssda.util import types


class SaltDatabaseService:
    def __init__(self, database_config: types.DatabaseConfiguration):
        self._connection = connect(
            database=database_config.database(),
            host=database_config.host(),
            user=database_config.username(),
            passwd=database_config.password(),
        )
        self._cursor = self._connection.cursor()

    def find_pi(self, block_visit_id: int) -> str:
        sql = """
SELECT CONCAT(FirstName, " ", Surname) as FullName FROM  BlockVisit
    JOIN `Block` USING(Block_Id)
    JOIN Proposal ON `Block`.Proposal_Id=Proposal.Proposal_Id
    JOIN ProposalCode ON Proposal.ProposalCode_Id=ProposalCode.ProposalCode_Id
    JOIN ProposalContact ON ProposalCode.ProposalCode_Id=ProposalContact.ProposalCode_Id
    JOIN Investigator ON ProposalContact.Leader_Id=Investigator.Investigator_Id
WHERE BlockVisit_Id=%s;
        """
        results = pd.read_sql(sql, self._connection, params=(block_visit_id,)).iloc[0]
        if results["FullName"]:
            return results["FullName"]
        raise ValueError("Observation have no Principal Investigator")

    def find_proposal_code(self, block_visit_id: int) -> str:
        sql = """
SELECT Proposal_Code FROM  BlockVisit
    JOIN `Block` USING(Block_Id)
    JOIN Proposal ON `Block`.Proposal_Id=Proposal.Proposal_Id
    JOIN ProposalCode ON Proposal.ProposalCode_Id=ProposalCode.ProposalCode_Id
WHERE BlockVisit_Id=%s;
        """
        results = pd.read_sql(sql, self._connection, params=(block_visit_id,)).iloc[0]
        if results["Proposal_Code"]:
            return f"{results['Proposal_Code']}"
        raise ValueError("Observation has no proposal code")

    def find_proposal_title(self, block_visit_id: int) -> str:
        sql = """
SELECT Title FROM  BlockVisit
    JOIN `Block` USING(Block_Id)
    JOIN Proposal ON `Block`.Proposal_Id=Proposal.Proposal_Id
    JOIN ProposalText 
        ON Proposal.ProposalCode_Id=ProposalText.ProposalCode_Id 
            AND Proposal.Semester_Id=ProposalText.Semester_Id
WHERE BlockVisit_Id=%s;
        """
        results = pd.read_sql(sql, self._connection, params=(block_visit_id,)).iloc[0]
        if results["Title"]:
            return f"{results['Title']}"
        raise ValueError("Observation has no title")

    def find_observation_status(self, block_visit_id: int) -> types.Status:
        if block_visit_id is None:
            return types.Status.ACCEPTED

        sql = """
SELECT BlockVisitStatus FROM BlockVisit JOIN BlockVisitStatus USING(BlockVisitStatus_Id) WHERE BlockVisit_Id=%s
        """
        results = pd.read_sql(sql, self._connection, params=(block_visit_id,)).iloc[0]

        if results["BlockVisitStatus"].lower() == "accepted":
            return types.Status.ACCEPTED
        if results["BlockVisitStatus"].lower() == "rejected":
            return types.Status.REJECTED
        if (
            results["BlockVisitStatus"].lower() == "deleted"
            or results["BlockVisitStatus"].lower() == "in queue"
        ):
            raise IgnoreObservationError
        raise ValueError("Observation has an unknown status.")

    def find_release_date(self, block_visit_id: int) -> datetime.datetime:
        sql = """
SELECT ReleaseDate FROM  BlockVisit
    JOIN `Block` USING(Block_Id)
    JOIN Proposal ON `Block`.Proposal_Id=Proposal.Proposal_Id
    JOIN ProposalGeneralInfo ON Proposal.ProposalCode_Id=ProposalGeneralInfo.ProposalCode_Id
WHERE BlockVisit_Id=%s;
        """
        results = pd.read_sql(sql, self._connection, params=(block_visit_id,)).iloc[0]
        if results["ReleaseDate"]:
            return results["ReleaseDate"]
        raise ValueError("Observation has no release date.")

    def find_meta_release_date(self, block_visit_id: int) -> datetime.datetime:
        return self.find_release_date(block_visit_id)

    def find_proposal_investigators(self, block_visit_id: int) -> List[str]:
        sql = """
SELECT PiptUser.PiptUser_Id FROM  BlockVisit
    JOIN `Block` USING(Block_Id)
    JOIN Proposal ON `Block`.Proposal_Id=Proposal.Proposal_Id
    JOIN ProposalInvestigator ON Proposal.ProposalCode_Id=ProposalInvestigator.ProposalCode_Id
    JOIN Investigator ON ProposalInvestigator.Investigator_Id=Investigator.Investigator_Id
    JOIN PiptUser ON Investigator.PiptUser_Id=PiptUser.PiptUser_Id
WHERE BlockVisit_Id=%s;
        """
        results = pd.read_sql(sql, self._connection, params=(block_visit_id,))
        if len(results):
            ps = []
            for index, row in results.iterrows():
                ps.append(row["PiptUser_Id"])
            return ps
        raise ValueError("Observation has no Investigators")

    def find_target_type(self, block_visit_id: int) -> str:
        # If there is no block visit, return the Unknown target type
        if block_visit_id is None:
            return "00.00.00.00"

        sql = """
SELECT TargetSubType.NumericCode as NumericCode FROM BlockVisit
    JOIN `Block` ON BlockVisit.Block_Id=`Block`.Block_Id
    JOIN Pointing ON `Block`.Block_Id=Pointing.Block_Id
    JOIN Observation ON Pointing.Pointing_Id=Observation.Pointing_Id
    JOIN Target ON Observation.Target_Id=Target.Target_Id
    JOIN TargetSubType ON Target.TargetSubType_Id=TargetSubType.TargetSubType_Id
    JOIN TargetType ON TargetType.TargetType_Id=TargetSubType.TargetType_Id
WHERE BlockVisit.BlockVisit_Id=%s
        """
        results = pd.read_sql(sql, self._connection, params=(block_visit_id,)).iloc[0]
        if results["NumericCode"]:
            return results["NumericCode"]
        raise ValueError(
            f"No numeric code defined for the target type of block visit {block_visit_id}"
        )

    def is_mos(self, slit_barcode: str) -> bool:

        sql = """
SELECT RssMaskType FROM RssMask JOIN RssMaskType USING(RssMaskType_Id)  WHERE Barcode=%s
        """
        results = pd.read_sql(sql, self._connection, params=(slit_barcode,))
        if len(results) <= 0:
            return False

        return results.iloc[0]["RssMaskType"] == "MOS"

    def find_block_code(self, block_visit_id) -> Optional[str]:
        sql = """ 
SELECT BlockCode FROM  BlockCode
    JOIN `Block` USING(BlockCode_Id)
    JOIN BlockVisit ON `Block`.Block_Id=BlockVisit.Block_Id
WHERE BlockVisit_Id=%s;
        """
        block_code = pd.read_sql(sql, self._connection, params=(block_visit_id,)).iloc[
            0
        ]
        if block_code["BlockCode"]:
            return block_code["BlockCode"]
        return None
