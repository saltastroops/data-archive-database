import os
import pytest
from datetime import date, datetime

from astropy import units as u
from ssda.util import types


# Artifact


def test_artifact_is_created_correctly():
    artifact = types.Artifact(
        content_checksum="asdf",
        content_length=123456 * types.byte,
        identifier="xyz",
        name="ngc1234.fits",
        plane_id=56987,
        path="/some/path/to/data.fits",
        product_type=types.ProductType.SCIENCE,
    )

    assert artifact.content_checksum == "asdf"
    assert artifact.content_length.to_value(types.byte) == 123456
    assert artifact.identifier == "xyz"
    assert artifact.name == "ngc1234.fits"
    assert artifact.plane_id == 56987
    assert artifact.path == "/some/path/to/data.fits"
    assert artifact.product_type == types.ProductType.SCIENCE


def test_artifact_checksum_must_have_at_most_32_characters():
    with pytest.raises(ValueError) as excinfo:
        types.Artifact(
            content_checksum="a" * 33,
            content_length=123456 * types.byte,
            identifier="xyz",
            name="ngc1234.fits",
            plane_id=56987,
            path="/some/path/to/data.fits",
            product_type=types.ProductType.SCIENCE,
        )

    assert "checksum" in str(excinfo)


def test_artifact_content_length_must_be_positive():
    with pytest.raises(ValueError) as excinfo:
        types.Artifact(
            content_checksum="asdf",
            content_length=-1 * types.byte,
            identifier="xyz",
            name="ngc1234.fits",
            plane_id=56987,
            path="/some/path/to/data.fits",
            product_type=types.ProductType.SCIENCE,
        )

    assert "content length" in str(excinfo) and "positive" in str(excinfo)


def test_artifact_content_length_must_have_a_file_size_unit():
    with pytest.raises(ValueError) as excinfo:
        types.Artifact(
            content_checksum="asdf",
            content_length=123456 * u.meter,
            identifier="xyz",
            name="ngc1234.fits",
            plane_id=56987,
            path="/some/path/to/data.fits",
            product_type=types.ProductType.SCIENCE,
        )

    assert "content length" in str(excinfo) and "unit" in str(excinfo)


def test_artifact_identifier_must_have_at_most_50_characters():
    with pytest.raises(ValueError) as excinfo:
        types.Artifact(
            content_checksum="asdf",
            content_length=123456 * types.byte,
            identifier="x" * 51,
            name="ngc1234.fits",
            plane_id=56987,
            path="/some/path/to/data.fits",
            product_type=types.ProductType.SCIENCE,
        )

    assert "identifier" in str(excinfo)


def test_artifact_name_must_have_at_most_200_characters():
    with pytest.raises(ValueError) as excinfo:
        types.Artifact(
            content_checksum="asdf",
            content_length=123456 * types.byte,
            identifier="xyz",
            name="n" * 201,
            plane_id=56987,
            path="p" * 201,
            product_type=types.ProductType.SCIENCE,
        )

    assert "name" in str(excinfo)


def test_artifact_path_must_have_at_most_200_characters():
    with pytest.raises(ValueError) as excinfo:
        types.Artifact(
            content_checksum="asdf",
            content_length=123456 * types.byte,
            identifier="xyz",
            name="ngc1234.fits",
            plane_id=56987,
            path="p" * 201,
            product_type=types.ProductType.SCIENCE,
        )

    assert "path" in str(excinfo)


# DatabaseConfiguration


def test_database_config_accepts_valid_configuration():
    assert types.DatabaseConfiguration(
        host="127.0.0.1",
        username="observation",
        password="secret",
        database="archive",
        port=3306,
    )


@pytest.mark.parametrize("port", [0, -1, -1024])
def test_database_config_rejects_non_positive_port(port):
    with pytest.raises(ValueError) as excinfo:
        types.DatabaseConfiguration(
            host="127.0.0.1",
            username="observation",
            password="secret",
            database="archive",
            port=port,
        )


def test_database_configuration_equality():
    some_config = types.DatabaseConfiguration(
        host="localhost",
        username="user",
        password="secret",
        database="archive",
        port=3306,
    )
    same_config = types.DatabaseConfiguration(
        host="localhost",
        username="user",
        password="secret",
        database="archive",
        port=3306,
    )

    assert some_config == same_config


def test_database_configuration_non_equality():
    some_config = types.DatabaseConfiguration(
        host="localhost",
        username="user",
        password="secret",
        database="archive",
        port=3306,
    )
    other_config = types.DatabaseConfiguration(
        host="127.0.0.1",
        username="user",
        password="secret",
        database="archive",
        port=3306,
    )
    assert some_config != other_config

    other_config = types.DatabaseConfiguration(
        host="localhost",
        username="otheruser",
        password="secret",
        database="archive",
        port=3306,
    )
    assert some_config != other_config

    other_config = types.DatabaseConfiguration(
        host="localhost",
        username="user",
        password="topsecret",
        database="archive",
        port=3306,
    )
    assert some_config != other_config

    other_config = types.DatabaseConfiguration(
        host="localhost",
        username="user",
        password="secret",
        database="observations",
        port=3306,
    )
    assert some_config != other_config

    other_config = types.DatabaseConfiguration(
        host="localhost",
        username="user",
        password="secret",
        database="archive",
        port=3307,
    )
    assert some_config != other_config


# Energy


def test_energy_is_created_correctly():
    energy = types.Energy(
        dimension=512,
        max_wavelength=7000 * u.nanometer,
        min_wavelength=5500 * u.nanometer,
        plane_id=83,
        resolving_power=1200,
        sample_size=2.34 * u.nanometer,
    )

    assert energy.dimension == 512
    assert energy.max_wavelength.to_value(u.nanometer) == 7000
    assert energy.min_wavelength.to_value(u.nanometer) == 5500
    assert energy.plane_id == 83
    assert energy.resolving_power == 1200
    assert energy.sample_size.to_value(u.nanometer) == 2.34


def test_energy_dimension_must_be_positive():
    with pytest.raises(ValueError) as excinfo:
        types.Energy(
            dimension=0,
            max_wavelength=7000 * u.nanometer,
            min_wavelength=5500 * u.nanometer,
            plane_id=83,
            resolving_power=1200,
            sample_size=2.34 * u.nanometer,
        )

    assert "dimension" in str(excinfo)


def test_energy_max_wavelength_must_be_positive():
    with pytest.raises(ValueError) as excinfo:
        types.Energy(
            dimension=512,
            max_wavelength=0 * u.nanometer,
            min_wavelength=5500 * u.nanometer,
            plane_id=83,
            resolving_power=1200,
            sample_size=2.34 * u.nanometer,
        )

    assert "maximum wavelength" in str(excinfo) and "positive" in str(excinfo)


def test_energy_max_wavelength_must_have_a_length_unit():
    with pytest.raises(ValueError) as excinfo:
        types.Energy(
            dimension=512,
            max_wavelength=7000 * u.second,
            min_wavelength=5500 * u.nanometer,
            plane_id=83,
            resolving_power=1200,
            sample_size=2.34 * u.nanometer,
        )

    assert "maximum wavelength" in str(excinfo) and "length" in str(excinfo)


def test_energy_min_wavelength_must_be_positive():
    with pytest.raises(ValueError) as excinfo:
        types.Energy(
            dimension=512,
            max_wavelength=7000 * u.nanometer,
            min_wavelength=0 * u.nanometer,
            plane_id=83,
            resolving_power=1200,
            sample_size=2.34 * u.nanometer,
        )

    assert "minimum wavelength" in str(excinfo) and "positive" in str(excinfo)


def test_energy_min_wavelength_must_have_a_length_unit():
    with pytest.raises(ValueError) as excinfo:
        types.Energy(
            dimension=512,
            max_wavelength=7000 * u.nanometer,
            min_wavelength=5500 * u.second,
            plane_id=83,
            resolving_power=1200,
            sample_size=2.34 * u.nanometer,
        )

    assert "minimum wavelength" in str(excinfo) and "length" in str(excinfo)


def test_energy_max_wavelength_must_not_be_less_than_min_wavelength():
    with pytest.raises(ValueError) as excinfo:
        types.Energy(
            dimension=512,
            max_wavelength=7000 * u.nanometer,
            min_wavelength=7000.1 * u.nanometer,
            plane_id=83,
            resolving_power=1200,
            sample_size=2.34 * u.nanometer
        )

    assert "minimum" in str(excinfo) and "maximum" in str(excinfo)


def test_energy_resolving_power_must_be_non_negative():
    with pytest.raises(ValueError) as excinfo:
        types.Energy(
            dimension=512,
            max_wavelength=7000 * u.nanometer,
            min_wavelength=5500 * u.nanometer,
            plane_id=83,
            resolving_power=-1,
            sample_size=2.34 * u.nanometer
        )

    assert "resolving power" in str(excinfo)


def test_energy_sample_size_must_have_a_length_unit():
    with pytest.raises(ValueError) as excinfo:
        types.Energy(
            dimension=512,
            max_wavelength=7000 * u.nanometer,
            min_wavelength=5500 * u.nanometer,
            plane_id=83,
            resolving_power=1200,
            sample_size=2.34 * u.second
        )

    assert 'sample size' in str(excinfo) and 'length' in str(excinfo)


def test_energy_sample_size_must_be_non_negative():
    with pytest.raises(ValueError) as excinfo:
        types.Energy(
            dimension=512,
            max_wavelength=7000 * u.nanometer,
            min_wavelength=5500 * u.nanometer,
            plane_id=83,
            resolving_power=1200,
            sample_size=-1 * u.nanometer
        )

    assert "sample size" in str(excinfo)


# FilePath


def test_file_path_requires_a_regular_file(mocker):
    def fake_isfile(path: str) -> bool:
        return "regular" in path

    mocker.patch.object(os.path, "isfile", new=fake_isfile)

    assert types.FilePath("regular.fits")

    with pytest.raises(ValueError) as excinfo:
        types.FilePath("missing.fits")
    assert "regular" in str(excinfo.value)


# Instrument


def test_instrument_for_name_rejects_invalid_name():
    with pytest.raises(ValueError) as excinfo:
        types.Instrument.for_name("Xghyu")
    assert "instrument name" in str(excinfo.value)


@pytest.mark.parametrize(
    "instrument",
    [
        ("Salticam", types.Instrument.SALTICAM),
        ("RSS", types.Instrument.RSS),
        ("HRS", types.Instrument.HRS),
    ],
)
def test_instruments_can_be_created_from_name(instrument):
    assert types.Instrument.for_name(instrument[0]) == instrument[1]


@pytest.mark.parametrize("name", ["RSS", "rss", "Rss", "rSs", "rSS"])
def test_instrument_for_name_is_case_insensitive(name):
    assert types.Instrument.for_name(name) == types.Instrument.RSS


# InstrumentKeywordValue


def test_instrument_keyword_value_is_created_correctly():
    instrument_keyword_value = types.InstrumentKeywordValue(
        instrument=types.Instrument.RSS,
        instrument_keyword=types.InstrumentKeyword.GRATING,
        observation_id=12,
        value="pg0900",
    )

    assert (
        instrument_keyword_value.instrument_keyword == types.InstrumentKeyword.GRATING
    )
    assert instrument_keyword_value.observation_id == 12
    assert instrument_keyword_value.value == "pg0900"


def test_instrument_keyword_value_too_long():
    with pytest.raises(ValueError) as excinfo:
        types.InstrumentKeywordValue(
            instrument=types.Instrument.RSS,
            instrument_keyword=types.InstrumentKeyword.GRATING,
            observation_id=12,
            value="a" * 201,
        )

    assert "value" in str(excinfo)


# Observation


def test_observation_is_created_correctly():
    observation = types.Observation(
        data_release=date(2020, 4, 7),
        instrument=types.Instrument.RSS,
        intent=types.Intent.SCIENCE,
        meta_release=date(2019, 9, 5),
        observation_group="ABC",
        observation_type=types.ObservationType.OBJECT,
        proposal_id=42,
        status=types.Status.ACCEPTED,
        telescope=types.Telescope.SALT,
    )

    assert observation.data_release == date(2020, 4, 7)
    assert observation.instrument == types.Instrument.RSS
    assert observation.intent == types.Intent.SCIENCE
    assert observation.meta_release == date(2019, 9, 5)
    assert observation.observation_group == "ABC"
    assert observation.observation_type == types.ObservationType.OBJECT
    assert observation.proposal_id == 42
    assert observation.status == types.Status.ACCEPTED
    assert observation.telescope == types.Telescope.SALT


def test_data_release_earlier_than_meta_release():
    with pytest.raises(ValueError) as excinfo:
        types.Observation(
            data_release=date(2020, 4, 7),
            instrument=types.Instrument.RSS,
            intent=types.Intent.SCIENCE,
            meta_release=date(2020, 4, 8),
            observation_group="ABC",
            observation_type=types.ObservationType.OBJECT,
            proposal_id=42,
            status=types.Status.ACCEPTED,
            telescope=types.Telescope.SALT,
        )

    assert "data release" in str(excinfo)


def test_observation_group_too_long():
    with pytest.raises(ValueError) as excinfo:
        types.Observation(
            data_release=date(2020, 4, 7),
            instrument=types.Instrument.RSS,
            intent=types.Intent.SCIENCE,
            meta_release=date(2019, 4, 7),
            observation_group="A" * 41,
            observation_type=types.ObservationType.OBJECT,
            proposal_id=42,
            status=types.Status.ACCEPTED,
            telescope=types.Telescope.SALT,
        )

    assert "observation group" in str(excinfo)


# ObservationTime


def test_observation_time_is_created_correctly():
    observation_time = types.ObservationTime(
        end_time=datetime(2019, 9, 6, 1, 12, 7, 0),
        exposure_time=500 * u.second,
        plane_id=123456,
        resolution=470 * u.second,
        start_time=datetime(2019, 9, 6, 1, 3, 47, 0),
    )

    assert observation_time.end_time == datetime(2019, 9, 6, 1, 12, 7, 0)
    assert observation_time.exposure_time.to_value(u.second) == 500
    assert observation_time.plane_id == 123456
    assert observation_time.resolution.to_value(u.second) == 470
    assert observation_time.start_time == datetime(2019, 9, 6, 1, 3, 47, 0)


def test_observation_start_time_must_not_be_later_than_end_time():
    with pytest.raises(ValueError) as excinfo:
        observation_time = types.ObservationTime(
            end_time=datetime(2019, 9, 6, 1, 12, 7, 0),
            exposure_time=500 * u.second,
            plane_id=123456,
            resolution=470 * u.second,
            start_time=datetime(2019, 9, 6, 1, 12, 8, 0),
        )

    assert "start" in str(excinfo) and "end" in str(excinfo)


def test_observation_exposure_time_must_be_non_negative():
    with pytest.raises(ValueError) as excinfo:
        types.ObservationTime(
            end_time=datetime(2019, 9, 6, 1, 12, 7, 0),
            exposure_time=-1 * u.second,
            plane_id=123456,
            resolution=470 * u.second,
            start_time=datetime(2019, 9, 6, 1, 3, 47, 0),
        )

    assert "exposure time" in str(excinfo) and "non-negative" in str(excinfo)


def test_observation_exposure_time_must_have_a_time_unit():
    with pytest.raises(ValueError) as excinfo:
        types.ObservationTime(
            end_time=datetime(2019, 9, 6, 1, 12, 7, 0),
            exposure_time=500 * u.meter,
            plane_id=123456,
            resolution=470 * u.second,
            start_time=datetime(2019, 9, 6, 1, 3, 47, 0),
        )

    assert "exposure time" in str(excinfo) and "unit" in str(excinfo)


def test_observation_time_resolution_must_be_non_negative():
    with pytest.raises(ValueError) as excinfo:
        types.ObservationTime(
            end_time=datetime(2019, 9, 6, 1, 12, 7, 0),
            exposure_time=500 * u.second,
            plane_id=123456,
            resolution=-470 * u.second,
            start_time=datetime(2019, 9, 6, 1, 3, 47, 0),
        )

    assert "resolution" in str(excinfo) and "non-negative" in str(excinfo)


def test_observation_time_resolution_must_have_a_time_unit():
    with pytest.raises(ValueError) as excinfo:
        types.ObservationTime(
            end_time=datetime(2019, 9, 6, 1, 12, 7, 0),
            exposure_time=500 * u.second,
            plane_id=123456,
            resolution=470 * u.meter,
            start_time=datetime(2019, 9, 6, 1, 3, 47, 0),
        )

    assert "time resolution" in str(excinfo) and "unit" in str(excinfo)


# Plane


def test_plane_is_created_correctly():
    plane = types.Plane(observation_id=67)

    assert plane.observation_id == 67


# Polarization


def test_polarization_is_created_correctly():
    polarization = types.Polarization(
        plane_id=956, stokes_parameter=types.StokesParameter.U
    )

    assert polarization.plane_id == 956
    assert polarization.stokes_parameter == types.StokesParameter.U


# Position


def test_position_is_created_correctly():
    position = types.Position(
        dec=-42.9 * u.degree, equinox=2000, plane_id=515, ra=128.9 * u.degree
    )

    assert position.dec.to_value(u.degree) == -42.9
    assert position.equinox == 2000
    assert position.plane_id == 515
    assert position.ra.to_value(u.degree) == 128.9


def test_position_declination_must_have_an_angular_unit():
    with pytest.raises(ValueError) as excinfo:
        types.Position(
            dec=-42.9 * u.meter, equinox=2000, plane_id=515, ra=128.9 * u.degree
        )

    assert "declination" in str(excinfo) and "angular" in str(excinfo)


@pytest.mark.parametrize("dec", [-180, -90.0001, 90.00001, 180])
def test_position_declination_must_be_in_allowed_range(dec):
    with pytest.raises(ValueError) as excinfo:
        types.Position(
            dec=dec * u.degree, equinox=2000, plane_id=515, ra=128.9 * u.degree
        )

    assert "declination" in str(excinfo) and "-90" in str(excinfo)


def test_position_equinox_must_not_be_earlier_than_1900():
    with pytest.raises(ValueError) as excinfo:
        types.Position(
            dec=12 * u.degree, equinox=1899.999, plane_id=515, ra=128.9 * u.degree
        )

    assert "equinox" in str(excinfo)


def test_position_right_ascension_must_have_an_angular_unit():
    with pytest.raises(ValueError) as excinfo:
        types.Position(
            dec=-42.9 * u.degree, equinox=2000, plane_id=515, ra=128.9 * u.meter
        )

    assert "right ascension" in str(excinfo) and "angular" in str(excinfo)


@pytest.mark.parametrize("ra", [-90, -0.0001, 360, 413.5])
def test_position_declination_must_be_in_allowed_range(ra):
    with pytest.raises(ValueError) as excinfo:
        types.Position(
            dec=-23.9 * u.degree, equinox=2000, plane_id=515, ra=ra * u.degree
        )

    assert "right ascension" in str(excinfo) and "360" in str(excinfo)


# Proposal


def test_proposal_is_created_correctly():
    proposal = types.Proposal(
        institution=types.Institution.SAAO, pi="John Doe", proposal_code='2019-1-SCI-042',  title="Some Proposal"
    )

    assert proposal.institution == types.Institution.SAAO
    assert proposal.pi == "John Doe"
    assert proposal.title == "Some Proposal"


def test_proposal_pi_too_long():
    with pytest.raises(ValueError) as excinfo:
        types.Proposal(
            institution=types.Institution.SAAO, pi=101 * "a", proposal_code='2019-1-SCI-042', title="Some Proposal"
        )

    assert "PI" in str(excinfo)


def test_proposal_proposal_code_too_long():
    with pytest.raises(ValueError) as excinfo:
        types.Proposal(
            institution=types.Institution.SAAO, pi='John Doe', proposal_code='p' * 51, title="Some Proposal"
        )

    assert "proposal code" in str(excinfo)


def test_proposal_title_too_long():
    with pytest.raises(ValueError) as excinfo:
        types.Proposal(
            institution=types.Institution.SALT, pi="John Doe", proposal_code='2019-1-SCI-042', title=201 * "a"
        )

    assert "title" in str(excinfo)


# Target


def test_target_is_created_correctly():
    target = types.Target(
        name="NGC 123", observation_id=1015, standard=False, target_type="10.1.9.4"
    )

    assert target.name == "NGC 123"
    assert target.observation_id == 1015
    assert target.standard is False
    assert target.target_type == "10.1.9.4"


def test_target_name_too_long():
    with pytest.raises(ValueError) as excinfo:
        target = types.Target(
            name="T" * 51, observation_id=1015, standard=False, target_type="10.1.9.4"
        )

    assert "target name" in str(excinfo)


# TaskExecutionMode


@pytest.mark.parametrize(
    "mode",
    [
        ("dummy", types.TaskExecutionMode.DUMMY),
        ("production", types.TaskExecutionMode.PRODUCTION),
    ],
)
def test_task_execution_modes_can_be_created_from_mode(mode):
    assert types.TaskExecutionMode.for_mode(mode[0]) == mode[1]


@pytest.mark.parametrize(
    "mode", ["production", "Production", "pRODuctIon", "PRODUCTION"]
)
def test_task_execution_for_mode_is_case_insensitive(mode):
    assert types.TaskExecutionMode.for_mode(mode) == types.TaskExecutionMode.PRODUCTION


# TaskName


@pytest.mark.parametrize(
    "task_name", [("delete", types.TaskName.DELETE), ("insert", types.TaskName.INSERT)]
)
def test_task_names_can_be_created_from_name(task_name):
    assert types.TaskName.for_name(task_name[0]) == task_name[1]


@pytest.mark.parametrize("name", ["insert", "Insert", "InSeRt", "INSERT"])
def test_task_name_for_name_is_case_insensitive(name):
    assert types.TaskName.for_name(name) == types.TaskName.INSERT
