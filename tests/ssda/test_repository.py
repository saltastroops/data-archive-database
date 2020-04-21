from datetime import date, datetime
from typing import Any, Optional, List

import astropy.units as u
from dateutil import tz

import ssda.database.ssda
from ssda.observation import ObservationProperties
from ssda.repository import delete, insert
from ssda.util import types
from ssda.util.types import ProposalType

INSTRUMENT_SETUP_ID = 492

OBSERVATION_GROUP_ID = 513

OBSERVATION_ID = 24

PLANE_ID = 12346

PROPOSAL_ID = 67

QUERIES = [
    types.SQLQuery(
        sql="INSERT INTO instrument_setup (filter_id) VALUES (%(filter_id)s)",
        parameters=dict(filter_id="46"),
    ),
    types.SQLQuery(
        sql="INSERT INTO rss_setup (instrument_setup_id, rss_fabry_perot_mode_id, rss_grating_id) VALUES (%(instrument_setup_id)s, %(fabry_perot_mode_id)s, %(grating_id)s)",
        parameters=dict(
            instrument_setup_id="45", fabry_perot_mode_id="89", grating_id="22"
        ),
    ),
]


def assert_equal_properties(a: Any, b: Any):
    for attr in dir(a):
        # The magic methods will not be the same for different instances, but we can
        # ignore them.
        if not attr.startswith("__"):
            assert getattr(a, attr) == getattr(b, attr)


class ObservationPropertiesStub(ObservationProperties):
    def artifact(self, plane_id: int) -> types.Artifact:
        return types.Artifact(
            content_checksum="chu346jh",
            content_length=13095 * types.byte,
            identifier="cv7hjas4",
            name="rss-12349.fits",
            plane_id=plane_id,
            path="/some/path/rss-12349.fits",
            product_type=types.ProductType.SCIENCE,
        )

    def energy(self, plane_id: int) -> types.Energy:
        return types.Energy(
            dimension=512,
            max_wavelength=7000 * u.nanometer,
            min_wavelength=6500 * u.nanometer,
            plane_id=plane_id,
            resolving_power=915,
            sample_size=2.74 * u.nanometer,
        )

    def instrument_keyword_values(
        self, observation_id: int
    ) -> List[types.InstrumentKeywordValue]:
        return [
            types.InstrumentKeywordValue(
                instrument=types.Instrument.RSS,
                instrument_keyword=types.InstrumentKeyword.GRATING,
                observation_id=observation_id,
                value="pg1300",
            ),
            types.InstrumentKeywordValue(
                instrument=types.Instrument.RSS,
                instrument_keyword=types.InstrumentKeyword.FILTER,
                observation_id=observation_id,
                value="some_filter",
            ),
        ]

    def instrument_setup(self, observation_id: int) -> types.InstrumentSetup:
        return types.InstrumentSetup(
            additional_queries=QUERIES,
            detector_mode=types.DetectorMode.NORMAL,
            filter=types.Filter.JOHNSON_U,
            instrument_mode=types.InstrumentMode.IMAGING,
            observation_id=observation_id,
        )

    def observation(
        self, observation_group_id: int, proposal_id: int
    ) -> types.Observation:
        return types.Observation(
            data_release=date(2020, 1, 1),
            instrument=types.Instrument.RSS,
            intent=types.Intent.SCIENCE,
            meta_release=date(2019, 10, 14),
            observation_group_id=observation_group_id,
            observation_type=types.ObservationType.OBJECT,
            proposal_id=proposal_id,
            status=types.Status.ACCEPTED,
            telescope=types.Telescope.SALT,
        )

    def observation_group(self):
        return types.ObservationGroup(group_identifier="B67", name="NGC 1234 Obs")

    def observation_time(self, plane_id: int) -> types.ObservationTime:
        return types.ObservationTime(
            end_time=datetime(
                2019, 9, 7, 23, 10, 10, tzinfo=tz.gettz("Africa/Johannesburg")
            ),
            exposure_time=40 * u.second,
            plane_id=plane_id,
            resolution=40 * u.second,
            start_time=datetime(
                2019, 9, 7, 23, 9, 30, tzinfo=tz.gettz("Africa/Johannesburg")
            ),
        )

    def plane(self, observation_id: int) -> types.Plane:
        return types.Plane(
            data_product_type=types.DataProductType.SPECTRUM,
            observation_id=observation_id,
        )

    def polarization(self, plane_id: int) -> types.Polarization:
        return types.Polarization(
            plane_id=plane_id, polarization_mode=types.PolarizationMode.CIRCULAR
        )

    def position(self, plane_id: int) -> Optional[types.Position]:
        return types.Position(
            dec=-23.7 * u.degree, equinox=2000, plane_id=plane_id, ra=245.9 * u.deg
        )

    def proposal(self) -> types.Proposal:
        return types.Proposal(
            institution=types.Institution.SALT,
            pi="John Doe",
            proposal_code="2019-1-SCI-042",
            proposal_type=ProposalType.SCIENCE,
            title="Om testing a proposal",
        )

    def proposal_investigators(
        self, proposal_id: int
    ) -> List[types.ProposalInvestigator]:
        return [
            types.ProposalInvestigator(proposal_id=proposal_id, investigator_id="a54"),
            types.ProposalInvestigator(proposal_id=proposal_id, investigator_id="b13"),
            types.ProposalInvestigator(proposal_id=proposal_id, investigator_id="c09"),
        ]

    def target(self, observation_id: int) -> Optional[types.Target]:
        return types.Target(
            name="Some Interesting Target",
            observation_id=observation_id,
            standard=False,
            target_type="10.7.89.5",
        )


def test_observation_is_deleted(mocker):
    # mock the database access
    mock_database_service = mocker.patch("ssda.database.ssda.DatabaseService")
    mock_database_service.return_value.find_observation_id.return_value = 584

    database_config: Any = None
    observation_properties = ObservationPropertiesStub()
    delete(observation_properties, ssda.database.ssda.DatabaseService(database_config))

    # a transaction is used
    mock_database_service.return_value.begin_transaction.assert_called_once()
    mock_database_service.return_value.commit_transaction.assert_called_once()
    mock_database_service.return_value.rollback_transaction.assert_not_called()

    # the observation is deleted
    mock_database_service.return_value.delete_observation.assert_called_once()
    assert mock_database_service.return_value.delete_observation.call_args[0][0] == 584


def test_non_existing_observations_are_not_deleted(mocker):
    # mock the database access
    mock_database_service = mocker.patch("ssda.database.ssda.DatabaseService")
    mock_database_service.return_value.find_observation_id.return_value = None

    database_config: Any = None
    observation_properties = ObservationPropertiesStub()
    delete(observation_properties, ssda.database.ssda.DatabaseService(database_config))

    # no observation is deleted
    mock_database_service.return_value.delete_observation.assert_not_called()


def test_transactions_are_rolled_back_if_deleting_fails(mocker):
    # mock the database access
    mock_database_service = mocker.patch("ssda.database.ssda.DatabaseService")
    mock_database_service.return_value.find_observation_id.return_value = 584
    mock_database_service.return_value.delete_observation.side_effect = ValueError()

    database_config: Any = None
    observation_properties = ObservationPropertiesStub()
    try:
        delete(
            observation_properties, ssda.database.ssda.DatabaseService(database_config)
        )
    except:
        pass

    # a transaction is used and rolled back
    mock_database_service.return_value.begin_transaction.assert_called_once()
    mock_database_service.return_value.commit_transaction.assert_not_called()
    mock_database_service.return_value.rollback_transaction.assert_called_once()


def test_all_content_is_inserted(mocker):
    # mock the database access
    mock_database_service = mocker.patch("ssda.database.ssda.DatabaseService")
    mock_database_service.return_value.find_observation_id.return_value = None
    mock_database_service.return_value.find_observation_group_id.return_value = None
    mock_database_service.return_value.find_proposal_id.return_value = None
    mock_database_service.return_value.insert_artifact.return_value = 713
    mock_database_service.return_value.insert_energy.return_value = 92346
    mock_database_service.return_value.insert_instrument_keyword_value.side_effect = [
        1409,
        1410,
    ]
    mock_database_service.return_value.insert_instrument_setup.return_value = (
        INSTRUMENT_SETUP_ID
    )
    mock_database_service.return_value.insert_instrument_specific_content.return_value = (
        None
    )
    mock_database_service.return_value.insert_observation.return_value = OBSERVATION_ID
    mock_database_service.return_value.insert_observation_group.return_value = (
        OBSERVATION_GROUP_ID
    )
    mock_database_service.return_value.insert_observation_time.return_value = 23011
    mock_database_service.return_value.insert_plane.return_value = PLANE_ID
    mock_database_service.return_value.insert_polarization.return_value = None
    mock_database_service.return_value.insert_position.return_value = 4943
    mock_database_service.return_value.insert_proposal.return_value = PROPOSAL_ID
    mock_database_service.return_value.insert_target.return_value = 14054

    database_config: Any = None
    observation_properties = ObservationPropertiesStub()
    insert(observation_properties, ssda.database.ssda.DatabaseService(database_config))

    # a transaction is used
    mock_database_service.return_value.begin_transaction.assert_called_once()
    mock_database_service.return_value.commit_transaction.assert_called_once()
    mock_database_service.return_value.rollback_transaction.assert_not_called()

    # proposal inserted
    mock_database_service.return_value.insert_proposal.assert_called_once()
    assert_equal_properties(
        mock_database_service.return_value.insert_proposal.call_args[0][0],
        observation_properties.proposal(),
    )

    # proposal investigators inserted
    assert (
        mock_database_service.return_value.insert_proposal_investigator.call_count == 3
    )
    for i in range(3):
        assert_equal_properties(
            mock_database_service.return_value.insert_proposal_investigator.call_args_list[
                i
            ][
                0
            ][
                0
            ],
            observation_properties.proposal_investigators(PROPOSAL_ID)[i],
        )

    # observation group inserted
    mock_database_service.return_value.insert_observation_group.assert_called_once()
    assert_equal_properties(
        mock_database_service.return_value.insert_observation_group.call_args[0][0],
        observation_properties.observation_group(),
    )

    # observation inserted
    mock_database_service.return_value.insert_observation.assert_called_once()
    assert_equal_properties(
        mock_database_service.return_value.insert_observation.call_args[0][0],
        observation_properties.observation(OBSERVATION_GROUP_ID, PROPOSAL_ID),
    )

    # target inserted
    mock_database_service.return_value.insert_target.assert_called_once()
    assert_equal_properties(
        mock_database_service.return_value.insert_target.call_args[0][0],
        observation_properties.target(OBSERVATION_ID),
    )

    # instrument keyword values inserted
    assert (
        mock_database_service.return_value.insert_instrument_keyword_value.call_count
        == 2
    )
    for i in range(2):
        assert_equal_properties(
            mock_database_service.return_value.insert_instrument_keyword_value.call_args_list[
                i
            ][
                0
            ][
                0
            ],
            observation_properties.instrument_keyword_values(OBSERVATION_ID)[i],
        )

    # instrument setup inserted
    mock_database_service.return_value.insert_instrument_setup.assert_called_once()
    assert_equal_properties(
        mock_database_service.return_value.insert_instrument_setup.call_args[0][0],
        observation_properties.instrument_setup(OBSERVATION_ID),
    )

    # instrument-specific content inserted
    assert (
        mock_database_service.return_value.insert_instrument_specific_content.call_count
        == 2
    )
    for i in range(2):
        instrument_specific_content_query = QUERIES[i].sql
        instrument_specific_content_parameters = {
            key: value for key, value in QUERIES[i].parameters.items()
        }
        instrument_specific_content_parameters[
            "instrument_setup_id"
        ] = INSTRUMENT_SETUP_ID
        assert_equal_properties(
            mock_database_service.return_value.insert_instrument_specific_content.call_args_list[
                i
            ][
                0
            ][
                0
            ],
            instrument_specific_content_query,
        )
        assert (
            mock_database_service.return_value.insert_instrument_specific_content.call_args_list[
                i
            ][
                0
            ][
                1
            ].items()
            == instrument_specific_content_parameters.items()
        )

    # plane inserted
    mock_database_service.return_value.insert_plane.assert_called_once()
    assert_equal_properties(
        mock_database_service.return_value.insert_plane.call_args[0][0],
        observation_properties.plane(OBSERVATION_ID),
    )

    # energy inserted
    mock_database_service.return_value.insert_energy.assert_called_once()
    assert_equal_properties(
        mock_database_service.return_value.insert_energy.call_args[0][0],
        observation_properties.energy(PLANE_ID),
    )

    # polarization inserted
    mock_database_service.return_value.insert_polarization.assert_called_once()
    assert_equal_properties(
        mock_database_service.return_value.insert_polarization.call_args[0][0],
        observation_properties.polarization(PLANE_ID),
    )

    # observation time inserted
    mock_database_service.return_value.insert_observation_time.assert_called_once()
    assert_equal_properties(
        mock_database_service.return_value.insert_observation_time.call_args[0][0],
        observation_properties.observation_time(PLANE_ID),
    )

    # position inserted
    mock_database_service.return_value.insert_position.assert_called_once()
    assert_equal_properties(
        mock_database_service.return_value.insert_position.call_args[0][0],
        observation_properties.position(PLANE_ID),
    )

    # artifact inserted
    mock_database_service.return_value.insert_artifact.assert_called_once()
    assert_equal_properties(
        mock_database_service.return_value.insert_artifact.call_args[0][0],
        observation_properties.artifact(PLANE_ID),
    )


def test_proposals_are_not_reinserted(mocker):
    # mock the database access
    mock_database_service = mocker.patch("ssda.database.ssda.DatabaseService")
    mock_database_service.return_value.find_observation_id.return_value = None
    mock_database_service.return_value.find_observation_group_id.return_value = (
        OBSERVATION_GROUP_ID
    )
    mock_database_service.return_value.find_proposal_id.return_value = PROPOSAL_ID
    mock_database_service.return_value.insert_artifact.return_value = 713
    mock_database_service.return_value.insert_energy.return_value = 92346
    mock_database_service.return_value.insert_instrument_keyword_value.side_effect = [
        1409,
        1410,
    ]
    mock_database_service.return_value.insert_instrument_setup.return_value = (
        INSTRUMENT_SETUP_ID
    )
    mock_database_service.return_value.insert_instrument_specific_content.return_value = (
        None
    )
    mock_database_service.return_value.insert_observation.return_value = OBSERVATION_ID
    mock_database_service.return_value.insert_observation_time.return_value = 23011
    mock_database_service.return_value.insert_plane.return_value = PLANE_ID
    mock_database_service.return_value.insert_polarization.return_value = None
    mock_database_service.return_value.insert_position.return_value = 4943
    mock_database_service.return_value.insert_proposal.return_value = PROPOSAL_ID
    mock_database_service.return_value.insert_target.return_value = 14054

    database_config: Any = None
    observation_properties = ObservationPropertiesStub()
    insert(observation_properties, ssda.database.ssda.DatabaseService(database_config))

    # a transaction is used
    mock_database_service.return_value.begin_transaction.assert_called_once()
    mock_database_service.return_value.commit_transaction.assert_called_once()
    mock_database_service.return_value.rollback_transaction.assert_not_called()

    # proposal not reinserted
    mock_database_service.return_value.insert_proposal.assert_not_called()

    # proposal investigators not reinserted
    mock_database_service.return_value.insert_proposal_investigator.assert_not_called()

    # observation inserted
    mock_database_service.return_value.insert_observation.assert_called_once()
    assert_equal_properties(
        mock_database_service.return_value.insert_observation.call_args[0][0],
        observation_properties.observation(OBSERVATION_GROUP_ID, PROPOSAL_ID),
    )

    # target inserted
    mock_database_service.return_value.insert_target.assert_called_once()
    assert_equal_properties(
        mock_database_service.return_value.insert_target.call_args[0][0],
        observation_properties.target(OBSERVATION_ID),
    )

    # instrument keyword values inserted
    assert (
        mock_database_service.return_value.insert_instrument_keyword_value.call_count
        == 2
    )
    for i in range(2):
        assert_equal_properties(
            mock_database_service.return_value.insert_instrument_keyword_value.call_args_list[
                i
            ][
                0
            ][
                0
            ],
            observation_properties.instrument_keyword_values(OBSERVATION_ID)[i],
        )

    # instrument setup inserted
    mock_database_service.return_value.insert_instrument_setup.assert_called_once()
    assert_equal_properties(
        mock_database_service.return_value.insert_instrument_setup.call_args[0][0],
        observation_properties.instrument_setup(OBSERVATION_ID),
    )

    # instrument-specific content inserted
    assert (
        mock_database_service.return_value.insert_instrument_specific_content.call_count
        == 2
    )
    for i in range(2):
        instrument_specific_content_query = QUERIES[i].sql
        instrument_specific_content_parameters = {
            key: value for key, value in QUERIES[i].parameters.items()
        }
        instrument_specific_content_parameters[
            "instrument_setup_id"
        ] = INSTRUMENT_SETUP_ID
        assert_equal_properties(
            mock_database_service.return_value.insert_instrument_specific_content.call_args_list[
                i
            ][
                0
            ][
                0
            ],
            instrument_specific_content_query,
        )
        assert (
            mock_database_service.return_value.insert_instrument_specific_content.call_args_list[
                i
            ][
                0
            ][
                1
            ].items()
            == instrument_specific_content_parameters.items()
        )

    # plane inserted
    mock_database_service.return_value.insert_plane.assert_called_once()
    assert_equal_properties(
        mock_database_service.return_value.insert_plane.call_args[0][0],
        observation_properties.plane(OBSERVATION_ID),
    )

    # energy inserted
    mock_database_service.return_value.insert_energy.assert_called_once()
    assert_equal_properties(
        mock_database_service.return_value.insert_energy.call_args[0][0],
        observation_properties.energy(PLANE_ID),
    )

    # polarization inserted
    mock_database_service.return_value.insert_polarization.assert_called_once()
    assert_equal_properties(
        mock_database_service.return_value.insert_polarization.call_args[0][0],
        observation_properties.polarization(PLANE_ID),
    )

    # observation time inserted
    mock_database_service.return_value.insert_observation_time.assert_called_once()
    assert_equal_properties(
        mock_database_service.return_value.insert_observation_time.call_args[0][0],
        observation_properties.observation_time(PLANE_ID),
    )

    # position inserted
    mock_database_service.return_value.insert_position.assert_called_once()
    assert_equal_properties(
        mock_database_service.return_value.insert_position.call_args[0][0],
        observation_properties.position(PLANE_ID),
    )

    # artifact inserted
    mock_database_service.return_value.insert_artifact.assert_called_once()
    assert_equal_properties(
        mock_database_service.return_value.insert_artifact.call_args[0][0],
        observation_properties.artifact(PLANE_ID),
    )


def test_observation_groups_are_not_reinserted(mocker):
    # mock the database access
    mock_database_service = mocker.patch("ssda.database.ssda.DatabaseService")
    mock_database_service.return_value.find_observation_id.return_value = None
    mock_database_service.return_value.find_observation_group_id.return_value = (
        OBSERVATION_GROUP_ID
    )
    mock_database_service.return_value.find_proposal_id.return_value = PROPOSAL_ID
    mock_database_service.return_value.insert_artifact.return_value = 713
    mock_database_service.return_value.insert_energy.return_value = 92346
    mock_database_service.return_value.insert_instrument_keyword_value.side_effect = [
        1409,
        1410,
    ]
    mock_database_service.return_value.insert_instrument_setup.return_value = (
        INSTRUMENT_SETUP_ID
    )
    mock_database_service.return_value.insert_instrument_specific_content.return_value = (
        None
    )
    mock_database_service.return_value.insert_observation.return_value = OBSERVATION_ID
    mock_database_service.return_value.insert_observation_time.return_value = 23011
    mock_database_service.return_value.insert_plane.return_value = PLANE_ID
    mock_database_service.return_value.insert_polarization.return_value = None
    mock_database_service.return_value.insert_position.return_value = 4943
    mock_database_service.return_value.insert_proposal.return_value = PROPOSAL_ID
    mock_database_service.return_value.insert_target.return_value = 14054

    database_config: Any = None
    observation_properties = ObservationPropertiesStub()
    insert(observation_properties, ssda.database.ssda.DatabaseService(database_config))

    # a transaction is used
    mock_database_service.return_value.begin_transaction.assert_called_once()
    mock_database_service.return_value.commit_transaction.assert_called_once()
    mock_database_service.return_value.rollback_transaction.assert_not_called()

    # observation group not reinserted
    mock_database_service.return_value.insert_observation_group.assert_not_called()

    # proposal investigators not reinserted
    assert (
        mock_database_service.return_value.insert_proposal_investigator.asserrt_not_called()
    )

    # observation inserted
    mock_database_service.return_value.insert_observation.assert_called_once()
    assert_equal_properties(
        mock_database_service.return_value.insert_observation.call_args[0][0],
        observation_properties.observation(OBSERVATION_GROUP_ID, PROPOSAL_ID),
    )

    # target inserted
    mock_database_service.return_value.insert_target.assert_called_once()
    assert_equal_properties(
        mock_database_service.return_value.insert_target.call_args[0][0],
        observation_properties.target(OBSERVATION_ID),
    )

    # instrument keyword values inserted
    assert (
        mock_database_service.return_value.insert_instrument_keyword_value.call_count
        == 2
    )
    for i in range(2):
        assert_equal_properties(
            mock_database_service.return_value.insert_instrument_keyword_value.call_args_list[
                i
            ][
                0
            ][
                0
            ],
            observation_properties.instrument_keyword_values(OBSERVATION_ID)[i],
        )

    # instrument setup inserted
    mock_database_service.return_value.insert_instrument_setup.assert_called_once()
    assert_equal_properties(
        mock_database_service.return_value.insert_instrument_setup.call_args[0][0],
        observation_properties.instrument_setup(OBSERVATION_ID),
    )

    # instrument-specific content inserted
    assert (
        mock_database_service.return_value.insert_instrument_specific_content.call_count
        == 2
    )
    for i in range(2):
        instrument_specific_content_query = QUERIES[i].sql
        instrument_specific_content_parameters = {
            key: value for key, value in QUERIES[i].parameters.items()
        }
        instrument_specific_content_parameters[
            "instrument_setup_id"
        ] = INSTRUMENT_SETUP_ID
        assert_equal_properties(
            mock_database_service.return_value.insert_instrument_specific_content.call_args_list[
                i
            ][
                0
            ][
                0
            ],
            instrument_specific_content_query,
        )
        assert (
            mock_database_service.return_value.insert_instrument_specific_content.call_args_list[
                i
            ][
                0
            ][
                1
            ].items()
            == instrument_specific_content_parameters.items()
        )

    # plane inserted
    mock_database_service.return_value.insert_plane.assert_called_once()
    assert_equal_properties(
        mock_database_service.return_value.insert_plane.call_args[0][0],
        observation_properties.plane(OBSERVATION_ID),
    )

    # energy inserted
    mock_database_service.return_value.insert_energy.assert_called_once()
    assert_equal_properties(
        mock_database_service.return_value.insert_energy.call_args[0][0],
        observation_properties.energy(PLANE_ID),
    )

    # polarization inserted
    mock_database_service.return_value.insert_polarization.assert_called_once()
    assert_equal_properties(
        mock_database_service.return_value.insert_polarization.call_args[0][0],
        observation_properties.polarization(PLANE_ID),
    )

    # observation time inserted
    mock_database_service.return_value.insert_observation_time.assert_called_once()
    assert_equal_properties(
        mock_database_service.return_value.insert_observation_time.call_args[0][0],
        observation_properties.observation_time(PLANE_ID),
    )

    # position inserted
    mock_database_service.return_value.insert_position.assert_called_once()
    assert_equal_properties(
        mock_database_service.return_value.insert_position.call_args[0][0],
        observation_properties.position(PLANE_ID),
    )

    # artifact inserted
    mock_database_service.return_value.insert_artifact.assert_called_once()
    assert_equal_properties(
        mock_database_service.return_value.insert_artifact.call_args[0][0],
        observation_properties.artifact(PLANE_ID),
    )


def test_observations_are_not_reinserted(mocker):
    # mock the database access
    mock_database_service = mocker.patch("ssda.database.ssda.DatabaseService")
    mock_database_service.return_value.find_observation_id.return_value = OBSERVATION_ID
    mock_database_service.return_value.find_proposal_id.return_value = None
    mock_database_service.return_value.insert_artifact.return_value = 713
    mock_database_service.return_value.insert_energy.return_value = 92346
    mock_database_service.return_value.insert_instrument_keyword_value.side_effect = [
        1409,
        1410,
    ]
    mock_database_service.return_value.insert_instrument_setup.return_value = (
        INSTRUMENT_SETUP_ID
    )
    mock_database_service.return_value.insert_instrument_specific_content.return_value = (
        None
    )
    mock_database_service.return_value.insert_observation.return_value = OBSERVATION_ID
    mock_database_service.return_value.insert_observation_time.return_value = 23011
    mock_database_service.return_value.insert_plane.return_value = PLANE_ID
    mock_database_service.return_value.insert_polarization.return_value = None
    mock_database_service.return_value.insert_position.return_value = 4943
    mock_database_service.return_value.insert_proposal.return_value = PROPOSAL_ID
    mock_database_service.return_value.insert_target.return_value = 14054

    database_config: Any = None
    observation_properties = ObservationPropertiesStub()
    insert(observation_properties, ssda.database.ssda.DatabaseService(database_config))

    # a transaction is used
    mock_database_service.return_value.begin_transaction.assert_called_once()
    mock_database_service.return_value.commit_transaction.assert_called_once()
    mock_database_service.return_value.rollback_transaction.assert_not_called()

    # proposal inserted
    mock_database_service.return_value.insert_proposal.assert_called_once()
    assert_equal_properties(
        mock_database_service.return_value.insert_proposal.call_args[0][0],
        observation_properties.proposal(),
    )

    # proposal investigators inserted
    assert (
        mock_database_service.return_value.insert_proposal_investigator.call_count == 3
    )
    for i in range(3):
        assert_equal_properties(
            mock_database_service.return_value.insert_proposal_investigator.call_args_list[
                i
            ][
                0
            ][
                0
            ],
            observation_properties.proposal_investigators(PROPOSAL_ID)[i],
        )

    # nothing else is inserted
    mock_database_service.return_value.insert_artifact.assert_not_called()
    mock_database_service.return_value.insert_energy.assert_not_called()
    mock_database_service.return_value.insert_instrument_keyword_value.assert_not_called()
    mock_database_service.return_value.insert_observation.assert_not_called()
    mock_database_service.return_value.insert_observation_time.assert_not_called()
    mock_database_service.return_value.insert_plane.assert_not_called()
    mock_database_service.return_value.insert_polarization.assert_not_called()
    mock_database_service.return_value.insert_position.assert_not_called()
    mock_database_service.return_value.insert_target.assert_not_called()


def test_transactions_are_rolled_back_if_inserting_fails(mocker):
    # mock the database access
    mock_database_service = mocker.patch("ssda.database.ssda.DatabaseService")
    mock_database_service.return_value.find_observation_id.return_value = None
    mock_database_service.return_value.find_proposal_id.return_value = None
    mock_database_service.return_value.insert_artifact.return_value = 713
    mock_database_service.return_value.insert_energy.side_effect = ValueError(
        "This is a fake error."
    )
    mock_database_service.return_value.insert_instrument_keyword_value.side_effect = [
        1409,
        1410,
    ]
    mock_database_service.return_value.insert_instrument_setup.return_value = (
        INSTRUMENT_SETUP_ID
    )
    mock_database_service.return_value.insert_instrument_specific_content.return_value = (
        None
    )
    mock_database_service.return_value.insert_observation.return_value = OBSERVATION_ID
    mock_database_service.return_value.insert_observation_time.return_value = 23011
    mock_database_service.return_value.insert_plane.return_value = PLANE_ID
    mock_database_service.return_value.insert_polarization.return_value = None
    mock_database_service.return_value.insert_position.return_value = 4943
    mock_database_service.return_value.insert_proposal.return_value = PROPOSAL_ID
    mock_database_service.return_value.insert_target.return_value = 14054

    database_config: Any = None
    observation_properties = ObservationPropertiesStub()
    try:
        insert(
            observation_properties, ssda.database.ssda.DatabaseService(database_config)
        )
    except ValueError:
        pass

    # the transaction is rolled back
    mock_database_service.return_value.begin_transaction.assert_called_once()
    mock_database_service.return_value.commit_transaction.assert_not_called()
    mock_database_service.return_value.rollback_transaction.assert_called_once()
