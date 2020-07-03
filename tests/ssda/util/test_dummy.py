import random

from faker import Faker

from ssda.util.dummy import DummyObservationProperties
from ssda.util.fits import DummyFitsFile


def test_dummy_observation_properties():
    random.seed(42)
    Faker().seed(42)

    fits_file = DummyFitsFile("/some/test/path20190930006.fits")
    observation_properties = DummyObservationProperties(fits_file)

    for _ in range(100):
        observation_properties.artifact(42)
        observation_properties.energy(42)
        observation_properties.instrument_keyword_values(42)
        observation_properties.observation(24, 42)
        observation_properties.observation_time(42)
        observation_properties.plane(42)

        observation_properties.polarization(42)
        observation_properties.position(42)
        observation_properties.proposal()
        observation_properties.proposal_investigators(42)
        observation_properties.target(42)
