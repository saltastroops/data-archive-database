import os
import pytest

from ssda.util.types import (
    Instrument,
    TaskName,
    FilePath,
    DatabaseConfiguration,
    TaskExecutionMode,
)


# DatabaseConfiguration


def test_database_config_accepts_valid_configuration():
    assert DatabaseConfiguration(
        host="127.0.0.1",
        username="observation",
        password="secret",
        database="archive",
        port=3306,
    )


@pytest.mark.parametrize("port", [0, -1, -1024])
def test_database_config_rejects_non_positive_port(port):
    with pytest.raises(ValueError) as excinfo:
        DatabaseConfiguration(
            host="127.0.0.1",
            username="observation",
            password="secret",
            database="archive",
            port=port,
        )


def test_database_configuration_equality():
    some_config = DatabaseConfiguration(
        host="localhost",
        username="user",
        password="secret",
        database="archive",
        port=3306,
    )
    same_config = DatabaseConfiguration(
        host="localhost",
        username="user",
        password="secret",
        database="archive",
        port=3306,
    )

    assert some_config == same_config


def test_database_configuration_non_equality():
    some_config = DatabaseConfiguration(
        host="localhost",
        username="user",
        password="secret",
        database="archive",
        port=3306,
    )
    other_config = DatabaseConfiguration(
        host="127.0.0.1",
        username="user",
        password="secret",
        database="archive",
        port=3306,
    )
    assert some_config != other_config

    other_config = DatabaseConfiguration(
        host="localhost",
        username="otheruser",
        password="secret",
        database="archive",
        port=3306,
    )
    assert some_config != other_config

    other_config = DatabaseConfiguration(
        host="localhost",
        username="user",
        password="topsecret",
        database="archive",
        port=3306,
    )
    assert some_config != other_config

    other_config = DatabaseConfiguration(
        host="localhost",
        username="user",
        password="secret",
        database="observations",
        port=3306,
    )
    assert some_config != other_config

    other_config = DatabaseConfiguration(
        host="localhost",
        username="user",
        password="secret",
        database="archive",
        port=3307,
    )
    assert some_config != other_config


# FilePath


def test_file_path_requires_a_regular_file(mocker):
    def fake_isfile(path: str) -> bool:
        return "regular" in path

    mocker.patch.object(os.path, "isfile", new=fake_isfile)

    assert FilePath("regular.fits")

    with pytest.raises(ValueError) as excinfo:
        FilePath("missing.fits")
    assert "regular" in str(excinfo.value)


# Instrument


def test_instrument_for_name_rejects_invalid_name():
    with pytest.raises(ValueError) as excinfo:
        Instrument.for_name("Xghyu")
    assert "instrument name" in str(excinfo.value)


@pytest.mark.parametrize(
    "instrument",
    [
        ("Salticam", Instrument.SALTICAM),
        ("RSS", Instrument.RSS),
        ("HRS", Instrument.HRS),
    ],
)
def test_instruments_can_be_created_from_name(instrument):
    assert Instrument.for_name(instrument[0]) == instrument[1]


@pytest.mark.parametrize("name", ["RSS", "rss", "Rss", "rSs", "rSS"])
def test_instrument_for_name_is_case_insensitive(name):
    assert Instrument.for_name(name) == Instrument.RSS


# TaskExecutionMode


@pytest.mark.parametrize(
    "mode",
    [("dummy", TaskExecutionMode.DUMMY), ("production", TaskExecutionMode.PRODUCTION)],
)
def test_task_execution_modes_can_be_created_from_mode(mode):
    assert TaskExecutionMode.for_mode(mode[0]) == mode[1]


@pytest.mark.parametrize(
    "mode", ["production", "Production", "pRODuctIon", "PRODUCTION"]
)
def test_task_execution_for_mode_is_case_insensitive(mode):
    assert TaskExecutionMode.for_mode(mode) == TaskExecutionMode.PRODUCTION


# TaskName


@pytest.mark.parametrize(
    "task_name", [("delete", TaskName.DELETE), ("insert", TaskName.INSERT)]
)
def test_task_names_can_be_created_from_name(task_name):
    assert TaskName.for_name(task_name[0]) == task_name[1]


@pytest.mark.parametrize("name", ["insert", "Insert", "InSeRt", "INSERT"])
def test_task_name_for_name_is_case_insensitive(name):
    assert TaskName.for_name(name) == TaskName.INSERT
