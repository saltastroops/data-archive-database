import pandas as pd
from enum import Enum

from connection import ssda_connect


class ObservationStatus(Enum):
    """
    An enumeration of the possible observation status values.

    The enum values must be the same as the status values in the SSDA's
    ObservationStatus table.

    """

    ACCEPTED = "Accepted"
    REJECTED = "Rejected"

    def id(self) -> int:
        """
        The id for this observation status in the SSDA's ObservationStatus table.

        Returns
        -------
        id : int
            The id.

        """

        sql = """
        SELECT observationStatusId FROM ObservationStatus WHERE status=%s
        """

        df = pd.read_sql(sql, con=ssda_connect(), params=(self.value,))

        if df.empty:
            raise ValueError("Unknown observation status value")

        return int(df["observationStatusId"][0])
