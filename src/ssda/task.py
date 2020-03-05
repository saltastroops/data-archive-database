from ssda.database.services import DatabaseServices
from ssda.repository import insert, delete
from ssda.salt_observation_properties import observation_properties
from ssda.util.dummy import DummyObservationProperties
from ssda.util.fits import StandardFitsFile, DummyFitsFile
from ssda.util.types import TaskName, TaskExecutionMode


def execute_task(
    task_name: TaskName,
    fits_path: str,
    task_mode: TaskExecutionMode,
    database_services: DatabaseServices,
) -> None:
    # If the FITS file already exists in the database, do nothing.
    if database_services.ssda.file_exists(fits_path):
        return

    # Get the observation properties.
    if task_mode == TaskExecutionMode.PRODUCTION:
        fits_file = StandardFitsFile(fits_path)

        _observation_properties = observation_properties(fits_file, database_services)

        # Check if the FITS file is to be ignored
        if _observation_properties.ignore_observation():
            return

    elif task_mode == TaskExecutionMode.DUMMY:
        _observation_properties = DummyObservationProperties(
            fits_file=DummyFitsFile(fits_path)
        )
    else:
        raise NotImplementedError

    # Execute the task
    if task_name == TaskName.INSERT:
        insert(
            observation_properties=_observation_properties,
            ssda_database_service=database_services.ssda,
        )
    elif task_name == TaskName.DELETE:
        delete(
            observation_properties=_observation_properties,
            database_service=database_services.ssda,
        )
    else:
        raise NotImplementedError
