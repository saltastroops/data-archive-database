from typing import cast

from ssda.database.ssda import SSDADatabaseService
from ssda.observation import ObservationProperties


def delete(
    observation_properties: ObservationProperties, database_service: SSDADatabaseService
) -> None:
    """
    Delete an observation.

    If the observation belongs to a proposal, the proposal is not deleted, irrespective
    of whether there are still observations for the proposal in the database.

    Parameters
    ----------
    observation_properties : ObservationProperties
        Observation properties.
    database_service : SSDADatabaseService
        Database service.

    """

    # find the observation
    # -1 is passed as plane id to the artifact method as the id is irrelevant
    observation_id = database_service.find_observation_id(
        observation_properties.artifact(-1).name
    )

    # only delete the observation if there actually is one
    if observation_id:
        # start the transaction
        database_service.begin_transaction()

        try:
            # delete the observation
            database_service.delete_observation(observation_id)

            # persist the changes
            database_service.commit_transaction()
        except BaseException as e:
            # undo any changes
            database_service.rollback_transaction()
            raise e


def insert(
    observation_properties: ObservationProperties,
    ssda_database_service: SSDADatabaseService,
) -> None:
    """
    Insert an observation.

    If the observation exists already, it is not inserted again, and it is not updated
    either.

    If the observation belongs to a proposal and that proposal is not in the database
    already, the proposal is inserted as well. Existing proposals are not inserted
    again, and they are not updated either.

    Parameters
    ----------
    observation_properties : ObservationProperties
        Observation properties.
    ssda_database_service : SSDADatabaseService
        Database service for accessing the database.

    """

    # start the transaction
    ssda_database_service.begin_transaction()

    try:
        # insert proposal (if need be)
        proposal = observation_properties.proposal()
        if proposal:
            proposal_id = ssda_database_service.find_proposal_id(
                proposal_code=proposal.proposal_code, institution=proposal.institution
            )
            if proposal_id is None:
                # insert proposal
                proposal_id = ssda_database_service.insert_proposal(proposal)

                # insert proposal investigators
                proposal_investigators = observation_properties.proposal_investigators(
                    proposal_id
                )
                for proposal_investigator in proposal_investigators:
                    ssda_database_service.insert_proposal_investigator(
                        proposal_investigator
                    )
        else:
            proposal_id = None

        # insert observation group (if need be)
        observation_group = observation_properties.observation_group()
        if observation_group is not None:
            group_identifier = observation_group.group_identifier
            telescope = observation_properties.observation(-1, -1).telescope
            observation_group_id = ssda_database_service.find_observation_group_id(
                cast(str, group_identifier), telescope
            )
            if observation_group_id is None:
                observation_group_id = ssda_database_service.insert_observation_group(
                    observation_group
                )
        else:
            observation_group_id = None

        # insert observation (if need be)
        # -1 is passed as plane id to the artifact method as the id is irrelevant
        artifact_name = observation_properties.artifact(-1).name
        observation_id = ssda_database_service.find_observation_id(artifact_name)
        if observation_id is None:
            observation = observation_properties.observation(
                observation_group_id=observation_group_id, proposal_id=proposal_id
            )
            observation_id = ssda_database_service.insert_observation(observation)
        else:
            # nothing else to do, so the changes can be committed
            ssda_database_service.commit_transaction()
            return

        # insert target
        target = observation_properties.target(observation_id)
        if target:
            ssda_database_service.insert_target(target)

        # insert instrument keyword values
        instrument_keyword_values = observation_properties.instrument_keyword_values(
            observation_id
        )
        for instrument_keyword_value in instrument_keyword_values:
            ssda_database_service.insert_instrument_keyword_value(
                instrument_keyword_value
            )

        # insert instrument setup
        instrument_setup = observation_properties.instrument_setup(observation_id)
        instrument_setup_id = ssda_database_service.insert_instrument_setup(
            instrument_setup
        )

        # insert instrument-specific content
        for query in instrument_setup.additional_queries:
            sql = query.sql
            parameters = {key: value for key, value in query.parameters.items()}
            parameters["instrument_setup_id"] = instrument_setup_id
            ssda_database_service.insert_instrument_specific_content(sql, parameters)

        # insert plane
        plane = observation_properties.plane(observation_id)
        plane_id = ssda_database_service.insert_plane(plane)

        # insert energy
        energy = observation_properties.energy(plane_id)
        if energy:
            ssda_database_service.insert_energy(energy)

        # insert polarization
        polarization = observation_properties.polarization(plane_id)
        if polarization:
            ssda_database_service.insert_polarization(polarization)

        # insert observation time
        observation_time = observation_properties.observation_time(plane_id)
        ssda_database_service.insert_observation_time(observation_time)

        # insert position
        position = observation_properties.position(plane_id)
        if position:
            ssda_database_service.insert_position(position)

        # insert artifact
        artifact = observation_properties.artifact(plane_id)
        ssda_database_service.insert_artifact(artifact)

        # commit the changes
        ssda_database_service.commit_transaction()
    except BaseException as e:
        ssda_database_service.rollback_transaction()
        raise e
