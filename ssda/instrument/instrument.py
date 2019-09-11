from enum import Enum
import pandas as pd
from typing import Type

from ssda.connection import ssda_connect
from ssda.instrument.instrument_fits_data import InstrumentFitsData
from ssda.instrument.rss.rss_fits_data import RssFitsData
from ssda.instrument.hrs.hrs_fits_data import HrsFitsData
from ssda.instrument.salticam.salticam_fits_data import SalticamFitsData


class Instrument(Enum):
    """
    Enumeration of the instruments.

    The enum values must be the same as the values of the instrumentName column in the
    Instrument table.

    """

    RSS = "RSS"
    HRS = "HRS"
    SALTICAM = "Salticam"

    def fits_data_class(self) -> Type[InstrumentFitsData]:
        """
        The type to use for creating FITS data access instances for this instrument.

        Note that a type is returned, so that you still have to call the constructor to
        get an InstrumentFitsData. For example:

        night = datetime.date(2019, 6, 18)

        fits_data_class = Instrument.RSS.fits_data_class()
        fits_data = fits_data_class(night)
        print(fits_data.fits_files())

        Returns
        -------
        fits_data_type : type
            InstrumentFitsData type.

        """
        if self == Instrument.RSS:
            return RssFitsData
        if self == Instrument.HRS:
            return HrsFitsData
        if self == Instrument.SALTICAM:
            return SalticamFitsData
        else:
            raise ValueError(
                "No InstrumentFitsData type found for {}".format(self.value)
            )

    def id(self) -> int:
        """
        The id of the instrument used for taking the data.

        This is the instrumentId value in the Instrument table and should not be
        confused with ids from any iof the instrument setup tables (such RSS or HRS).

        Returns
        -------
        id : int
            The instrument id.

        """

        sql = """
        SELECT instrumentId FROM Instrument WHERE instrumentName=%s
        """
        df = pd.read_sql(sql, con=ssda_connect(), params=(self.value,))

        if len(df) > 0:
            return int(df["instrumentId"][0])
        else:
            raise ValueError(
                "There is no database entry for the instrument {}.".format(self.value)
            )
