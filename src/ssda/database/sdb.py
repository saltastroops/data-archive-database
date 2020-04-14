import datetime
import uuid
from dataclasses import dataclass

import pandas as pd
import pytz
from typing import Dict, List, Optional, Tuple, Union
from pymysql import connect

from ssda.util import types


@dataclass
class FileDataItem:
    UTStart: datetime
    FileName: str
    BlockVisit_Id: int
    Target_Name: str
    Proposal_Code: str


class SaltDatabaseService:
    def __init__(self, database_config: types.DatabaseConfiguration):
        self._connection = connect(
            database=database_config.database(),
            host=database_config.host(),
            user=database_config.username(),
            passwd=database_config.password(),
        )
        self._cursor = self._connection.cursor()

    @staticmethod
    def is_real_proposal_code(proposal_code: str) -> bool:
        return proposal_code.startswith('20')

    def find_block_visit_ids(self, night: datetime.date) -> Dict[str, Optional[Union[int, str]]]:
        """
        Find the block visit ids fromm the SDB.

        The id is, in principle, found in the following way.

        * If the FileData table contains a block visit id, that id is used.
        * If it has no block visit id, the proposal code and target name are used to
          query for the block visit id.

        A night may have several block visits for a proposal code and target name. In
        this case the first block visit id is used until either a new proposal code
        - target pair or an existing block visit are encountered. In case of the former
        the next block visit id, in case of the latter the existing block visit is used
        henceforth.

        Due to issues with the SDB and FITS files, sometimes this function cannot find a
        block visit id. In this case a random UUID value is assigned instead.

        Parameters
        ----------
        night : date
            The night for which the block visit ids are obtained.

        Returns
        -------
        dict
            A dictionary of the file names and block visit ids.

        """

        # Extract data from the FileData table.
        night_date = datetime.datetime(night.year, night.month, night.day)
        start_time = datetime.datetime(night.year, night.month, night.day, 12, 0, 0, 0, tzinfo=pytz.utc)
        end_time = start_time + datetime.timedelta(hours=24)
        file_data_sql = """
SELECT FileData.UTStart, FileData.FileName, ProposalCode.Proposal_Code, FileData.Target_Name, FileData.BlockVisit_Id
FROM FileData
JOIN ProposalCode ON FileData.ProposalCode_Id = ProposalCode.ProposalCode_Id
WHERE UTStart BETWEEN %s AND %s
ORDER BY UTStart
        """
        file_data_results = pd.read_sql(file_data_sql, self._connection, params=(start_time, end_time))
        file_data = [
            FileDataItem(
                UTStart=row.UTStart.to_pydatetime(),
                FileName=row.FileName,
                Proposal_Code=row.Proposal_Code,
                Target_Name=row.Target_Name.strip(),
                BlockVisit_Id=int(row.BlockVisit_Id) if not pd.isna(row.BlockVisit_Id) else None,
            )
            for row in file_data_results.itertuples()
        ]

        # Correct for multiple target names in the same block visit.
        if night == datetime.date(2016, 10, 20):
            for fd in file_data:
                if fd.Proposal_Code == "2016-1-SCI-049" and fd.Target_Name.startswith("N132D-pos"):
                    fd.Target_Name = "N132D-pos1"

        # Fix incorrect block visit id.
        if night == datetime.date(2015, 2, 25):
            for fd in file_data:
                if fd.BlockVisit_Id == 8082:
                    fd.BlockVisit_Id = 8092

        # Ignore block visit ids of other dates
        if night == datetime.date(2016, 2, 22):
            for fd in file_data:
                if fd.BlockVisit_Id == 10906:
                    fd.BlockVisit_Id = None
        if night == datetime.date(2018, 4, 16):
            for fd in file_data:
                if fd.BlockVisit_Id == 18937:
                    fd.BlockVisit_Id = None

        # There might be calibration files not belonging to any proposal which still
        # have a block visit id, although they shouldn't.
        for fd in file_data:
            if not SaltDatabaseService.is_real_proposal_code(fd.Proposal_Code):
                fd.BlockVisit_Id = None

        # Get the block visit ids independently from the proposal code and target name.
        block_visits_sql = """
SELECT DISTINCT ProposalCode.Proposal_Code, Target.Target_Name, BlockVisit.BlockVisit_Id, BlockVisitStatus.BlockVisitStatus
FROM BlockVisit
JOIN BlockVisitStatus ON BlockVisit.BlockVisitStatus_Id = BlockVisitStatus.BlockVisitStatus_Id
JOIN NightInfo ON BlockVisit.NightInfo_Id = NightInfo.NightInfo_Id
JOIN Block ON BlockVisit.Block_Id = Block.Block_Id
JOIN Pointing ON Block.Block_Id = Pointing.Block_Id
JOIN Observation ON Pointing.Pointing_Id = Observation.Pointing_Id
JOIN Target ON Observation.Target_Id = Target.Target_Id
JOIN ProposalCode ON Block.ProposalCode_Id = ProposalCode.ProposalCode_Id
JOIN FileData ON FileData.ProposalCode_Id = ProposalCode.ProposalCode_Id AND FileData.Target_Name = Target.Target_Name
WHERE FileData.UTStart BETWEEN %s AND %s AND NightInfo.Date=%s
ORDER BY ProposalCode.Proposal_Code, Target.Target_Name, BlockVisit.BlockVisit_Id
        """
        block_visits_results = pd.read_sql(block_visits_sql, self._connection, params=(start_time, end_time, night_date))

        # We'd miss some block visits if we don't change their status from "Deleted" or
        # "In queue".
        def correct_block_visit_status(row):
            if row.BlockVisit_Id in (8595, 9582, 9584, 11308, 11314, 12252, 14317):
                return "Rejected"
            else:
                return row.BlockVisitStatus

        # Each combination of proposal code and target name is linked to a list of
        # corresponding block visit ids. We also link them to an index variable, so
        # that we can keep track of which block visit id in a list should be used if
        # a block visit id is missing in the file_data obtained above.
        #
        # We ignore block visit ids that are in the queue, and (for reasons that will
        # become apparent soon) store deleted block visit ids separately.
        #
        # The following code implicitly assumes that a block visit with a smaller id
        # value has been observed earlier. This is not a good assumption, but it is
        # correct and we don't have much of a choice.
        block_visit_ids = {}
        for row in block_visits_results.itertuples():
            block_visit_status = correct_block_visit_status(row)
            if block_visit_status == 'In queue':
                continue
            key = (row.Proposal_Code, row.Target_Name.strip())
            if key not in block_visit_ids:
                block_visit_ids[key] = {'current_index': 0, 'ids': [], 'deleted_ids': []}
            if block_visit_status in ('Accepted', 'Rejected'):
                block_visit_ids[key]['ids'].append(row.BlockVisit_Id)
            elif block_visit_status == 'Deleted':
                block_visit_ids[key]['deleted_ids'].append(row.BlockVisit_Id)
            else:
                raise ValueError(f"Unsupported block visit status: {block_visit_status}")

        # Sometimes a block visit has been added twice to the OCS and one of these has
        # been deleted afterwards. But there is no guarantee that the correct one has
        # been deleted. Hence we must replace a "deleted" block visit in file_data with
        # the one block visit id (for this proposal and target) that is not in
        # file_data.
        #
        # We start by figuring out which block visit ids aren't used in file_data...
        for key in block_visit_ids:
            # Start by assigning all ids. We'll remove the used ones in the next for
            # loop.
            block_visit_ids[key]['unused_ids'] = set(block_visit_ids[key]['ids'])
        for i, fd in enumerate(file_data):
            key = (fd.Proposal_Code, fd.Target_Name)
            if fd.BlockVisit_Id and key in block_visit_ids:
                block_visit_ids[key]['unused_ids'].discard(fd.BlockVisit_Id)

        # ... and now replace the wrong block visit ids.

        def is_deleted(block_visit_id):
            for key in block_visit_ids:
                if block_visit_id in block_visit_ids[key]['deleted_ids']:
                    return True

            return False

        def unused_alternatives(block_visit_id):
            for key in block_visit_ids:
                if block_visit_id in block_visit_ids[key]['deleted_ids']:
                    return block_visit_ids[key]['unused_ids']

            return set()

        def block_visit_details(block_visit_id):
            for key in block_visit_ids:
                bvd = block_visit_ids[key]
                if block_visit_id in bvd['ids'] or block_visit_id in bvd['deleted_ids']:
                    return bvd

            return None

        for fd in file_data:
            if is_deleted(fd.BlockVisit_Id):
                unused_ids = unused_alternatives(fd.BlockVisit_Id)
                if len(unused_ids) == 1:
                    fd.BlockVisit_Id = list(unused_ids)[0]
                elif len(unused_ids) == 0:
                    # There should be no deleted block visit with data (without another
                    # block visit, that is. Hence we should raise an error. But in fact
                    # there are such blocks, and thus we just use one of their ids.
                    bvd = block_visit_details(fd.BlockVisit_Id)
                    bvd['deleted_ids'].remove(fd.BlockVisit_Id)
                    bvd['ids'].append(fd.BlockVisit_Id)
                    bvd['ids'] = sorted(bvd['ids'])
                else:
                    continue

        # Now that we have all the data, we can try to fill the gaps in file_data.
        previous_key = (None, None)
        for index, fd in enumerate(file_data):
            # If the proposal code or target has changed, generally a new block has
            # started. However, if the proposal code has remained the same and the old
            # target has no block visit id, it is a calibration. We then must assume we
            # are still in the same block.
            key = (fd.Proposal_Code, fd.Target_Name)
            if index > 0 and key != previous_key and not (previous_key[0] == key[0] and (previous_key not in block_visit_ids or key not in block_visit_ids)):
                if previous_key in block_visit_ids:
                    block_visit_ids[previous_key]['current_index'] += 1
            previous_key = key

            if fd.BlockVisit_Id and key in block_visit_ids:
                # Update the current id index
                try:
                    real_index = block_visit_ids[key]['ids'].index(fd.BlockVisit_Id)
                except ValueError:
                    raise Exception(f"The block visit id {fd.BlockVisit_Id} could not be found.")
                if block_visit_ids[key]['current_index'] < real_index:
                    # We might have to catch up with the real index.
                    block_visit_ids[key]['current_index'] = real_index
                # In principle we should raise an error if the current index is ahead of
                # the real index, as this should never happen. However, in practice it
                # might be that other calibrations are taken before files for the
                # proposal and target are resumed. So the real index may indeed be
                # behind the current index.
            else:
                # Update the block visit id.
                if key in block_visit_ids:
                    current_index = block_visit_ids[key]['current_index']
                    if current_index >= len(block_visit_ids[key]['ids']):
                        # This shouldn't happen, but it does. Sometimes a block is
                        # attempted again after several other observations, but without
                        # a new block visit id. So we shrug our shoulders and do the
                        # best we, taking the last available id.
                        current_index = len(block_visit_ids[key]['ids']) - 1

                        # But it might also be that there simply is no block visit id,
                        # in which case there isn't terribly much we can do.
                        if current_index < 0:
                            continue

                    fd.BlockVisit_Id = block_visit_ids[key]['ids'][current_index]

        def previous_block_visit_id(index: int) -> Optional[int]:
            proposal_code = file_data[index].Proposal_Code
            target_name = file_data[index].Target_Name
            i = index - 1
            while i >= 0 and file_data[i].Proposal_Code == proposal_code:
                key_in_block_visits =  (proposal_code, target_name) in block_visit_ids
                if key_in_block_visits and file_data[i].Target_Name != target_name:
                    return None
                block_visit_id = file_data[i].BlockVisit_Id
                if block_visit_id:
                    if key_in_block_visits or file_data[i].Target_Name == target_name:
                        return block_visit_id
                i -= 1
            return None

        def next_block_visit_id(index: int) -> Optional[int]:
            proposal_code = file_data[index].Proposal_Code
            target_name = file_data[index].Target_Name
            i = index + 1
            while i < len(file_data) and file_data[i].Proposal_Code == proposal_code:
                key_in_block_visits =  (proposal_code, target_name) in block_visit_ids
                if key_in_block_visits and file_data[i].Target_Name != target_name:
                    return None
                block_visit_id = file_data[i].BlockVisit_Id
                if block_visit_id:
                    if (proposal_code, target_name) not in block_visit_ids or file_data[i].Target_Name == target_name:
                        return block_visit_id
                i += 1
            return None

        # There might have been calibration files which belong to a proposal but have no
        # block visit id. We'll assign block visit ids if possible, but record an error
        # if there is any ambiguity.
        for i, fd in enumerate(file_data):
            if not SaltDatabaseService.is_real_proposal_code(fd.Proposal_Code):
                # This file does not belong to a proposal
                continue
            if fd.BlockVisit_Id:
                continue

            # Proposals such as engineering proposals might have no block visits in the
            # database.
            proposal_code_found = False
            for key in block_visit_ids.keys():
                if key[0] == fd.Proposal_Code:
                    proposal_code_found = True
                    break
            if not proposal_code_found:
                continue

            previous_id = previous_block_visit_id(i)
            next_id = next_block_visit_id(i)
            if previous_id and next_id and previous_id != next_id:
                # Oh dear. The same target is observed before and after for different
                # block visits. We thus have to guess or throw up our arms in despair.
                # If the file is a Salticam one, it likely is an acquisition image, and
                # we guess it belongs to the next observation...
                if fd.FileName.startswith("S2"):
                    previous_id = None
                else:
                    # ... but otherwise we give up.
                    continue
            if not previous_id and not next_id:
                # Oops. All the files have no block visit id... So we have to guess,
                # take the current index and hope for the best.
                if (fd.Proposal_Code, fd.Target_Name) in block_visit_ids:
                    previous_id = block_visit_ids[(fd.Proposal_Code, fd.Target_Name)]['current_index']
                else:
                    # Well, if there is no current index, there is nothing we can do.
                    # We'll try again below, though,
                    continue
            if previous_id:
                fd.BlockVisit_Id = previous_id
            else:
                fd.BlockVisit_Id = next_id

        # We might still have files attached to a proposal without a block visit id.
        # As we still want to group these, we assign a random block visit id to them.
        for index, fd in enumerate(file_data):
            proposal_code = fd.Proposal_Code
            if SaltDatabaseService.is_real_proposal_code(proposal_code) and fd.BlockVisit_Id is None:
                random_block_visit_id = str(uuid.uuid4())

                # Assign the random id to this file and all neighbouring files of the
                # same proposal.
                i = index
                while i < len(file_data) and file_data[i].Proposal_Code == proposal_code:
                    file_data[i].BlockVisit_Id = random_block_visit_id
                    i += 1

        # Collect the start times and corresponding block visit ids
        return {fd.FileName: fd.BlockVisit_Id for fd in file_data}

    def find_block_visit_id(
        self, proposal_id: str, target_name: str, observing_night: datetime
    ) -> Optional[int]:
        sql = """
        SELECT BlockVisit_Id
FROM NightInfo
JOIN BlockVisit ON NightInfo.NightInfo_Id = BlockVisit.NightInfo_Id
JOIN Block ON BlockVisit.Block_Id = Block.Block_Id
JOIN Pointing ON BlockVisit.Block_Id = Pointing.Block_Id
JOIN Observation ON Pointing.Pointing_Id = Observation.Pointing_Id
JOIN Target ON Observation.Target_Id = Target.Target_Id
JOIN Proposal ON Block.Proposal_Id = Proposal.Proposal_Id
JOIN ProposalCode ON Proposal.ProposalCode_Id = ProposalCode.ProposalCode_Id
WHERE ProposalCode.Proposal_Code =%s
AND Target.Target_Name=%s
AND NightInfo.Date=%s;
        """
        results = pd.read_sql(
            sql, self._connection, params=(proposal_id, target_name, observing_night,)
        ).iloc[0]
        if results["BlockVisit_Id"]:
            return int(results["BlockVisit_Id"])
        return None

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
        # Observations not belonging to a proposal are accepted by default.
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
        if results["BlockVisitStatus"].lower() == "deleted":
            return types.Status.DELETED
        if results["BlockVisitStatus"].lower() == "in queue":
            return types.Status.INQUEUE
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
