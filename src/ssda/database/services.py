from typing import NamedTuple

import ssda.database.ssda


class DatabaseServices(NamedTuple):
    ssda: ssda.database.ssda.DatabaseService
