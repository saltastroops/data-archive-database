import os
from typing import List, Tuple

from astropy.units import Quantity
from ssda.util import types
from astropy import units as u

dirname = os.path.dirname(__file__)


def _parse_filter_name(_filter: str, instrument: types.Instrument) -> str:
    if instrument.value == "Salticam":
        if _filter == 'Halpha-S1':
            return 'H-alpha'
        if _filter == 'SDSSr-S1':
            return 'SDSS_rp'
        if _filter == 'SDSSi-S1':
            return 'SDSS_ip'
        if _filter == 'SDSSg-S1':
            return 'SDSS_gp'
        if _filter == 'SDSSu-S1':
            return 'SDSS_up'
        if _filter == 'SDSSz-S1':
            return 'SDSS_zp'
        if _filter == 'CLR-S1':
            return 'Fused_silica_clear'
    return _filter


def wavelengths_and_transmissions(filter_name: str, instrument: types.Instrument) -> List[Tuple[Quantity, float]]:
    wavelengths = []
    filt_name = _parse_filter_name(filter_name, instrument)
    if not instrument or not filter_name:
        raise ValueError("Filter name and instrument must be provided to use this method")
    filename = os.path.join(dirname, f"{instrument.value.lower()}/{filt_name}.txt")
    with open(filename, 'r') \
            as file:
        for line in file.readlines():

            if len(line.split()) == 2 and not line.startswith("!") and not line.startswith("#"):
                wavelengths.append((float(line.split()[0]) * u.angstrom, float(line.split()[1])))
    return wavelengths


def fp_fwhm(rss_fp_mode: types.RSSFabryPerotMode) -> List[Tuple[Quantity, Quantity]]:
    """
    The list of wavelength-transmission pairs for an HRS mode.

    The list items are not guaranteed to be sorted.

    Parameters
    ----------
    rss_fp_mode

    Returns TODO need finish this
    -------

    """
    def _parse_fp_mode(fp_mode_abbr: str) -> types.RSSFabryPerotMode:
        if fp_mode_abbr.upper() == "LR":
            return types.RSSFabryPerotMode.LOW_RESOLUTION
        if fp_mode_abbr.upper() == "MR":
            return types.RSSFabryPerotMode.MEDIUM_RESOLUTION
        if fp_mode_abbr.upper() == "HR":
            return types.RSSFabryPerotMode.HIGH_RESOLUTION
        if fp_mode_abbr.upper() == "TF":
            return types.RSSFabryPerotMode.TUNABLE_FILTER
        raise ValueError(f"Mode {fp_mode_abbr} is not known.")

    if not rss_fp_mode:
        raise ValueError("A resolution must be provided to use this method")

    fp_modes = []
    filename = os.path.join(dirname,"rss/properties_of_fp_modes.txt")
    with open(filename, 'r') as file:
        for line in file.readlines():
            if line and not line.startswith("!") and not line.startswith("#"):
                if len(line.split()) > 7 and line.split()[0] in ["TF", "LR", "MR", "HR"]:
                    if _parse_fp_mode(line.split()[0]) == rss_fp_mode:  # Resolution
                        fp_modes.append((
                            float(line.split()[2]) * u.nm,   # wavelength,
                            float(line.split()[3]) * u.nm    # fwhm,
                        ))

    return fp_modes
