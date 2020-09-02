import logging
from datetime import date, datetime, timedelta
from typing import cast, Any, Dict, Optional, List
import os

import astropy.units as u
from psycopg2 import connect

from ssda.util import types
from ssda.util.fits import get_fits_base_dir
from ssda.util.setup_logger import setup_logger

info_log = setup_logger(
    "info_logger",
    "ssda_sync_info.log",
    logging.Formatter("%(asctime)s %(levelname)s - %(message)s"),
)


class SSDADatabaseService:
    """
    Access to the database.

    """

    def __init__(self, database_config: types.DatabaseConfiguration):
        self._connection = connect(
            user=database_config.username(),
            password=database_config.password(),
            host=database_config.host(),
            port=database_config.port(),
            database=database_config.database(),
        )

    def begin_transaction(self) -> None:
        """
        Start a transaction.

        """

        # PostgreSQL automatically starts a transaction, so there is nothing to do
        pass

    def commit_transaction(self) -> None:
        """
        Commit the current transaction.

        """

        self._connection.commit()

    def connection(self) -> connect:
        return self._connection

    def delete_observation(self, observation_id: int) -> None:
        """
        Delete an observation.

        Parameters
        ----------
        observation_id : int
            Database id of the observation to delete.

        """

        with self._connection.cursor() as cur:
            sql = """
            DELETE FROM observation WHERE observation_id=%(observation_id)s
            """

            cur.execute(sql, dict(observation_id=observation_id))

    def find_observation_group_id(
        self, group_identifier: str, telescope: types.Telescope
    ) -> Optional[int]:
        """
        Find the database id of an observation group.

        Parameters
        ----------
        group_identifier : str
            Identifier for the observation group.
        telescope : Telescope
            Telescope used for the observations in the group.

        Returns
        -------
        Optional[int]
            The database id for the observation group, or None if there is no observation
            group in the database for the group identifier and telescope.

        """

        with self._connection.cursor() as cur:
            sql = """
            SELECT observations.observation.observation_group_id
            FROM observations.observation_group
            JOIN observations.observation ON observations.observation_group.observation_group_id=
            observations.observation.observation_group_id
            JOIN observations.telescope ON observations.observation.telescope_id = observations.telescope.telescope_id
            WHERE observations.observation_group.group_identifier=%(group_identifier)s AND observations.telescope.name=%(telescope)s
            """
            cur.execute(
                sql, dict(group_identifier=group_identifier, telescope=telescope.value)
            )

            observation_group_id = cur.fetchone()
            if observation_group_id:
                return cast(int, observation_group_id[0])
            else:
                return None

    def find_observation_id(self, artifact_name: str) -> Optional[int]:
        """
        Find the database id of an observation.

        Parameters
        ----------
        artifact_name : str
            Name of an artifact for the observation.

        Returns
        -------
        Optional[int]
            The database id of the observation, or None if there is no observation for
            the artifact name.

        """

        with self._connection.cursor() as cur:
            sql = """
            SELECT observations.observation.observation_id
            FROM observations.observation
            JOIN observations.plane ON observations.observation.observation_id = observations.plane.observation_id
            JOIN observations.artifact ON observations.plane.plane_id = observations.artifact.plane_id
            WHERE observations.artifact.name=%(artifact_name)s
            """
            cur.execute(sql, dict(artifact_name=artifact_name))

            observation_id = cur.fetchone()
            if observation_id:
                return cast(int, observation_id[0])
            else:
                return None

    def find_owner_institution_user_ids(
        self, plane_id: int, proposal_id: Optional[int]
    ) -> Optional[List[int]]:
        """
        Find the database institution user id values of the institution users who own the data related to the position.
        If the data is public (or the proposal id is None), None is returned.

        Parameters
        ----------
        plane_id : int
            Id of the plane to which the position belongs.
        proposal_id: Optional[int]
            Database proposal id

        Returns
        -------
        Optional[List[int]]
            The database id of institution users who own the data, or None if the data is public.

        """

        if proposal_id is None:
            return None

        # Released data is owned by nobody
        data_release = self._find_data_release_date_for_plane(plane_id)
        if data_release <= datetime.now().date():
            return None

        with self._connection.cursor() as cur:
            sql = """
                SELECT array_agg(institution_user_id)
                FROM proposal_investigator
                WHERE proposal_id=%(proposal_id)s
                """
            cur.execute(sql, dict(proposal_id=proposal_id))
            result = cur.fetchone()

            # Proposals without an investigator are deemed public. An example of this
            # are gravitational wave proposals for SALT.
            return result[0] if len(result[0]) else None

    def find_proposal_investigator_user_ids(
        self, proposal_code: str, institution: types.Institution
    ) -> List[str]:
        with self._connection.cursor() as cur:
            sql = """
SELECT user_id
FROM admin.institution_user
    JOIN admin.proposal_investigator ON institution_user.institution_user_id=proposal_investigator.institution_user_id
    JOIN observations.proposal ON proposal_investigator .proposal_id = proposal.proposal_id
    JOIN observations.institution ON proposal.institution_id = institution.institution_id
WHERE proposal_code=%(proposal_code)s AND name=%(institution)s
            """
            cur.execute(
                sql, dict(proposal_code=proposal_code, institution=institution.value)
            )
            results = cur.fetchall()
            return [str(result[0]) for result in results] if results else []

    def find_salt_proposal_details(self) -> Dict[str, types.SALTProposalDetails]:
        """
        Find proposal details.

        Returns
        -------
        Optional[SALTProposalDetails]
            The proposal details, or None if there is no proposal for the
            proposal code abd institution.
        """

        institution = types.Institution.SALT

        with self._connection.cursor() as cur:
            sql = """
SELECT proposal_code, pi, title
FROM observations.proposal
    JOIN observations.institution ON proposal.institution_id = institution.institution_id
WHERE name=%(institution)s
               """
            cur.execute(sql, dict(institution=institution.value))
            results = cur.fetchall()
            salt_proposals = dict()
            for proposal in results:
                proposal_code = proposal[0]
                release_date = self.find_salt_proposal_release_date(
                    proposal_code=proposal_code
                )
                investigators = self.find_proposal_investigator_user_ids(
                    proposal_code=proposal_code, institution=institution
                )
                salt_proposals[proposal_code] = types.SALTProposalDetails(
                    pi=proposal[1],
                    meta_release=release_date[1],
                    data_release=release_date[0],
                    proposal_code=proposal_code,
                    title=proposal[2],
                    institution=institution,
                    investigators=investigators,
                )
            return salt_proposals

    def find_salt_proposal_release_date(self, proposal_code: str) -> (date, date):
        with self._connection.cursor() as cur:
            sql = """
SELECT DISTINCT data_release, meta_release
FROM observation
    JOIN proposal ON observation.proposal_id = proposal.proposal_id
    JOIN observations.institution ON proposal.institution_id = institution.institution_id
WHERE proposal_code=%(proposal_code)s AND name=%(institution)s
            """
            cur.execute(
                sql,
                dict(
                    proposal_code=proposal_code,
                    institution=types.Institution.SALT.value,
                ),
            )
            return cur.fetchone()

    def _find_data_release_date_for_plane(self, plane_id) -> date:
        """
        Find the release date for the data of a plane.

        Parameters
        ----------
        plane_id : int
            Plane id.

        Returns
        -------
        date
            Release date
        """
        with self._connection.cursor() as cur:
            sql = """
                SELECT observation.data_release
                FROM observation
                JOIN plane ON observation.observation_id = plane.observation_id
                WHERE plane.plane_id=%(plane_id)s;
                """
            cur.execute(sql, dict(plane_id=plane_id))
            result = cur.fetchone()
            return cast(date, result[0])

    def find_proposal_id(
        self, proposal_code: str, institution: types.Institution
    ) -> Optional[int]:
        """
        Find the database id of a proposal.

        Parameters
        ----------
        proposal_code : str
            Proposal code.
        institution
            Institution to which the proposal was submitted.

        Returns
        -------
        Optional[int]
            The database id of the proposal, or None if there is no proposal for the
            proposal code abd institution.

        """

        with self._connection.cursor() as cur:
            sql = """
            SELECT proposal_id
            FROM observations.proposal
            JOIN observations.institution ON proposal.institution_id = institution.institution_id
            WHERE proposal_code=%(proposal_code)s AND name=%(institution)s
            """
            cur.execute(
                sql, dict(proposal_code=proposal_code, institution=institution.value)
            )
            result = cur.fetchone()
            if result:
                return cast(int, result[0])
            else:
                return None

    def find_observation_ids(self, start_date: date, end_date: date) -> List[int]:
        """
        The observation ids that are observed in a date range. The start date and the end date are inclusive.

        Parameters
        ----------
        start_date: date
            Start date.
        end_date: date
            End date.

        Returns
        -------
        The observation ids.

        """
        with self._connection.cursor() as cur:
            sql = """
SELECT observations.observation.observation_id
FROM observations.observation
    JOIN observations.plane ON observations.observation.observation_id = observations.plane.observation_id
    JOIN observations.observation_time ON observations.plane.plane_id = observations.observation_time.plane_id
WHERE night >= %(start_date)s AND night <= %(end_date)s
            """
            cur.execute(sql, dict(start=start_date, end=end_date))

            observation_ids = cur.fetchall()
            return [cast(int, obs[0]) for obs in observation_ids]

    def find_salt_observation_group(
        self, proposal_code: str
    ) -> Dict[str, types.SALTObservationGroup]:
        """
        Find an observation group.

        Parameters
        ----------
        proposal_code : str
            Proposal code.

        Returns
        -------
        Optional[types.SALTObservationGroup]
            The observation groups for the proposal.

        """

        with self._connection.cursor() as cur:
            sql = """
WITH tel(telescope_id) AS(
    SELECT telescope_id FROM telescope WHERE name = %(telescope)s
)
SELECT DISTINCT
    group_identifier, status
FROM observations.observation
    JOIN observations.proposal ON proposal.proposal_id = observation.proposal_id
    JOIN observations.status ON status.status_id = observation.status_id
    JOIN observations.observation_group ON observation_group.observation_group_id = observation.observation_group_id
WHERE proposal_code=%(proposal_code)s AND telescope_id = (SELECT telescope_id FROM tel)
            """
            cur.execute(
                sql,
                dict(proposal_code=proposal_code, telescope=types.Telescope.SALT.value),
            )
            results = cur.fetchall()

            og = dict()
            for result in results:
                group_identifier = result[0]
                og[group_identifier] = types.SALTObservationGroup(
                    status=types.Status.for_value(result[1]),
                    group_identifier=group_identifier,
                )

            return og

    def file_exists(self, path: str) -> bool:
        """
        Check if the FITS file already exists.

        Parameters
        ----------
        path : str
            FITS file path.

        Returns
        -------
        bool

        """

        with self._connection.cursor() as cur:
            sql = """
            SELECT EXISTS(SELECT 1 FROM observations.artifact WHERE (paths).raw=%(path)s);
            """
            cur.execute(sql, dict(path=os.path.relpath(path, get_fits_base_dir())))
            return cur.fetchone()[0]

    def insert_proposal_access_rule(
        self, proposal_id: int, access_rule: Optional[types.AccessRule]
    ):
        if not access_rule:
            return

        with self._connection.cursor() as cur:
            sql = """
            WITH ar (id) AS (
                SELECT access_rule_id
                FROM admin.access_rule
                WHERE access_rule=%(access_rule)s
            )
            INSERT INTO admin.proposal_access_rule (proposal_id, access_rule_id)
            VALUES (%(proposal_id)s, (SELECT id FROM ar));
            """
            cur.execute(
                sql, dict(proposal_id=proposal_id, access_rule=access_rule.value)
            )

    def insert_artifact(self, artifact: types.Artifact) -> int:
        """
        Insert an artifact.

        Parameters
        ----------
        artifact : Artifact
            Artifact.

        Returns
        -------
        int
            Database id of the inserted artifact.

        """

        with self._connection.cursor() as cur:
            sql = """
            WITH pt (product_type_id) AS (
                SELECT product_type_id
                FROM observations.product_type
                WHERE product_type.product_type=%(product_type)s
            )
            INSERT INTO observations.artifact (content_checksum,
                                  content_length,
                                  identifier,
                                  name,
                                  paths,
                                  plane_id,
                                  product_type_id)
            VALUES (%(content_checksum)s,
                    %(content_length)s,
                    %(identifier)s,
                    %(name)s,
                    %(paths)s,
                    %(plane_id)s,
                    (SELECT product_type_id FROM pt))
            RETURNING artifact_id
            """

            cur.execute(
                sql,
                dict(
                    content_checksum=artifact.content_checksum,
                    content_length=artifact.content_length.to_value(types.byte),
                    identifier=str(artifact.identifier),
                    name=artifact.name,
                    paths=(str(artifact.paths.raw), str(artifact.paths.reduced)),
                    plane_id=artifact.plane_id,
                    product_type=artifact.product_type.value,
                ),
            )

            return cast(int, cur.fetchone()[0])

    def insert_energy(self, energy: Optional[types.Energy]) -> Optional[int]:
        """
        Insert spectral details.

        Nothing is done and None is returned if None is passed as the energy argument.

        Parameters
        ----------
        energy : Optional[Energy]
            Spectral details.

        Returns
        -------
        Optional[int]
            Database id of the inserted spectral details, or None if None is passed as
            energy argument.

        """

        if not energy:
            return None

        with self._connection.cursor() as cur:
            sql = """
            INSERT INTO observations.energy (dimension,
                                max_wavelength,
                                min_wavelength,
                                plane_id,
                                resolving_power,
                                sample_size)
            VALUES (%(dimension)s,
                   %(max_wavelength)s,
                   %(min_wavelength)s,
                   %(plane_id)s,
                   %(resolving_power)s,
                   %(sample_size)s)
            RETURNING energy_id
            """

            cur.execute(
                sql,
                dict(
                    dimension=energy.dimension,
                    max_wavelength=energy.max_wavelength.to_value(u.meter),
                    min_wavelength=energy.min_wavelength.to_value(u.meter),
                    plane_id=energy.plane_id,
                    resolving_power=energy.resolving_power,
                    sample_size=energy.sample_size.to_value(u.meter),
                ),
            )

            return cast(int, cur.fetchone()[0])

    def delete_institution_memberships(self, institution_user_id: int):
        """
        Delete the membership details of an institution user.

        Parameters
        ----------
        institution_user_id : int
            Institution user id.

        """

        sql = """
        DELETE FROM admin.institution_membership
        WHERE institution_user_id=%(institution_user_id)s
        """

        with self._connection.cursor() as cur:
            cur.execute(sql, dict(institution_user_id=institution_user_id))

    def insert_institution_memberships(
        self,
        institution_user_id: int,
        institution_memberships: List[types.InstitutionMembership],
    ):
        """
        Insert membership details for an institution user.

        Parameters
        ----------
        institution_user_id : int
            Institution user id.
        institution_memberships : List[InstitutionMembership]
            Membership details.

        """

        sql = """
        INSERT INTO institution_membership (institution_user_id, membership_end, membership_start)
        VALUES (%(institution_user_id)s, %(membership_end)s, %(membership_start)s)
        """

        with self._connection.cursor() as cur:
            for institution_membership in institution_memberships:
                cur.execute(
                    sql,
                    dict(
                        institution_user_id=institution_user_id,
                        membership_end=institution_membership.membership_end,
                        membership_start=institution_membership.membership_start,
                    ),
                )

    def update_institution_memberships(
        self,
        institution_user_id: int,
        institution_memberships: List[types.InstitutionMembership],
    ):
        """
        Update the membership details of an institution user.

        Existing membershiop details are replaced with the new ones.

        Parameters
        ----------
        institution_user_id : int
            Institution user id.
        institution_memberships : List[InstitutionMembership]
            Membership details.

        """

        self.delete_institution_memberships(institution_user_id)
        self.insert_institution_memberships(
            institution_user_id, institution_memberships
        )

    def insert_institution_user(
        self, user_id: str, institution: types.Institution
    ) -> int:
        """
        Insert an institution user in the database if the institution user does not exist
        and return the new database institution user id.
        If the institution user already exist, the database institution user id is retrieved.

        Parameters
        ----------
        institution: Institution
            Institution to which the user belongs.
        user_id : str
            Unique identifier used by the institution for the user.

        Returns
        -------
        int
            Database id of the institution user.

        """

        with self._connection.cursor() as cur:
            # Insert the institution user (if they don't exist yet).
            # It is safe to assume that ssda_user_id is NULL for a new institution user;
            # a non-NULL value would mean that the institution user exists already, as
            # it would have been created during registration.
            sql = """
            WITH inst (institution_id) AS (
                SELECT institution_id FROM observations.institution WHERE name=%(institution)s
            )
            INSERT INTO admin.institution_user (institution_id, user_id)
            VALUES ((SELECT institution_id FROM inst), %(user_id)s)
            ON CONFLICT (user_id, institution_id)
            DO NOTHING
            RETURNING institution_user_id
            """

            cur.execute(sql, dict(institution=institution.value, user_id=user_id))

            result = cur.fetchone()
            if result:
                return cast(int, result[0])
            else:
                sql = """
                WITH inst (institution_id) AS (
                    SELECT institution_id FROM observations.institution WHERE name=%(institution)s
                )
                SELECT institution_user_id FROM admin.institution_user
                WHERE institution_id=(SELECT institution_id FROM inst) AND user_id=%(user_id)s
                """

                cur.execute(sql, dict(institution=institution.value, user_id=user_id))

                result = cur.fetchone()

                return cast(int, result[0])

    def insert_instrument_keyword_value(
        self, instrument_keyword_value: types.InstrumentKeywordValue
    ) -> None:
        """
        Insert an instrument keyword value.

        Parameters
        ----------
        instrument_keyword_value : InstrumentKeywordValue
            Instrument keyword value.

        Returns
        -------
        int
            Database id of the inserted instrument keyword value.

        """

        with self._connection.cursor() as cur:
            sql = """
            WITH instr (instrument_id) AS (
                SELECT instrument_id FROM observations.instrument WHERE name=%(instrument)s
            ),
            ik (instrument_keyword_id) AS (
                SELECT instrument_keyword_id
                FROM observations.instrument_keyword
                WHERE keyword=%(keyword)s
            )
            INSERT INTO observations.instrument_keyword_value (instrument_id,
                                                  instrument_keyword_id,
                                                  observation_id,
                                                  value)
            VALUES ((SELECT instrument_id FROM instr),
                    (SELECT instrument_keyword_id FROM ik),
                    %(observation_id)s,
                    %(value)s)
            """
            cur.execute(
                sql,
                dict(
                    instrument=instrument_keyword_value.instrument.value,
                    keyword=instrument_keyword_value.instrument_keyword.value,
                    observation_id=instrument_keyword_value.observation_id,
                    value=instrument_keyword_value.value,
                ),
            )

    def insert_instrument_setup(self, instrument_setup: types.InstrumentSetup) -> int:
        """
        Insert an instrument setup.

        Parameters
        ----------
        instrument_setup : InstrumentSetup
            Instrument setup.

        Returns
        -------
        int
            The database id of the inserted instrument setup.

        """

        with self._connection.cursor() as cur:
            sql = """
            WITH d (id) AS (
                SELECT detector_mode_id FROM observations.detector_mode
                WHERE detector_mode.detector_mode=%(detector_mode)s
            ),
            f (id) AS (
                SELECT filter_id FROM observations.filter WHERE name=%(filter)s
            ),
            im (id) AS (
                SELECT instrument_mode_id FROM observations.instrument_mode
                WHERE instrument_mode.instrument_mode=%(instrument_mode)s
            )
            INSERT INTO observations.instrument_setup (detector_mode_id,
                                          filter_id,
                                          instrument_mode_id,
                                          observation_id)
            VALUES ((SELECT id FROM d),
                   (SELECT id FROM f),
                   (SELECT id FROM im),
                   %(observation_id)s)
            RETURNING instrument_setup_id
            """

            cur.execute(
                sql,
                dict(
                    detector_mode=instrument_setup.detector_mode.value,
                    filter=instrument_setup.filter.value
                    if instrument_setup.filter
                    else None,
                    instrument_mode=instrument_setup.instrument_mode.value,
                    observation_id=instrument_setup.observation_id,
                ),
            )

            return cast(int, cur.fetchone()[0])

    def insert_instrument_specific_content(
        self, sql: str, parameters: Dict[str, Any]
    ) -> None:
        """
        Insert instrument-specific content.

        The method executes the given SQL statement with the supplied query parameters.

        Parameters
        ----------
        sql : str
            SQL statement to execute.
        parameters : Dict[str, any]
            Query parameters.

        """

        with self._connection.cursor() as cur:
            cur.execute(sql, parameters)

    def insert_observation(self, observation: types.Observation) -> int:
        """
        Insert an observation.

        Parameters
        ----------
        observation : Observation
            Observation.

        Returns
        -------
        int
            The database id of the inserted observation.

        """

        with self._connection.cursor() as cur:
            sql = """
            WITH instr (instrument_id) AS (
                SELECT instrument_id FROM observations.instrument WHERE name=%(instrument)s
            ),
            i (intent_id) AS (
                SELECT intent_id FROM observations.intent WHERE observations.intent.intent=%(intent)s
            ),
            st (status_id) AS (
                SELECT status_id FROM observations.status WHERE observations.status.status=%(status)s
            ),
            tel (telescope_id) AS (
                SELECT telescope_id FROM observations.telescope WHERE name=%(telescope)s
            )
            INSERT INTO observations.observation (data_release,
                                     instrument_id,
                                     intent_id,
                                     meta_release,
                                     observation_group_id,
                                     proposal_id,
                                     status_id,
                                     telescope_id)
            VALUES (
                %(data_release)s,
                (SELECT instrument_id FROM instr),
                (SELECT intent_id FROM i),
                %(meta_release)s,
                %(observation_group_id)s,
                %(proposal_id)s,
                (SELECT status_id FROM st),
                (SELECT telescope_id FROM tel)
            )
            RETURNING observation.observation_id
            """

            cur.execute(
                sql,
                dict(
                    data_release=observation.data_release,
                    instrument=observation.instrument.value,
                    intent=observation.intent.value,
                    meta_release=observation.meta_release,
                    observation_group_id=observation.observation_group_id,
                    proposal_id=observation.proposal_id,
                    status=observation.status.value,
                    telescope=observation.telescope.value,
                ),
            )

            return cast(int, cur.fetchone()[0])

    def insert_observation_group(
        self, observation_group: types.ObservationGroup
    ) -> int:
        """
        Insert an observation group.

        Parameters
        ----------
        observation_group : ObservationGroup
            Observation group.

        Returns
        -------
        The database id of the inserted observation group.

        """

        with self._connection.cursor() as cur:
            sql = """
            INSERT INTO observations.observation_group (group_identifier,
                                           name)
            VALUES (%(group_identifier)s,
                    %(name)s)
            RETURNING observation_group_id
            """

            cur.execute(
                sql,
                dict(
                    group_identifier=observation_group.group_identifier,
                    name=observation_group.name,
                ),
            )

            return cast(int, cur.fetchone()[0])

    def insert_observation_time(self, observation_time: types.ObservationTime) -> int:
        """
        Insert an observation time.

        Parameters
        ----------
        observation_time : ObservationTime
            Observation time.

        Returns
        -------
        The database id of the inserted observation time.

        """

        with self._connection.cursor() as cur:
            sql = """
            INSERT INTO observations.observation_time (end_time,
                                          exposure_time,
                                          night,
                                          plane_id,
                                          resolution,
                                          start_time)
            VALUES (%(end_time)s,
                    %(exposure_time)s,
                    %(night)s,
                    %(plane_id)s,
                    %(resolution)s,
                    %(start_time)s)
            RETURNING observation_time_id
            """

            cur.execute(
                sql,
                dict(
                    end_time=observation_time.end_time,
                    exposure_time=observation_time.exposure_time.to_value(u.second),
                    night=(observation_time.start_time - timedelta(hours=12)).date(),
                    plane_id=observation_time.plane_id,
                    resolution=observation_time.resolution.to_value(u.second),
                    start_time=observation_time.start_time,
                ),
            )

            return cast(int, cur.fetchone()[0])

    def insert_plane(self, plane: types.Plane) -> int:
        """
        Insert a plane.

        Parameters
        ----------
        plane : Plane
            Plane.

        Returns
        -------
        int
            The database id of the inserted plane.

        """

        with self._connection.cursor() as cur:
            sql = """
            WITH dpt (data_product_type_id) AS (
                SELECT data_product_type_id
                FROM observations.data_product_type
                WHERE product_type=%(data_product_type)s
            )
            INSERT INTO observations.plane (data_product_type_id, observation_id)
            VALUES ((SELECT data_product_type_id FROM dpt),
                    %(observation_id)s)
            RETURNING plane_id
            """

            cur.execute(
                sql,
                dict(
                    observation_id=plane.observation_id,
                    data_product_type=plane.data_product_type.value,
                ),
            )

            return cast(int, cur.fetchone()[0])

    def insert_polarization(self, polarization: types.Polarization) -> None:
        """
        Insert a polarization.

        Parameters
        ----------
        polarization : Polarization
            Polarization.

        Returns
        -------
        The database id of the inserted polarization.

        """

        with self._connection.cursor() as cur:
            sql = """
            WITH pp (polarization_mode_id) AS (
                SELECT polarization_mode_id
                FROM observations.polarization_mode
                WHERE polarization_mode.name=%(pattern)s
            )
            INSERT INTO observations.polarization (plane_id, polarization_mode_id)
            VALUES (%(plane_id)s, (SELECT polarization_mode_id FROM pp))
            """

            cur.execute(
                sql,
                dict(
                    plane_id=polarization.plane_id,
                    pattern=polarization.polarization_mode.value,
                ),
            )

    def insert_position(
        self, position: types.Position, proposal_id: Optional[int]
    ) -> int:
        """
        Inert a position.

        Parameters
        ----------
        position : Position
            Position.
        proposal_id: Optional[int]
            Database proposal id

        Returns
        -------
        int
            The database id of the inserted position.

        """

        owner_institution_user_ids = self.find_owner_institution_user_ids(
            position.plane_id, proposal_id
        )

        with self._connection.cursor() as cur:
            sql = """
            INSERT INTO observations.position (dec, equinox, owner_institution_user_ids, plane_id, ra)
            VALUES (%(dec)s, %(equinox)s, %(owner_institution_user_ids)s, %(plane_id)s, %(ra)s)
            RETURNING position_id
            """

            cur.execute(
                sql,
                dict(
                    dec=position.dec.to_value(u.degree),
                    equinox=position.equinox,
                    owner_institution_user_ids=owner_institution_user_ids,
                    plane_id=position.plane_id,
                    ra=position.ra.to_value(u.degree),
                ),
            )

            return cast(int, cur.fetchone()[0])

    def insert_proposal(self, proposal: types.Proposal) -> int:
        """
        Insert a proposal.

        Parameters
        ----------
        proposal : proposal
            Proposal.

        Returns
        -------
        int
            The database id of the inserted proposal.

        """

        with self._connection.cursor() as cur:
            sql = """
            WITH inst (institution_id) AS (
                SELECT institution_id FROM observations.institution WHERE name=%(institution)s
            ),
            pt (proposal_type_id) AS (
                SELECT proposal_type_id FROM observations.proposal_type WHERE proposal_type=%(proposal_type)s
            )
            INSERT INTO observations.proposal (institution_id, pi, proposal_code, proposal_type_id, title)
            VALUES (
                (SELECT institution_id FROM inst),
                %(pi)s,
                %(proposal_code)s,
                (SELECT proposal_type_id FROM pt),
                %(title)s
            )
            RETURNING proposal_id
            """
            cur.execute(
                sql,
                dict(
                    institution=proposal.institution.value,
                    pi=proposal.pi,
                    proposal_code=proposal.proposal_code,
                    proposal_type=proposal.proposal_type.value,
                    title=proposal.title,
                ),
            )

            return cast(int, cur.fetchone()[0])

    def insert_proposal_investigator(
        self, proposal_investigator: types.ProposalInvestigator
    ) -> None:
        """
        Insert a proposal investigator.
        Parameters
        ----------
        proposal_investigator : ProposalInvestigator
            Proposal investigator.
        """

        # insert institution user if not exist
        institution_user_id = self.insert_institution_user(
            proposal_investigator.investigator_id, proposal_investigator.institution
        )

        # update membership details
        self.update_institution_memberships(
            institution_user_id, proposal_investigator.institution_memberships
        )

        with self._connection.cursor() as cur:
            sql = """
            INSERT INTO admin.proposal_investigator (institution_user_id, proposal_id)
            VALUES (%(institution_user_id)s, %(proposal_id)s)
            """

            cur.execute(
                sql,
                dict(
                    institution_user_id=institution_user_id,
                    proposal_id=proposal_investigator.proposal_id,
                ),
            )

    def insert_target(self, target: types.Target) -> int:
        """
        Insert a target.

        Parameters
        ----------
        target : Target
            Target.

        Returns
        -------
        int
            The database id of the inserted target.

        """

        with self._connection.cursor() as cur:
            sql = """
            WITH tt (target_type_id) AS (
                SELECT target_type_id FROM observations.target_type WHERE numeric_code=%(numeric_code)s
            )
            INSERT INTO observations.target (name, observation_id, standard, target_type_id)
            VALUES (%(name)s,
                    %(observation_id)s,
                    %(standard)s,
                    (SELECT tt.target_type_id FROM tt))
            RETURNING target_id
            """

            cur.execute(
                sql,
                dict(
                    name=target.name,
                    observation_id=target.observation_id,
                    standard=target.standard,
                    numeric_code=target.target_type,
                ),
            )

            return cast(int, cur.fetchone()[0])

    def update_investigators(
        self,
        proposal_code: str,
        institution: types.Institution,
        proposal_investigators: List[types.ProposalInvestigator],
    ):
        """
        Update the investigators for a proposal. Existing investigators are deleted.
        Parameters
        ----------
        proposal_code : str
            Proposal code.
        institution : Institution
            Institution.
        proposal_investigators : List[ProposalInvestiogator]
            New proposal investigators.
        """

        with self._connection.cursor() as cur:
            sql = """
WITH prop_id (proposal_id) AS (
    SELECT proposal_id
    FROM proposal
        JOIN institution on proposal.institution_id = institution.institution_id
    WHERE proposal_code=%(proposal_code)s AND name=%(institution)s
)
DELETE FROM admin.proposal_investigator
WHERE proposal_id = (SELECT proposal_id FROM prop_id)
            """
            cur.execute(
                sql, dict(proposal_code=proposal_code, institution=institution.value)
            )
            proposal_investigators_str = ""
            for proposal_investigator in proposal_investigators:
                self.insert_proposal_investigator(
                    proposal_investigator=proposal_investigator
                )
                proposal_investigators_str += (
                    proposal_investigator.investigator_id + ", "
                )
            info_log.info(
                msg=f"The investigator ids for {proposal_code} have been changed to "
                f"{proposal_investigators_str[:-2] + '.'}"
            )

    def update_observation_group_status(
        self, group_identifier: str, status: types.Status, telescope: types.Telescope
    ) -> None:
        """
        Update the status of all observations in an observation group.
        Parameters
        ----------
        group_identifier : str
            Identifier for the observation group.
        status : Status
            New status.
        telescope : Telescope
            Telescope used for observing the group.
        """

        with self._connection.cursor() as cur:
            sql = """
WITH
    obs_id (observation_group_id) AS (
        SELECT DISTINCT observation_group.observation_group_id FROM observation_group
            JOIN observation ON observation_group.observation_group_id=observation.observation_group_id
            JOIN telescope ON observation.telescope_id = telescope.telescope_id
        WHERE group_identifier=%(group_identifier)s AND telescope.name=%(telescope)s
    ),
    stat (status_id) AS (
        SELECT status_id
        FROM observations.status
        WHERE status=%(status)s
    )
UPDATE observation
SET status_id=(SELECT status_id FROM stat)
WHERE observation_group_id=(SELECT observation_group_id FROM obs_id)
            """
            cur.execute(
                sql,
                dict(
                    group_identifier=group_identifier,
                    status=status.value,
                    telescope=telescope.value,
                ),
            )
            info_log.info(
                msg=f"The status of block visit id {group_identifier} has changed to {status.value}"
            )

    def update_pi(self, proposal_id: int, pi: str) -> None:
        """
        Update the PI for a SALT proposal.
        Parameters
        ----------
        proposal_id: int
            SSDA proposal id.
        pi: str
            The PI's name
        """

        with self._connection.cursor() as cur:
            sql = """
                UPDATE proposal
                    SET pi=%(pi)s
                WHERE proposal_id=%(proposal_id)s
            """
            cur.execute(sql, dict(proposal_id=proposal_id, pi=pi))

    def update_proposal_title(self, proposal_id: int, title: str) -> None:
        """
        Update the PI for a SALT proposal.
        Parameters
        ----------
        proposal_id: int
            SSDA proposal id.
        title: str
            The title of a proposal.
        """

        with self._connection.cursor() as cur:
            sql = """
                UPDATE proposal
                    SET title=%(title)s
                WHERE proposal_id=%(proposal_id)s
            """
            cur.execute(sql, dict(proposal_id=proposal_id, title=title))

    def update_proposal_release_date(
        self, proposal_id: int, release_dates: types.ReleaseDates
    ) -> None:
        with self._connection.cursor() as cur:
            sql = """
UPDATE observation
SET
    meta_release=%(meta_release_date)s,
    data_release=%(data_release_date)s
WHERE proposal_id=%(proposal_id)s
                    """
            cur.execute(
                sql,
                dict(
                    data_release_date=release_dates.data_release,
                    meta_release_date=release_dates.meta_release,
                    proposal_id=proposal_id,
                ),
            )

    def rollback_transaction(self) -> None:
        """
        Roll back the changes made during the current transaction.

        """

        self._connection.rollback()
