import hashlib
import os
import random
import re
import string
from datetime import datetime, timedelta
from typing import List, NamedTuple, Optional, Tuple

import astropy.units as u
from astropy.units import Quantity
from dateutil import tz
from faker import Faker

from ssda.observation import ObservationProperties
from ssda.util import types
from ssda.util.fits import FitsFile


class FilenameDeterminedProperties(NamedTuple):
    institution: types.Institution
    observation_group_identifier: Optional[str]
    proposal_code: Optional[str]
    telescope: types.Telescope


class DummyObservationProperties(ObservationProperties):
    """
    A class for generating fake observation properties.

    See the ObservationProperties base class for documentation on the methods.

    Parameters
    ----------
    fits_file : FitsFile
        FITS file.

    """

    def __init__(self, fits_file: FitsFile):
        self._fits_file = fits_file
        self._faker = Faker()

        # If the script is run multiple times, proposals should not be reinserted. This
        # means that for a given file the proposal code and institution must always be
        # the same. The same is true for observation groups, so that group identifiers
        # and the telescope must always be the same as well.
        filename = os.path.basename(fits_file.path())
        filename_determined_properties = DummyObservationProperties.filename_determined_properties(
            filename
        )
        self._institution = filename_determined_properties.institution
        self._observation_group_identifier = (
            filename_determined_properties.observation_group_identifier
        )
        self._proposal_code = filename_determined_properties.proposal_code
        self._telescope = filename_determined_properties.telescope

        self._instrument = random.choice(
            [types.Instrument.HRS, types.Instrument.RSS, types.Instrument.SALTICAM]
        )
        if random.random() > 0.05:
            self._has_target = True
        else:
            self._has_target = False

    @staticmethod
    def filename_determined_properties(filename: str) -> FilenameDeterminedProperties:
        """
        Generate values for parameters based on a filename.

        Parameters
        ----------
        filename : str
            Filename.

        Returns
        -------
        FilenameDeterminedProperties
            Properties determined by the filename.
        """

        # Get the date and the running number per night from the filename
        number_search = re.search(r"\d+", filename)
        if not number_search:
            raise ValueError(f"Filename unsupported: {filename}")
        running_number = number_search.group(0)
        night = running_number[:8]
        try:
            file_in_night = int(running_number[8:])
        except BaseException as e:
            # some files don't follow the usual naming convention
            file_in_night = 1000  # arbitrary value

        # Get a "random" number based on the night and proposal number
        md5_hash = hashlib.md5(filename.encode()).hexdigest()
        characters = "abcdef" + string.digits
        random_number = characters.index(md5_hash[0])

        institutions = [institution for institution in types.Institution]
        telescopes = [telescope for telescope in types.Telescope]
        if random_number > 10:
            institution_index = random_number % len(institutions)
            institution = institutions[institution_index]
            telescope_index = random_number % len(telescopes)
            telescope = telescopes[telescope_index]
            return FilenameDeterminedProperties(
                institution=institution,
                observation_group_identifier=None,
                proposal_code=None,
                telescope=telescope,
            )

        # Group observations in groups of up to 10
        proposal_in_night = 1 + file_in_night // 10
        proposal_code = f"Proposal-{night}-{proposal_in_night}"

        # Choose an institution based on the proposal number
        institution_index = proposal_in_night % len(institutions)
        institution = institutions[institution_index]

        # Choose a telescope based on the proposal number
        telescope_index = proposal_in_night % len(telescopes)
        telescope = telescopes[telescope_index]

        # Choose a group identifier based on the night abd the proposal number
        observation_group_identifier = f"B-{night}-{proposal_in_night}"

        return FilenameDeterminedProperties(
            institution=institution,
            observation_group_identifier=observation_group_identifier,
            proposal_code=proposal_code,
            telescope=telescope,
        )

    def artifact(self, plane_id: int) -> types.Artifact:
        def identifier(n: int) -> str:
            characters = string.ascii_lowercase + string.digits
            return "".join(random.choices(characters, k=n))

        def product_type() -> types.ProductType:
            return random.choice(list(p for p in types.ProductType))

        return types.Artifact(
            content_checksum=self._fits_file.checksum(),
            content_length=self._fits_file.size(),
            identifier=identifier(10),
            name=os.path.basename(self._fits_file.path()),
            plane_id=plane_id,
            path=self._fits_file.path(),
            product_type=product_type(),
        )

    def energy(self, plane_id: int) -> Optional[types.Energy]:
        if random.random() < 0.05:
            return None

        def wavelengths() -> Tuple[Quantity, Quantity]:
            wavelength_interval = 5000 * random.random()
            min_wavelength = (
                3000 + ((9000 - wavelength_interval) - 3000) * random.random()
            )
            max_wavelength = min_wavelength + wavelength_interval
            return min_wavelength, max_wavelength

        wavelength_values = wavelengths()

        return types.Energy(
            dimension=random.randint(1, 1024),
            max_wavelength=wavelength_values[1] * u.angstrom,
            min_wavelength=wavelength_values[0] * u.angstrom,
            plane_id=plane_id,
            resolving_power=8000 * random.random(),
            sample_size=100 * random.random() * u.angstrom,
        )

    def instrument_keyword_values(
        self, observation_id: int
    ) -> List[types.InstrumentKeywordValue]:
        values: List[types.InstrumentKeywordValue] = []

        return values

    def instrument_setup(self, observation_id: int) -> types.InstrumentSetup:
        if self._instrument == types.Instrument.RSS:
            sql = """
            WITH fpm (id) AS (
                SELECT rss_fabry_perot_mode_id FROM rss_fabry_perot_mode WHERE fabry_perot_mode=%(fabry_perot_mode)s
            ),
                 rg (id) AS (
                     SELECT rss_grating_id FROM rss_grating WHERE grating=%(grating)s
                 )
            INSERT INTO rss_setup (instrument_setup_id, rss_fabry_perot_mode_id, rss_grating_id)
            VALUES (%(instrument_setup_id)s, (SELECT id FROM fpm), (SELECT id FROM rg))
            """

            fabry_perot_modes = [fpm for fpm in types.RSSFabryPerotMode]
            fabry_perot_mode = random.choice(fabry_perot_modes)
            gratings = [g for g in types.RSSGrating]
            grating = random.choice(gratings)
            parameters = dict(
                fabry_perot_mode=fabry_perot_mode.value, grating=grating.value
            )
            queries = [types.SQLQuery(sql=sql, parameters=parameters)]
        elif self._instrument == types.Instrument.HRS:
            hrs_modes = [hm for hm in types.HRSMode]
            hrs_mode = random.choice(hrs_modes)
            sql = """
            WITH hm (id) AS (
                SELECT hrs_mode_id FROM hrs_mode WHERE hrs_mode.hrs_mode=%(hrs_mode)s
            )
            INSERT INTO hrs_setup (instrument_setup_id, hrs_mode_id)
            VALUES (%(instrument_setup_id)s, (SELECT id FROM hm))
            """
            parameters = dict(hrs_mode=hrs_mode.value)
            queries = [types.SQLQuery(sql=sql, parameters=parameters)]
        else:
            queries = []

        detector_modes = [d for d in types.DetectorMode]
        detector_mode = random.choice(detector_modes)
        filters = [f for f in types.Filter]
        filter = random.choice(filters)
        instrument_modes = [im for im in types.InstrumentMode]
        instrument_mode = random.choice(instrument_modes)

        return types.InstrumentSetup(
            additional_queries=queries,
            detector_mode=detector_mode,
            filter=filter,
            instrument_mode=instrument_mode,
            observation_id=observation_id,
        )

    def observation(
        self, observation_group_id: Optional[int], proposal_id: Optional[int]
    ) -> types.Observation:
        now = datetime.now().date()
        data_release = self._faker.date_between("-5y", now + timedelta(days=500))
        meta_release = self._faker.date_between("-5y", now + timedelta(days=500))
        if meta_release > data_release:
            meta_release = data_release
        intent = random.choice([intent for intent in types.Intent])
        observation_type = random.choice(
            [observation_type for observation_type in types.ObservationType]
        )
        status = random.choice([status for status in types.Status])
        if self._instrument in (
            types.Instrument.HRS,
            types.Instrument.RSS,
            types.Instrument.SALTICAM,
        ):
            telescope = types.Telescope.SALT
        else:
            telescope = random.choice(
                [types.Telescope.LESEDI, types.Telescope.ONE_DOT_NINE]
            )

        return types.Observation(
            data_release=data_release,
            instrument=self._instrument,
            intent=intent,
            meta_release=meta_release,
            observation_group_id=observation_group_id,
            observation_type=observation_type,
            proposal_id=proposal_id,
            status=status,
            telescope=telescope,
        )

    def observation_group(self) -> Optional[types.ObservationGroup]:
        if self._observation_group_identifier:
            name = self._faker.text(max_nb_chars=20)
            return types.ObservationGroup(
                group_identifier=self._observation_group_identifier, name=name
            )
        else:
            return None

    def observation_time(self, plane_id: int) -> types.ObservationTime:
        start_time = self._faker.date_time_between("-5y", tzinfo=tz.gettz("UTC"))
        exposure_time = 10 * u.second + 4000 * random.random() * u.second
        end_time = start_time + timedelta(seconds=exposure_time.to_value(u.second))
        return types.ObservationTime(
            end_time=end_time,
            exposure_time=exposure_time,
            plane_id=plane_id,
            resolution=exposure_time,
            start_time=start_time,
        )

    def plane(self, observation_id: int) -> types.Plane:
        data_product_types = [
            data_product_type for data_product_type in types.DataProductType
        ]

        return types.Plane(
            observation_id=observation_id,
            data_product_type=random.choice(data_product_types),
        )

    def polarization(self, plane_id: int) -> Optional[types.Polarization]:
        all_polarization_patterns = [pattern for pattern in types.PolarizationPattern]
        if random.random() > 0.9:
            polarization_pattern = random.choice(all_polarization_patterns)
            return types.Polarization(
                plane_id=plane_id, polarization_pattern=polarization_pattern
            )
        else:
            return None

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
            return types.Proposal(
                institution=self._institution,
                pi=self._faker.name(),
                proposal_code=self._proposal_code,
                title=self._faker.text(max_nb_chars=100),
            )
        else:
            return None

    def proposal_investigators(
        self, proposal_id: int
    ) -> List[types.ProposalInvestigator]:
        investigator_ids = list(range(1, 201))

        return [
            types.ProposalInvestigator(
                proposal_id=proposal_id, investigator_id=str(investigator_id)
            )
            for investigator_id in random.sample(
                investigator_ids, k=random.randint(0, 10)
            )
        ]

    def target(self, observation_id: int) -> Optional[types.Target]:
        if not self._has_target:
            return None

        if not self._proposal_code and random.random() > 0.5:
            standard = True
        else:
            standard = False
        target_types = [
            "15.00.50.00",
            "50.02.01.00",
            "12.13.00.00",
            "51.02.00.00",
            "51.00.00.00",
        ]

        return types.Target(
            name=self._faker.text(max_nb_chars=20),
            observation_id=observation_id,
            standard=standard,
            target_type=random.choice(target_types),
        )
