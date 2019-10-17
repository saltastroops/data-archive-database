import math

import pytest
from astropy import units as u
from unittest import mock

from ssda.filter_wavelength_files.reader import ReadInstrumentWavelength
from ssda.util import types
from ssda.util.energy_cal import linear_pol, image_wavelength_intervals, fabry_perot_fwhm_calculation, \
    hrs_interval, imaging_mode_cal, rss_energy_cal, slit_width_from_barcode, get_resolution_element


def test_linear_pol():
    # checking if
    test_list = [(0, 0), (1, 0.1), (2, 0.2), (3, 0.4), (4, 0.2), (5, 0.1), (6, 0.0)]
    # After liner pol I am expecting ((2, 2), (4,2))

    results = linear_pol(test_list)

    assert results[0] == (pytest.approx(2), .2)
    assert results[1] == (4, .2)
    test_list = [(0, 0.0), (1, 0.1), (1.1, 0.15), (2, 0.2), (2.3, 0.3), (2.9, 0.39), (3, 0.4), (4, 0.2), (5, 0.1), (6, 0.0)]
    # List with random numbers same results as above
    results = linear_pol(test_list)
    assert results[0] == (2, .2)
    assert results[1] == (4, .2)

    #  Exponential curve must fail
    test_list_1 = [(0, 0.0), (1, 0.1), (2, 0.4), (3, 0.9)]

    with pytest.raises(ValueError) as exc_info:
        linear_pol(test_list_1)
    assert exc_info.type is ValueError
    assert 'full maximum of give array' in exc_info.value.args[0]

    with pytest.raises(ValueError) as exc_info:
        linear_pol([])
    assert exc_info.type is ValueError
    assert 'is an empty' in exc_info.value.args[0]


def test_image_wavelength_intervals(mocker):
    with mocker.patch.object(ReadInstrumentWavelength, 'wavelengths_and_transmissions',
                             return_value=[(0, 0), (1, 1), (2, 2), (3, 4), (4, 2), (5, 1), (6, 0)]) as mm:
        result = image_wavelength_intervals(
            filter_name="abc",
            instrument=types.Instrument.RSS
        )
        assert result["lambda1"] == (2, 2)
        assert result["lambda2"] == (4, 2)


def test_fabry_perot_fwhm_calculation(mocker):
    with mocker.patch.object(
            ReadInstrumentWavelength, 'fp_hwfm',
            return_value=[("LR", 0, 0), ("LR", 1, 1), ("LR", 2, 2), ("LR", 3, 4), ("LR", 4, 2), ("LR", 5, 1),
                          ("LR", 6, 0)]) as mm:
        assert fabry_perot_fwhm_calculation(resolution="low resolution", wavelength=3) == 4
        assert fabry_perot_fwhm_calculation(resolution="low resolution", wavelength=4) == 2
        assert fabry_perot_fwhm_calculation(resolution="low resolution", wavelength=3.5) == 3

    with mocker.patch.object(
            ReadInstrumentWavelength, 'fp_hwfm',
            return_value=[("HR", 0, 0), ("HR", 1, 1), ("HR", 2, 3), ("HR", 3, 4), ("HR", 4, 3), ("HR", 5, 4),
                          ("HR", 6, 2)]) as mm:
        assert fabry_perot_fwhm_calculation(resolution="high resolution", wavelength=3) == 4
        assert fabry_perot_fwhm_calculation(resolution="high resolution", wavelength=4) == 3
        assert fabry_perot_fwhm_calculation(resolution="high resolution", wavelength=5.5) == 3


def test_hrs_interval():
    # Test if the correct interval and power is found for HRS
    assert hrs_interval('blue', 'medium resolution')["interval"] == (370, 555)
    assert hrs_interval('blue', 'medium resolution')["power"] == 43400

    assert hrs_interval('blue', 'high resolution')["interval"] == (370, 555)
    assert hrs_interval('blue', 'high resolution')["power"] == 66700

    assert hrs_interval('red', 'low resolution')["interval"] == (555, 890)
    assert hrs_interval('red', 'low resolution')["power"] == 14000

    # Test is no resolution error raised for bad resolution name
    with pytest.raises(ValueError) as exc_info:
        hrs_interval('red', 'no resolution')
    assert exc_info.type is ValueError
    assert 'Resolution not found' in exc_info.value.args[0]

    # Test is no arm found if arm is not red or blue
    with pytest.raises(ValueError) as exc_info:
        hrs_interval('green', 'no resolution')
    assert exc_info.type is ValueError
    assert 'Arm not known' in exc_info.value.args[0]


def mock_image_wavelength_intervals(a, b):
    return {"lambda1": (2, .2), "lambda2": (4, 0.2)}


@mock.patch('ssda.util.energy_cal.image_wavelength_intervals', side_effect=mock_image_wavelength_intervals)
def test_imaging_mode_cal(mocked_function):

    tes = imaging_mode_cal(plane_id=1, filter_name="method using filter is mocked", instrument=types.Instrument.RSS)
    assert tes.plane_id == 1
    assert tes.resolving_power == pytest.approx(0.6)
    assert tes.dimension == 1
    assert tes.max_wavelength == 4 * u.meter
    assert mocked_function.called


def fake_value_header(key):
    headers = {
        "OBSMODE": "image"
    }
    return headers.get(key)


def mock_imaging_mode_cal(plane_id, filter_name, instrument):
    return


def mock_get_wavelength_cal():
    return


def mock_fabry_perot_fwhm_calculation():
    return


@mock.patch('ssda.util.energy_cal.fabry_perot_fwhm_calculation', side_effect=mock_fabry_perot_fwhm_calculation)
@mock.patch('ssda.util.energy_cal.get_wavelength', side_effect=mock_get_wavelength_cal)
@mock.patch('ssda.util.energy_cal.imaging_mode_cal', side_effect=mock_imaging_mode_cal)
def test_rss_energy_cal_image(mocked_imaging_mode_cal, mocked_get_wavelength, mocked_fabry_perot_fwhm):
    """
    test that rss energy calculations calls the right updating method depending on the obs mode
    """
    def fake_value_header(key):
        headers = {
            "OBSMODE": "IMAGING",
            "FILTER": "any"
        }
        return headers.get(key)

    rss_energy_cal(header_value=fake_value_header, plane_id=1)
    assert mocked_imaging_mode_cal.called
    assert not mocked_get_wavelength.called
    assert not mocked_fabry_perot_fwhm.called

    # Test if obs mode doen't exist
    def bad_value_header(key):
        headers = {
            "OBSMODE": "Bad Mode",
            "FILTER": "any"
        }
        return headers.get(key)

    with pytest.raises(ValueError) as exc_info:
        rss_energy_cal(header_value=bad_value_header, plane_id=1)
    assert exc_info.type is ValueError
    assert 'RSS energy not calculated' in exc_info.value.args[0]


@mock.patch('ssda.util.energy_cal.fabry_perot_fwhm_calculation', side_effect=mock_fabry_perot_fwhm_calculation)
@mock.patch('ssda.util.energy_cal.get_wavelength', side_effect=mock_get_wavelength_cal)
@mock.patch('ssda.util.energy_cal.imaging_mode_cal', side_effect=mock_imaging_mode_cal)
def test_rss_energy_cal_image_1(mocked_imaging_mode_cal, mocked_get_wavelength, mocked_fabry_perot_fwhm):
    """
    test that rss energy calculations calls the right updating method depending on the obs mode
    """
    def fake_value_header(key):
        headers = {
            "OBSMODE": "SPECTROSCOPY",
            "FILTER": "any"
        }
        return headers.get(key)
    rss_energy_cal(header_value=fake_value_header, plane_id=1)
    assert mocked_imaging_mode_cal.called
    assert not mocked_get_wavelength.called
    assert not mocked_fabry_perot_fwhm.called

    # Test if obs mode doen't exist
    def bad_value_header(key):
        headers = {
            "OBSMODE": "Bad Mode",
            "FILTER": "any"
        }
        return headers.get(key)

    with pytest.raises(ValueError) as exc_info:
        rss_energy_cal(header_value=bad_value_header, plane_id=1)
    assert exc_info.type is ValueError
    assert 'RSS energy not calculated' in exc_info.value.args[0]


def test_slit_width_from_barcode():
    """
    Test Slit width from barcode can calculate.
    """
    assert slit_width_from_barcode("P000000N02") == 0.333333 * u.arcsec
    assert slit_width_from_barcode("P000000P09") == 1.5 * u.arcsec
    assert slit_width_from_barcode("P000000P08") == 1.5 * u.arcsec
    assert slit_width_from_barcode("P001000P08") == 1.0 * u.arcsec
    with pytest.raises(TypeError) as exc_info:
        slit_width_from_barcode(None)
    assert exc_info.type is TypeError
    assert "'NoneType' object is not subscriptable" in exc_info.value.args[0]


def test_get_resolution_element():
    assert get_resolution_element(grating_angle=30 * u.deg, grating_frequency=1 * 1/u.mm, slit_width=5 * u.arcsec) \
        == 15394.902011247219
    assert get_resolution_element(grating_angle=30 * u.deg, grating_frequency=1 * 1/u.mm, slit_width=.5 * u.arcsec) \
        == 1539.4902011247218
    assert get_resolution_element(grating_angle=((30*math.pi)/180) * u.rad, grating_frequency=1 * 1/u.mm,
                                  slit_width=5 * u.arcsec) \
        == 15394.902011247219
