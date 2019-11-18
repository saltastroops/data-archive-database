import os
from typing import List, Tuple


def _filter_name(_filter: str) -> str:
    fn = _filter
    if _filter == 'Halpha-S1':
        fn = 'H-alpha'
    if _filter == 'SDSSr-S1':
        fn = 'SDSS_rp'
    if _filter == 'SDSSi-S1':
        fn = 'SDSS_ip'
    if _filter == 'SDSSg-S1':
        fn = 'SDSS_gp'
    if _filter == 'SDSSu-S1':
        fn = 'SDSS_up'
    if _filter == 'SDSSz-S1':
        fn = 'SDSS_zp'
    if _filter == 'CLR-S1':
        fn = 'Fused_silica_clear'
    return fn


def wavelengths_and_transmissions(filter_name_, instrument_) -> List[Tuple[float, float]]:
    wavelength = []
    filter_name = filter_name_
    if not instrument_ or not filter_name_:
        raise ValueError("Filter name and instrument must be provided to use this method")
    if instrument_.value.lower() == 'salticam':
        filter_name = _filter_name(filter_name_)

    with open(f'{os.environ["PATH_TO_WAVELENGTH_FILES"]}/{instrument_.value.lower()}/{filter_name}.txt', 'r') \
            as file:
        for line in file.readlines():
            la = line.split()
            if len(la) and not (la[0] == "!" or la[0] == "#"):
                wavelength.append((float(la[0]), float(la[1])))
    return wavelength


def fp_hwfm(resolution) -> List[Tuple[str, float, float]]:
    if not resolution:
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
    reso = 'LR' if (resolution.lower() == "low resolution") else \
        'MR' if (resolution.lower() == "medium resolution") else \
            'HR' if (resolution.lower() == "high resolution") else \
                'TF' if (resolution.lower() == "frame transfer") else None

    if not reso:
        raise ValueError("Resolution not found for fabry perot")

    return [x for x in fp_modes if x[0].upper() == reso]
