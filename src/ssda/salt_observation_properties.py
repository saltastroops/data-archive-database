from ssda.database.services import DatabaseServices
from ssda.instrument.bcam_observation_properties import BcamObservationProperties
from ssda.instrument.hrs_observation_properties import HrsObservationProperties
from ssda.instrument.rss_observation_properties import RssObservationProperties
from ssda.instrument.salticam_observation_properties import SalticamObservationProperties
from ssda.observation import ObservationProperties
from ssda.util import types
from ssda.util.fits import FitsFile


def observation_properties(
    fits_file: FitsFile, database_services: DatabaseServices
) -> ObservationProperties:
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

        if fits_file.instrument() == types.Instrument.BCAM:
            return BcamObservationProperties(fits_file, database_services.sdb)

        raise ValueError(
            f"Unknown instrument for file {fits_file.file_path()}: { fits_file.instrument()}"
        )
    raise ValueError(
        f"Unknown telescope for file {fits_file.file_path()}: {fits_file.telescope()}"
    )
