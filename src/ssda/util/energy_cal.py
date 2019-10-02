from astropy.units import Quantity
import os
import math

from ssda.filter_wavelength_files.reader import ReadInstrumentWavelength
from ssda.util import types


# the focal length of the RSS imaging lens (in mm)
FOCAL_LENGTH_RSS_IMAGING_LENS = 328

# The location (in x direction) of the intersection between the center CCD and the optical axis in mm
RSS_OPTICAL_AXIS_ON_CCD = 0.3066

# The size of a pixel on the RSS CCD chips (in millimeters)
RSS_PIXEL_SIZE = 0.015

# the focal length of the telescope (in mm)
FOCAL_LENGTH_TELESCOPE = 46200

# the focal length of the RSS collimator (in mm)
FOCAL_LENGTH_RSS_COLLIMATOR = 630


def linear_pol(list_of_tuple: list) -> tuple:
    half_y = max(list_of_tuple, key=lambda item: item[1])[1]/2
    x_1_at_half_y = None
    x_2_at_half_y = None

    for i, t in enumerate(list_of_tuple):
        if t[1] > half_y:
            m = (list_of_tuple[i][1] - list_of_tuple[i - 1][1])/(
                    list_of_tuple[i][0] - list_of_tuple[i - 1][0])
            c = list_of_tuple[i][1] - m * list_of_tuple[i][0]
            x_1_at_half_y = (half_y - c)/m
            break

    for i, t in enumerate(list_of_tuple[::-1]):
        if t[1] > half_y:
            m = (list_of_tuple[::-1][i][1] - list_of_tuple[::-1][i - 1][1])/(
                    list_of_tuple[::-1][i][0] - list_of_tuple[::-1][i - 1][0])
            c = list_of_tuple[::-1][i][1] - m * list_of_tuple[::-1][i][0]
            x_2_at_half_y = (half_y - c)/m
            break
    return (x_1_at_half_y, half_y), (x_2_at_half_y, half_y)


def image_wavelength_intervals(filter_name: str, instrument: types.Instrument) -> dict:
    """
    It opens the file with the wavelength curve of the filter name and return the full width half max points of it

    Parameter
    ---------
        filter_name: str
            The name of the filter you need intervals of

        instrument: types.Instrument
            THe instrument used for the filter
    Return
    ------
        points: Dict
            The two points that that form fwhm on the curve where lambda1 being the small wavelength and lambda2 is
            the larger wavelength
    """
    unsorted_wavelength = ReadInstrumentWavelength(instrument=instrument,
                                                   filter_name=filter_name).wavelengths_and_transmissions

    sorted_wavelength = sorted(unsorted_wavelength, key=lambda element: element[0])
    lambda1, lambda2 = linear_pol(sorted_wavelength)

    if not lambda1[0] or not lambda1[1] or not lambda2:
        raise ValueError(f"One or both wavelength are not found lambda1={lambda1} lambda2={lambda2}")
    return {
        "lambda1": lambda1,
        "lambda2": lambda2
    }


def fabry_perot_fwhm_calculation(resolution: str, wavelength: float):
    """
    Calculates the full width half maximum of fabry perot for the given resolution and wavelength

    Parameter
    ---------
    resolution: String
        A full name of the resolution like
    wavelength: float

    Return
    ------
    Full width half maximum
    """
    fp_modes = []
    fwhm = None
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
    reso = 'lr' if (resolution.lower() == "low resolution") else \
        'mr' if (resolution.lower() == "medium resolution") else \
            'hr' if (resolution.lower() == "high resolution") else \
                'tf' if (resolution.lower() == "frame transfer") else None

    if not reso:
        raise ValueError("Resolution not found for fabry perot")

    resolution_fp_modes = [x for x in fp_modes if x[0].upper() == reso]
    sorted_wavelength = sorted(resolution_fp_modes, key=lambda element: element[1])

    for i, w in enumerate(sorted_wavelength):
        if w[1] > wavelength:
            m = (sorted_wavelength[i][2] - sorted_wavelength[i - 1][2])/(
                    sorted_wavelength[i][1] - sorted_wavelength[i - 1][1])
            c = sorted_wavelength[i][2] - m * sorted_wavelength[i][1]
            fwhm = wavelength * m + c
            break
    if fwhm is None:
        raise ValueError("Full width half maximum could not be calculated")
    return fwhm


def get_wavelength(x, grating_angle, camera_angle, grating_frequency):
    """
    Returns the wavelength at the specified distance {@code x}
    from the center of the middle CCD.

    See http://www.sal.wisc.edu/~khn/salt/Outgoing/3170AM0010_Spectrograph_Model_Draft_2.pdf
    for the constants.
    Parameters
    ----------
        x: float
            Distance (in spectral direction from center (in pixels)
        grating_angle: float
            The grating angle (in degrees)
        camera_angle: float
            The camera angle (in degrees)
        grating_frequency: float
            The grating frequency (in grooves/mm)
    Return
    ------
        the wavelength (in metres)
    """
    # What is the outgoing angle beta0 for the center of the middle chip? (Normally, the camera angle will be twice the
    # grating angle, so that the incoming angle (i.e. the grating angle) alpha is equal to beta0.
    alpha0 = 0  # grating rotation home error, in degrees
    beta_ae = -0.063  # alignment error of the articulation home, in degrees
    f_a = -4.2e-5  # correction factor allowing for the mechanical error in placement of the articulation detent ring
    lambda1 = 1e7 / grating_frequency    # grating period
    alpha = math.radians(grating_angle + alpha0)
    beta0 = math.radians((1 + f_a) * camera_angle + beta_ae - (grating_angle + alpha0))

    # The relevant distance for the optics is that from the optical axis rather than that from the CCD center.
    x -= RSS_OPTICAL_AXIS_ON_CCD / RSS_PIXEL_SIZE

    # "FUDGE FACTOR"
    x += 20.9

    # The outgoing angle for a distance x is slightly different the correction dbeta is given by
    # tan(dbeta) = x / f_cam with the focal length f_cam of the imaging lens. Note that x must be converted from pixels
    # to a length.
    dbeta = math.atan((x * RSS_PIXEL_SIZE) / FOCAL_LENGTH_RSS_IMAGING_LENS)
    beta = beta0 + dbeta

    # The wavelength can now be obtained from the grating equation.
    wavelength = lambda1 * (math.sin(alpha) + math.sin(beta))

    # The CAOM expects the wavelength to be in metres, not Angstroms.
    return wavelength / 1e10


def get_resolution_element(grating_frequency,  grating_angle,  slit_width):
    """
    Returns the resolution element for the given grating frequency, grating angle and slit width.

    Parameters
    ----------
        grating_frequency:
           the grating frequence (in grooves/mm)
        grating_angle:
            the grating angle (in degrees)
        slit_width:
            the slit width (in arcseconds)

    Return
    ------
    resolution_element
        The resolution element

    """

    Lambda = 1**7 / grating_frequency
    return math.radians(slit_width / 3600) * Lambda * math.cos(math.radians(grating_angle)) * (
            FOCAL_LENGTH_TELESCOPE / FOCAL_LENGTH_RSS_COLLIMATOR)


def get_wavelength_resolution(grating_angle, camera_angle, grating_frequency, slit_width):
    """
    Returns the resolution at the center of the middle CCD. This is the ratio of the resolution element and
    the wavelength at the CD's center.

    Parameters
    ----------
        grating_angle: float
            he grating angle (in degrees)
        camera_angle: float
            The camera angle (in degrees)
        grating_frequency: float
            the grating frequency (in grooves/mm)
        slit_width: float
            the slit width (in arcseconds)
    Return
    ------
    resolution
        The resolution

    """
    wavelength = get_wavelength(0, grating_angle, camera_angle, grating_frequency)
    wavelength_resolution_element = get_resolution_element(grating_frequency, grating_angle, slit_width)
    return wavelength / wavelength_resolution_element


def slit_width_from_barcode(barcode: str) -> float:
    """
    Returns the slit width for the given barcode.

    Parameters
    ----------
        barcode: str
    Return
    ------
    slit_width
        The slit width (in arcseconds)

    """
    if barcode == "P000000N02":
        return 0.333333

    if barcode == "P000000P08" or barcode == "P000000P09":
        return 1.5

    return float(barcode[2:6]) / 100


def get_grating_frequency(grating: str) -> float:
    """
    Returns a grating frequency

    Parameter
    ---------
        grating: str
            Grating name
    Return
    ------
        Grating frequency
    """
    grating_table = {
        "pg0300": 300,
        "pg0900": 903.89,
        "pg1300": 1299.6,
        "pg1800": 1801.89,
        "pg2300": 2302.60,
        "pg3000": 3000.55
    }
    if not grating_table[grating]:
        raise ValueError("Grating frequency not found on grating table")

    return grating_table[grating]


def hrs_interval(arm: str, resolution: str) -> dict:
    """
    Dictionary with wavelength interval (interval) as a 2D tuple where first entry being lower bound and second is the
    maximum  bound and resolving power (power)

    Parameter
    ---------
        arm: String
            HRS arm that is either red or blue
        resolution: String
            A full name of  the resolution like Low Resolution
    Return
    ------
        dict like {
            "interval": (370, 555),
             "power": 15000
         }
    """
    if arm.lower() not in ['red', 'blue']:
        raise ValueError('Arm not known')

    reso = 'lr' if (resolution.lower() == "low resolution") else \
        'mr' if (resolution.lower() == "medium resolution") else \
            'hr' if (resolution.lower() == "high resolution") else \
                'hs-p' if (resolution.lower() == "high stability (p)") else \
                    'hs-o' if (resolution.lower() == "high stability (o)") else None
    if not resolution:
        raise ValueError("Resolution not found")

    interval_table = {
        "blue": {
            "lr": {
                "interval": (370, 555),
                "power": 15000
            },
            "mr": {
                "interval": (370, 555),
                "power": 43400
            },
            "hr": {
                "interval": (370, 555),
                "power": 66700
            },
            "hs-p": {
                "interval": (370, 555),
                "power": 66900
            },
            "hs-o": {
                "interval": (370, 555),
                "power": 94600
            }
        },
        "red": {
            "lr": {
                "interval": (555, 890),
                "power": 14000
            },
            "mr": {
                "interval": (555, 890),
                "power": 39600
            },
            "hr": {
                "interval": (555, 890),
                "power": 73700
            },
            "hs-p": {
                "interval": (555, 890),
                "power": 64600
            },
            "hs-o": {
                "interval": (555, 890),
                "power": 84200
            }
        }
    }
    return interval_table[arm][reso]


def imaging_mode_cal(plane_id: int, filter_name: str, instrument: types.Instrument) -> types.Energy:

    fwhm_points = image_wavelength_intervals(filter_name, instrument)
    lambda1, lambda2 = fwhm_points["lambda1"], fwhm_points["lambda2"]
    resolving_power = lambda1[1] * (lambda1[0] + lambda2[0]) / (lambda2[0] - lambda1[0])
    return types.Energy(
        dimension=1,
        max_wavelength=Quantity(
            value=lambda2[0],
            unit=types.meter
        ),
        min_wavelength=Quantity(
            value=lambda1[0],
            unit=types.meter
        ),
        plane_id=plane_id,
        resolving_power=resolving_power,
        sample_size=Quantity(
            value=abs(lambda2[0]-lambda1[0]),
            unit=types.meter
        )
    )


def rss_energy_cal(header_value, plane_id):
    observation_mode = header_value("OBSMODE").strip().upper()
    if observation_mode.upper() == "IMAGING":
        return imaging_mode_cal(plane_id=plane_id,
                                filter_name=header_value("FILTER").strip(),
                                instrument=types.Instrument.RSS)

    if observation_mode == "SPECTROSCOPY":
        grating_angle = float(header_value("GR-ANGLE").strip())
        camera_angle = float(header_value("AR-ANGLE").strip())
        slit_barcode = header_value("MASKID").strip()
        spectral_binning = int(header_value("CCDSUM").strip().split()[0])
        grating_frequency = get_grating_frequency(header_value("GRATING").strip())
        energy_interval = (
            get_wavelength(3162, grating_angle, camera_angle, grating_frequency=grating_frequency),
            get_wavelength(-3162, grating_angle, camera_angle, grating_frequency=grating_frequency)
        )
        dimension = 6096 // spectral_binning
        sample_size = get_wavelength(spectral_binning, grating_angle, camera_angle, grating_frequency) - \
                      get_wavelength(0, grating_angle, camera_angle, grating_frequency)
        return types.Energy(
            dimension=dimension,
            max_wavelength=Quantity(
                value=energy_interval[0],
                unit=types.meter
            ),
            min_wavelength=Quantity(
                value=energy_interval[1],
                unit=types.meter
            ),
            plane_id=plane_id,
            resolving_power=get_wavelength_resolution(
                grating_angle,
                camera_angle,
                grating_frequency,
                slit_width=slit_width_from_barcode(slit_barcode)),
            sample_size=Quantity(
                value=abs(sample_size),
                unit=types.meter
            )
        )

    if observation_mode == "FABRY-PEROT":
        etalon_state = header_value("ET-STATE")
        if etalon_state.strip().lower() == "s1 - etalon open":
            return

        if etalon_state.strip().lower() == "s3 - etalon 2":
            resolution = header_value("ET2MODE").strip().upper()  # TODO CHECK with encarni which one use ET2/1
            lambda1 = float(header_value("ET2WAVE0"))
        elif etalon_state.strip().lower() == "s2 - etalon 1" or etalon_state.strip().lower() == "s4 - etalon 1 & 2":
            resolution = header_value("ET1MODE").strip().upper()  # TODO CHECK with encarni which one use ET2/1
            lambda1 = float(header_value("ET1WAVE0"))
        else:
            raise ValueError("Unknown Etelo state for  FP")

        fwhm = fabry_perot_fwhm_calculation(resolution=resolution, wavelength=lambda1)
        energy_intervals = ((lambda1 - fwhm) / 2, (lambda1 + fwhm) / 2)
        return types.Energy(
            dimension=1,
            max_wavelength=Quantity(
                value=energy_intervals[1],
                unit=types.meter
            ),
            min_wavelength=Quantity(
                value=energy_intervals[0],
                unit=types.meter
            ),
            plane_id=plane_id,
            resolving_power=lambda1/fwhm,
            sample_size=Quantity(
                value=fwhm,
                unit=types.meter
            )
        )

    raise ValueError("RSS energy not calculated")


def hrs_energy_cal(plane_id, arm, resolution):

    interval = hrs_interval(arm=arm, resolution=resolution)
    return types.Energy(
        dimension=1,
        max_wavelength=Quantity(
            value=max(interval["interval"]),
            unit=types.meter
        ),
        min_wavelength=Quantity(
            value=min(interval["interval"]),
            unit=types.meter
        ),
        plane_id=plane_id,
        resolving_power=interval["power"],
        sample_size=Quantity(
            value=abs(interval["interval"][0]-interval["interval"][1]),
            unit=types.meter
        )
    )


def scam_energy_cal(plane_id: int, filter_name: str,):
    return imaging_mode_cal(plane_id=plane_id, filter_name=filter_name, instrument=types.Instrument.SALTICAM)