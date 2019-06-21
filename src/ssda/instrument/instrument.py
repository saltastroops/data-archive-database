from enum import Enum
from typing import Type

from ssda.instrument.instrument_fits_data import InstrumentFitsData
from ssda.instrument.rss.rss_fits_data import RssFitsData


class Instrument(Enum):
    RSS = "RSS"

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
        else:
            raise ValueError('No InstrumentFitsData type found for {}'.format(self.value))

