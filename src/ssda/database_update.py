from datetime import date, datetime, timedelta
from enum import Enum
import os
import pandas as pd
from typing import Dict, Generator, List, NamedTuple, Optional, Set

from ssda.connection import ssda_connect
from ssda.instrument.instrument import Instrument
from ssda.instrument.instrument_fits_data import InstrumentFitsData, Target
from ssda.telescope import Telescope


class UpdateAction(Enum):
    DELETE = "Delete"
    INSERT = "Insert"
    UPDATE = "Update"


def fits_data_from_date_range_gen(start_date: date, end_date: date, instruments: Set[Instrument]) -> Generator[InstrumentFitsData, None, None]:
    """
    A generator for returning InstrumentFitsData instances for a date range.

    The instances are returned ordered by date. Within a date first the instances for
    the first instrument, then those for the second instrument are returned, and so on.
    Within an instrument the instances are sorted by their file path.

    One instance is returned at a time.

    If a list of instruments is supplied, only InstrumentFitsData instances for these
    instruments are returned.

    Parameters
    ----------
    start_date : date
        The start date (inclusive).
    end_date : date
        The end date (inclusive).
    instruments : list of instruments
        Consider only these instruments.

    Returns
    -------
    generator : InstrumentFitsData instance generator
        Generator for the InstrumentFitsData instances.

    """

    # Sanity check: the date order must be correct
    if start_date > end_date:
        raise ValueError("The start date must be earlier than the end date.")

    # If no instruments are given, all instruments are considered
    if not instruments or len(instruments) == 0:
        instruments = set(Instrument)

    # Loop over all nights
    dt = timedelta(days=1)
    night = start_date
    while night <= end_date:
        # Loop over all instruments
        for instrument in instruments:
            # Loop over all FITS files for the instrument
            fits_data_class = instrument.fits_data_class()
            for fits_file in sorted(fits_data_class.fits_files(night)):
                yield fits_data_class(fits_file)
            night += dt


def fits_data_from_file_gen(fits_file: str, instrument: Instrument) -> Generator[InstrumentFitsData, None, None]:
    """
    A generator for returning an InstrumentFitsData instance for a FITS file.

    The generator yields exactly one value.

    Parameters
    ----------
    fits_file : str
        File path of the FITS file.
    instrument : Instrument
        Instrument which took the data for the FITS file.

    Returns
    -------
    generator : InstrumentFitsData instance generator
        Generator yielding one InstrumentFitsData instance.

    """

    fits_data_class = instrument.fits_data_class()
    yield fits_data_class(fits_file)


def update_database(action: UpdateAction, fits_data: InstrumentFitsData):
    """
    Perform a database update from FITS data.

    Parameters
    ----------
    action : UpdateAction
        Action to perform (insert, update or delete).
    fits_data : InstrumentFitsData
        FITS data to update the database with

    """

    if action == UpdateAction.INSERT:
        insert(fits_data)
    elif action == UpdateAction.UPDATE:
        update(fits_data)
    elif action == UpdateAction.DELETE:
        delete(fits_data)


def insert(fits_data: InstrumentFitsData) -> None:
    db_update = DatabaseUpdate(fits_data)
    try:
        # Maybe the file content been added to the database already?
        fits_base_path_length = len(os.environ["FITS_BASE_DIR"])
        path = os.path.abspath(fits_data.file_path)[fits_base_path_length:]
        sql = """
        SELECT dataFileId FROM DataFile WHERE path=%s
        """
        df = pd.read_sql(sql, con=ssda_connect(), params=(path,))
        if len(df) > 0:
            return

        # Add the FITS file content to the database
        db_update.insert_proposal()
        observation_id = db_update.insert_observation()
        target_id = db_update.insert_target()
        db_update.insert_data_file(observation_id=observation_id, target_id=target_id)
        db_update.insert_data_previews()
        db_update.insert_instrument()
        db_update.insert_proposal_investigators()

        db_update.commit()
    except Exception as e:
        db_update.rollback()
        raise e


def update(fits_data: InstrumentFitsData) -> None:
    db_update = DatabaseUpdate(fits_data)
    try:
        # Update the database from the FITS file content
        db_update.update_proposal()
        db_update.update_observation()
        target_id = db_update.update_target()
        db_update.update_data_file(target_id)
        db_update.update_data_previews()
        db_update.update_instrument()
        db_update.update_proposal_investigators()

    except Exception as e:
        db_update.rollback()
        raise e


def delete(fits_data: InstrumentFitsData) -> None:
    raise NotImplemented()


class ProposalProperties(NamedTuple):
    proposal_code: str
    pi_given_name: str
    pi_family_name: str
    proposal_title: str
    institution_id: int


class ObservationProperties(NamedTuple):
    proposal_code: str
    proposal_id: int
    telescope: Telescope
    telescope_id: int
    telescope_observation_id: str
    night: date
    observation_status_id: int


class TargetProperties(NamedTuple):
    target: Target
    target_type_id: int


class DataFileProperties(NamedTuple):
    name: str
    path: str
    start_time: datetime
    size: int
    data_category_id: int


class InstrumentProperties(NamedTuple):
    telescope_id: int
    header_values: Dict[str, str]


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
        properties = self.proposal_properties()

        if properties is None:
            return None

        # Maybe the proposal exists already?
        existing_proposal_id = self.proposal_id(properties.proposal_code)
        if existing_proposal_id is not None:
            return existing_proposal_id

        # Create the proposal
        sql = """
        INSERT INTO Proposal (proposalCode,
                              principalInvestigatorGivenName,
                              principalInvestigatorFamilyName,
                              title,
                              institutionId)
                    VALUES (%(proposal_code)s,
                            %(given_name)s,
                             %(family_name)s,
                             %(proposal_title)s,
                             %(institution_id)s)
        """
        params = dict(
            proposal_code=properties.proposal_code,
            given_name=properties.pi_given_name,
            family_name=properties.pi_family_name,
            proposal_title=properties.proposal_title,
            institution_id=properties.institution_id,
        )
        self.cursor.execute(sql, params)

        # Get the proposal id
        return self.proposal_id(properties.proposal_code)

    def update_proposal(self):
        """
        Update an existing proposal from the FITS data.

        An error if raised if the proposal does not exist already.

        The id of the updated proposal is returned.

        Returns
        -------
        id : int
            The proposal id.

        """

        # Collect the proposal properties
        properties = self.proposal_properties()

        if properties is None:
            return None

        # Check that the proposal exists already
        proposal_id = self.proposal_id(properties.proposal_code)
        if proposal_id is None:
            raise ValueError('There exists no proposal with proposal code {}'.format(properties.proposal_code))

        # Update the proposal
        sql = """
        UPDATE Proposal SET proposalCode=%(proposal_code)s,
                            principalInvestigatorGivenName=%(given_name)s,
                            principalInvestigatorFamilyName=%(family_name)s,
                            title=%(proposal_title)s,
                            institutionId=%(institution_id)s
        WHERE proposalId=%(proposal_id)s
        """
        params = dict(proposal_code=properties.proposal_code,
                      given_name=properties.pi_given_name,
                      family_name=properties.pi_family_name,
                      proposal_title=properties.proposal_title,
                      institution_id=properties.institution_id,
                      proposal_id=proposal_id)
        self.cursor.execute(sql, params)

        # Return the proposal id
        return proposal_id

    def proposal_properties(self) -> Optional[ProposalProperties]:
        """
        The proposal properties, as obtained from the FITS data.

        None is returned if the FITS data is not linked to a proposal.

        Returns
        -------
        properties : ProposalProperties
            Proposal properties.

        """

        proposal_code = self.fits_data.proposal_code()
        principal_investigator = self.fits_data.principal_investigator()
        if principal_investigator:
            given_name = principal_investigator.given_name
            family_name = principal_investigator.family_name
        else:
            given_name = None
            family_name = None
        proposal_title = self.fits_data.proposal_title()
        institution = self.fits_data.institution()

        if proposal_code is None:
            return None

        return ProposalProperties(proposal_code=proposal_code,
                                  pi_given_name=given_name,
                                  pi_family_name=family_name,
                                  proposal_title=proposal_title,
                                  institution_id=institution.id())

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
            return int(df["proposalId"][0])
        else:
            return None

    # Proposal ------------------------------------------------------------------- End

    # Observation ---------------------------------------------------------------- Start

    def insert_observation(self) -> int:
        """
        Insert the observation for FITS data into the database.

        The observation is not added again if it exists in the database already.

        The primary key of the entry in the Proposal table is returned, irrespective of
        whether the proposal has been created or existed already.

        If the inserted observation is linked to a proposal, that proposal must exist
        in the database already.

        Returns
        -------
        id : int
            Primary key of the Observation table entry.

        """

        # Collect the observation properties
        properties = self.observation_properties()

        # Consistency check: Does the proposal exist already?
        if properties.proposal_code is not None and properties.proposal_id is None:
            raise ValueError(
                "The proposal {} has not been inserted into the database yet.".format(
                    properties.proposal_code
                )
            )

        # Maybe the observation exists already?
        if properties.telescope_id and properties.telescope_observation_id:
            existing_observation_id = self.observation_id(
                properties.telescope, properties.telescope_observation_id
            )
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
        insert_params = dict(
            proposal_id=properties.proposal_id,
            telescope_id=properties.telescope_id,
            telescope_observation_id=properties.telescope_observation_id,
            night=properties.night,
            observation_status_id=properties.observation_status_id,
        )
        self.cursor.execute(insert_sql, insert_params)

        # Get the observation id
        return self.last_insert_id()

    def update_observation(self):
        """
        Update the observation for the FITS data.

        An error is raised if there exists no observation entry for the FITS data yet.

        Returns
        -------
        id : int
            The observation id.

        """

        # Get the id of the observation linked to the FITS data
        path = self.fits_file_path_for_db()
        id_sql = """
        SELECT observationId FROM DataFile WHERE path=%s
        """.format(path)
        id_df = pd.read_sql(id_sql, con=self._ssda_connection, params=(path,))
        if len(id_df) == 0:
            raise ValueError('There exists no DataFile entry for the path {}.'.format(path))
        observation_id = int(id_df['observationId'][0])

        # Collect the observation properties
        properties = self.observation_properties()

        # Update the observation
        update_sql = """
        UPDATE Observation
               SET proposalId=%(proposal_id)s,
                   telescopeId=%(telescope_id)s,
                   telescopeObservationId=%(telescope_observation_id)s,
                   night=%(night)s,
                   observationStatusId=%(observation_status_id)s
        WHERE observationId=%(observation_id)s                            
        """
        update_params = dict(
            proposal_id=properties.proposal_id,
            telescope_id=properties.telescope_id,
            telescope_observation_id=properties.telescope_observation_id,
            night=properties.night,
            observation_status_id=properties.observation_status_id,
            observation_id=observation_id
        )
        self.cursor.execute(update_sql, update_params)

        # Return the observation id
        return observation_id

    def observation_properties(self):
        """
        The observation properties, as obtained from the FITS file.

        Returns
        -------
        properties : ObservationProperties
            Observation properties,

        """

        proposal_code = self.fits_data.proposal_code()
        proposal_id = self.proposal_id(proposal_code)
        telescope = self.fits_data.telescope()
        telescope_id = telescope.id()
        telescope_observation_id = self.fits_data.telescope_observation_id()
        night = self.fits_data.night()
        observation_status_id = self.fits_data.observation_status().id()

        return ObservationProperties(proposal_code=proposal_code,
                                     proposal_id=proposal_id,
                                     telescope_id=telescope_id,
                                     telescope=telescope,
                                     telescope_observation_id=telescope_observation_id,
                                     night=night,
                                     observation_status_id=observation_status_id)

    def observation_id(
        self, telescope: Telescope, telescope_observation_id: str
    ) -> Optional[int]:
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
        params = dict(
            telescope_id=telescope.id(),
            telescope_observation_id=telescope_observation_id,
        )
        df = pd.read_sql(sql, con=self._ssda_connection, params=params)
        if len(df) > 0:
            return int(df["observationId"][0])
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
        properties = self.target_properties()

        # No properties - no target
        if properties is None:
            return

        # Insert the target
        insert_sql = """
        INSERT INTO Target(
                name,
                rightAscension,
                declination,
                position,
                targetTypeId
              )
        VALUES (%(name)s,
                %(ra)s,
                %(dec)s,
                ST_GeomFromText('POINT(%(shifted_ra)s %(dec)s)', 123456),
                %(target_type_id)s)
        """
        insert_params = dict(
            name=properties.target.name,
            ra=properties.target.ra,
            dec=properties.target.dec,
            shifted_ra=properties.target.ra - 180,
            target_type_id=properties.target_type_id,
        )
        self.cursor.execute(insert_sql, insert_params)

        # Get the target id
        return self.last_insert_id()

    def update_target(self) -> Optional[int]:
        """
        Update an existing target from FITS data.

        An error is raised if there is no DataFile entry for the FITS data in the
        database already.

        If the FITS file defines a target, but there was no target in the database yet,
        a new target entry is created.

        If the FITS file defines no target, but there is one in the database, this
        target entry is deleted.

        The id of the updated Target entry is returned, or None if no target is defined
        in the FITS data.

        Returns
        -------
        id : int
            The target id.

        """

        # Get the existing target id for the FITS data
        path = self.fits_file_path_for_db()
        id_sql = """
        SELECT targetId FROM DataFile WHERE path=%s
        """.format(path)
        id_df = pd.read_sql(id_sql, con=self._ssda_connection, params=(path,))
        if len(id_df) == 0:
            raise ValueError('There exists no DataFile entry for the path {}.'.format(path))
        target_id = id_df['targetId'][0]
        if target_id is not None:
            target_id = int(target_id)

        # Collect the target properties
        properties = self.target_properties()

        # If there was no target before, but there is one now, we have to create a new
        # target entry
        if target_id is None and properties is not None:
            return self.insert_target()

        # If there was a target before, but there is none now, we have to delete the
        # target entry.
        if target_id is not None and properties is None:
             self.delete_target()

        # If there is no target, there is nothing left to do
        if properties is None:
            return None

        # Update the target
        update_sql = """
        UPDATE Target
               SET name=%(name)s,
                   rightAscension=%(ra)s,
                   declination=%(dec)s,
                   position=ST_GeomFromText('POINT(%(shifted_ra)s %(dec)s)', 123456),
                   targetTypeId=%(target_type_id)s
        WHERE targetId=%(target_id)s
        """
        update_params = dict(name=properties.target.name,
                             ra=properties.target.ra,
                             dec=properties.target.dec,
                             shifted_ra=properties.target.ra - 180,
                             target_type_id=properties.target_type_id,
                             target_id=target_id)
        self.cursor.execute(update_sql, update_params)

        # Return the target id
        return target_id

    def delete_target(self):
        raise NotImplementedError()

    def target_properties(self) -> Optional[TargetProperties]:
        """
        The target properties, as obtained from the FITS data.

        None is returned if no target is defined in the FITS data.

        Returns
        -------
        properties : TargetProperties
            Target properties.

        """

        target = self.fits_data.target()
        if target is None:
            return None

            # Get the target type id
        if target.target_type is not None:
            target_type_id_sql = """
                      SELECT targetTypeId FROM TargetType WHERE numericValue = %s
                """
            target_type_id_df = pd.read_sql(
                sql=target_type_id_sql, con=ssda_connect(), params=(target.target_type,)
            )
            if target_type_id_df.empty:
                raise ValueError(
                    "The target type {} is not included in the TargetType table.".format(
                        target.target_type
                    )
                )
            target_type_id = int(target_type_id_df["targetTypeId"][0])
        else:
            target_type_id = None

        return TargetProperties(target=target,
                                target_type_id=target_type_id)

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
        properties = self.data_file_properties()

        # Maybe the data file exists already?
        if observation_id is not None:
            existing_data_file_id = self.data_file_id()
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
        VALUES (%(data_category_id)s,
                %(start_time)s,
                %(name)s,
                %(path)s,
                %(target_id)s,
                %(size)s,
                %(observation_id)s)
        """
        params = dict(
            data_category_id=properties.data_category_id,
            start_time=properties.start_time,
            name=properties.name,
            path=properties.path,
            target_id=target_id,
            size=properties.size,
            observation_id=observation_id,
        )
        self.cursor.execute(sql, params)

        # Get the data file id
        return self.last_insert_id()

    def update_data_file(self, target_id: Optional[int]):
        """
        Update the DataFile entry from the FITS data.

        An error is raised if the data file entry does not exist in the database yet.

        The id of the updated data file entry is returned.

        Parameters
        ----------
        target_id : int
            Target id.

        Returns
        -------
        id : int
            The data file id.

        """

        # Get the data file id
        data_file_id = self.data_file_id(True)

        # Collect the properties which might need updating
        properties = self.data_file_properties()

        # Update the data file entry
        update_sql = """
        UPDATE DataFile
               SET name=%(name)s,
                   path=%(path)s,
                   startTime=%(start_time)s,
                   size=%(size)s,
                   dataCategoryId=%(data_category_id)s,
                   targetId=%(target_id)s
        WHERE dataFileId=%(data_file_id)s
        """
        update_params = dict(name=properties.name,
                             path=properties.path,
                             start_time=properties.start_time,
                             size=properties.size,
                             data_category_id=properties.data_category_id,
                             target_id=target_id,
                             data_file_id=data_file_id)
        self.cursor.execute(update_sql, update_params)

        # Return the data file id
        return data_file_id

    def data_file_properties(self):
        """
        The data file properties, as obtained from the FITS file.

        Returns
        -------
        properties : DataFileProperties
            Data file properties.

        """

        name = os.path.basename(self.fits_data.file_path)
        path = self.fits_file_path_for_db()
        start_time = self.fits_data.start_time()
        size = self.fits_data.file_size
        data_category_id = self.fits_data.data_category().id()

        return DataFileProperties(name=name,
                                  path=path,
                                  start_time=start_time,
                                  size=size,
                                  data_category_id=data_category_id)

    def fits_file_path_for_db(self):
        """
        The file path of the FITS file, as stored in the database.

        The path stored in the database is the absolute path of the file with the base
        directory (as defined by the `FITS_BASE_DIR` environment variable.

        Returns
        -------
        path : str
            The file path of the FITS file.

        """

        base_path_length = len(os.environ["FITS_BASE_DIR"])

        return os.path.abspath(self.fits_data.file_path)[base_path_length:]

    def data_file_id(self, must_exist) -> Optional[int]:
        """
        The id of the data file for a file path.

        The primary key of the DataFile entry with the given file path is returned. None
        is returned if there exists no such entry.

        Returns
        -------
        id : int
            The data file id.
        must_exist : bool
            Whether to raise an error if no data file entry exists.

        """

        path = self.fits_file_path_for_db()
        sql = """
        SELECT dataFileId FROM DataFile WHERE path=%s
        """
        df = pd.read_sql(sql, con=self._ssda_connection, params=(path,))

        if len(df) > 0:
            return int(df["dataFileId"][0])
        else:
            if must_exist:
                raise ValueError('There exists no DataFile entry for the path {}.'.format(self.fits_data.file_path))
            return None

    # DataFile ------------------------------------------------------------------- End

    # DataPreview ---------------------------------------------------------------- Start

    def insert_data_previews(self) -> List[id]:
        """
        Insert the data preview entries for FITS data into the database.

        The preview files referenced by the data preview entries are created.

        Preview data is only created and stored in the database if the data for the FITS
        file is non-proprietary.

        """

        # Only proceed for non-proprietary data
        if self.fits_data.is_proprietary():
            return []

        # Create the preview files
        preview_files = self.fits_data.create_preview_files()

        # Enter the data for all preview files into the database
        ids = []
        for index, preview_file in enumerate(preview_files):
            # Collect the preview data
            base_dir_path_length = len(os.environ["PREVIEW_BASE_DIR"])
            name = os.path.basename(preview_file)
            path = os.path.abspath(preview_file)[base_dir_path_length:]
            order = index + 1

            # Maybe the data preview entry exists already?
            data_file_id = self.data_file_id(True)
            if not self.exists_data_preview(order):
                # It doesn't exist, so it is inserted
                sql = """
                INSERT INTO DataPreview(
                        dataFileId,
                        `order`,
                        name,
                        path
                )
                VALUES (%(data_file_id)s, %(order)s, %(name)s, %(path)s)
                """
                params = dict(
                    data_file_id=data_file_id, order=order, name=name, path=path
                )
                self.cursor.execute(sql, params)

                # Store the data preview entry id
                ids.append(self.last_insert_id())

    def update_data_previews(self):
        """
        Update existing preview files from the FITS data.

        The preview files referenced by the data preview entries are updated as well.

        An error is raised if no DataFile entry exists for the FITS data.

        """

        # Delete any existing preview data for the FITS data
        self.delete_data_previews()

        # (Re-)Insert the preview data
        self.insert_data_previews()

    def delete_data_previews(self):
        """
        Delete all DataPreview entries linked to the FITS data.

        The preview files referenced by the data preview entries are deleted as well.

        An error is raised if no DataFile entry exists for the FITS data.

        """

        # Get the id of the data file entry linked to the FITS data
        data_file_id = self.data_file_id(True)

        # Get the paths of the existing preview files for the FITS data
        existing_sql = """
        SELECT path FROM DataPreview WHERE dataFileId=%s
        """
        existing_df = pd.read_sql(existing_sql, con=self._ssda_connection, params=(data_file_id,))
        existing_paths = existing_df['path']

        # Remove the existing preview files
        for path in existing_paths:
            os.remove(os.path.join(os.environ["PREVIEW_BASE_DIR"], path.lstrip('/')))

        # Remove all preview data entries for the data file id
        delete_sql = """
        DELETE FROM DataPreview WHERE dataFileId=%s
        """
        self.cursor.execute(delete_sql, (data_file_id,))

    def exists_data_preview(self, order):
        """
        Check whether there exists a DataPreview for an order.

        The primary key of the DataPreview entry is returned, or None if there is no
        such entry.

        Parameters
        ----------
        order

        Returns
        -------
        id : int
            The data preview entry id.

        """

        data_file_id = self.data_file_id(True)

        sql = """
        SELECT dataPreviewId
               FROM DataPreview
        WHERE dataFileId=%(data_file_id)s AND `order`=%(order)s
        """
        params = dict(data_file_id=data_file_id, order=order)
        df = pd.read_sql(sql, con=self._ssda_connection, params=params)

        if len(df) > 0:
            return int(df["dataPreviewId"][0])
        else:
            return None

    # DataPreview ---------------------------------------------------------------- End

    # Instrument ----------------------------------------------------------------- Start

    def insert_instrument(self,) -> int:
        """
        Insert the instrument details.

        The primary key column of the table must the string you get when concatenating
        the table name in lower case and 'Id'. For example, for the RSS table this
        column must be named rssId.

        The primary key of the instrument entry is returned.

        Returns
        -------
        id : int
            The primary key of the instrument entry.

        """

        # Get the data file id.
        data_file_id = self.data_file_id(False)

        # Maybe the instrument entry exists already?
        existing_instrument_id = self.instrument_id()
        if existing_instrument_id is not None:
            return existing_instrument_id

        # Collect all the instrument details
        properties = self.instrument_properties()

        # Construct the SQL query
        table = self.fits_data.instrument_table()
        columns = list(properties.header_values.keys())
        sql = """
        INSERT INTO {table}(
                dataFileId,
                telescopeId,
                {columns}
        )
        VALUES (%(data_file_id)s, %(telescope_id)s, {values})
        """.format(
            table=table,
            columns=", ".join(columns),
            values=", ".join(["%({})s".format(properties.header_values[column]) for column in columns]),
        )

        # Collect the parameters
        params = dict(data_file_id=data_file_id, telescope_id=properties.telescope_id)
        for column in columns:
            params[column] = properties.header_values[column]

        # Insert the instrument entry
        self.cursor.execute(sql, params)

        # Get the instrument entry id
        return self.last_insert_id()

    def update_instrument(self):
        """
        Update the instrument entry for the FITS data.

        An error is raised if there exists no instrument entry yet.

        Returns
        -------
        id : int
            The primary key of the updated instrument entry.
        """

        # Get the data file id
        data_file_id = self.data_file_id(True)

        # Get the instrument id
        instrument_id = self.instrument_id()
        if instrument_id is None:
            raise ValueError('No instrument entry exists for the FITS file {}'.format(self.fits_data.file_path))

        # Collect all the instrument details
        properties = self.instrument_properties()

        # Construct the SQL query
        table = self.fits_data.instrument_table()
        columns = list(properties.header_values.keys())
        sql = """
        UPDATE {table}
               SET {update_set}
        WHERE {id_column}=%(instrument_id)s
        """.format(table=table, update_set=', '.join(['{column}=%({column})s'.format(column=column) for column in columns]), id_column=self.fits_data.instrument_id_column())

        # Collect the parameters
        params = dict(data_file_id=data_file_id, telescope_id=properties.telescope_id, instrument_id=instrument_id)
        for column in columns:
            params[column] = properties.header_values[column]

        # Update the instrument entry
        self.cursor.execute(sql, params)

    def instrument_id(self) -> Optional[int]:
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

        data_file_id = self.data_file_id(False)

        if data_file_id is None:
            return None

        table = self.fits_data.instrument_table()
        id_column = table.lower() + "Id"
        id_sql = "SELECT " + id_column + " FROM " + table + " WHERE dataFileId=%s"
        id_df = pd.read_sql(id_sql, con=ssda_connect(), params=(data_file_id,))
        if len(id_df) > 0:
            return int(id_df[id_column])
        else:
            return None

    def instrument_properties(self) -> InstrumentProperties:
        """
        The instrument properties, as obtained from the FITS file.

        Returns
        -------
        properties : InstrumentProperties
            Instrument properties,

        """

        telescope_id = self.fits_data.telescope().id()
        instrument_details_file = self.fits_data.instrument_details_file()
        header_values = {}
        with open(instrument_details_file, "r") as fin:
            for line in fin:
                if line.strip() == "" or line.startswith("#"):
                    continue
                keyword, column = line.split()
                header_values[column] = self.fits_data.header.get(keyword)

        return InstrumentProperties(telescope_id=telescope_id, header_values=header_values)

    # Instrument ----------------------------------------------------------------- End

    # ProposalInvestigator ------------------------------------------------------- Start

    def insert_proposal_investigators(self) -> None:
        """
        Insert the proposal investigators.

        If the FITS file is linked to a proposal, the proposal must exist in the
        database already.

        Returns
        -------

        """

        # Get the proposal id
        proposal_code = self.fits_data.proposal_code()
        proposal_id = self.proposal_id(proposal_code)

        # No proposal id - no investigators
        if proposal_id is None:
            return

        # Consistency check: Does the proposal exist already?
        if proposal_code is not None and proposal_id is None:
            raise ValueError(
                "The proposal {} has not been inserted into the database yet.".format(
                    proposal_code
                )
            )

        # Insert the investigators
        for investigator_id in self.fits_data.investigator_ids():
            # Maybe the entry exists already?
            select_sql = """
            SELECT COUNT(*) AS entryCount
                   FROM ProposalInvestigator
                   WHERE proposalId=%(proposal_id)s AND institutionUserId=%(investigator_id)s
            """
            select_params = dict(
                proposal_id=proposal_id, investigator_id=investigator_id
            )
            select_df = pd.read_sql(
                select_sql, con=self._ssda_connection, params=select_params
            )
            if int(select_df["entryCount"][0]) > 0:
                continue

            # Insert the entry
            insert_sql = """
            INSERT INTO ProposalInvestigator(
                    proposalId,
                    institutionUserId
            )
            VALUES (%(proposal_id)s, %(investigator_id)s)
            """
            insert_params = dict(
                proposal_id=proposal_id, investigator_id=investigator_id
            )
            self.cursor.execute(insert_sql, insert_params)

    def update_proposal_investigators(self):
        """
        Update the proposal investigator entries for the FITS data.

        """

        # Delete any existing investigators
        self.delete_proposal_investigators()

        # (Re-)Insert the investigators
        self.insert_proposal_investigators()

    def delete_proposal_investigators(self):
        """
        Delete the proposal investigator entries for the FITS data.

        """
        # Get the proposal id
        proposal_code = self.fits_data.proposal_code()
        proposal_id = self.proposal_id(proposal_code)

        # There are no proposal investigators if there is no proposal id
        if proposal_id is None:
            return

        # Delete the proposal investigators for the proposal id
        sql = """
        DELETE FROM ProposalInvestigator WHERE proposalId=%s
        """
        self.cursor.execute(sql, (proposal_id,))

    # ProposalInvestigator ------------------------------------------------------- End

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
        if len(id_df) == 0 or not id_df["lastId"][0]:
            raise ValueError(
                "The id of the last executed INSERT statement is unavailable."
            )

        return int(id_df["lastId"])
