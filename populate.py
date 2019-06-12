from astropy.coordinates import Angle
from datetime import date, timedelta
import os
import pandas as pd
from typing import List, Optional
from pymysql import Connection

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
        populate_with_data(RssFitsData(f))


def populate_with_data(fits_data: InstrumentFitsData) -> None:
    db_update = DatabaseUpdate(fits_data)
    try:
        # Maybe the file content been added to the database already?
        fits_base_path_length = len(os.environ['FITS_BASE_DIR'])
        path = os.path.abspath(fits_data.file_path)[fits_base_path_length:]
        sql = """
        SELECT dataFileId FROM DataFile WHERE path=%s
        """
        df = pd.read_sql(sql, con=ssda_connect(), params=(path,))
        if len(df) > 0:
            return

        # Add the file content to the database
        proposal_id = db_update.insert_proposal()
        observation_id = db_update.insert_observation(proposal_id)
        target_id = db_update.insert_target()
        data_file_id = db_update.insert_data_file(observation_id=observation_id, target_id=target_id)
        db_update.insert_data_preview(data_file_id)
        db_update.insert_instrument(data_file_id)

        db_update.commit()
    except Exception as e:
        db_update.rollback()
        raise e


class DatabaseUpdate:
    """
    Update the SSDA.

    All updates are done as part of a transaction. You need to call the commit method
    to commit the transaction. Use the rollback method to roll back the transaction.

    Parameters:
    -----------
    fits_data : InstrumentFitsData
        FITS data to use for updating the database.

    """

    def __init__(self, fits_data: InstrumentFitsData):
        self.fits_data = fits_data
        self._ssda_connection = ssda_connect()
        self._ssda_connection.autocommit(False)
        self.cursor = self._ssda_connection.cursor()

    def commit(self):
        """
        Commit all the updates to the database.

        """

        self._ssda_connection.commit()

    def rollback(self):
        """
        Roll back all the updates to the database.

        """

        self._ssda_connection.rollback()

    # Proposal ------------------------------------------------------------------- Start

    def insert_proposal(self) -> Optional[int]:
        """
        Insert the proposal for FITS data into the database.

        The proposal is not added again if it exists in the database already. No
        proposal is added if the FITS file is not linked to any proposal.

        The primary key of the entry in the Proposal table is returned, irrespective of
        whether the proposal has been created or existed already. In case there is no
        proposal, None is returned instead,

        Parameters
        ----------
        fits_data : InstrumentFitsData
            Instrument FITS data.

        Returns
        -------
        id : int or None
            Primary key of the Proposal table entry.

        """

        # Collect the proposal properties
        proposal_code = self.fits_data.proposal_code()
        principal_investigator = self.fits_data.principal_investigator()
        if principal_investigator:
            given_name = principal_investigator.given_name
            family_name = principal_investigator.family_name
        else:
            given_name = None
            family_name = None
        proposal_title = self.fits_data.proposal_title()

        if proposal_code is None:
            return None

        # Maybe the proposal exists already?
        existing_proposal_id = self.proposal_id(proposal_code)
        if existing_proposal_id is not None:
            return existing_proposal_id

        # Create the proposal
        sql = """
        INSERT INTO Proposal (proposalCode,
                              principalInvestigatorGivenName,
                              principalInvestigatorFamilyName,
                              title)
                    VALUES (%(proposal_code)s,
                            %(given_name)s,
                             %(family_name)s,
                             %(proposal_title)s)
        """
        params = dict(proposal_code=proposal_code,
                             given_name=given_name,
                             family_name=family_name,
                             proposal_title=proposal_title)
        self.cursor.execute(sql, params)

        # Get the proposal id
        return self.last_insert_id()

    def proposal_id(self, proposal_code):
        """
        The id of the proposal with a given proposal code.

        The primary key of the Proposal entry with the given proposal code is returned.
        None is returned if there exists no such entry.

        Parameters
        ----------
        proposal_code : str
            Proposal code.

        Returns
        -------
        id : int
            The proposal id.

        """

        sql = """
        SELECT proposalId FROM Proposal WHERE proposalCode=%s
        """
        df = pd.read_sql(sql, con=self._ssda_connection, params=(proposal_code,))
        if len(df) > 0:
            return int(df['proposalId'][0])
        else:
            return None

    # Proposal ------------------------------------------------------------------- End

    # Observation ---------------------------------------------------------------- Start

    def insert_observation(self, proposal_id: int) -> int:
        """
        Insert the observation for FITS data into the database.

        The observation is not added again if it exists in the database already.

        The primary key of the entry in the Proposal table is returned, irrespective of
        whether the proposal has been created or existed already.

        Parameters
        ----------
        proposal_id : int or None
            Primary key of the Proposal table entry for the proposal to which the
            observation belongs.

        Returns
        -------
        id : int
            Primary key of the Observation table entry.

        """

        # Collect the observation properties.
        telescope = self.fits_data.telescope()
        telescope_id = telescope.id()
        telescope_observation_id = self.fits_data.telescope_observation_id()
        night = self.fits_data.night()
        observation_status_id = self.fits_data.observation_status().id()

        # Maybe the observation exists already?
        if telescope_id and telescope_observation_id:
            existing_observation_id = self.observation_id(telescope, telescope_observation_id)
            if existing_observation_id is not None:
                return existing_observation_id

        # Create the observation
        insert_sql = """
        INSERT INTO Observation (proposalId,
                                 telescopeId,
                                 telescopeObservationId,
                                 night,
                                 observationStatusId)
                    VALUES (%(proposal_id)s,
                            %(telescope_id)s,
                            %(telescope_observation_id)s,
                            %(night)s,
                            %(observation_status_id)s)
        """
        insert_params = dict(proposal_id=proposal_id,
                             telescope_id=telescope_id,
                             telescope_observation_id=telescope_observation_id,
                             night=night,
                             observation_status_id=observation_status_id)
        self.cursor.execute(insert_sql, insert_params)

        # Get the observation id
        return self.last_insert_id()

    def observation_id(self, telescope: Telescope, telescope_observation_id: str) -> Optional[int]:
        """
        The id of the observation for a telescope and telescope observation id.

        The primary key of the Observation entry with the given telescope observation id
        and the id corresponding to the given telescope is returned. None is returned if
         there exists no such entry.

        Parameters
        ----------
        telescope : Telescope
            Telescope.
        telescope_observation_id: str
            Telescope observation id.

        Returns
        -------
        id : int
            The observation id.

        """

        sql = """
            SELECT observationId FROM Observation
                   WHERE telescopeId=%(telescope_id)s
                         AND telescopeObservationId=%(telescope_observation_id)s
            """
        params = dict(telescope_id=telescope.id(),
                      telescope_observation_id=telescope_observation_id)
        df = pd.read_sql(sql, con=self._ssda_connection, params=params)
        if len(df) > 0:
            return int(df['observationId'][0])
        else:
            return None

    # Observation ---------------------------------------------------------------- End

    # Target --------------------------------------------------------------------- Start

    def insert_target(self) -> Optional[int]:
        """
        Insert the target for FITS data into the database.

        No entry is created if the FITS data does not specify a target.

        The primary key of the Target table entry is returned, or None if no target is
        specified in the FITS data.

        Returns
        -------
        id : int
            Primary key of the Target table entry.

        """

        # Collect the target properties
        target = self.fits_data.target()
        if target is None:
            return None

        # Get the target type id
        if target.target_type is not None:
            target_type_id_sql = """
                  SELECT targetTypeId FROM TargetType WHERE numericValue = %s
            """
            target_type_id_df = pd.read_sql(sql=target_type_id_sql, con=ssda_connect(), params=(target.target_type,))
            if target_type_id_df.empty:
                raise ValueError('The target type {} is not included in the TargetType table.'.format(target.target_type_id))
            target_type_id = int(target_type_id_df['targetTypeId'][0])
        else:
            target_type_id = None

        # Insert the target
        insert_sql = """
        INSERT INTO Target(
                name,
                rightAscension,
                declination,
                position,
                targetTypeId
              )
        VALUES (%(name)s, %(ra)s, %(dec)s, ST_GeomFromText('POINT(%(shifted_ra)s %(dec)s)', 123456), %(target_type_id)s)
        """
        insert_params = dict(name=target.name, ra=target.ra, dec=target.dec, shifted_ra=target.ra - 180, target_type_id=target_type_id)
        self.cursor.execute(insert_sql, insert_params)

        # Get the target id
        return self.last_insert_id()

    # Target --------------------------------------------------------------------- End

    # DataFile ------------------------------------------------------------------- Start

    def insert_data_file(self, observation_id: int, target_id: Optional[int]):
        """
        Insert the data file for FITS data into the database.

        The primary key of the DataFile table entry is returned.

        Parameters
        ----------
        observation_id
        target_id

        Returns
        -------

        """
        # Collect the data file properties
        base_path_length = len(os.environ['FITS_BASE_DIR'])
        data_category = self.fits_data.data_category()
        start_time = self.fits_data.start_time()
        name = os.path.basename(self.fits_data.file_path)
        path = os.path.abspath(self.fits_data.file_path)[base_path_length:]
        size = self.fits_data.file_size

        # Maybe the data file exists already?
        if observation_id is not None:
            existing_data_file_id = self.data_file_id(observation_id, name)
            if existing_data_file_id is not None:
                return existing_data_file_id

        # Insert the data file
        sql = """
        INSERT INTO DataFile(
                dataCategoryId,
                startTime,
                name,
                path,
                targetId,
                size,
                observationId
              )
        VALUES (%(data_category_id)s, %(start_time)s, %(name)s, %(path)s, %(target_id)s, %(size)s, %(observation_id)s)
        """
        params = dict(data_category_id=data_category.id(), start_time=start_time, name=name, path=path, target_id=target_id, size=size, observation_id=observation_id)
        self.cursor.execute(sql, params)

        # Get the data file id
        return self.last_insert_id()

    def data_file_id(self, observation_id: int, name: str) -> Optional[int]:
        """
        The id of the data file for an observation and file name.

        The primary key of the DataFile entry with the given observation id and file
        name is returned. None is returned if there exists no such entry.

        Parameters
        ----------
        observation_id : int
            Observation id.
        name : str
            File name.

        Returns
        -------
        id : int
            The data file id.

        """

        sql = """
        SELECT dataFileId FROM DataFile WHERE observationId=%(observation_id)s AND name=%(name)s
        """
        params = dict(observation_id=observation_id, name=name)
        df = pd.read_sql(sql, con=self._ssda_connection, params=params)

        if len(df) > 0:
            return int(df['dataFileId'][0])
        else:
            return None

    # DataFile ------------------------------------------------------------------- End

    # DataPreview ---------------------------------------------------------------- Start

    def insert_data_preview(self, data_file_id: int) -> List[id]:
        """
        Insert the data preview entries for FITS data into the database.

        The preview files referenced by the data preview entries are created.

        The list of primary keys of the DataPreview table entries is returned.

        Returns
        -------
        ids : list of id
            The primary keys of the DataPreview entries.

        """

        # Create the preview files
        preview_files = self.fits_data.create_preview_files()

        # Enter the data for all preview files into the database
        ids = []
        for index, preview_file in enumerate(preview_files):
            # Collect the preview data
            base_dir_path_length = len(os.environ['PREVIEW_BASE_DIR'])
            name = os.path.basename(preview_file)
            path = os.path.abspath(preview_file)[base_dir_path_length:]
            order = index + 1

            # Maybe the data preview entry exists already?
            existing_data_preview_id = self.data_preview_id(data_file_id, order)
            if existing_data_preview_id is None:
                # It doesn't exist, so it is inserted
                sql = """
                INSERT INTO DataPreview(
                        name,
                        path,
                        dataFileId,
                        `order`
                )
                VALUES (%(name)s, %(path)s, %(data_file_id)s, %(order)s)
                """
                params = dict(name=name, path=path, data_file_id=data_file_id, order=order)
                self.cursor.execute(sql, params)

                # Store the data preview entry id
                ids.append(self.last_insert_id())

        return ids

    def data_preview_id(self, data_file_id, order):
        """
        The id of the data preview entry for a data file and order.

        The primary key of the DataPreview entry is returned, or None if there is no
        such entry.

        Parameters
        ----------
        data_file_id
        order

        Returns
        -------
        id : int
            The data preview entry id.

        """

        sql = """
        SELECT dataPreviewId FROM DataPreview WHERE dataFileId=%(data_file_id)s AND `order`=%(order)s
        """
        params = dict(data_file_id=data_file_id, order=order)
        df = pd.read_sql(sql, con=self._ssda_connection, params=params)

        if len(df) > 0:
            return int(df['dataPreviewId'][0])
        else:
            return None

    # DataPreview ---------------------------------------------------------------- End

    # Instrument ----------------------------------------------------------------- Start

    def insert_instrument(self, data_file_id: int) -> int:
        """
        Insert the instrument details.

        The primary key column of the table must the string you get when concatenating
        the table name in lower case and 'Id'. For example, for the RSS table this
        column must be named rssId.

        The primary key of the instrument entry is returned.

        Parameters
        ----------
        data_file_id : int
            The data file id.

        Returns
        -------
        id : int
            The primary key of the instrument entry.

        """

        # Maybe the instrument entry exists already?
        existing_instrument_id = self.instrument_id(data_file_id)
        if existing_instrument_id is not None:
            return existing_instrument_id

        # Collect all the instrument details
        telescope = self.fits_data.telescope()
        instrument_details_file = self.fits_data.instrument_details_file()
        keywords = []
        columns = []
        with open(instrument_details_file, 'r') as fin:
            for line in fin:
                if line.strip() == '' or line.startswith('#'):
                    continue
                keyword, column = line.split()
                keywords.append(keyword)
                columns.append(column)

        # Construct the SQL query
        table = self.fits_data.instrument_table()
        sql = """
        INSERT INTO {table}(
                dataFileId,
                telescopeId,
                {columns}
        )
        VALUES (%(data_file_id)s, %(telescope_id)s, {values})
        """.format(table=table,
                   columns=', '.join(columns),
                   values=', '.join(['%({})s'.format(column) for column in columns]))

        # Collect the parameters
        params = dict(data_file_id=data_file_id, telescope_id=telescope.id())
        for i in range(len(keywords)):
            params[columns[i]] = self.fits_data.header.get(keywords[i])

        # Insert the instrument entry
        self.cursor.execute(sql, params)

        # Get the instrument entry id
        return self.last_insert_id()

    def instrument_id(self, data_file_id: int) -> Optional[int]:
        """
        The id for the instrument entry for a data file id.

        The primary key of the instrument entry is returned, or None if there is no such
        entry.

        Parameters
        ----------
        data_file_id : int
            The data file id.

        Returns
        -------
        id : int
            The instrument entry id.

        """

        if data_file_id is None:
            return None

        table = self.fits_data.instrument_table()
        id_column = table.lower() + 'Id'
        id_sql = 'SELECT ' + id_column + ' FROM ' + table + ' WHERE dataFileId=%s'
        id_df = pd.read_sql(id_sql, con=ssda_connect(), params=(data_file_id,))
        if len(id_df) > 0:
            return int(id_df[id_column])
        else:
            return None

# Instrument ----------------------------------------------------------------- End

    def last_insert_id(self) -> id:
        """
        Get the primary key of the last executed INSERT statement.

        Returns
        -------
        id : int
            The primary key.

        """

        id_sql = """SELECT LAST_INSERT_ID() AS lastId"""
        id_df = pd.read_sql(id_sql, con=self._ssda_connection)
        if len(id_df) == 0 or not id_df['lastId'][0]:
            raise ValueError('The id of the last executed INSERT statement is unavailable.')

        return int(id_df['lastId'])
