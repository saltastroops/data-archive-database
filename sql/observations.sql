DROP SCHEMA IF EXISTS observations CASCADE;

CREATE SCHEMA observations;

SET search_path TO observations, extensions;

-- LOOKUP TABLES

-- data_product_type

CREATE TABLE data_product_type
(
    data_product_type_id serial PRIMARY KEY,
    product_type         varchar(30) UNIQUE NOT NULL
);

COMMENT ON TABLE data_product_type IS 'Type of data product, such as image or spectrum.';

INSERT INTO data_product_type (product_type)
VALUES ('Image'),
       ('Science');

-- institution

CREATE TABLE institution
(
    institution_id   serial PRIMARY KEY,
    abbreviated_name varchar(20) UNIQUE  NOT NULL,
    name             varchar(200) UNIQUE NOT NULL
);

COMMENT ON TABLE institution IS 'An institution which grants observing time';
COMMENT ON COLUMN institution.name IS 'The name of the institution.';

INSERT INTO institution (abbreviated_name, name)
VALUES ('SAAO', 'South African Astronomical Observatory'),
       ('SALT', 'Southern African Large Telescope');

-- instrument

CREATE TABLE instrument
(
    instrument_id serial PRIMARY KEY,
    name          varchar(50) UNIQUE NOT NULL
);

COMMENT ON TABLE instrument IS 'An instrument for taking observation data.';
COMMENT ON COLUMN instrument.name IS 'Instrument name.';

INSERT INTO instrument (name)
VALUES ('BVIT'),
       ('HIPPO'),
       ('HRS'),
       ('RSS'),
       ('Salticam'),
       ('SHOC'),
       ('SpupNIC');

-- instrument_keyword

CREATE TABLE instrument_keyword
(
    instrument_keyword_id serial PRIMARY KEY,
    keyword               varchar(30) UNIQUE NOT NULL
);

COMMENT ON TABLE instrument_keyword IS 'A keyword describing an instrument setup property.';

INSERT INTO instrument_keyword (keyword)
VALUES ('Filter'),
       ('Grating');

-- intent

CREATE TABLE intent
(
    intent_id serial PRIMARY KEY,
    intent    varchar(30) UNIQUE NOT NULL
);

COMMENT ON TABLE intent IS 'The intent of an observation, such as "Science" or "Arc".';

INSERT INTO intent (intent)
VALUES ('Arc'),
       ('Bias'),
       ('Flat'),
       ('Science');

-- observation_type

CREATE TABLE observation_type
(
    observation_type_id serial PRIMARY KEY,
    observation_type    varchar(32) UNIQUE NOT NULL
);

COMMENT ON TABLE observation_type IS 'An observation type, as given by the value for the OBSTYPE FITS header keyword.';

INSERT INTO observation_type (observation_type)
VALUES ('Object');

-- product_type

CREATE TABLE product_type
(
    product_type_id serial PRIMARY KEY,
    product_type    varchar(30) UNIQUE NOT NULL
);

COMMENT ON TABLE product_type IS 'Type of product, as listed in http://www.opencadc.org/caom2/ProductType/';

INSERT INTO product_type (product_type)
VALUES ('Arc'),
       ('Auxiliary'),
       ('Bias'),
       ('Calibration'),
       ('Dark'),
       ('Flat'),
       ('Info'),
       ('Noise'),
       ('Preview'),
       ('Science'),
       ('Thumbnail'),
       ('Weight');

-- status

CREATE TABLE status
(
    status_id serial PRIMARY KEY,
    status    varchar(20) UNIQUE NOT NULL
);

COMMENT ON TABLE status IS 'An observation status, i.e. whether the observation has been accepted or rejected.';

INSERT INTO status (status)
VALUES ('Accepted'),
       ('Rejected');

-- stokes_parameters

CREATE TABLE stokes_parameter
(
    stokes_parameter_id serial PRIMARY KEY,
    stokes_parameter    varchar(5) UNIQUE NOT NULL
);

COMMENT ON TABLE stokes_parameter IS 'A Stokes parameter for describing polarization.';

INSERT INTO stokes_parameter (stokes_parameter)
VALUES ('I'),
       ('Q'),
       ('U'),
       ('V');

-- target_type

CREATE TABLE target_type
(
    target_type_id serial PRIMARY KEY,
    numeric_code   varchar(30) UNIQUE  NOT NULL,
    description    varchar(100) UNIQUE NOT NULL
);

COMMENT ON TABLE target_type IS 'Target type according to the SIMBAD classification scheme.';
COMMENT ON COLUMN target_type.numeric_code IS 'Numeric code for the target type.';
COMMENT ON COLUMN target_type.description IS 'Human-friendly description of the target type.';

-- The target types are added at the bottom of this file.

-- telescope

CREATE TABLE telescope
(
    telescope_id serial PRIMARY KEY,
    name         varchar(30) UNIQUE NOT NULL
);

COMMENT ON TABLE telescope IS 'A telescope.';
COMMENT ON COLUMN telescope.name IS 'The telescope name.';

INSERT INTO telescope (name)
VALUES ('Lesedi'),
       ('1.9 m'),
       ('SALT');

-- OTHER TABLES

-- proposal

CREATE TABLE proposal
(
    proposal_id    bigserial PRIMARY KEY,
    institution_id int          NOT NULL REFERENCES institution (institution_id),
    pi             varchar(100) NOT NULL,
    proposal_code  varchar(50)  NOT NULL,
    title          varchar(200) NOT NULL
);

CREATE UNIQUE INDEX proposal_code_institution_unique ON proposal (proposal_code, institution_id);

CREATE INDEX proposal_institution_id ON Proposal (institution_id);

COMMENT ON TABLE proposal IS 'A proposal.';
COMMENT ON COLUMN proposal.institution_id IS 'The institution to which the proposal was submitted.';
COMMENT ON COLUMN proposal.pi IS 'The Principal Investigator of the proposal.';
COMMENT ON COLUMN proposal.title IS 'The proposal title.';

-- observation

CREATE TABLE observation
(
    observation_id      bigserial PRIMARY KEY,
    data_release        date NOT NULL,
    instrument_id       int  NOT NULL REFERENCES Instrument (instrument_id),
    intent_id           int  NOT NULL REFERENCES Intent (intent_id),
    meta_release        date NOT NULL,
    observation_group   varchar(40),
    observation_type_id int REFERENCES observation_type (observation_type_id),
    proposal_id         int REFERENCES proposal (proposal_id) ON DELETE CASCADE,
    status_id           int  NOT NULL REFERENCES status (status_id),
    telescope_id        int  NOT NULL REFERENCES Telescope (telescope_id),
    CONSTRAINT meta_not_after_data_release_check CHECK (meta_release <= data_release)
);

CREATE INDEX observation_type_idx ON observation (observation_type_id);
CREATE INDEX observation_status_idx ON status (status_id);

COMMENT ON TABLE observation IS 'An observation in the sense of data taken for a single FITS file.';
COMMENT ON COLUMN observation.data_release IS 'Date when the data for this observation becomes public.';
COMMENT ON COLUMN observation.instrument_id IS 'Instrument tha took the data for this observation.';
COMMENT ON COLUMN observation.meta_release IS 'Date when the metadata for this observation becomes public.';
COMMENT ON COLUMN observation.observation_group IS 'Identifier for the logical group to which this observation belongs';

-- instrument_keyword_value

CREATE TABLE instrument_keyword_value
(
    instrument_id         int NOT NULL REFERENCES instrument (instrument_id),
    instrument_keyword_id int NOT NULL REFERENCES instrument_keyword (instrument_keyword_id),
    observation_id        int NOT NULL REFERENCES observation (observation_id) ON DELETE CASCADE,
    value                 varchar(200)
);

CREATE INDEX instrument_keyword_value_instrument_idx ON instrument_keyword_value (instrument_id);
CREATE INDEX instrument_keyword_value_instrument_keyword_idx ON instrument_keyword_value (instrument_keyword_id);
CREATE INDEX instrument_keyword_value_observation_id ON instrument_keyword_value (observation_id);

COMMENT ON TABLE instrument_keyword_value IS 'Value for an instrument keyword for an observation.';

-- plane

CREATE TABLE plane
(
    plane_id             bigserial PRIMARY KEY,
    data_product_type_id int NOT NULL REFERENCES data_product_type (data_product_type_id),
    observation_id       int NOT NULL REFERENCES observation (observation_id) ON DELETE CASCADE
);

CREATE INDEX plane_data_product_type_idx ON plane (data_product_type_id);
CREATE INDEX plane_observation_idx ON plane (observation_id);

COMMENT ON TABLE plane IS 'A component of an observation that describes one product of the observation';

-- target

CREATE TABLE target
(
    target_id      bigserial PRIMARY KEY,
    name           varchar(50) NOT NULL,
    observation_id int         NOT NULL REFERENCES observation (observation_id) ON DELETE CASCADE,
    standard       boolean     NOT NULL,
    target_type_id int REFERENCES target_type (target_type_id)
);

CREATE INDEX target_observation_idx ON target (observation_id);
CREATE INDEX target_target_type_idx ON Target (target_type_id);

COMMENT ON TABLE target IS 'An observed target.';
COMMENT ON COLUMN target.name IS 'The target name.';
COMMENT ON COLUMN target.observation_id IS 'The observation during which the target was observed.';
COMMENT ON COLUMN target.standard IS 'Whether the target is typically used as a standard (astrometric, photometric, etc';

-- energy

CREATE TABLE energy
(
    energy_id       bigserial PRIMARY KEY,
    dimension       int              NOT NULL CHECK (dimension > 0),
    max_wavelength  double precision NOT NULL CHECK (max_wavelength > 0),
    min_wavelength  double precision NOT NULL CHECK (min_wavelength > 0),
    plane_id        int              NOT NULL REFERENCES Plane (plane_id) ON DELETE CASCADE,
    resolving_power double precision NOT NULL CHECK (resolving_power >= 0),
    sample_size     double precision NOT NULL CHECK (sample_size >= 0),
    CONSTRAINT correct_wavelength_order_check CHECK (min_wavelength <= max_wavelength)
);

CREATE INDEX energy_max_wavelength_idx ON Energy (max_wavelength);
CREATE INDEX energy_min_wavelength_idx ON Energy (min_wavelength);
CREATE INDEX energy_plane_idx ON Energy (plane_id);

COMMENT ON TABLE energy IS 'Spectral observation properties.';
COMMENT ON COLUMN energy.dimension IS 'The number of pixels in spectral direction.';
COMMENT ON COLUMN energy.max_wavelength IS 'The maximum observed wavelength, in metres.';
COMMENT ON COLUMN Energy.min_wavelength IS 'The minimum observed wavelength, in metres.';
COMMENT ON COLUMN Energy.resolving_power IS 'The resolving power for the instrument setup.';
COMMENT ON COLUMN Energy.sample_size IS 'The size of the wavelength dispersion per pixel, in metres.';

-- polarization

CREATE TABLE polarization
(
    polarization_id     bigserial PRIMARY KEY,
    plane_id            int NOT NULL REFERENCES Plane (plane_id) ON DELETE CASCADE,
    stokes_parameter_id int NOT NULL REFERENCES stokes_parameter (stokes_parameter_id)
);

CREATE INDEX polarization_plane_idx ON polarization (plane_id);
CREATE INDEX polarization_stokes_idx ON polarization (stokes_parameter_id);

COMMENT ON TABLE polarization IS 'A junction table for linking planes and measured Stokes parameters.';

-- observation_time

CREATE TABLE observation_time
(
    observation_time_id bigserial PRIMARY KEY,
    end_time            timestamp with time zone NOT NULL,
    exposure_time       double precision         NOT NULL CHECK (exposure_time >= 0),
    plane_id            int                      NOT NULL REFERENCES Plane (plane_id) ON DELETE CASCADE,
    resolution          double precision         NOT NULL CHECK (resolution >= 0),
    start_time          timestamp with time zone NOT NULL,
    CONSTRAINT start_not_after_end_time_check CHECK (start_time <= end_time)
);

CREATE INDEX observation_time_plane_idx ON Plane (plane_id);
CREATE INDEX observation_time_start_time_idx ON observation_time (start_time);

COMMENT ON TABLE observation_time IS 'The time when the observation data were taken.';
COMMENT ON COLUMN observation_time.end_time IS 'The time when the observation finished.';
COMMENT ON COLUMN observation_time.exposure_time IS 'The exposure time for the observation, in seconds.';
COMMENT ON COLUMN observation_time.resolution IS 'The time resolution of the observation, in seconds.';
COMMENT ON COLUMN observation_time.start_time IS 'The time when the observation started. ';

-- position

CREATE TABLE position
(
    position_id bigserial PRIMARY KEY,
    dec         double precision NOT NULL CHECK (dec BETWEEN -90 AND 90),
    equinox     double precision NOT NULL CHECK (equinox >= 1900),
    plane_id    int              NOT NULL REFERENCES plane (plane_id) ON DELETE CASCADE,
    ra          double precision NOT NULL CHECK (0 <= ra AND ra < 360)
);

CREATE INDEX position_dec_idx ON position (dec);
CREATE INDEX position_plane_idx ON position (plane_id);
CREATE INDEX position_ra_idx ON position (ra);

COMMENT ON TABLE position IS 'The target position.';
COMMENT ON COLUMN position.dec IS 'Declination, in degrees between -90 and 90.';
COMMENT ON COLUMN position.ra IS 'Right ascension, in degrees between 0 and 360.';

-- artifact

CREATE TABLE artifact
(
    artifact_id      bigserial PRIMARY KEY,
    content_checksum varchar(32)         NOT NULL,
    content_length   bigint              NOT NULL CHECK (content_length > 0),
    identifier       varchar(50) UNIQUE  NOT NULL,
    name             varchar(200)        NOT NULL,
    path             varchar(255) UNIQUE NOT NULL,
    plane_id         int                 NOT NULL REFERENCES Plane (plane_id) ON DELETE CASCADE,
    product_type_id  int REFERENCES product_type (product_type_id)
);

CREATE INDEX artifact_plane ON artifact (plane_id);
CREATE INDEX artifact_product ON artifact (product_type_id);

COMMENT ON TABLE artifact IS 'A data product, such as a FITS file.';
COMMENT ON COLUMN artifact.identifier IS 'Unique identifier string for this artifact.';
COMMENT ON COLUMN artifact.name IS 'The name of the artifact.';
COMMENT ON COLUMN artifact.path IS 'String indicating where the artifact is stored.';

-- Insert target types

INSERT INTO target_type (numeric_code, description)
VALUES ('15.00.51.00', 'spiral galaxy'),
       ('12.05.05.00', 'interacting galaxies'),
       ('15.00.50.00', 'elliptical galaxy'),
       ('14.06.50.00', 'neutron star'),
       ('12.13.11.00', 'cataclysmic variable star'),
       ('00.00.00.00', 'object of unknown nature'),
       ('50.02.01.00', 'Pluto'),
       ('12.13.01.00', 'eclipsing binary'),
       ('14.09.04.03', 'pulsar'),
       ('12.03.00.00', 'cluster of galaxies'),
       ('12.11.01.00', 'globular cluster'),
       ('12.11.00.00', 'cluster of stars'),
       ('14.06.18.00', 'brown dwarf (M<0.08solMass)'),
       ('15.15.00.00', 'active galactic nucleus'),
       ('12.11.02.00', 'open (galactic) cluster'),
       ('06.50.00.00', 'supersoft source'),
       ('14.06.25.00', 'pre-main sequence star'),
       ('14.09.00.00', 'variable star'),
       ('14.00.00.00', 'star'),
       ('15.15.04.00', 'quasar'),
       ('14.06.16.00', 'white dwarf'),
       ('12.13.00.00', 'double, binary or multiple star'),
       ('15.00.53.00', 'irregular galaxy'),
       ('14.09.01.00', 'variable star of irregular type'),
       ('50.01.07.00', 'Uranus'),
       ('12.13.11.06', 'nova'),
       ('51.01.02.00', 'photometric standard'),
       ('15.15.03.00', 'blazar'),
       ('13.08.50.00', 'bipolar nebula'),
       ('51.01.01.00', 'astrometric standard'),
       ('51.02.02.00', 'dome flat'),
       ('51.01.06.00', 'guide star'),
       ('51.01.04.00', 'polarimetric standard'),
       ('51.01.05.00', 'radial velocity standard'),
       ('51.02.01.00', 'sky flat'),
       ('51.01.04.01', 'spectropolarimetric standard'),
       ('51.01.03.00', 'spectroscopic standard'),
       ('15.00.52.00', 'dwarf galaxy'),
       ('15.00.00.00', 'galaxy'),
       ('15.14.00.00', 'gravitationally lensed image'),
       ('15.15.02.00', 'Seyfert galaxy'),
       ('15.12.00.00', 'starburst galaxy'),
       ('15.50.00.00', 'galaxy with supernova'),
       ('12.50.00.00', 'star field'),
       ('13.08.06.00', 'dark cloud (nebula)'),
       ('13.08.51.00', 'gaseous nebula'),
       ('13.14.50.00', 'outflow or jet'),
       ('13.08.07.00', 'reflection nebula'),
       ('13.13.00.00', 'supernova remnant'),
       ('50.03.02.00', 'asteroid'),
       ('50.03.01.00', 'comet'),
       ('50.01.03.00', 'Earth'),
       ('50.03.03.00', 'Trans-Neptunian object'),
       ('50.01.05.00', 'Jupiter'),
       ('50.01.04.00', 'Mars'),
       ('50.01.01.00', 'Mercury'),
       ('50.01.03.01', 'Moon'),
       ('50.01.08.00', 'Neptune'),
       ('50.04.00.00', 'planetary moon'),
       ('50.05.00.00', 'planetary ring'),
       ('50.01.06.00', 'Saturn'),
       ('50.01.02.00', 'Venus'),
       ('14.06.51.00', 'black hole'),
       ('14.09.05.03', 'Cepheid variable star'),
       ('07.03.00.00', 'gamma-ray burst'),
       ('09.03.00.00', '(micro)lensing event'),
       ('14.07.50.00', 'nearby star'),
       ('14.07.00.00', 'high proper-motion star'),
       ('14.09.08.00', 'supernova'),
       ('14.06.30.00', 'Wolf-Rayet star'),
       ('01.00.00.00', 'radio-source'),
       ('01.14.00.00', 'maser'),
       ('06.00.00.00', 'X-ray source'),
       ('07.00.00.00', 'gamma-ray source'),
       ('08.00.00.00', 'inexistent objects'),
       ('08.03.00.00', 'not an object (artefact)'),
       ('09.00.00.00', 'gravitational source'),
       ('09.07.00.00', 'possible gravitational lens'),
       ('09.08.00.00', 'possible gravitationally lensed image'),
       ('09.09.00.00', 'gravitational lens'),
       ('09.11.00.00', 'gravitational lens system (lens+images)'),
       ('10.00.00.00', 'candidate objects'),
       ('10.02.00.00', 'possible supercluster of galaxies'),
       ('10.03.00.00', 'possible cluster of galaxies'),
       ('10.04.00.00', 'possible Group of galaxies'),
       ('10.11.00.00', 'physical binary candidate'),
       ('10.11.01.00', 'eclipsing binary candidate'),
       ('10.11.11.00', 'cataclysmic binary candidate'),
       ('10.11.12.00', 'X-ray binary candidate'),
       ('10.11.12.02', 'low-mass X-ray binary candidate'),
       ('10.11.12.03', 'high-mass X-ray binary candidate'),
       ('10.12.00.00', 'possible peculiar star'),
       ('10.12.01.00', 'young stellar object candidate'),
       ('10.12.02.00', 'pre-main sequence star candidate'),
       ('10.12.02.03', 'T Tau star candidate'),
       ('10.12.03.00', 'possible carbon Star'),
       ('10.12.04.00', 'possible S Star'),
       ('10.12.05.00', 'possible star with envelope of OH/IR type'),
       ('10.12.06.00', 'possible star with envelope of CH type'),
       ('10.12.07.00', 'possible Wolf-Rayet star'),
       ('10.12.08.00', 'possible Be star'),
       ('10.12.11.00', 'possible horizontal branch star'),
       ('10.12.12.00', 'possible red giant Branch star'),
       ('10.12.13.00', 'possible red supergiant star'),
       ('10.12.14.00', 'possible asymptotic giant branch star'),
       ('10.12.15.00', 'post-AGB star candidate'),
       ('10.12.16.00', 'candidate blue straggler Star'),
       ('10.12.18.00', 'white dwarf candidate'),
       ('10.12.20.00', 'neutron star candidate'),
       ('10.12.22.00', 'black hole candidate'),
       ('10.12.23.00', 'supernova candidate'),
       ('10.12.24.00', 'low-mass star candidate'),
       ('10.12.26.00', 'brown dwarf candidate'),
       ('12.00.00.00', 'composite object'),
       ('12.01.00.00', 'region defined in the sky'),
       ('12.01.05.00', 'underdense region of the Universe'),
       ('12.02.00.00', 'supercluster of galaxies'),
       ('12.04.00.00', 'group of galaxies'),
       ('12.04.05.00', 'compact group of galaxies'),
       ('12.04.50.00', 'group of quasars'),
       ('12.05.00.00', 'pair of galaxies'),
       ('12.10.00.00', 'possible globular cluster'),
       ('12.12.00.00', 'association of stars'),
       ('12.13.01.01', 'eclipsing binary of Algol type'),
       ('12.13.01.02', 'eclipsing binary of beta Lyr type'),
       ('12.13.01.03', 'eclipsing binary of W UMa type'),
       ('12.13.01.08', 'star showing eclipses by its planet'),
       ('12.13.02.00', 'spectroscopic binary'),
       ('12.13.11.02', 'cataclysmic var. DQ Her type'),
       ('12.13.11.03', 'cataclysmic var. AM Her type'),
       ('12.13.11.05', 'nova-like Star'),
       ('12.13.11.07', 'dwarf nova'),
       ('12.13.12.00', 'X-ray binary'),
       ('12.13.12.02', 'low mass X-ray binary'),
       ('12.13.12.03', 'high mass X-ray binary'),
       ('13.00.00.00', 'insterstellar matter'),
       ('13.01.00.00', 'part of cloud'),
       ('13.02.00.00', 'possible planetary nebula'),
       ('13.03.00.00', 'cometary globule'),
       ('13.04.00.00', 'bubble'),
       ('13.06.00.00', 'emission object'),
       ('13.08.00.00', 'cloud or nebula'),
       ('13.08.03.00', 'galactic nebula'),
       ('13.08.04.00', 'bright nebula'),
       ('13.08.12.00', 'molecular cloud'),
       ('13.08.12.03', 'globule (low-mass dark cloud)'),
       ('13.08.12.06', 'dense core inside a molecular cloud'),
       ('13.08.13.00', 'high-velocity cloud'),
       ('13.09.00.00', 'HII (ionized) region'),
       ('13.10.00.00', 'planetary nebula'),
       ('13.11.00.00', 'HI shell'),
       ('13.12.00.00', 'supernova remnant candidate'),
       ('13.14.00.00', 'circumstellar matter'),
       ('13.14.01.00', 'outflow candidate'),
       ('13.14.15.00', 'outflow'),
       ('13.14.16.00', 'Herbig-Haro object'),
       ('14.01.00.00', 'star in cluster'),
       ('14.02.00.00', 'star in nebula'),
       ('14.03.00.00', 'star in association'),
       ('14.04.00.00', 'star in double system'),
       ('14.05.00.00', 'star suspected of variability'),
       ('14.06.00.00', 'peculiar star'),
       ('14.06.01.00', 'horizontal branch star'),
       ('14.06.02.00', 'young stellar object'),
       ('14.06.05.00', 'emission-line star'),
       ('14.06.05.03', 'Be star'),
       ('14.06.06.00', 'blue straggler star'),
       ('14.06.10.00', 'red giant branch star'),
       ('14.06.12.00', 'asymptotic giant branch star (He-burning)'),
       ('14.06.12.03', 'carbon star'),
       ('14.06.12.06', 'S star'),
       ('14.06.13.00', 'red supergiant star'),
       ('14.06.15.00', 'post-AGB star (proto-PN)'),
       ('14.06.16.01', 'pulsating white dwarf'),
       ('14.06.17.00', 'low-mass star (M<1solMass)'),
       ('14.06.23.00', 'star with envelope of OH/IR type'),
       ('14.06.24.00', 'star with envelope of CH type'),
       ('14.06.25.03', 'T Tau-type star'),
       ('14.08.00.00', 'high-velocity star'),
       ('14.09.01.01', 'variable star of Orion type'),
       ('14.09.01.02', 'variable star with rapid variations'),
       ('14.09.03.00', 'eruptive variable star'),
       ('14.09.03.01', 'flare star'),
       ('14.09.03.02', 'variable star of FU Ori type'),
       ('14.09.03.04', 'variable star of R CrB type'),
       ('14.09.04.00', 'rotationally variable star'),
       ('14.09.04.01', 'variable star of alpha2 CVn type'),
       ('14.09.04.02', 'ellipsoidal variable star'),
       ('14.09.04.04', 'variable of BY Dra type'),
       ('14.09.04.05', 'variable of RS CVn type'),
       ('14.09.05.00', 'pulsating variable star'),
       ('14.09.05.02', 'variable star of RR Lyr type'),
       ('14.09.05.05', 'variable star of delta Sct type'),
       ('14.09.05.06', 'variable star of RV Tau type'),
       ('14.09.05.07', 'variable star of W Vir type'),
       ('14.09.05.08', 'variable star of beta Cep type'),
       ('14.09.05.09', 'classical Cepheid (delta Cep type)'),
       ('14.09.05.10', 'variable star of gamma Dor type'),
       ('14.09.06.00', 'long-period variable star'),
       ('14.09.06.01', 'variable Star of Mira Cet type'),
       ('14.09.06.04', 'semi-regular pulsating star'),
       ('14.09.09.00', 'symbiotic star'),
       ('14.14.00.00', 'sub-stellar object'),
       ('14.14.02.00', 'extra-solar planet candidate'),
       ('14.50.00.00', 'isolated star (not a member of a particular galaxy)'),
       ('15.01.00.00', 'part of a galaxy'),
       ('15.02.00.00', 'galaxy in cluster of galaxies'),
       ('15.02.02.00', 'brightest galaxy in a cluster (BCG)'),
       ('15.03.00.00', 'galaxy in group of galaxies'),
       ('15.04.00.00', 'galaxy in Pair of galaxies'),
       ('15.05.00.00', 'galaxy with high redshift'),
       ('15.06.00.00', 'absorption line system'),
       ('15.06.01.00', 'Ly alpha absorption line system'),
       ('15.06.02.00', 'damped Ly-alpha absorption line system'),
       ('15.06.03.00', 'metallic absorption line system'),
       ('15.06.05.00', 'Lyman limit system'),
       ('15.06.08.00', 'broad absorption line system'),
       ('15.07.00.00', 'radio galaxy'),
       ('15.08.00.00', 'HII galaxy'),
       ('15.09.00.00', 'low surface brightness galaxy'),
       ('15.10.00.00', 'possible active galactic nucleus'),
       ('15.10.07.00', 'possible quasar'),
       ('15.10.11.00', 'possible blazar'),
       ('15.10.17.00', 'possible BL Lac'),
       ('15.11.00.00', 'emission-line galaxy'),
       ('15.13.00.00', 'blue compact galaxy'),
       ('15.14.01.00', 'gravitationally lensed image of a galaxy'),
       ('15.14.07.00', 'gravitationally lensed image of a quasar'),
       ('15.15.01.00', 'LINER-type active galactic nucleus'),
       ('15.15.02.01', 'Seyfert 1 galaxy'),
       ('15.15.02.02', 'Seyfert 2 galaxy'),
       ('15.15.03.01', 'BL Lac - type object'),
       ('15.15.03.02', 'optically violently variable object'),
       ('50.00.00.00', 'solar system object'),
       ('50.01.00.00', 'planet'),
       ('50.02.00.00', 'dwarf planet'),
       ('50.02.02.00', 'Ceres'),
       ('50.02.03.00', 'Haumea'),
       ('50.02.04.00', 'MakeMake'),
       ('50.02.05.00', 'Eris'),
       ('50.03.00.00', 'small Solar System body'),
       ('51.00.00.00', 'calibration'),
       ('51.01.00.00', 'standard'),
       ('51.02.00.00', 'flat'),
       ('52.00.00.00', 'man-made object');
