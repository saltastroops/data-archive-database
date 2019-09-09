from abc import ABC

from ssda.database import DatabaseService
from ssda.observation import StandardObservationProperties, DummyObservationProperties, \
    ObservationProperties
from ssda.repository import insert
from ssda.util.fits import StandardFitsFile
from ssda.util.types import TaskName, TaskExecutionMode


def execute_task(
    task_name: TaskName, fits_path: str, task_mode: TaskExecutionMode
) -> None:
    # Get the database service.
    database_service = DatabaseService(None)

    # Get the observation properties.
    if task_mode == TaskExecutionMode.PRODUCTION:
        fits_file = StandardFitsFile(fits_path)
        observation_properties: ObservationProperties = StandardObservationProperties(fits_file)
    elif task_name == TaskName.INSERT:
        observation_properties = DummyObservationProperties()
    else:
        raise NotImplementedError

    # Execute the task
    if task_name == TaskName.INSERT:
        insert(observation_properties=observation_properties, database_service=database_service)
    elif task_name == TaskName.DELETE:
        raise NotImplementedError
    else:
        raise NotImplementedError

