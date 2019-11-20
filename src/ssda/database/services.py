from typing import NamedTuple

from ssda.database.ssda import SSDADatabaseService
from ssda.database.sdb import SaltDatabaseService



class DatabaseServices(NamedTuple):
    sdb: SaltDatabaseService
    ssda: SSDADatabaseService
