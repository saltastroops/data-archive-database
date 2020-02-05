from datetime import datetime, timedelta

from astropy import units as u
from typing import Any, Optional

from astropy.units import Quantity
from astropy.units import def_unit, Quantity
from dateutil.tz import tz

from ssda.instrument.rss_observation_properties import RssObservationProperties
from ssda.util import types
from ssda.util.salt_observation import SALTObservation


class FakeSaltDatabaseService:
    def __init__(self, database_config: Any):
        pass

    def find_pi(self, block_visit: str) -> Optional[str]:
        return f"pi of block {block_visit}"

    def find_proposal_code(self, block_visit: str) -> Optional[str]:
        return f"proposal code of {block_visit}"

    def find_proposal_title(self, block_visit: str) -> Optional[str]:
        return f"Title of block {block_visit}"

    def find_release_date(self, block_visit: str) -> Optional[datetime]:
        return datetime(2019, 1, 1)

    def find_meta_release_date(self, block_visit: str) -> Optional[datetime]:
        return datetime(2019, 1, 1)

    def find_observation_status(self, block_visit: str) -> Optional[str]:
        return


class FakeProposal(object):
    def __init__(self, pi: str, title: str, proposal_code: str):
        self._institution = types.Institution.SALT
        self._pi = pi
        self._proposal_code = proposal_code
        self._title = title

    @property
    def institution(self) -> types.Institution:
        return self._institution

    @property
    def pi(self) -> str:
        return self._pi

    @property
    def title(self) -> str:
        return self._title

    @property
    def proposal_code(self) -> str:
        return self._proposal_code


def fake_proposal(pi: str, title: str, proposal_code: str) -> Any:
    return FakeProposal(
        pi=pi,
        title=title,
        proposal_code=proposal_code
    )


class FakeFitsFile(object):
    def __init__(self, headers):
        self._headers=headers
        self._size = {"OBJECT": "arc"}
        self._file_path = "path"

    @property
    def header_value(self, key_word) -> Any:
        return self._headers.get(key_word)

    @property
    def headers(self) -> Any:
        return self._header_value

    def size(self) -> Any:
        return self._header_value

    def checksum(self) -> str:
        return ""

    def file_path(self):
        return self._file_path

    def instrument(self) -> str:
        """
        The instrument a file belongs too.

        Returns
        -------
        str :
            The Instrument.

        """

        return ""
    pass


class FakeSALTObservation(object):
    def __init__(self, proposal=None):
        if proposal:
            self._proposal = proposal
        else:
            self._proposal = fake_proposal(pi="Name_1", title="Title_1", proposal_code="Code_1")

    @property
    def proposal(self) -> Optional[Any]:
        return self._proposal
    pass


def fake_fit_file() -> Any:
    return FakeFitsFile()


def fake_database_service() -> Any:
    return FakeSaltDatabaseService(None)


def fake_salt_observation(proposal: dict = None) -> Any:
    return FakeSALTObservation(proposal)


rss_obs = RssObservationProperties(
    fits_file=fake_fit_file(),
    database_service=fake_database_service()
)

salt_obs = SALTObservation(
    fits_file=fake_fit_file(),
    database_service=fake_database_service()
)


def test_artifact(mocker):
    with mocker.patch.object(rss_obs, 'artifact', return_value=types.Artifact(
            content_checksum="Sum_1",
            content_length=Quantity(value=100, unit=types.byte),
            identifier="randomtext",
            name="filename.fits",
            plane_id=1,
            path="path/to/file/filename.fits",
            product_type=types.ProductType.ARC,
    )):
        assert rss_obs.artifact(1).product_type == types.ProductType.ARC


def test_energy(mocker):
    with mocker.patch.object(rss_obs, 'energy', return_value=types.Energy(
            dimension=1,
            max_wavelength=Quantity(value=2, unit=u.meter),
            min_wavelength=Quantity(
                value=1,
                unit=u.meter
            ),
            plane_id=1,
            resolving_power=1.0,
            sample_size=Quantity(
                value=1,
                unit=u.meter
            )
    )):
        energy = rss_obs.energy(1)
        assert energy.dimension == 1
        assert energy.max_wavelength.value == 2
        assert energy.min_wavelength.value == 1
        assert energy.resolving_power == 1.0


#  Done
def test_observation(mocker):
    with mocker.patch.object(rss_obs, 'observation', return_value=types.Observation(
            data_release=datetime(year=2019, month=1, day=1),
            instrument=types.Instrument.RSS,
            intent=types.Intent.CALIBRATION,
            meta_release=datetime(year=2019, month=1, day=1),
            observation_group="1001",
            observation_type=types.ObservationType.OBJECT,
            proposal_id=101,
            status=types.Status.ACCEPTED,
            telescope=types.Telescope.SALT
    )):
        observation = rss_obs.observation(101)
        assert observation.telescope == types.Telescope.SALT
        assert observation.proposal_id == 101
        assert observation.observation_group == "1001"


def test_observation_time(mocker):
    start_time = datetime(year=2019, month=1, day=1, hour=0, minute=0, second=0, tzinfo=tz.gettz("Africa/Johannesburg"))
    exposure_time = 100
    with mocker.patch.object(rss_obs, 'observation_time', return_value=types.ObservationTime(
            end_time=start_time + timedelta(seconds=exposure_time),
            exposure_time=exposure_time * u.second,
            plane_id=1,
            resolution=exposure_time * u.second,
            start_time=start_time
    )):
        observation_time = rss_obs.observation_time(1)
        assert observation_time.end_time == datetime(year=2019, month=1, day=1, hour=0, minute=1, second=40,
                                                                tzinfo=tz.gettz("Africa/Johannesburg"))
        assert observation_time.exposure_time == Quantity(value=100, unit=u.second)


def test_polarizations(mocker):
    with mocker.patch.object(rss_obs, 'polarizations', return_value=[
        types.Polarization(
            plane_id=1,
            stokes_parameter=types.StokesParameter.I
        )
    ]):
        assert rss_obs.polarizations(1)[0].stokes_parameter == types.StokesParameter.I


def test_position(mocker):
    with mocker.patch.object(rss_obs, 'position', return_value=(
            types.Position(
                dec=50 * u.degree,
                equinox=2000,
                plane_id=1,
                ra=100 * u.degree
            )
    )):
        position = rss_obs.position(1)
        assert position.dec == Quantity(value=50, unit=u.degree)
        assert position.ra == Quantity(value=100, unit=u.degree)
        assert position.equinox == 2000


def test_proposal(mocker):
    with mocker.patch.object(rss_obs, 'proposal', return_value=types.Proposal(
            institution=types.Institution.SALT,
            pi="Name_1",
            proposal_code="Code_1",
            title="Title_1"
    )):
        assert rss_obs.proposal().institution == types.Institution.SALT
        assert rss_obs.proposal().pi == "Name_1"
        assert rss_obs.proposal().proposal_code == "Code_1"
        assert rss_obs.proposal().title == "Title_1"


def test_proposal_investigators(mocker):

    with mocker.patch.object(rss_obs, 'proposal_investigators', return_value=[
        types.ProposalInvestigator(
            proposal_id=101,
            investigator_id="Investigator_1"
        ),
        types.ProposalInvestigator(
            proposal_id=101,
            investigator_id="Investigator_2"
        ),
        types.ProposalInvestigator(
            proposal_id=101,
            investigator_id="Investigator_3"
        )
    ]):
        assert rss_obs.proposal_investigators(101)[0].investigator_id == "Investigator_1"
        assert rss_obs.proposal_investigators(101)[1].investigator_id == "Investigator_2"
        assert rss_obs.proposal_investigators(101)[2].investigator_id == "Investigator_3"
