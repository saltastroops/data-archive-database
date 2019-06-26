from enum import Enum
import pandas as pd

from ssda.connection import ssda_connect


class Institution(Enum):
    """
    Enumeration of the institutions.

    The values must be the same as those of the institutionName column in the
    Institution table.

    """

    SAAO = "SAAO"
    SALT = "SALT"

    def id(self) -> int:
        """
        Return the primary key opf the Institution entry for this institution.

        Returns
        -------
        id : int
            The primary key.

        """

        sql = """
        SELECT institutionId FROM Institution WHERE institutionName=%s
        """
        df = pd.read_sql(sql, con=ssda_connect(), params=(self.value,))

        return int(df["institutionId"][0])
