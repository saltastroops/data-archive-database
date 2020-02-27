import json
from typing import cast, Any, Dict, Optional
import os

import astropy.units as u
import psycopg2
from psycopg2 import connect

from ssda.util import types
from ssda.util.fits import get_fits_base_dir


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
            SELECT observation.observation_group_id
            FROM observation_group
            JOIN observation ON observation_group.observation_group_id=observation.observation_group_id
            JOIN telescope ON observation.telescope_id = telescope.telescope_id
            WHERE observation_group.group_identifier=%(group_identifier)s AND telescope.name=%(telescope)s
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
            SELECT observation.observation_id
            FROM observation
            JOIN plane ON observation.observation_id = plane.observation_id
            JOIN artifact ON plane.plane_id = artifact.plane_id
            WHERE artifact.name=%(artifact_name)s
            """
            cur.execute(sql, dict(artifact_name=artifact_name))

            observation_id = cur.fetchone()
            if observation_id:
                return cast(int, observation_id[0])
            else:
                return None

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
                FROM product_type
                WHERE product_type.product_type=%(product_type)s
            )
            INSERT INTO artifact (content_checksum,
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
            INSERT INTO energy (dimension,
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
                SELECT instrument_id FROM instrument WHERE name=%(instrument)s
            ),
            ik (instrument_keyword_id) AS (
                SELECT instrument_keyword_id
                FROM instrument_keyword
                WHERE keyword=%(keyword)s
            )
            INSERT INTO instrument_keyword_value (instrument_id,
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
                SELECT detector_mode_id FROM detector_mode
                WHERE detector_mode.detector_mode=%(detector_mode)s
            ),
            f (id) AS (
                SELECT filter_id FROM filter WHERE name=%(filter)s
            ),
            im (id) AS (
                SELECT instrument_mode_id FROM instrument_mode
                WHERE instrument_mode.instrument_mode=%(instrument_mode)s
            )
            INSERT INTO instrument_setup (detector_mode_id,
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
                SELECT instrument_id FROM instrument WHERE name=%(instrument)s
            ),
            i (intent_id) AS (
                SELECT intent_id FROM intent WHERE intent.intent=%(intent)s
            ),
            ot (observation_type_id) AS (
                SELECT observation_type_id
                FROM observation_type
                WHERE observation_type.observation_type=%(observation_type)s
            ),
            st (status_id) AS (
                SELECT status_id FROM status WHERE status.status=%(status)s
            ),
            tel (telescope_id) AS (
                SELECT telescope_id FROM telescope WHERE name=%(telescope)s
            )
            INSERT INTO observation (data_release,
                                     instrument_id,
                                     intent_id,
                                     meta_release,
                                     observation_group_id, 
                                     observation_type_id,
                                     proposal_id,
                                     status_id,
                                     telescope_id)
            VALUES (
                %(data_release)s,
                (SELECT instrument_id FROM instr),
                (SELECT intent_id FROM i),
                %(meta_release)s,
                %(observation_group_id)s,
                (SELECT observation_type_id FROM ot),
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
                    observation_type=observation.observation_type.value,
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
            INSERT INTO observation_group (group_identifier,
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
            INSERT INTO observation_time (end_time,
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
                    night=observation_time.start_time.date(),
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
                FROM data_product_type
                WHERE product_type=%(data_product_type)s
            )
            INSERT INTO plane (data_product_type_id, observation_id)
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
                FROM polarization_mode
                WHERE polarization_mode.name=%(pattern)s
            )
            INSERT INTO polarization (plane_id, polarization_mode_id)
            VALUES (%(plane_id)s, (SELECT polarization_mode_id FROM pp))
            """

            cur.execute(
                sql,
                dict(
                    plane_id=polarization.plane_id,
                    pattern=polarization.polarization_mode.value,
                ),
            )

    def insert_position(self, position: types.Position) -> int:
        """
        Inert a position.

        Parameters
        ----------
        position : Position
            Position.

        Returns
        -------
        int
            The database id of the inserted position.

        """

        with self._connection.cursor() as cur:
            sql = """
            INSERT INTO position (dec, equinox, plane_id, ra)
            VALUES (%(dec)s, %(equinox)s, %(plane_id)s, %(ra)s)
            RETURNING position_id
            """

            cur.execute(
                sql,
                dict(
                    dec=position.dec.to_value(u.degree),
                    equinox=position.equinox,
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
            )
            INSERT INTO observations.proposal (institution_id, pi, proposal_code, title)
            VALUES (
                (SELECT institution_id FROM inst),
                %(pi)s,
                %(proposal_code)s,
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

        with self._connection.cursor() as cur:
            sql = """
            INSERT INTO admin.proposal_investigator (institution_user_id, proposal_id)
            VALUES (%(user_id)s, %(proposal_id)s)
            """

            cur.execute(
                sql,
                dict(
                    user_id=proposal_investigator.investigator_id,
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
                SELECT target_type_id FROM target_type WHERE numeric_code=%(numeric_code)s
            )
            INSERT INTO Target (name, observation_id, standard, target_type_id)
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

    def rollback_transaction(self) -> None:
        """
        Roll back the changes made during the current transaction.

        """

        self._connection.rollback()
