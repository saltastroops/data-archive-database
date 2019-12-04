from ssda.database.services import DatabaseServices
from ssda.instrument.hrs_observation_properties import HrsObservationProperties
from ssda.instrument.rss_observation_properties import RssObservationProperties
from ssda.instrument.salticam_observation_properties import SalticamObservationProperties
from ssda.observation import ObservationProperties
from ssda.repository import insert, delete
from ssda.util import types
from ssda.util.dummy import DummyObservationProperties
from ssda.util.fits import StandardFitsFile, DummyFitsFile, FitsFile
from ssda.util.types import TaskName, TaskExecutionMode


def observation_property(fits_file: FitsFile, database_services: DatabaseServices) -> ObservationProperties:
    """
    It determines which observation properties to use for thw fits file

    Parameters
    ----------
    fits_file: FitsFile
        A Fits file
    database_services: DatabaseServices
        The database services

    Returns
    -------
    ObservationProperties
        The observation properties

    """

    if fits_file.telescope() == types.Telescope.SALT:
        if fits_file.instrument() == types.Instrument.RSS:
            return RssObservationProperties(fits_file, database_services.sdb)

        if fits_file.instrument() == types.Instrument.HRS:
            return HrsObservationProperties(fits_file, database_services.sdb)

        if fits_file.instrument() == types.Instrument.SALTICAM:
            return SalticamObservationProperties(fits_file, database_services.sdb)
    raise ValueError(f"Unknown telescope for file {fits_file.file_path()}")


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
