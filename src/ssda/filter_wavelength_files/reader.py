import os
from typing import Optional, List, Tuple, Iterable

from ssda.util import types


class ReadInstrumentWavelength:
    def __init__(self, filter_name: Optional[str] = None, instrument: Optional[types.Instrument] = None, resolution: Optional[str] = None):
        self._filter_name = filter_name
        self._instrument = instrument
        self._resolution = resolution

    def wavelengths_and_transmissions(self) -> List[Tuple[float, float]]:
        wavelength = []
        filter_name = self._filter_name
        if not self._instrument or not self._filter_name:
            raise ValueError("Filter name and instrument must be provided to use this method")
        if self._instrument.value.lower() == 'salticam':
            if self._filter_name == 'Halpha-S1':
                filter_name = 'H-alpha'
            if self._filter_name == 'SDSSr-S1':
                filter_name = 'SDSS_rp'

        with open(f'{os.environ["PATH_TO_WAVELENGTH_FILES"]}/{self._instrument.value.lower()}/{filter_name}.txt', 'r') \
                as file:
            for line in file.readlines():
                la = line.split()
                if len(la) and not (la[0] == "!" or la[0] == "#"):
                    wavelength.append((float(la[0]), float(la[1])))
        return wavelength

    def fp_hwfm(self) -> List[Tuple[str, float, float]]:
        if not self._resolution:
            raise ValueError("Resolution must be provided to use this method")
        fp_modes = []
        with open(f'{os.environ["PATH_TO_WAVELENGTH_FILES"]}/rss/properties_of_fp_modes.txt', 'r') as file:
            for line in file.readlines():
                fp = line.split()
                if len(fp) > 7 and fp[0] in ["TF", "LR", "MR", "HR"]:
                    fp_modes.append(
                        (
                            fp[0],          # Mode
                            float(fp[2]),   # wavelength,
                            float(fp[3])    # fwhm,
                        )
                    )
        reso = 'LR' if (self._resolution.lower() == "low resolution") else \
            'MR' if (self._resolution.lower() == "medium resolution") else \
            'HR' if (self._resolution.lower() == "high resolution") else \
            'TF' if (self._resolution.lower() == "frame transfer") else None

        if not reso:
            raise ValueError("Resolution not found for fabry perot")

        return [x for x in fp_modes if x[0].upper() == reso]

