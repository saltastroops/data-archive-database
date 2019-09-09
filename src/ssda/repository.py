from ssda.database import DatabaseService
from ssda.observation import ObservationProperties


def insert(observation_properties: ObservationProperties, database_service: DatabaseService) -> None:
    # start the transaction
    database_service.begin_transaction()

    try:
        # insert proposal (if need be)
        proposal = observation_properties.proposal()
        if proposal:
            proposal_id = database_service.find_proposal_id(proposal_code=proposal.proposal_code, institution=proposal.institution)
            if proposal_id is None:
                # insert proposal
                proposal_id = database_service.insert_proposal(proposal)

                # insert proposal investigators
                proposal_investigators = observation_properties.proposal_investigators(proposal_id)
                for proposal_investigator in proposal_investigators:
                    database_service.insert_proposal_investigator(proposal_investigator)
        else:
            proposal_id = None

        # insert observation (if need be)
        artifact_name = observation_properties.artifact(-1).name
        observation_id = database_service.find_observation_id(artifact_name)
        if observation_id is None:
            observation = observation_properties.observation(proposal_id)
            observation_id = database_service.insert_observation(observation)
        else:
            # nothing else to do, sp the changes can be committed
            database_service.commit_transaction()
            return

        # insert target
        target = observation_properties.target(observation_id)
        database_service.insert_target(target)

        # insert instrument keyword values
        instrument_keyword_values = observation_properties.instrument_keyword_values(observation_id)
        for instrument_keyword_value in instrument_keyword_values:
            database_service.insert_instrument_keyword_value(instrument_keyword_value)

        # insert plane
        plane = observation_properties.plane(observation_id)
        plane_id = database_service.insert_plane(plane)

        # insert energy
        energy = observation_properties.energy(plane_id)
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
        database_service.insert_position(position)

        # insert artifact
        artifact = observation_properties.artifact(plane_id)
        database_service.insert_artifact(artifact)

        # commit the changes
        database_service.commit_transaction()
    except BaseException as e:
        database_service.rollback_transaction()
        raise e
