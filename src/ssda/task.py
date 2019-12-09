from ssda.database.services import DatabaseServices
from ssda.repository import insert, delete
from ssda.salt_observation_properties import observation_property
from ssda.util.dummy import DummyObservationProperties
from ssda.util.fits import StandardFitsFile, DummyFitsFile
from ssda.util.types import TaskName, TaskExecutionMode


def execute_task(
    task_name: TaskName, fits_path: str, task_mode: TaskExecutionMode, database_services: DatabaseServices
) -> None:

    # Get the observation properties.
    if task_mode == TaskExecutionMode.PRODUCTION:
        fits_file = StandardFitsFile(fits_path)
        observation_properties = observation_property(fits_file, database_services)
    elif task_mode == TaskExecutionMode.DUMMY:
        observation_properties = DummyObservationProperties(fits_file=DummyFitsFile(fits_path))
    else:
        raise NotImplementedError

    # Execute the task
    if task_name == TaskName.INSERT:
        insert(
            observation_properties=observation_properties,
            ssda_database_service=database_services.ssda,
        )
    elif task_name == TaskName.DELETE:
        delete(
            observation_properties=observation_properties,
            database_service=database_services.ssda,
        )
    else:
        raise NotImplementedError
