import os
from pathlib import Path
from typing import List, Tuple

from astropy.units import Quantity
from ssda.util import types
from astropy import units as u

dirname = os.path.dirname(__file__)


def _parse_filter_name(_filter: str, instrument: types.Instrument) -> str:
    if instrument.value == "Salticam" or instrument.value == "BCAM":
        if _filter == "Halpha-S1" or _filter == "H-alpha":
            return "H-alpha"
        if _filter == "SDSSr-S1" or _filter.replace("'", "") == "SDSS-r":
            return "SDSS_rp"
        if _filter == "SDSSi-S1" or _filter.replace("'", "") == "SDSS-i":
            return "SDSS_ip"
        if _filter == "SDSSg-S1" or _filter.replace("'", "") == "SDSS-g":
            return "SDSS_gp"
        if _filter == "SDSSu-S1" or _filter.replace("'", "") == "SDSS-u":
            return "SDSS_up"
        if _filter == "SDSSz-S1" or _filter.replace("'", "") == "SDSS-z":
            return "SDSS_zp"
        if _filter == "CLR-S1":
            return "Fused_silica_clear"
        if _filter == "B-S1":
            return "Johnson_B"
        if _filter == "U-S1":
            return "Johnson_U"
        if _filter == "I-S1":
            return "Cousins_I"
        if _filter == "R-S1":
            return "Cousins_R"
        if _filter == "380-40":
            return "380nm_40nm_FWHM"
        if _filter == "Su-S1":
            return "Stroemgren_u"
        if _filter == "V-S1":
            return "Johnson_V"
        if _filter == "Sv-S1":
            return "Stroemgren_v"
        if _filter == "Sb-S1":
            return "Stroemgren_b"
        if _filter == "Sy-S1":
            return "Stroemgren_y"
    return _filter


def wavelengths_and_transmissions(
    filter_name: str, instrument: types.Instrument
) -> List[Tuple[Quantity, float]]:
    wavelengths = []
    filt_name = _parse_filter_name(filter_name, instrument)
    if not instrument or not filter_name:
        raise ValueError(
            "Filter name and instrument must be provided to use this method"
        )
    instrument_path_name = instrument.value.lower()
    if instrument_path_name == "bcam":
        instrument_path_name = "salticam"  # No filters for bcam it uses salticam'
    if instrument_path_name == "rss":
        filepath = Path(f"{dirname}/{instrument_path_name}/{filt_name}.txt")
        # Rss may use a Salticam filter.
        # If a Salticam filter is used, read the filter from the Salticam filters.
        if not filepath.exists():
            instrument_path_name = "salticam"

    filename = f"{dirname}/{instrument_path_name}/{filt_name}.txt"
    with open(filename, "r") as file:
        for line in file.readlines():

            if (
                len(line.split()) == 2
                and not line.startswith("!")
                and not line.startswith("#")
            ):
                wavelengths.append(
                    (float(line.split()[0]) * u.angstrom, float(line.split()[1]))
                )
    return wavelengths


def fp_fwhm(rss_fp_mode: types.RSSFabryPerotMode) -> List[Tuple[Quantity, Quantity]]:
    """
    The list of wavelength-transmission pairs for an HRS mode.

    The list items are not guaranteed to be sorted.

    Parameters
    ----------
    rss_fp_mode

    Returns TODO need finish this
    ----------

    """
    if not rss_fp_mode:
        raise ValueError("A resolution must be provided to use this method")

    fp_modes = []
    filename = os.path.join(dirname, "rss/properties_of_fp_modes.txt")
    with open(filename, "r") as file:
        for line in file.readlines():
            if line and not line.startswith("!") and not line.startswith("#"):
                if len(line.split()) > 7 and line.split()[0] in [
                    "TF",
                    "LR",
                    "MR",
                    "HR",
                ]:
                    if (
                        types.RSSFabryPerotMode.parse_fp_mode(line.split()[0])
                        == rss_fp_mode
                    ):  # Resolution
                        fp_modes.append(
                            (
                                float(line.split()[2]) * u.nm,  # wavelength,
                                float(line.split()[3]) * u.nm,  # fwhm,
                            )
                        )

    return fp_modes
