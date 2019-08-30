import glob
import pytest
from datetime import date
from typing import Iterator, NamedTuple

import ssda.util.fits
from ssda.util.types import Instrument, DateRange


def fake_fits_file_dir(night: date, instrument: Instrument, base_dir: str) -> str:
    date_str = night.strftime("%Y-%m-%d")

    return f"{base_dir}/{date_str}/{instrument.value}"


def fake_iglob(path: str) -> Iterator[str]:
    jan_1 = "2019-01-01"
    jan_2 = "2019-01-02"
    oct_27 = "2019-10-27"
    oct_28 = "2019-10-28"

    files = []
    if "RSS" in path:
        if jan_1 in path:
            files = ["RSS_A.fits", "RSS_B.fits"]
        if jan_2 in path:
            files = ["RSS_C.fits"]
        if oct_27 in path:
            files = ["RSS_D.fits", "RSS_E.fits", "RSS_F.fits"]
        if oct_28 in path:
            files = ["RSS_G.fits"]
    if "Salticam" in path:
        if jan_1 in path:
            files = []
        if jan_2 in path:
            files = ["Salticam_A.fits"]
        if oct_27 in path:
            files = ["Salticam_B.fits"]
        if oct_28 in path:
            files = ["Salticam_C.fits"]
    if "HRS" in path:
        if jan_1 in path:
            files = []
        if jan_2 in path:
            files = ["HRS_A.fits"]
        if oct_27 in path:
            files = ["HRS_B.fits"]
        if oct_28 in path:
            files = ["HRS_C.fits"]

    dir = path.replace("*.fits", "")
    return (f"{dir}{file}" for file in files)


def test_fits_file_paths_returns_correct_paths(mocker):
    mocker.patch.object(glob, "iglob", new=fake_iglob)
    mocker.patch.object(ssda.util.fits, "fits_file_dir", new=fake_fits_file_dir)

    # several nights
    paths = set(
        ssda.util.fits.fits_file_paths(
            DateRange(date(2019, 1, 1), date(2019, 10, 28)),
            {Instrument.RSS, Instrument.SALTICAM},
            "/fits",
        )
    )
    assert paths == {
        "/fits/2019-01-01/RSS/RSS_A.fits",
        "/fits/2019-01-01/RSS/RSS_B.fits",
        "/fits/2019-01-02/RSS/RSS_C.fits",
        "/fits/2019-10-27/RSS/RSS_D.fits",
        "/fits/2019-10-27/RSS/RSS_E.fits",
        "/fits/2019-10-27/RSS/RSS_F.fits",
        "/fits/2019-01-02/Salticam/Salticam_A.fits",
        "/fits/2019-10-27/Salticam/Salticam_B.fits",
    }

    # single night
    paths = set(
        ssda.util.fits.fits_file_paths(
            DateRange(date(2019, 10, 28), date(2019, 10, 29)), {Instrument.HRS}, "/fits"
        )
    )
    assert paths == {"/fits/2019-10-28/HRS/HRS_C.fits"}

    # no instrument
    paths = set(
        ssda.util.fits.fits_file_paths(
            DateRange(date(2019, 1, 1), date(2019, 10, 28)), set(), "/fits"
        )
    )
    assert paths == set()


class FitsFileDirParams(NamedTuple):
    night: date
    instrument: Instrument
    base_dir: str
    path: str


@pytest.mark.parametrize(
    "params",
    [
        FitsFileDirParams(
            night=date(2019, 7, 17),
            instrument=Instrument.HRS,
            base_dir="/fits",
            path="/fits/salt/data/2019/0717/hrs/raw",
        ),
        FitsFileDirParams(
            night=date(2020, 10, 3),
            instrument=Instrument.HRS,
            base_dir="/",
            path="/salt/data/2020/1003/hrs/raw",
        ),
        FitsFileDirParams(
            night=date(2019, 1, 4),
            instrument=Instrument.RSS,
            base_dir="/fits",
            path="/fits/salt/data/2019/0104/rss/raw",
        ),
        FitsFileDirParams(
            night=date(2020, 11, 23),
            instrument=Instrument.RSS,
            base_dir="/",
            path="/salt/data/2020/1123/rss/raw",
        ),
        FitsFileDirParams(
            night=date(2019, 3, 30),
            instrument=Instrument.SALTICAM,
            base_dir="/fits",
            path="/fits/salt/data/2019/0330/scam/raw",
        ),
        FitsFileDirParams(
            night=date(2020, 12, 1),
            instrument=Instrument.SALTICAM,
            base_dir="/",
            path="/salt/data/2020/1201/scam/raw",
        ),
    ],
)
def test_fits_file_dir_returns_correct_dir(params):
    assert (
        ssda.util.fits.fits_file_dir(
            night=params.night, instrument=params.instrument, base_dir=params.base_dir
        )
        == params.path
    )
