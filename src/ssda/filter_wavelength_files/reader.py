import os

from ssda.util import types


class ReadInstrumentWavelength:
    def __init__(self, filter_name: str = None, instrument: types.Instrument = None, resolution: str = None):
        self._filter_name = filter_name
        self._instrument = instrument
        self._resolution = resolution

    @property
    def wavelengths_and_transmissions(self) -> list:
        wavelength = []
        if not self._instrument.lower() or not self._filter_name:
            raise ValueError("filter name and instrument must be provided to use this method")
        with open(f'{os.environ["PATH_TO_WAVELENGTH_FILES"]}/{self._instrument.lower()}/{self._filter_name}.txt', 'r') \
                as file:
            for line in file.readlines():
                la = line.split()
                if len(la) and not (la[0] == "!" or la[0] == "#"):
                    wavelength.append((float(la[0]), float(la[1])))
        return wavelength

