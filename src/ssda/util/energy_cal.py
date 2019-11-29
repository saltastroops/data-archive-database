from typing import Any, Tuple, Dict, List, Optional
from astropy.units import Quantity
from astropy import units as u
import numpy as np

from ssda.data.salt_data_files_reader import wavelengths_and_transmissions, fp_hwfm
from ssda.util import types


# the focal length of the RSS imaging lens
FOCAL_LENGTH_RSS_IMAGING_LENS = 328 * u.mm

# The location (in x direction) of the intersection between the center CCD and the optical axis
RSS_OPTICAL_AXIS_ON_CCD = 0.3066 * u.mm

# The size of a pixel on the RSS CCD chips
RSS_PIXEL_SIZE = 0.015 * u.mm

# the focal length of the telescope
FOCAL_LENGTH_TELESCOPE = 46200 * u.mm

# the focal length of the RSS collimator
FOCAL_LENGTH_RSS_COLLIMATOR = 630 * u.mm


def x_at_half_y_max(curve: List[Tuple[Quantity, float]]) -> Quantity:
    """
    The value of x at half of maximum y in the given line/curve
    The curve have be sorted by x values (index 0)

    Parameters
    ----------
    curve: List
        A two dimension array defining a curve or a line

    Returns
    -------
    x_at_half_y_max: Quantity
        The value of x at half of maximum y
    """
    half_y_max = max(p[1] for p in curve) / 2
    _x_at_half_y_max = None
    for i, t in enumerate(curve):
        # Move through the points, starting from minimum x, until we've just passed half the maximum y value.
        if t[1] > half_y_max:
            if i == 0:
                _x_at_half_y_max = t[0]
                break
            # Calculate the line y = m * x + c passing through the point before and after the half maximum.
            # Use this line to get an estimate of the x where y=half_y_max.
            m = (curve[i][1] - curve[i - 1][1]) / (
                    curve[i][0] - curve[i - 1][0])
            c = curve[i][1] - m * curve[i][0]
            _x_at_half_y_max = (half_y_max - c)/m
            break
    return _x_at_half_y_max


def fwhm_interval(wavelengths_transmissions: List[Tuple[Quantity, float]]) -> Tuple[Quantity, Quantity]:
    """
    A full width half maximum of array of 2D tuples

    Parameter
    ---------
    wavelengths_and_transmissions: List
       The pairs of wavelengths and transmissions

    Return
    ------
    points: Tuple
        A lower and a upper bound of the full width half maximum
    """
    sorted_wavelengths = sorted(wavelengths_transmissions, key=lambda element: element[0])
    reversed_sorted_wavelengths = sorted_wavelengths[::-1]

    x_1_at_half_y_max = x_at_half_y_max(sorted_wavelengths)
    x_2_at_half_y_max = x_at_half_y_max(reversed_sorted_wavelengths)

    return x_1_at_half_y_max, x_2_at_half_y_max


def filter_fwhm_interval(filter_name: str, instrument: types.Instrument) \
        -> Tuple[Tuple[float, float], Tuple[float, float]]:
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
    wavelength_transmission_pairs = wavelengths_and_transmissions(instrument=instrument, filter_name=filter_name)

    lambda_min, lambda_max = fwhm_interval(wavelength_transmission_pairs)

    return lambda_min, lambda_max


def fabry_perot_fwhm_interval(rss_fp_mode: types.RSSFabryPerotMode, wavelength: Quantity) -> Quantity:
    """
    Calculates the full width half maximum of fabry perot for the given resolution and wavelength

    Parameter
    ---------
    resolution: RSSFabryPerotMode
        A full name of the resolution like
    wavelength: Quantity
        A wavelength

    Return
    ------
    fwhm:
        The full width half maximum
    """

    fwhm = None
    fp_fwhm_intervals = fp_hwfm(rss_fp_mode=rss_fp_mode)
    if wavelength < min(fp_fwhm_intervals, key=lambda item: item[1])[1] or \
            wavelength > max(fp_fwhm_intervals, key=lambda item: item[1])[1]:
        raise ValueError("Wavelength is out of range")
    sorted_points = sorted(fp_fwhm_intervals, key=lambda element: element[1])

    for i, w in enumerate(sorted_points):
        #  sorted_points defines a function f of the FWHM as a function of the wavelength.
        #  We use linear interpolation to estimate the value of f at the given wavelength.
        if w[1] > wavelength:
            m = (sorted_points[i][2] - sorted_points[i - 1][2])/(
                    sorted_points[i][1] - sorted_points[i - 1][1])
            c = sorted_points[i][2] - m * sorted_points[i][1]
            fwhm = wavelength * m + c
            break
    if fwhm is None:
        raise ValueError("Full width half maximum could not be calculated")
    return fwhm


def rss_ccd_wavelength(x: float, grating_angle: Quantity, camera_angle: Quantity, grating_frequency: Quantity) \
        -> Quantity:
    """
    Returns the wavelength at the specified distance
    from the center of the middle CCD.

    for the constants.
    Parameters
    ----------
    x: float
        Distance (in spectral direction from center (in pixels)
    grating_angle: Quantity
        The grating angle
    camera_angle: Quantity
        The camera angle
    grating_frequency: Quantity
        The grating frequency

    Return
    ------
    wavelength: metres
        The wavelength
    """
    # What is the outgoing angle beta0 for the center of the middle chip? (Normally, the camera angle will be twice the
    # grating angle, so that the incoming angle (i.e. the grating angle) alpha is equal to beta0.
    alpha0 = 0 * u.deg  # grating rotation home error.
    beta_ae = -0.063 * u.deg  # alignment error of the articulation home
    f_a = -4.2e-5  # correction factor allowing for the mechanical error in placement of the articulation detent ring
    Lambda = 1 / grating_frequency    # grating period
    alpha = grating_angle + alpha0
    beta0 = (1 + f_a) * camera_angle + beta_ae - (grating_angle + alpha0)

    # The relevant distance for the optics is that from the optical axis rather than that from the CCD center.
    x -= RSS_OPTICAL_AXIS_ON_CCD / RSS_PIXEL_SIZE

    # "FUDGE FACTOR"
    x += 20.9

    # The outgoing angle for a distance x is slightly different the correction dbeta is given by
    # tan(dbeta) = x / f_cam with the focal length f_cam of the imaging lens. Note that x must be converted from pixels
    # to a length.
    dbeta = np.arctan((x * RSS_PIXEL_SIZE) / FOCAL_LENGTH_RSS_IMAGING_LENS)
    beta = beta0 + dbeta

    # The wavelength can now be obtained from the grating equation.
    return Lambda * (np.sin(alpha) + np.sin(beta))


def rss_resolution_element(grating_frequency: Quantity, grating_angle: Quantity, slit_width: Quantity) -> Quantity:
    """
    Returns the resolution element for the given grating frequency, grating angle and slit width.

    Parameters
    ----------
    grating_frequency:
       The grating frequency
    grating_angle:
        The grating angle
    slit_width:
        The slit width

    Return
    ------
    resolution_element
        The resolution element

    """

    Lambda = 1/grating_frequency
    # TODO some thing is not right below units were supposed to be arcsec but got arcsec * mm
    return slit_width * Lambda * np.cos(grating_angle) * (FOCAL_LENGTH_TELESCOPE / FOCAL_LENGTH_RSS_COLLIMATOR)


def rss_resolution(grating_angle: Quantity, camera_angle: Quantity, grating_frequency: Quantity,
                   slit_width: Quantity) -> Quantity:
    """
    Returns the resolution at the center of the middle CCD. This is the ratio of the resolution element and
    the wavelength at the CCD's center.

    Parameters
    ----------
    grating_angle: Quantity
        The grating angle
    camera_angle: Quantity
        The camera angle
    grating_frequency: Quantity
        The grating frequency
    slit_width: Quantity
        The slit width

    Return
    ------
    resolution
        The resolution

    """
    wavelength = rss_ccd_wavelength(0, grating_angle, camera_angle, grating_frequency)
    wavelength_resolution_element = rss_resolution_element(grating_frequency, grating_angle, slit_width)
    return wavelength / wavelength_resolution_element


def rss_slit_width_from_barcode(barcode: str) -> Quantity:
    """
    Returns the slit width for the given barcode.

    Parameters
    ----------
    barcode: str

    Return
    ------
    slit_width
        The slit width

    """
    if barcode == "P000000N02":
        return 0.333333 * u.arcsec

    if barcode == "P000000P08" or barcode == "P000000P09":
        return 1.5 * u.arcsec

    return (float(barcode[2:6]) / 100) * u.arcsec


def get_grating_frequency(grating: str) -> Quantity:
    """
    Returns a grating frequency

    Parameter
    ---------
    grating: str
        Grating name
    Return
    ------
    The grating frequency (in grooves/mm)
    """
    grating_table = {
        "pg0300": 300,
        "pg0900": 903.89,
        "pg1300": 1299.6,
        "pg1800": 1801.89,
        "pg2300": 2302.60,
        "pg3000": 3000.55
    }
    if not grating or grating.lower() not in grating_table:
        raise ValueError("Grating frequency not found on grating table")

    return grating_table[grating.lower()] / u.mm


def hrs_resolving_power(arm: types.HRSArm, hrs_mode: types.HRSMode) -> float:
    """
   The HRS wavelength interval (interval) as a 2D tuple where first entry being lower bound and second is the
   maximum  bound and resolving power (power)

   Parameter
   ---------
    arm: HRS Arm
        HRS arm that is either Red or Blue
    resolution: HRSMode
        A full name of  the resolution like Low Resolution
   Return
   ------
    power: float
        HRS resolving power
   """

    if types.HRSArm.BLUE == arm:
        if hrs_mode == types.HRSMode.LOW_RESOLUTION:
            return 15000
        if hrs_mode == types.HRSMode.MEDIUM_RESOLUTION:
            return 43400
        if hrs_mode == types.HRSMode.HIGH_RESOLUTION:
            return 66700
        if hrs_mode == types.HRSMode.HIGH_STABILITY:
            return 66900

    if types.HRSArm.RED == arm:
        if hrs_mode == types.HRSMode.LOW_RESOLUTION:
            return 14000
        if hrs_mode == types.HRSMode.MEDIUM_RESOLUTION:
            return 39600
        if hrs_mode == types.HRSMode.HIGH_RESOLUTION:
            return 73700
        if hrs_mode == types.HRSMode.HIGH_STABILITY:
            return 64600

    raise ValueError(f"Unknown HRS arm {arm.value}")


def hrs_wavelength_interval(arm: types.HRSArm) -> Tuple[Quantity, Quantity]:
    """
    The HRS wavelength interval (interval) as a 2D tuple where first entry being lower bound and second is the
    maximum  bound.

    Parameter
    ---------
    arm: HRSArm
       HRS arm, either Red or Blue
    Return
    ------
    hrs_interval: tuple
        The HRS interval.
    """

    if types.HRSArm.BLUE == arm:
        return 370 * u.mn, 555 * u.mn

    if types.HRSArm.RED == arm:
        return 555 * u.mn, 890 * u.mn

    raise ValueError(f"Unknown HRS arm {arm.value}")


def imaging_spectral_properties(plane_id: int, filter_name: str, instrument: types.Instrument) -> types.Energy:
    """
    Spectral properties of a Salticam setup.

    Parameter
    ----------
    plane_id: int
        Plane id of of this file
    filter_name: str
        Filter name used for this file
    instrument: Instrument
        Instrument used for this file
    Return
    ------
    Spectral properties
        Calculated spectral properties
    """
    fwhm_points = filter_fwhm_interval(filter_name, instrument)
    lambda_min, lambda_max = fwhm_points[0], fwhm_points[1]
    resolving_power = 0.5 * (lambda_min + lambda_max) / (lambda_max - lambda_min)
    return types.Energy(
        dimension=1,
        max_wavelength=lambda_max,
        min_wavelength=lambda_min,
        plane_id=plane_id,
        resolving_power=resolving_power,
        sample_size=abs(lambda_max-lambda_min)
    )


def rss_spectral_properties(header_value: Any, plane_id: int) -> Optional[types.Energy]:
    """
     Spectral properties for an RSS setup.

    Parameter
    ----------
    header_value: Function
        Observation method to get FITS header value using key
    plane_id: int
        Plane id of of this file
    Return
    ------
    Spectral properties
        RSS Spectral properties
    """
    filter = header_value("FILTER").strip()
    if not filter or \
            filter.upper() == "EMPTY" or \
            filter in ["PC00000", "PC03200", "PC03400", "PC03850", "PC04600"]:
        return None
    observation_mode = header_value("OBSMODE").strip().upper()
    if observation_mode.upper() == "IMAGING":
        return imaging_spectral_properties(plane_id=plane_id,
                                           filter_name=header_value("FILTER").strip(),
                                           instrument=types.Instrument.RSS)

    if observation_mode.upper() == "SPECTROSCOPY":
        grating_angle = float(header_value("GR-ANGLE").strip()) * u.deg
        camera_angle = float(header_value("AR-ANGLE").strip()) * u.deg
        slit_barcode = header_value("MASKID").strip()
        spectral_binning = int(header_value("CCDSUM").strip().split()[0])
        grating_frequency = get_grating_frequency(header_value("GRATING").strip())
        wavelength_interval = (
            rss_ccd_wavelength(
                3162,
                grating_angle,
                camera_angle,
                grating_frequency=grating_frequency
            ),
            rss_ccd_wavelength(
                -3162,
                grating_angle,
                camera_angle,
                grating_frequency=grating_frequency
            )
        )
        dimension = 6096 // spectral_binning
        sample_size = rss_ccd_wavelength(
            spectral_binning,
            grating_angle,
            camera_angle,
            grating_frequency
        ) - rss_ccd_wavelength(
            0,
            grating_angle,
            camera_angle,
            grating_frequency
        )
        return types.Energy(
            dimension=dimension,
            max_wavelength=Quantity(
                value=wavelength_interval[0],
                unit=u.meter
            ),
            min_wavelength=Quantity(
                value=wavelength_interval[1],
                unit=u.meter
            ),
            plane_id=plane_id,
            resolving_power=rss_resolution(
                grating_angle,
                camera_angle,
                grating_frequency=grating_frequency,
                slit_width=rss_slit_width_from_barcode(slit_barcode)),
            sample_size=Quantity(
                value=abs(sample_size),
                unit=u.meter
            )
        )

    if observation_mode == "FABRY-PEROT":
        etalon_state = header_value("ET-STATE")
        if etalon_state.strip().lower() == "s1 - etalon open":
            return None

        if etalon_state.strip().lower() == "s3 - etalon 2":
            resolution = header_value("ET2MODE").strip().upper()  # TODO CHECK with encarni which one use ET2/1
            _lambda = float(header_value("ET2WAVE0"))
        elif etalon_state.strip().lower() == "s2 - etalon 1" or etalon_state.strip().lower() == "s4 - etalon 1 & 2":
            resolution = header_value("ET1MODE").strip().upper()  # TODO CHECK with encarni which one use ET2/1
            _lambda = float(header_value("ET1WAVE0"))  # Todo what are this units?
        else:
            raise ValueError("Unknown etalon state")

        fwhm = fabry_perot_fwhm_interval(rss_fp_mode=resolution, wavelength=_lambda)
        wavelength_interval = (_lambda - fwhm / 2, _lambda + fwhm / 2)
        return types.Energy(
            dimension=1,
            max_wavelength=Quantity(
                value=wavelength_interval[1],
                unit=u.meter
            ),
            min_wavelength=Quantity(
                value=wavelength_interval[0],
                unit=u.meter
            ),
            plane_id=plane_id,
            resolving_power=_lambda/fwhm,
            sample_size=Quantity(
                value=fwhm,
                unit=u.meter
            )
        )

    raise ValueError(f"Unsupported observation mode: {observation_mode}")


def hrs_spectral_properties(plane_id: int, arm: types.HRSArm, hrs_mode: types.HRSMode) -> Optional[types.Energy]:
    """
     Method to calculate an spectral properties of HRS instrument

    Parameter
    ----------
    plane_id: int
        Plane id of of this file
    arm: HRSArm
        HRS arm either red or blue
    hrs_mode: HRSMode
        HRS resolution (Low, Medium, ...) Resolution

    Return
    ------
    Spectral properties
        HRS spectral properties.
    """

    interval = hrs_wavelength_interval(arm=arm)
    return types.Energy(
        dimension=1,
        max_wavelength=Quantity(
            value=max(interval),
            unit=u.meter
        ),
        min_wavelength=Quantity(
            value=min(interval),
            unit=u.meter
        ),
        plane_id=plane_id,
        resolving_power=hrs_resolving_power(arm=arm, hrs_mode=hrs_mode),
        sample_size=Quantity(
            value=interval[1]-interval[0],
            unit=u.meter
        )
    )


def salticam_spectral_properties(plane_id: int, filter_name: str) -> Optional[types.Energy]:
    """

    Spectral properties of a Salticam setup.

    Parameter
    ----------
        plane_id: int
            Plane id of of this file
        filter_name: str
            filter user for this file

    Return
    ------
        Spectral properties
           SALTICAM spectral properties
    """
    if filter_name == "OPEN":
        return None
    if filter_name == "CLR-S1":
        return None
    if filter_name == "SDSSz-S1":
        return None
    return imaging_spectral_properties(plane_id=plane_id, filter_name=filter_name, instrument=types.Instrument.SALTICAM)
