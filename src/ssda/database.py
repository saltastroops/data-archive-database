from typing import cast, Optional

import astropy.units as u
import psycopg2
from psycopg2 import connect

from ssda.util import types


class DatabaseService:
    """
    Access to the database.

    """

    def __init__(self, connection: psycopg2.extensions.connection):
        self._connection = connection

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
            FROM proposal
            JOIN institution ON proposal.institution_id = institution.institution_id
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
                                  path,
                                  plane_id,
                                  product_type_id)
            VALUES (%(content_checksum)s,
                    %(content_length)s,
                    %(identifier)s,
                    %(name)s,
                    %(path)s,
                    %(plane_id)s,
                    (SELECT product_type_id FROM pt))
            RETURNING artifact_id
            """

            cur.execute(
                sql,
                dict(
                    content_checksum=artifact.content_checksum,
                    content_length=artifact.content_length.to_value(types.byte),
                    identifier=artifact.identifier,
                    name=artifact.name,
                    path=artifact.path,
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
                                     observation_group, 
                                     observation_type_id,
                                     proposal_id,
                                     status_id,
                                     telescope_id)
            VALUES (
                %(data_release)s,
                (SELECT instrument_id FROM instr),
                (SELECT intent_id FROM i),
                %(meta_release)s,
                %(observation_group)s,
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
                    observation_group=observation.observation_group,
                    observation_type=observation.observation_type.value,
                    proposal_id=observation.proposal_id,
                    status=observation.status.value,
                    telescope=observation.telescope.value,
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
                                          plane_id,
                                          resolution,
                                          start_time)
            VALUES (%(end_time)s,
                    %(exposure_time)s,
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

    def insert_polarization(self, polarization: types.Polarization) -> int:
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
            WITH sp (stokes_parameter_id) AS (
                SELECT stokes_parameter_id
                FROM stokes_parameter
                WHERE stokes_parameter.stokes_parameter=%(stokes_parameter)s
            )
            INSERT INTO polarization (plane_id, stokes_parameter_id)
            VALUES (%(plane_id)s, (SELECT stokes_parameter_id FROM sp))
            RETURNING polarization_id
            """

            cur.execute(
                sql,
                dict(
                    plane_id=polarization.plane_id,
                    stokes_parameter=polarization.stokes_parameter.value,
                ),
            )

            return cast(int, cur.fetchone()[0])

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
                SELECT institution_id FROM institution WHERE name=%(institution)s
            )
            INSERT INTO proposal (institution_id, pi, proposal_code, title)
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
    ) -> int:
        """
        Insert a proposal investigator.

        Parameters
        ----------
        proposal_investigator : ProposalInvestigator
            Proposal investigator.

        Returns
        -------
        int
            The database id of the inserted proposal investigator.

        """

        pass

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
