from abc import ABC

from ssda.database import DatabaseService
from ssda.observation import StandardObservationProperties, ObservationProperties
from ssda.util.dummy import DummyObservationProperties
from ssda.repository import delete, insert
from ssda.util.fits import DummyFitsFile, StandardFitsFile
from ssda.util.types import TaskName, TaskExecutionMode


def execute_task(
    task_name: TaskName,
    fits_path: str,
    task_mode: TaskExecutionMode,
    database_service: DatabaseService,
) -> None:
    # Get the observation properties.
    if task_mode == TaskExecutionMode.PRODUCTION:
        fits_file = StandardFitsFile(fits_path)
        observation_properties: ObservationProperties = StandardObservationProperties(
            fits_file
        )
    elif task_mode == TaskExecutionMode.DUMMY:
        fits_file = DummyFitsFile(fits_path)
        observation_properties = DummyObservationProperties(fits_file)
    else:
        raise NotImplementedError

    # Execute the task
    if task_name == TaskName.INSERT:
        insert(
            observation_properties=observation_properties,
            database_service=database_service,
        )
    elif task_name == TaskName.DELETE:
        delete(
            observation_properties=observation_properties,
            database_service=database_service,
        )
    else:
        raise NotImplementedError
