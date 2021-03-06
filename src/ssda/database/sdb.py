import functools
import hashlib
import os

import pytz
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from enum import Enum
from typing import Callable, Dict, Iterable, List, Optional, Set, Tuple, Union

from dateutil import relativedelta
import pandas as pd
from pymysql import connect

from ssda.util import types
from ssda.util.fits import (
    FitsFile,
    fits_file_paths,
    StandardFitsFile,
    get_fits_base_dir,
)
from ssda.util.salt_fits import parse_start_datetime
from ssda.util.types import ProposalType
from ssda.util.warnings import record_warning


class BlockVisitIdStatus(Enum):
    CONFIRMED = 1
    GUESSED = 2
    INFERRED = 3
    RANDOM = 4


@dataclass
class FileDataItem:
    """
    Details from a FileData table entry.

    """

    ut_start: datetime
    file_name: str
    block_visit_id: Optional[Union[int, str]]
    block_visit_id_status: Optional[BlockVisitIdStatus]
    target_name: str
    proposal_code: Optional[str]


@dataclass(frozen=True)
class BlockKey:
    """
    A proposal code and a target name, which together are used to identify a block.

    """

    proposal_code: str
    target_name: str


class SaltDatabaseService:
    def __init__(self, database_config: types.DatabaseConfiguration):
        self._connection = connect(
            database=database_config.database(),
            host=database_config.host(),
            user=database_config.username(),
            passwd=database_config.password(),
        )
        self._cursor = self._connection.cursor()
        self._proposal_codes_existing: Dict[str, bool] = {}

    def find_block_visit_ids(
        self, night: date, include_fits_headers: bool = True
    ) -> Dict[str, FileDataItem]:
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
        block visit id. In this case a hashcode based on night, proposal code and target
        name is used.

        Parameters
        ----------
        night : date
            The night for which the block visit ids are obtained.

        Returns
        -------
        dict
            A dictionary of the file names and block visit ids.

        """

        file_data = self._find_raw_file_data(night, include_fits_headers)

        # Find the (accepted and rejected) block visit ids as well as the ignored
        # deleted or queued) block visit ids.
        block_visit_ids = self._find_raw_block_visit_ids(
            night, ["Accepted", "Rejected"]
        )
        ignored_block_visit_ids = self._find_raw_block_visit_ids(
            night, ["Deleted", "In queue"]
        )

        # Remove all block visit ids which don't exist for this night.
        SaltDatabaseService._ignore_wrong_block_visit_ids(
            file_data, block_visit_ids, ignored_block_visit_ids
        )

        # Mark the existing block visit ids as confirmed.
        SaltDatabaseService._mark_confirmed_block_visit_ids(file_data)

        # Try to fill the gaps in the file data.
        self._fill_block_visit_id_gaps(file_data, block_visit_ids, night)

        # Update the status of the guessed and inferred block visit ids.
        SaltDatabaseService._update_block_visit_id_status_values(
            file_data, block_visit_ids
        )

        # Return a dictionary of filenames and corresponding file data.
        return {fd.file_name: fd for fd in file_data}

    def is_existing_proposal_code(self, proposal_code: str) -> bool:
        """
        Does a proposal code exist?

        Parameters
        ----------
        proposal_code : str
            Proposal code.

        Returns
        -------
        bool
            Whether the proposal code exists.

        """

        if proposal_code in self._proposal_codes_existing:
            return self._proposal_codes_existing[proposal_code]

        sql = """
    SELECT COUNT(*) AS ProposalCount
    FROM Proposal
    JOIN ProposalCode ON Proposal.ProposalCode_Id=ProposalCode.ProposalCode_Id
    WHERE Proposal_Code=%s
            """
        results = pd.read_sql(sql, self._connection, params=(proposal_code,))

        existing = results.ProposalCount[0] > 0
        self._proposal_codes_existing[proposal_code] = existing

        return existing

    def _find_raw_file_data(
        self, night: date, include_fits_headers: bool
    ) -> List[FileDataItem]:
        """
        Extract file data from the FileData table and, if requested, the FITS headers.

        Some database inconsistencies are corrected, but missing block visit ids are
        not addressed.

        Parameters
        ----------
        night : date
            Observing night.
        include_fits_headers : bool
            Whether to include data from FITS headers.

        Returns
        -------
        List[FileDataItem]
            Raw file data.

        """

        # Extract data from the FileData table and - if requested - the FITS headers.
        file_data_from_db = self._find_file_data_from_database(night)
        file_data_from_fits = (
            self._find_file_data_from_fits_headers(night)
            if include_fits_headers
            else []
        )

        # Merge data from database and FITS headers.
        file_data = self._merge_file_data(file_data_from_db, file_data_from_fits)

        # Correct for multiple target names in the same block visit.
        if night == date(2016, 10, 20):
            for fd in file_data:
                if fd.proposal_code == "2016-1-SCI-049" and fd.target_name.startswith(
                    "N132D-pos"
                ):
                    fd.target_name = "N132D-pos1"

        # Fix incorrect block visit id.
        if night == date(2015, 2, 25):
            for fd in file_data:
                if fd.block_visit_id == 8082:
                    fd.block_visit_id = 8092

        # Ignore block visit ids of other dates
        if night == date(2016, 2, 22):
            for fd in file_data:
                if fd.block_visit_id == 10906:
                    fd.block_visit_id = None
        if night == date(2018, 4, 16):
            for fd in file_data:
                if fd.block_visit_id == 18937:
                    fd.block_visit_id = None

        # There might be calibration files not belonging to any proposal which still
        # have a block visit id, although they shouldn't.
        for fd in file_data:
            if not fd.proposal_code or not self.is_existing_proposal_code(
                fd.proposal_code
            ):
                fd.block_visit_id = None

        return file_data

    def _find_file_data_from_database(self, night: date) -> List[FileDataItem]:
        """
        Collect file data from the database.

        Parameters
        ----------
        night : date
            Observing night.

        Returns
        -------
        List[FileDataItem]
            The file data.

        """

        start_time = datetime(
            night.year, night.month, night.day, 12, 0, 0, 0, tzinfo=pytz.utc
        )
        end_time = start_time + timedelta(hours=24)
        file_data_sql = """
    SELECT FileData.UTStart, FileData.FileName, ProposalCode.Proposal_Code, FileData.Target_Name, FileData.BlockVisit_Id
    FROM FileData
    JOIN ProposalCode ON FileData.ProposalCode_Id = ProposalCode.ProposalCode_Id
    WHERE UTStart BETWEEN %s AND %s
    ORDER BY UTStart
            """
        file_data_results = pd.read_sql(
            file_data_sql, self._connection, params=(start_time, end_time)
        )

        return [
            FileDataItem(
                ut_start=row.UTStart.to_pydatetime().replace(tzinfo=timezone.utc),
                file_name=row.FileName,
                proposal_code=row.Proposal_Code,
                target_name=row.Target_Name.strip(),
                block_visit_id=int(row.BlockVisit_Id)
                if not pd.isna(row.BlockVisit_Id)
                else None,
                block_visit_id_status=None,
            )
            for row in file_data_results.itertuples()
        ]

    def _find_file_data_from_fits_headers(self, night: date) -> List[FileDataItem]:
        """
        Collect the file data from the FITS file headers.

        Parameters
        ----------
        night : date
            Observing night.

        Returns
        -------
        List[FileDataItem]
            The file data.

        """

        def _parse_header(fits: FitsFile) -> FileDataItem:
            start_date = fits.header_value("DATE-OBS")
            start_time = fits.header_value("TIME-OBS")
            if not start_date:
                raise ValueError("No DATE-OBS header value.")
            if not start_time:
                raise ValueError("No TIME-OBS header value.")
            ut_start = parse_start_datetime(start_date, start_time)
            file_name = os.path.basename(fits.file_path())
            bvisit_id_header_value = fits.header_value("BVISITID")
            block_visit_id = bvisit_id_header_value if bvisit_id_header_value else None
            object_header_value = fits.header_value("OBJECT")
            target_name = object_header_value if object_header_value else ""
            proposal_code_header_value = fits.header_value("PROPID")
            proposal_code = (
                proposal_code_header_value if proposal_code_header_value else None
            )

            return FileDataItem(
                ut_start=ut_start,
                file_name=file_name,
                block_visit_id=block_visit_id,
                block_visit_id_status=None,
                target_name=target_name,
                proposal_code=proposal_code,
            )

        nights = types.DateRange(start=night, end=night + timedelta(days=1))
        instruments = types.Instrument.instruments(types.Telescope.SALT)
        base_dir = get_fits_base_dir()

        return [
            _parse_header(StandardFitsFile(f))
            for f in fits_file_paths(nights, instruments, base_dir)
        ]

    def _merge_file_data(
        self,
        file_data_from_db: Iterable[FileDataItem],
        file_data_from_fits: Iterable[FileDataItem],
    ) -> List[FileDataItem]:
        """
        Merge the file data from the database and FITS file headers.

        If file data is recorded in both the database and the FITS file headers, the
        database version is used.

        Parameters
        ----------
        file_data_from_db : Iterable[FileDataItem]
            File data from the database.
        file_data_from_fits : Iterable[FileDataItem]
            File data from the FITS file headers.

        Returns
        -------
        List[FileDataItem]
            Merged file data.

        """

        # Create dictionaries with the filename as key...
        db_data_dict = {fd.file_name: fd for fd in file_data_from_db}
        fits_data_dict = {fd.file_name: fd for fd in file_data_from_fits}

        # ... merge them (using the database data if there are duplicates)...
        file_data = db_data_dict.copy()
        for file_name, fd in fits_data_dict.items():
            if file_name not in file_data:
                file_data[file_name] = fd

        # ... and turn the result into a list sorted by start time.
        return sorted(file_data.values(), key=lambda fd: fd.ut_start)

    def _find_raw_block_visit_ids(
        self, night: date, status_values: List[str]
    ) -> Dict[BlockKey, List[int]]:
        """
        Extract block visit ids from database tables other than FileData.

        Parameters
        ----------
        night : date

        Returns
        -------

        """

        # Get the block visit ids independently from the proposal code and target name.
        night_date = datetime(night.year, night.month, night.day)
        start_time = datetime(
            night.year, night.month, night.day, 12, 0, 0, 0, tzinfo=pytz.utc
        )
        end_time = start_time + timedelta(hours=24)
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
    JOIN FileData ON FileData.ProposalCode_Id = ProposalCode.ProposalCode_Id
    WHERE FileData.UTStart BETWEEN %s AND %s AND NightInfo.Date=%s
    ORDER BY ProposalCode.Proposal_Code, Target.Target_Name, BlockVisit.BlockVisit_Id
            """
        block_visits_results = pd.read_sql(
            block_visits_sql,
            self._connection,
            params=(start_time, end_time, night_date),
        )

        # We'd miss some block visits if we don't change their status from "Deleted" or
        # "In queue".
        def correct_block_visit_status(_row):
            if _row.BlockVisit_Id in (8595, 9582, 9584, 11308, 11314, 12252, 14317):
                return "Rejected"
            else:
                return _row.BlockVisitStatus

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
        block_visit_ids: Dict[BlockKey, List[int]] = defaultdict(list)
        for row in block_visits_results.itertuples():
            block_visit_status = correct_block_visit_status(row)
            if block_visit_status in status_values:
                key = BlockKey(
                    proposal_code=row.Proposal_Code, target_name=row.Target_Name.strip()
                )
                block_visit_ids[key].append(int(row.BlockVisit_Id))

        return block_visit_ids

    @staticmethod
    def _ignore_wrong_block_visit_ids(
        file_data: List[FileDataItem],
        block_visit_ids: Dict[BlockKey, List[int]],
        ignored_block_visit_ids: Dict[BlockKey, List[int]],
    ):
        """
        Ignore invalid block visit ids.

        A block visit id is invalid if it isn't in the list of block visit ids or
        ignored block visit ids, which means that the block visit is associated with
        another night.

        If an invalid block visit id is found, it is replaced with None in the file
        data.

        Parameters
        ----------
        file_data : List[FileDataItem]
            File data.
        block_visit_ids : Dict[BlockKey, List[int]]
            Block visit ids.
        ignored_block_visit_ids : Dict[BlockKey, List[int]]
            Ignored block visit ids.

        """

        # Extract all id values from the block visit id and ignored block visit id
        # dictionaries.
        id_values: List[int] = sorted(
            functools.reduce(
                lambda x, y: [*x, *y],
                [*block_visit_ids.values(), *ignored_block_visit_ids.values()],
                [],
            )
        )

        # Replace ids that cannot be found among the id values with None.
        for fd in file_data:
            if fd.block_visit_id and fd.block_visit_id not in id_values:
                fd.block_visit_id = None
                fd.block_visit_id_status = None

    @staticmethod
    def _mark_confirmed_block_visit_ids(file_data: List[FileDataItem],):
        """
        Mark all non-None block visit ids as being confirmed, i.e not guessed, inferred
        or random.

        Parameters
        ----------
        file_data : List[FileDataItem]
            File data.

        """

        for fd in file_data:
            if fd.block_visit_id:
                fd.block_visit_id_status = BlockVisitIdStatus.CONFIRMED

    @staticmethod
    def create_block_visit_id_provider(
        file_data: List[FileDataItem],
        block_visit_ids: Dict[BlockKey, List[int]],
        night: date,
    ) -> Callable[[BlockKey], Union[int, str]]:
        """
        Create a function for requesting block visit id values.

        The function accepts a BlockVisitKey as its only parameter.

        If for a combination of proposal code there exist block visit ids not used by
        any other file, the first of these is returned by the function. A returned value
        won't be returned again. If there is no block visit id available a hashcode
        based on night, proposal code and target name is returned instead.

        This implies that the returned block visit id is a string if and only if it is
        not an existing block visit id (i.e. a hashcode).

        Parameters
        ----------
        file_data : List[FileDataItem]
            File data.
        block_visit_ids : Dict[BlockKey]
            Block visit ids.
        night : date
            Observing night.

        Returns
        -------
        Callable[[BlockVisitsKey], Union[int, str]]
            A function for requesting block visit ids.

        """

        # Get the block visit ids not used already.
        available_ids: Dict[BlockKey, List[int]] = defaultdict(list)

        for key, ids in block_visit_ids.items():
            available_ids[key] = sorted(ids)

        # All block visit ids used in the file data are unavailable.
        for fd in file_data:
            if fd.block_visit_id:
                for key in available_ids:
                    if fd.block_visit_id in available_ids[key]:
                        available_ids[key].remove(int(fd.block_visit_id))

        # Define the function for requesting block visit id values.
        def request_block_visit_id(_key: BlockKey):
            if _key in available_ids and available_ids[_key]:
                return available_ids[_key].pop(0)
            else:
                id_string = f"{night.isoformat()}{_key.proposal_code}{_key.target_name}"
                fake_id = hashlib.md5(id_string.encode("UTF-8")).hexdigest()
                return fake_id

        return request_block_visit_id

    def _fill_block_visit_id_gaps(
        self,
        file_data: List[FileDataItem],
        block_visit_ids: Dict[BlockKey, List[int]],
        night: date,
    ):
        """
        Fill in missing block visit ids for files that contain target observations.

        This is done by looping over all file data, starting from the earliest. Files
        that have the same proposal code and target are deemed to belong to the same
        block visit if there are no other proposal code - target combinations between
        them, ignoring calibration files with the same proposal code.

        So, for example, in

        File A: NGC 123 --- 2020-1-SCI-042
        File B: ARC     --- 2020-1-SCI-042
        File C: NGC 123 --- 2020-1-SCI-042

        A and B are considered to belong to the same block visit, whereas in all the
        following cases they are not:

        File A: NGC 123 --- 2020-1-SCI-042
        File B: ARC     --- 2020-1-SCI-042
        File C: NGC 765 --- 2020-1-SCI-042

        File A: NGC 123 --- 2020-1-SCI-042
        File B: ARC     --- 2020-1-SCI-042
        File C: NGC 123 --- 2020-1-SCI-314

        File A: NGC 123 --- 2020-1-SCI-042
        File B: ARC     --- 2020-1-SCI-512
        File C: NGC 123 --- 2020-1-SCI-042

        This can lead to ambiguity, as in the following case:

        File A: NGC 123 --- 2020-1-SCI-042 (block visit id: 12)
        File B: NGC 123 --- 2020-1-SCI-042 (block visit id missing)
        File C: NGC 123 --- 2020-1-SCI-042 (block visit id: 12)

        File B might belong to either the first or the second block visit. In this case
        the following rules are used:

        1. If the ambiguous file is a Salticam file, it is considered to belong to the
           later block visit.
        2. Otherwise it gets its own block visit id.

        Parameters
        ----------
        file_data : list
            File data.
        block_visit_ids : dict
            Block visit ids.
        night : date
            Observing night.

        """

        block_visit_id_provider = self.create_block_visit_id_provider(
            file_data, block_visit_ids, night
        )

        def block_visit_id_for_file(
            _index: int, forward_search: bool
        ) -> Optional[Union[str, int]]:
            """
            What is the block visit id of the nearest earlier file which has a block
            visit id and could belong to the same block?

            """

            proposal_code = file_data[_index].proposal_code
            target_name = file_data[_index].target_name

            def is_calibration(target: str):
                """
                Is the target a calibration?

                As target names in the FileData and Target table may differ for the same
                block visit, we cannot rely on block_visit_ids to decide the question.

                """

                return (
                    target.upper() == "ARC"
                    or target.upper() == "BIAS"
                    or target.upper() == "FLAT"
                    or target.upper().startswith("FLAT ")
                    or target.upper().startswith("FLAT-")
                )

            file_is_calibration = is_calibration(target_name)
            i = _index + 1 if forward_search else _index - 1
            while (
                0 <= i < len(file_data) and file_data[i].proposal_code == proposal_code
            ):
                # A file may belong to the same block if it has the same proposal code
                # and either has the same target name or is a calibration. In case of
                # the latter that file has no corresponding block visit id entry as its
                # target is not a real one.
                other_file_is_calibration = is_calibration(file_data[i].target_name)
                if (
                    not file_is_calibration
                    and not other_file_is_calibration
                    and file_data[i].target_name != target_name
                ):
                    # Both files have a real target, but they are different. So they
                    # belong to different block visits.
                    return None
                block_visit_id = file_data[i].block_visit_id
                if block_visit_id and (
                    file_is_calibration
                    or other_file_is_calibration
                    or file_data[i].target_name == target_name
                ):
                    # At least one of the two files is a calibration or both files have
                    # the same target. So we've found a block visit id!
                    return block_visit_id
                if forward_search:
                    i += 1
                else:
                    i -= 1

            # There are no files left.
            return None

        for index, fd in enumerate(file_data):
            # If there is a block visit id already, there is nothing to do.
            if fd.block_visit_id:
                continue

            # Files which don't belong to a proposal have no block visit id.
            if not fd.proposal_code:
                continue
            if not self.is_existing_proposal_code(fd.proposal_code):
                continue

            # Figure out the possible block visit ids
            previous_id = block_visit_id_for_file(index, False)
            next_id = block_visit_id_for_file(index, True)
            key = BlockKey(proposal_code=fd.proposal_code, target_name=fd.target_name)

            if previous_id is None and next_id is None:
                # There is no block visit id to be found, so we have to ask for one.
                fd.block_visit_id = block_visit_id_provider(key)
                fd.block_visit_id_status = (
                    BlockVisitIdStatus.RANDOM
                    if type(fd.block_visit_id) == str
                    else BlockVisitIdStatus.GUESSED
                )
                continue

            if previous_id is None and next_id is not None:
                # As there is no previous id, we can safely group with the later file.
                fd.block_visit_id = next_id
                fd.block_visit_id_status = BlockVisitIdStatus.INFERRED
                continue

            if previous_id is not None and next_id is None:
                # As there is no next id, we can safely group with the earlier file.
                fd.block_visit_id = previous_id
                fd.block_visit_id_status = BlockVisitIdStatus.INFERRED
                continue

            if previous_id == next_id:
                fd.block_visit_id = previous_id
                fd.block_visit_id_status = BlockVisitIdStatus.INFERRED
                continue
            else:
                # The file could belong to two block visits. So if it's a Salticam/BCAM
                # file, we group with the later file, otherwise we use a new block visit
                # id.
                if fd.file_name.startswith("S2") or fd.file_name.startswith("B2"):
                    fd.block_visit_id = next_id
                    fd.block_visit_id_status = BlockVisitIdStatus.INFERRED
                    continue
                else:
                    fd.block_visit_id = block_visit_id_provider(key)
                    fd.block_visit_id_status = (
                        BlockVisitIdStatus.RANDOM
                        if type(fd.block_visit_id) == str
                        else BlockVisitIdStatus.GUESSED
                    )
                    continue

    @staticmethod
    def _update_block_visit_id_status_values(file_data, block_visit_ids):
        """
        Update the block visit id status value from GUESSED or INFERRED to CONFIRMED
        or RANDOM where possible.

        Replacement with CONFIRMED is deemed possible if the sequence of block visit ids
        for the proposal code - target combination is the same irrespective of whether
        it is inferred from the BlockVisit table or from the FileData table.

        Only accepted and rejected block visits are used for inferring block visit
        sequences from the BlockVisit table.

        The INFERRED status is replaced with the status of the block visit id which has
        been inferred.

        Parameters
        ----------
        file_data : List[FileDataItem]
            File data.
        block_visit_ids : Dict[BlockKey, List[int]]
            Block visit ids.

        """

        # Get the sequence of block visits in the file data
        fd_sequences: Dict[BlockKey, List[int]] = defaultdict(list)
        for fd in file_data:
            key = BlockKey(proposal_code=fd.proposal_code, target_name=fd.target_name)
            if key in block_visit_ids:
                # Add the id to the end of the sequence, if it isn't the last sequence
                # item already.
                if (
                    not len(fd_sequences[key])
                    or fd_sequences[key][-1] != fd.block_visit_id
                ):
                    fd_sequences[key].append(fd.block_visit_id)

        # Check whether we can assume that guessed values are correct
        for fd in file_data:
            if fd.block_visit_id_status == BlockVisitIdStatus.GUESSED:
                key = BlockKey(
                    proposal_code=fd.proposal_code, target_name=fd.target_name
                )
                if key in fd_sequences and block_visit_ids[key] == fd_sequences[key]:
                    fd.block_visit_id_status = BlockVisitIdStatus.CONFIRMED

        # Check which ids have been deemed guessed, random or real...
        status_values: Dict[int, BlockVisitIdStatus] = {}
        for fd in file_data:
            if fd.block_visit_id_status in (
                BlockVisitIdStatus.CONFIRMED,
                BlockVisitIdStatus.GUESSED,
                BlockVisitIdStatus.RANDOM,
            ):
                # Make sure that the status values are consistent.
                if (
                    fd.block_visit_id in status_values
                    and status_values[fd.block_visit_id] != fd.block_visit_id_status
                ):
                    if status_values[fd.block_visit_id] == BlockVisitIdStatus.CONFIRMED:
                        record_warning(
                            Warning(
                                f"The block visit id {fd.block_visit_id} has been "
                                f"marked both as {status_values[fd.block_visit_id]} "
                                f"and {fd.block_visit_id_status}."
                            )
                        )
                        fd.block_visit_id_status = BlockVisitIdStatus.CONFIRMED
                    else:
                        raise Exception(
                            f"The block visit id {fd.block_visit_id} has been "
                            f"marked both as {status_values[fd.block_visit_id]} "
                            f"and {fd.block_visit_id_status}."
                        )
                status_values[fd.block_visit_id] = fd.block_visit_id_status

        # ... and update the inferred and guessed status values accordingly.
        for fd in file_data:
            if (
                fd.block_visit_id_status
                in (BlockVisitIdStatus.GUESSED, BlockVisitIdStatus.INFERRED)
                and fd.block_visit_id in status_values
            ):
                fd.block_visit_id_status = status_values[fd.block_visit_id]

    def find_pi(self, proposal_code: str) -> str:
        sql = """
SELECT CONCAT(FirstName, " ", Surname) as FullName
FROM ProposalCode
    JOIN ProposalContact ON ProposalCode.ProposalCode_Id=ProposalContact.ProposalCode_Id
    JOIN Investigator ON ProposalContact.Leader_Id=Investigator.Investigator_Id
WHERE ProposalCode.Proposal_Code=%s;
        """
        results = pd.read_sql(sql, self._connection, params=(proposal_code,))
        if not len(results):
            raise ValueError(
                f'No Principal Investigator found for proposal code "{proposal_code}". Does the proposal code exist?'
            )
        results = results.iloc[0]
        if results["FullName"]:
            return results["FullName"]
        raise ValueError("Observation have no Principal Investigator")

    def find_proposal_title(self, proposal_code: str) -> str:
        sql = """
SELECT Title
FROM ProposalText
        JOIN ProposalCode ON ProposalText.ProposalCode_Id=ProposalCode.ProposalCode_Id
        JOIN Semester ON ProposalText.Semester_Id=Semester.Semester_Id
WHERE ProposalCode.Proposal_Code=%s
ORDER BY Semester.Year DESC, Semester.Semester DESC
LIMIT 1
        """
        results = pd.read_sql(sql, self._connection, params=(proposal_code,)).iloc[0]
        if results["Title"]:
            return f"{results['Title']}"
        raise ValueError("Observation has no title")

    def find_observation_status(
        self, block_visit_id: Optional[Union[int, str]]
    ) -> types.Status:
        # Observations not belonging to a proposal are accepted by default.
        if block_visit_id is None:
            return types.Status.ACCEPTED

        # Observations with an unknown block visit are rejected by default.
        try:
            block_visit_id = int(block_visit_id)
        except ValueError:
            return types.Status.REJECTED

        status_sql = """
SELECT BlockVisitStatus
FROM BlockVisit
     JOIN BlockVisitStatus USING(BlockVisitStatus_Id)
WHERE BlockVisit_Id=%s
        """
        status_results = pd.read_sql(
            status_sql, self._connection, params=(block_visit_id,)
        )

        if not len(status_results):
            raise Exception(
                f"No block visit status found for block visit id " f"{block_visit_id}."
            )

        status_results = status_results.iloc[0]

        if status_results["BlockVisitStatus"].lower() == "accepted":
            return types.Status.ACCEPTED
        if status_results["BlockVisitStatus"].lower() == "rejected":
            return types.Status.REJECTED

        # What block visits have there been for the block in the same night?
        visits_sql = """
SELECT DISTINCT BlockVisit_Id, BlockVisitStatus
FROM BlockVisit AS bv
JOIN BlockVisitStatus AS bvs ON bv.BlockVisitStatus_Id = bvs.BlockVisitStatus_Id
WHERE bv.Block_Id=(SELECT bv2.Block_Id FROM BlockVisit AS bv2 WHERE bv2.BlockVisit_Id=%(id)s)
      AND bv.NightInfo_Id=(SELECT bv3.NightInfo_Id FROM BlockVisit AS bv3 WHERE bv3.BlockVisit_Id=%(id)s);
        """
        visits_results = pd.read_sql(
            visits_sql, self._connection, params={"id": block_visit_id}
        )
        all_visits = len(visits_results)
        accepted_visits = len(
            visits_results[visits_results["BlockVisitStatus"] == "Accepted"]
        )
        rejected_visits = len(
            visits_results[visits_results["BlockVisitStatus"] == "Rejected"]
        )
        other_visits = all_visits - accepted_visits - rejected_visits

        # We don't know which visit corresponds to a deleted/queued visit, However, this
        # doesn't matter if there are enough accepted/rejected visits and if there
        # aren't both accepted and rejected visits, as in this case it is reasonable to
        # assume that there is a corresponding visit and there is only one possible
        # status for it.
        if rejected_visits == 0 and accepted_visits >= other_visits:
            return types.Status.ACCEPTED
        if accepted_visits == 0 and rejected_visits >= other_visits:
            return types.Status.REJECTED

        # If there are neither accepted nor rejected block visits, the block visit
        # status should be correct.
        if accepted_visits == 0 and rejected_visits == 0:
            if status_results["BlockVisitStatus"].lower() == "deleted":
                return types.Status.DELETED
            if status_results["BlockVisitStatus"].lower() == "in queue":
                return types.Status.IN_QUEUE

        # Despite best effort no block visit status could be determined. Let's play it
        # safe and declare the visit rejected.
        record_warning(
            Warning(
                f"The block visit status could not be determined for the block visit id {block_visit_id}. It is therefore marked as rejected."
            )
        )
        return types.Status.REJECTED

    def find_release_date(self, proposal_code: str) -> Tuple[date, date]:
        sql = """
SELECT MAX(EndSemester) AS EndSemester, ProposalType, ProprietaryPeriod
FROM BlockVisit
JOIN Block ON BlockVisit.Block_Id=Block.Block_Id
JOIN ProposalCode ON Block.ProposalCode_Id=ProposalCode.ProposalCode_Id
JOIN ProposalGeneralInfo ON ProposalCode.ProposalCode_Id=ProposalGeneralInfo.ProposalCode_Id
JOIN ProposalType ON ProposalGeneralInfo.ProposalType_Id=ProposalType.ProposalType_Id
JOIN NightInfo ON BlockVisit.NightInfo_Id=NightInfo.NightInfo_Id
JOIN Semester ON Date BETWEEN Semester.StartSemester AND Semester.EndSemester
WHERE Proposal_Code=%s;
        """
        results = pd.read_sql(sql, self._connection, params=(proposal_code,)).iloc[0]

        end_semester = results["EndSemester"]
        proposal_type = results["ProposalType"]

        # Gravitational wave proposals never become public (and are only
        # accessible by SALT partners). However, their meta data becomes public
        # immediately.
        if proposal_type == "Gravitational Wave Event":
            release_date = datetime.strptime("2100-01-01", "%Y-%m-%d").date()
            meta_release_date = datetime.today().date()

            return release_date, meta_release_date

        proprietary_period = results["ProprietaryPeriod"]

        # If there is no end semester (probably because there is no block visit for the
        # proposal) we assume the end of the current semester.
        if not end_semester:
            end_semester_sql = """
            SELECT EndSemester
            FROM Semester
            WHERE DATE(NOW()) BETWEEN Semester.StartSemester AND Semester.EndSemester
            """
            end_semester_results = pd.read_sql(end_semester_sql, self._connection).iloc[
                0
            ]
            end_semester = end_semester_results["EndSemester"]

        if proprietary_period is None:
            raise ValueError(
                f"The proprietary period is NULL for proposal {proposal_code}."
            )

        # The semester end date in the SDB is the last day of a month.
        # However, it is easier (and more correct) to use the first day of the
        # following month.
        # We therefore add a day in addition to the proprietary period.
        release_date = (
            end_semester
            + relativedelta.relativedelta(days=1)
            + relativedelta.relativedelta(months=proprietary_period)
        )

        return release_date, release_date

    def find_proposal_investigators(self, proposal_code: str) -> List[str]:
        # Gravitational wave proposals by definition have no investigator
        if self.sdb_proposal_type(proposal_code) == "Gravitational Wave Event":
            return []

        sql = """
SELECT PiptUser.PiptUser_Id
FROM ProposalInvestigator
    JOIN ProposalCode ON ProposalInvestigator.ProposalCode_Id=ProposalCode.ProposalCode_Id
    JOIN Investigator ON ProposalInvestigator.Investigator_Id=Investigator.Investigator_Id
    JOIN PiptUser ON Investigator.PiptUser_Id=PiptUser.PiptUser_Id
WHERE ProposalCode.Proposal_Code=%s;
        """
        results = pd.read_sql(sql, self._connection, params=(proposal_code,))
        if len(results):
            ps = []
            for index, row in results.iterrows():
                ps.append(row["PiptUser_Id"])
            return ps
        raise ValueError("Observation has no Investigators")

    def find_target_type(self, block_visit_id: Optional[Union[int, str]]) -> str:
        # If there is no block visit, return the Unknown target type
        if block_visit_id is None:
            return "00.00.00.00"

        # If the block visit id is no integer, return the Unknown target type
        try:
            block_visit_id = int(block_visit_id)
        except ValueError:
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

        results = pd.read_sql(sql, self._connection, params=(block_visit_id,))

        if not len(results):
            return "00.00.00.00"

        results = results.iloc[0]

        if results["NumericCode"]:
            return results["NumericCode"]
        raise ValueError(
            f"No numeric code defined for the target type of block visit "
            f"{block_visit_id}"
        )

    def is_mos(self, slit_barcode: str) -> bool:

        sql = """
SELECT RssMaskType FROM RssMask JOIN RssMaskType USING(RssMaskType_Id)  WHERE Barcode=%s
        """
        results = pd.read_sql(sql, self._connection, params=(slit_barcode,))
        if len(results) <= 0:
            return False

        return results.iloc[0]["RssMaskType"] == "MOS"

    def institution_memberships(
        self, user_id: int
    ) -> List[types.InstitutionMembership]:
        # TODO: This should be replaced with an improved version, getting the date
        # intervals from the SDB
        partner_membership_intervals = {
            "AMNH": [(date(2011, 9, 1), date(2100, 1, 1))],
            "CMU": [(date(2011, 9, 1), date(2013, 4, 30))],
            "DC": [(date(2011, 9, 1), date(2100, 1, 1))],
            "DUR": [(date(2017, 5, 1), date(2019, 4, 30))],
            "GU": [
                (date(2011, 9, 1), date(2015, 4, 30)),
                (date(2016, 5, 1), date(2017, 10, 31)),
            ],
            "HET": [(date(2011, 9, 1), date(2015, 4, 30))],
            "IUCAA": [(date(2011, 9, 1), date(2100, 1, 1))],
            "POL": [(date(2011, 9, 1), date(2100, 1, 1))],
            "RSA": [(date(2011, 9, 1), date(2100, 1, 1))],
            "RU": [(date(2011, 9, 1), date(2100, 1, 1))],
            "UC": [
                (date(2011, 9, 1), date(2014, 10, 31)),
                (date(2015, 5, 1), date(2016, 10, 31)),
                (date(2017, 5, 1), date(2019, 4, 30)),
            ],
            "UKSC": [(date(2011, 9, 1), date(2100, 1, 1))],
            "UNC": [(date(2011, 9, 1), date(2020, 4, 30))],
            "UW": [(date(2011, 9, 1), date(2100, 1, 1))],
        }

        sql = """
                    SELECT Partner_Code
                    FROM PiptUser
                    JOIN Investigator ON PiptUser.PiptUser_Id = Investigator.PiptUser_Id
                    JOIN Institute ON Investigator.Institute_Id = Institute.Institute_Id
                    JOIN Partner ON Institute.Partner_Id = Partner.Partner_Id
                    WHERE PiptUser.PiptUser_Id=%s AND Partner.Partner_Code != "OTH" AND Partner.Virtual = 0
                """

        df = pd.read_sql(sql, self._connection, params=(user_id,))
        membership_intervals: Set[types.InstitutionMembership] = set()
        for partner_code in df["Partner_Code"]:
            for partner_membership_interval in partner_membership_intervals[
                partner_code
            ]:
                institution_membership = types.InstitutionMembership(
                    membership_end=partner_membership_interval[1],
                    membership_start=partner_membership_interval[0],
                )
                membership_intervals.add(institution_membership)

        sorted_intervals = sorted(list(membership_intervals))
        return sorted_intervals

    def find_proposal_type(self, proposal_code: str) -> ProposalType:
        db_proposal_type = self.sdb_proposal_type(proposal_code)
        commissioning_types = ("Commissioning",)
        engineering_types = ("Engineering",)
        science_types = (
            "Director Discretionary Time (DDT)",
            "Gravitational Wave Event",
            "Key Science Program",
            "Large Science Proposal",
            "Science",
            "Science - Long Term",
        )
        science_verification_types = ("Science Verification",)

        if db_proposal_type in commissioning_types:
            return ProposalType.COMMISSIONING
        elif db_proposal_type in engineering_types:
            return ProposalType.ENGINEERING
        elif db_proposal_type in science_types:
            return ProposalType.SCIENCE
        elif db_proposal_type in science_verification_types:
            return ProposalType.SCIENCE_VERIFICATION
        else:
            raise ValueError(
                f"The SDB proposal type {db_proposal_type} is not supported."
            )

    def find_proposal_observation_groups(
        self, proposal_code
    ) -> Dict[str, types.SALTObservationGroup]:
        """
        The observation groups (i.e. block visits) taken for a proposal.
        Parameters
        ----------
        proposal_code: str
            The proposal code.
        Returns
        -------
            The observation group.
        """

        sql = """
SELECT BlockVisit_Id, BlockVisitStatus
FROM BlockVisit
    JOIN `Block` USING(Block_Id)
    JOIN BlockVisitStatus USING(BlockVisitStatus_Id)
    JOIN ProposalCode USING(ProposalCode_Id)
WHERE Proposal_Code = %s
        """
        results = pd.read_sql(sql, self._connection, params=(proposal_code,))
        ps = dict()
        if len(results):
            for index, row in results.iterrows():
                block_visit_id = str(row["BlockVisit_Id"])
                if row["BlockVisitStatus"] in ["Accepted", "Rejected"]:
                    ps[block_visit_id] = types.SALTObservationGroup(
                        group_identifier=block_visit_id,
                        status=types.Status.for_value(row["BlockVisitStatus"]),
                    )

        return ps

    def find_phase2_proposals(
        self, from_date: date
    ) -> Dict[str, types.SALTProposalDetails]:
        """
        Details of all current phase 2 proposals, irrespective of their status,
        submitted on or after a date.

        Older proposals aren't included as they may give errors.

        Deleted proposals may be included.

        Parameters
        ----------
        from_date : date
            Date from which onward proposals are included.

        Returns
        -------
        dict
            The list of proposal details.

        """

        sql = """
SELECT DISTINCT Proposal_Code, Title, CONCAT(FirstName, " ", Surname) as FullName
FROM Proposal
    JOIN ProposalCode USING(ProposalCode_Id)
    JOIN ProposalText USING(ProposalCode_Id)
    JOIN ProposalContact USING(ProposalCode_Id)
    JOIN Investigator ON Leader_Id = Investigator_Id
    JOIN ProposalGeneralInfo USING(ProposalCode_Id)
WHERE Current = 1 AND Phase = 2 AND SubmissionDate >= %(from_date)s
            """
        results = pd.read_sql(sql, self._connection, params=dict(from_date=from_date))
        proposals = dict()
        for _, row in results.iterrows():
            proposal_code = row["Proposal_Code"]
            release_date = self.find_release_date(proposal_code=proposal_code)
            investigators = self.find_proposal_investigator_user_ids(
                proposal_code=proposal_code
            )
            proposals[proposal_code] = types.SALTProposalDetails(
                pi=row["FullName"],
                meta_release=release_date[1],
                data_release=release_date[0],
                proposal_code=proposal_code,
                title=row["Title"],
                institution=types.Institution.SALT,
                investigators=investigators,
            )
        return proposals

    def find_proposal_investigator_user_ids(self, proposal_code: str) -> List[str]:
        if "GWE" in proposal_code:
            return []

        sql = """
SELECT PiptUser.PiptUser_Id
FROM ProposalInvestigator
    JOIN ProposalCode ON ProposalInvestigator.ProposalCode_Id=ProposalCode.ProposalCode_Id
    JOIN Investigator ON ProposalInvestigator.Investigator_Id=Investigator.Investigator_Id
    JOIN PiptUser ON Investigator.PiptUser_Id=PiptUser.PiptUser_Id
WHERE ProposalCode.Proposal_Code=%s;
        """
        results = pd.read_sql(sql, self._connection, params=(proposal_code,))
        if len(results):
            ps = []
            for index, row in results.iterrows():
                ps.append(str(row["PiptUser_Id"]))
            return ps
        raise ValueError("Observation has no Investigators")

    def sdb_proposal_type(self, proposal_code: str) -> str:
        with self._connection.cursor():
            sql = """
            SELECT ProposalType
            FROM ProposalType
            JOIN ProposalGeneralInfo ON ProposalType.ProposalType_Id = ProposalGeneralInfo.ProposalType_Id
            JOIN ProposalCode ON ProposalGeneralInfo.ProposalCode_Id = ProposalCode.ProposalCode_Id
            WHERE ProposalCode.Proposal_Code=%s
            """
            results = pd.read_sql(sql, self._connection, params=(proposal_code,))

            if not len(results):
                raise ValueError(
                    f"No proposal type could be found for the proposal code {proposal_code}."
                )

            results = results.iloc[0]
            return str(results["ProposalType"])

    def is_block_visit_in_night(self, block_visit_id: int, night: date) -> bool:
        """
        Check whether a block visit was done in a given night.

        Parameters
        ----------
        block_visit_id : int
            Block visit id.
        night : date
            Observing night.

        Returns
        -------
        bool
            Whether the block visit was done in the night.

        """

        sql = """
        SELECT COUNT(*) AS BlockVisitCount
        FROM BlockVisit
        JOIN NightInfo ON BlockVisit.NightInfo_Id = NightInfo.NightInfo_Id
        WHERE BlockVisit.BlockVisit_Id=%(block_visit_id)s AND NightInfo.Date=%(night)s
        """
        results = pd.read_sql(
            sql,
            self._connection,
            params={"block_visit_id": block_visit_id, "night": night},
        ).iloc[0]

        return results["BlockVisitCount"] > 0
