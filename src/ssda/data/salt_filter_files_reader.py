import os
from typing import List, Tuple


def _filter_name(_filter: str) -> str:
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
    raise _filter


def wavelengths_and_transmissions(filter_name, instrument) -> List[Tuple[float, float]]:
    wavelengths = []
    filt_name = filter_name
    if not instrument or not filter_name:
        raise ValueError("Filter name and instrument must be provided to use this method")
    if instrument.value.lower() == 'salticam':
        filt_name = _filter_name(filter_name)

    with open(f'{os.environ["PATH_TO_WAVELENGTH_FILES"]}/{instrument.value.lower()}/{filt_name}.txt', 'r') \
            as file:
        for line in file.readlines():
            if len(line.split()) and not line.split()[0].startswith("!") and not line.split()[0].startswith("#"):
                wavelengths.append((float(line.split()[0]), float(line.split()[1])))
    return wavelengths


def fp_hwfm(resolution) -> List[Tuple[str, float, float]]:
    if not resolution:
        raise ValueError("A resolution must be provided to use this method")
    fp_modes = []
    with open(f'{os.environ["PATH_TO_WAVELENGTH_FILES"]}/rss/properties_of_fp_modes.txt', 'r') as file:
        for line in file.readlines():
            if len(line.split()) and not line.split()[0].startswith("!") and not line.split()[0].startswith("#"):
                if len(line.split()) > 7 and line.split()[0] in ["TF", "LR", "MR", "HR"]:
                    fp_modes.append(
                        (
                            line.split()[0],          # Mode
                            float(line.split()[2]),   # wavelength,
                            float(line.split()[3])    # fwhm,
                        )
                    )

    if resolution.lower() == "low resolution":
        reso = 'LR'
    elif resolution.lower() == "medium resolution":
        reso = 'MR'
    elif resolution.lower() == "high resolution":
        reso = 'HR'
    elif resolution.lower() == "frame transfer":
        reso = "TF"
    else:
        reso = None

    if not reso:
        raise ValueError(f"Resolution {resolution} not found for fabry perot")

    return [x for x in fp_modes if x[0].upper() == reso]
