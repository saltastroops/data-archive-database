from click import UsageError
from click.testing import CliRunner
from datetime import date, datetime
from typing import NamedTuple, Optional, Set
import pytest
import glob

import ssda.cli
import ssda.task
import ssda.util.fits
from ssda.cli import parse_date, validate_options, main
from ssda.util.dummy import DummyObservationProperties
from ssda.util.types import Instrument, DateRange


class Options(NamedTuple):
    start: Optional[date]
    end: Optional[date]
    file: Optional[str]
    instruments: Set[Instrument]
    fits_base_dir: Optional[str]


def _options(
    start: Optional[date] = None,
    end: Optional[date] = None,
    file: Optional[str] = None,
    instruments=None,
    fits_base_dir=None,
) -> Options:
    if instruments is None:
        instruments = {}
    return Options(
        start=start,
        end=end,
        file=file,
        instruments=instruments,
        fits_base_dir=fits_base_dir,
    )


# parsing dates


def test_parse_date_parses_correctly():
    today = date(2019, 8, 30)
    yesterday = date(2019, 8, 29)

    now = lambda: datetime(2019, 8, 30, 5, 9, 13)

    assert parse_date("2019-05-04", now) == date(2019, 5, 4)

    assert parse_date("yesterday", now) == yesterday

    assert parse_date("today", now) == today


@pytest.mark.parametrize(
    "invalid_date", ["1 Jan 2019", "19-01-05", "2019/09/03", "2019-05-32"]
)
def test_parse_date_rejects_invalid_dates(invalid_date: str):
    now = lambda: datetime(2019, 8, 30, 5, 9, 13)

    with pytest.raises(UsageError) as excinfo:
        parse_date(invalid_date, now)
    assert "date" in str(excinfo.value)


# main function


def test_a_start_date_requires_an_end_date():
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "--start",
            "2019-04-09",
            "--fits-base-dir",
            "/tmp",
            "--instrument",
            "RSS",
            "--task",
            "insert",
            "--mode",
            "dummy",
        ],
    )
    assert result.exit_code != 0
    assert "start" in str(result.output)


def test_an_end_date_requires_a_start_date():
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "--end",
            "2019-04-09",
            "--fits-base-dir",
            "/tmp",
            "--task",
            "insert",
            "--mode",
            "dummy",
        ],
    )
    assert result.exit_code != 0
    assert "end" in str(result.output)


def test_file_is_not_allowed_with_dates():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("whatever.fits", "w") as f:
            f.write("Dummy FITS file")
        result = runner.invoke(
            main,
            [
                "--start",
                "2019-04-08",
                "--end",
                "2019-04-09",
                "--fits-base-dir",
                "/tmp",
                "--instrument",
                "RSS",
                "--task",
                "insert",
                "--mode",
                "dummy",
                "--file",
                "whatever.fits",
            ],
        )
        assert result.exit_code != 0
        assert "file" in str(result.output)


def test_file_is_not_allowed_with_an_instrument():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("whatever.fits", "w") as f:
            f.write("Dummy FITS file")
        result = runner.invoke(
            main,
            [
                "--instrument",
                "RSS",
                "--task",
                "insert",
                "--mode",
                "dummy",
                "--file",
                "whatever.fits",
            ],
        )
        assert result.exit_code != 0
        assert "file" in str(result.output) and "instrument" in str(result.output)


def test_a_base_directory_is_required_with_dates():
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "--start",
            "2019-04-08",
            "--end",
            "2019-04-09",
            "--instrument",
            "RSS",
            "--task",
            "insert",
            "--mode",
            "dummy",
        ],
    )
    assert result.exit_code != 0
    assert "base directory" in str(result.output)


def test_a_base_directory_is_not_allowed_with_a_file():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("whatever.fits", "w") as f:
            f.write("Dummy FITS file")
        result = runner.invoke(
            main,
            [
                "--file",
                "whatever.fits",
                "--fits-base-dir",
                "/tmp",
                "--instrument",
                "RSS",
                "--task",
                "insert",
                "--mode",
                "dummy",
            ],
        )
        assert result.exit_code != 0
        assert "base" in str(result.output) and "file" in str(result.output)


def test_the_start_date_must_be_earlier_than_the_end_date():
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "--start",
            "2019-04-09",
            "--end",
            "2019-04-09",
            "--fits-base-dir",
            "/tmp",
            "--instrument",
            "RSS",
            "--task",
            "insert",
            "--mode",
            "dummy",
        ],
    )
    assert result.exit_code != 0
    assert "start" in str(result.output) and "end" in str(result.output)

    result = runner.invoke(
        main,
        [
            "--start",
            "2019-04-10",
            "--end",
            "2019-04-09",
            "--fits-base-dir",
            "/tmp",
            "--instrument",
            "RSS",
            "--task",
            "insert",
            "--mode",
            "dummy",
        ],
    )
    assert result.exit_code != 0
    assert "start" in str(result.output) and "end" in str(result.output)
