import os
import random
import string
from datetime import datetime, timedelta
from typing import List, Optional, Set

import astropy.units as u
from astropy.units import Quantity
from dateutil import tz
from faker import Faker

from ssda.observation import ObservationProperties
from ssda.util import types
from ssda.util.fits import FitsFile


class DummyObservationProperties(ObservationProperties):
    def __init__(self, fits_file: FitsFile):
        self._fits_file = fits_file
        self._faker = Faker()
        self._institution = random.choice([types.Institution.SAAO, types.Institution.SALT])
        self._instrument = random.choice([types.Instrument.HRS, types.Instrument.RSS, types.Instrument.SALTICAM])
        if random.random() > 0.05:
            self._proposal_code = 'Proposal-{}'.format(random.randint(1, 2000))
        else:
            self._proposal_code = None
        if random.random() > 0.05:
            self._has_target = True
        else:
            self._has_target = False

    def artifact(self, plane_id: int) -> types.Artifact:
        def identifier(n: int) -> str:
            characters = string.ascii_lowercase + string.digits
            return ''.join(random.choices(characters, k=n))

        def product_type() -> types.ProductType:
            return random.choice(list(p for p in types.ProductType))

        return types.Artifact(content_checksum=self._fits_file.checksum(),
                              content_length=self._fits_file.size(),
                              identifier=identifier(10),
                              name=os.path.basename(self._fits_file.path()),
                              plane_id=plane_id,
                              path=self._fits_file.path(),
                              product_type=product_type())

    def energy(self, plane_id: int) -> Optional[types.Energy]:
        def wavelengths() -> (Quantity, Quantity):
            wavelength_interval = 5000 * random.random()
            min_wavelength = 3000 + ((9000 - wavelength_interval) - 3000) * random.random()
            max_wavelength = min_wavelength + wavelength_interval
            return min_wavelength, max_wavelength

        wavelength_values = wavelengths()

        return types.Energy(dimension=random.randint(1, 1024),
                            max_wavelength=wavelength_values[1] * u.angstrom,
                            min_wavelength=wavelength_values[0] * u.angstrom,
                            plane_id=plane_id,
                            resolving_power=8000 * random.random(),
                            sample_size=100 * random.random() * u.angstrom)

    def instrument_keyword_values(self, observation_id: int) -> List[
        types.InstrumentKeywordValue]:
        values = []

        # RSS
        if self._instrument == types.Instrument.RSS:
            grating = random.choice(['pg0300', 'pg0900', 'pg1300', 'pg1800', 'pg2300', 'pg3000', None])
            bandpass = random.choice(['pc00000', 'pc03200', 'pc03400', 'pc03850', 'pc04600', 'pi06530', 'pi08005', None])
            if random.random() > 0.5:
                values.append(types.InstrumentKeywordValue(instrument=types.Instrument.RSS, instrument_keyword=types.InstrumentKeyword.BANDPASS, observation_id=observation_id, value=bandpass))
            if random.random() > 0.5:
                values.append(types.InstrumentKeywordValue(instrument=types.Instrument.RSS, instrument_keyword=types.InstrumentKeyword.GRATING, observation_id=observation_id, value=grating))

        # Salticam
        elif self._instrument == types.Instrument.SALTICAM:
            bandpass = random.choice(['U-S1', 'B-S1', 'V-S1', 'R-S1', 'I-S1', 'Halpha-S1', None])
            if random.random() > 0.5:
                values.append(types.InstrumentKeywordValue(instrument=types.Instrument.SALTICAM, instrument_keyword=types.InstrumentKeyword.BANDPASS, observation_id=observation_id, value=bandpass))

        return values

    def observation(self, proposal_id: Optional[int]) -> types.Observation:
        now = datetime.now().date()
        data_release = self._faker.date_between('-5y', now + timedelta(days=500))
        meta_release = self._faker.date_between('-5y', now + timedelta(days=500))
        if meta_release > data_release:
            meta_release = data_release
        intent = random.choice([intent for intent in types.Intent])
        if self._proposal_code:
            observation_group = '{proposal_code}-{index}'.format(proposal_code=self._proposal_code, index=random.randint(1, 10))
        else:
            observation_group = None
        observation_type = random.choice([observation_type for observation_type in types.ObservationType])
        status = random.choice([status for status in types.Status])
        if self._instrument in (types.Instrument.HRS, types.Instrument.RSS, types.Instrument.SALTICAM):
            telescope = types.Telescope.SALT
        else:
            telescope = random.choice([types.Telescope.LESEDI, types.Telescope.ONE_DOT_NINE])

        return types.Observation(data_release=data_release,
                                 instrument=self._instrument,
                                 intent=intent,
                                 meta_release=meta_release,
                                 observation_group=observation_group,
                                 observation_type=observation_type,
                                 proposal_id=proposal_id,
                                 status=status,
                                 telescope=telescope)

    def observation_time(self, plane_id: int) -> types.ObservationTime:
        start_time = self._faker.date_time_between('-5y', tzinfo=tz.gettz('UTC'))
        exposure_time = 10 * u.second + 4000 * random.random() * u.second
        end_time = start_time + timedelta(seconds=exposure_time.to_value(u.second))
        return types.ObservationTime(end_time=end_time,
                                     exposure_time=exposure_time,
                                     plane_id=plane_id,
                                     resolution=exposure_time,
                                     start_time=start_time)

    def plane(self, observation_id: int) -> types.Plane:
        return types.Plane(observation_id=observation_id)

    def polarizations(self, plane_id: int) -> List[types.Polarization]:
        all_stokes_parameters = [parameter for parameter in types.StokesParameter]
        if random.random() > 0.9:
            parameter_count = random.randint(1, len(all_stokes_parameters))
            stokes_parameters = random.sample(all_stokes_parameters, k=parameter_count)
        else:
            stokes_parameters = []

        return [types.Polarization(plane_id=plane_id, stokes_parameter=stokes_parameter)
                for stokes_parameter in stokes_parameters]

    def position(self, plane_id: int) -> Optional[types.Position]:
        if not self._has_target:
            return None

        dec = self._faker.latitude() * u.degree
        if random.random() > 0.1:
            equinox = 2000
        else:
            equinox = 1950
        # convert from [-180, 180] to [0, 360]
        ra = (float(self._faker.longitude()) + 180) * u.degree
        return types.Position(dec=dec, equinox=equinox, plane_id=plane_id, ra=ra)

    def proposal(self) -> Optional[types.Proposal]:
        if self._proposal_code:
            return types.Proposal(institution=self._institution,
                                  pi=self._faker.name(),
                                  proposal_code=self._proposal_code,
                                  title=self._faker.text(max_nb_chars=100))
        else:
            return None

    def proposal_investigators(self, proposal_id: int) -> List[
        types.ProposalInvestigator]:
        investigator_ids = list(range(1, 201))

        return [types.ProposalInvestigator(proposal_id=proposal_id, investigator_id=str(investigator_id)) for investigator_id in random.sample(investigator_ids, k=random.randint(0, 10))]

    def target(self, observation_id: int) -> Optional[types.Target]:
        if not self._has_target:
            return None

        if not self._proposal_code and random.random() > 0.5:
            standard = True
        else:
            standard = False
        target_types = ['15.00.50.00', '50.02.01.00', '12.13.00.00', '51.02.00.00', '51.00.00.00']

        return types.Target(name=self._faker.text(max_nb_chars=20), observation_id=observation_id, standard=standard, target_type=random.choice(target_types))

