from ssda.database.services import DatabaseServices
from ssda.repository import insert, delete
from ssda.salt_observation_properties import observation_properties
from ssda.util.dummy import DummyObservationProperties
from ssda.util.fits import StandardFitsFile, DummyFitsFile
from ssda.util.types import TaskName, TaskExecutionMode, Status


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
        proposal_id = fits_file.header_value("PROPID")
        # If the FITS file is junk, do not store its data.
        if proposal_id == "JUNK":
            return
        # Do not store engineering data.
        if "ENG" in proposal_id:
            return
        
        observation_date = fits_file.header_value("DATE-OBS")
        # If the FITS header does not include the observation date, do not store its data.
        if not observation_date:
            return

        block_visit_id = (
            None
            if not fits_file.header_value("BVISITID")
            else int(fits_file.header_value("BVISITID"))
        )

        # Observations not belonging to a proposal are accepted by default.
        status = (
            Status.ACCEPTED
            if not block_visit_id
            else database_services.sdb.find_observation_status(block_visit_id)
        )

        if status == Status.DELETED or status == Status.INQUEUE:
            return

        _observation_properties = observation_properties(fits_file, database_services)
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
