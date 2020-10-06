import dsnparse
from ssda.database.sdb import SaltDatabaseService
from ssda.database.services import DatabaseServices
from ssda.database.ssda import SSDADatabaseService
from ssda.util.types import DatabaseConfiguration


def ssda_configuration() -> DatabaseConfiguration:
    ssda_db_config = dsnparse.parse_environ("SSDA_DSN")
    return DatabaseConfiguration(
        username=ssda_db_config.user,
        password=ssda_db_config.secret,
        host=ssda_db_config.host,
        port=ssda_db_config.port,
        database=ssda_db_config.database,
    )


def sdb_configuration() -> DatabaseConfiguration:
    sdb_db_config = dsnparse.parse_environ("SDB_DSN")
    return DatabaseConfiguration(
        username=sdb_db_config.user,
        password=sdb_db_config.secret,
        host=sdb_db_config.host,
        port=3306,
        database=sdb_db_config.database,
    )


def database_services() -> DatabaseServices:
    ssda_db_config = ssda_configuration()
    sdb_db_config = sdb_configuration()
    ssda_database_service = SSDADatabaseService(ssda_db_config)
    sdb_database_service = SaltDatabaseService(sdb_db_config)

    return DatabaseServices(ssda=ssda_database_service, sdb=sdb_database_service)
