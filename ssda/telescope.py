import pandas as pd
from enum import Enum

from ssda.connection import ssda_connect


class Telescope(Enum):
    """
    Enumeration of the telescopes included in the SSDA.

    The enum values must be the same as the telescope names in the Telescope table.

    """

    LESEDI = "LESEDI"
    ONE_DOT_NINE = "1.9 m"
    SALT = "SALT"

    def id(self) -> int:
        """
        The id for this telescope in the SSDA's Telescope table.

        Returns
        -------
        id : int
            The id.

        """

        sql = """
            SELECT telescopeId from Telescope where telescopeName =%s
        """

        df = pd.read_sql(sql, con=ssda_connect(), params=(self.value,))

        if df.empty:
            raise ValueError("Unknown telescope name: {}".format(self.value))

        return int(df["telescopeId"][0])
