from ssda.database.ssda import DatabaseService
from ssda.observation import ObservationProperties


def delete(
    observation_properties: ObservationProperties, database_service: DatabaseService
) -> None:
    """
    Delete an observation.

    If the observation belongs to a proposal, the proposal is not deleted, irrespective
    of whet

    Parameters
    ----------
    observation_properties
    database_service

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
    observation_properties: ObservationProperties, database_service: DatabaseService
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
    database_service : DatabaseService
        Database service for accessing the database.

    """

    # start the transaction
    database_service.begin_transaction()

    try:
        # insert proposal (if need be)
        proposal = observation_properties.proposal()
        if proposal:
            proposal_id = database_service.find_proposal_id(
                proposal_code=proposal.proposal_code, institution=proposal.institution
            )
            if proposal_id is None:
                # insert proposal
                proposal_id = database_service.insert_proposal(proposal)

                # insert proposal investigators
                proposal_investigators = observation_properties.proposal_investigators(
                    proposal_id
                )
                for proposal_investigator in proposal_investigators:
                    database_service.insert_proposal_investigator(proposal_investigator)
        else:
            proposal_id = None

        # insert observation (if need be)
        # -1 is passed as plane id to the artifact method as the id is irrelevant
        artifact_name = observation_properties.artifact(-1).name
        observation_id = database_service.find_observation_id(artifact_name)
        if observation_id is None:
            observation = observation_properties.observation(proposal_id)
            observation_id = database_service.insert_observation(observation)
        else:
            # nothing else to do, so the changes can be committed
            database_service.commit_transaction()
            return

        # insert target
        target = observation_properties.target(observation_id)
        if target:
            database_service.insert_target(target)

        # insert instrument keyword values
        instrument_keyword_values = observation_properties.instrument_keyword_values(
            observation_id
        )
        for instrument_keyword_value in instrument_keyword_values:
            database_service.insert_instrument_keyword_value(instrument_keyword_value)

        # insert plane
        plane = observation_properties.plane(observation_id)
        plane_id = database_service.insert_plane(plane)

        # insert energy
        energy = observation_properties.energy(plane_id)
        if energy:
            database_service.insert_energy(energy)

        # insert polarizations
        polarizations = observation_properties.polarizations(plane_id)
        for polarization in polarizations:
            database_service.insert_polarization(polarization)

        # insert observation time
        observation_time = observation_properties.observation_time(plane_id)
        database_service.insert_observation_time(observation_time)

        # insert position
        position = observation_properties.position(plane_id)
        if position:
            database_service.insert_position(position)

        # insert artifact
        artifact = observation_properties.artifact(plane_id)
        database_service.insert_artifact(artifact)

        # commit the changes
        database_service.commit_transaction()
    except BaseException as e:
        database_service.rollback_transaction()
        raise e
