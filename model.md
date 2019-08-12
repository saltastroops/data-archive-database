# Database model

The database model is designed to be compliant with the [Common Archive Observation Model (CAOM)](http://www.opencadc.org/caom2/#caom2) as much as possible. In the following sections the tables are described.

## Tables

### Observation

A single top-level entry in the data archive. This generally corresponds to a single data file.

Column | Description | SALT | SAAO
--- | --- | --- | ---
collection | the name of the data collection this observation belongs to | "SALT" | "SAAO"
observationID | the collection-specific identifier for this observation | See below |
metaRelease | timestamp after which metadata for the observation instance is public | the date after which the data is public | 
type | the type of observation (FITS OBSTYPE keyword); usually OBJECT for intent = science | FITS OBSTYPE keyword |
intent | the intent of the original observer in acquiring this data, such as "SCIENCE" or "ARC" | See below |
algorithm | the algorithm or process that created this observation | "exposure" |
instrumentId | id of the instrument used to acquire the data | id in Instrument table | id in Instrument table
proposalId | id of the proposal to which the observation belongs | id in Proposal table | id in Proposal table
targetId | id of the observed target | id in Target table | id in Target table
targetPositionId | id of the target position | id in TargetPosition table | id in TargetPosition table
telescopeId | id of the telescope used for taking the data | id in Telescope table | id in Telescope table

The observationID value for SALT depends on whether the observation forms part of a proposal. If it does, the proposal code, the block visit id and a running number are concatenated with a dash. An example would be 2019-1-SCI-042-21563-7.

[TODO: How is the type determined?]

### Instrument

An instrument taking observation data, such as RSS or SHOC.

Column | Description | SALT | SAAO
--- | --- | --- | ---
id | internal id | internal id | internal id
name | instrument name | instrument name | instrument name

### Proposal

A description of the science proposal or programme that initiated an observation.

Column | Description | SALT | SAAO
--- | --- | --- | ---
id | internal id | internal id | internal id
proposalID | collection-specific identifier for the proposal | proposal code |
pi | proper name of the principal investigator | first name and surname of the PI |
title | title of the proposal | title of the proposal |

### Telescope

A telescope used to acquire the data for an observation.

Column | Description | SALT | SAAO
--- | --- | --- | ---
id | internal id | internal id | internal id
name | telescope name | "SALT" | telescope name
geoLocationX | x-coordinate of the geocentric location of the telescope at the time of observation (see FITS WCS Paper III) | ? | ?
geoLocationY | y-coordinate of the geocentric location of the telescope at the time of observation (see FITS WCS Paper III) | ? | ?
geoLocationZ | z-coordinate of the geocentric location of the telescope at the time of observation (see FITS WCS Paper III) | ? | ?

### Target

A target of an observation.

Column | Description | SALT | SAAO
--- | --- | --- | ---
id | internal id | internal id | internal id
name | proper name of the target | target name | target name
simbadTargetTypeId | id of numeric SIMBAD target type code | id in SimbadTargetType table | id in SimbadTargetType table
type | type of target; typically used to figure out what the target name means and where to look for additional information about it | ? | ?
standard | indicates that the target is typically used as a standard (astrometric, photometric, etc) | ? | ?
moving | indicates that the target is a moving object; used for solar system objects but not high proper motion stars | true if the target is a Horizons target | ?

[TODO: Can we figure out the type?]

### TargetPosition

The intended position of an observation (not the position of the intended or actual target).
 
This table differs markedly from the TargetPosition object in the CAOM, as it explicitly uses `ra` and `dec` as column names and does not include a `coordsys` column.

Column | Description | SALT | SAAO
--- | --- | --- | ---
id | internal id | internal id | internal id
equinox | the equinox of the coordinates | the equinox
ra | the right ascension | see below |
dec | the declination | see below |

For SALT in general the coordinates from the Target table are used. However, in case of a non-sidereal target the coordinates from the FITS file are used instead.

### Plane

A component of an observation that describes one product of the observation.

The table does not include the calibration level.

Column | Description | SALT | SAAO
--- | --- | --- | ---
id | internal id | internal id | internal id
productID | collection- and observationID-specific identifier for this product | FITS filename without the file extension |
metaRelease | timestamp after which metadata for the plane is public; this metaRelease timestamp applies to all children of the plane and to artifacts with releaseType=meta | the date after which the data is public |
dataRelease | timestamp after which data for the plane is public; this dataRelease timestamp applies to all children of the plane and to artifacts with releaseType=data | the date after which the data is public |
dataProductType | standard classification of the type of data product; describes the logical data type for the main artifacts | "image" for Salticam and RSS imaging and Fabry-Perot, "spectrum" otherwise |
energyId | id of energy description | id in Energy table | id in Energy table
polarizationId | id of polarization description | id in Polarization table
positionId | id of the position description | id in Position table | id in Position table
quality | id of the quality | id of entry in Quality table | id of entry in Quality table
timeId | id of the time description | id of entry in Time table | id of entry in Time table

### Energy

A description of the energy coverage and sampling of the data.

Column | Description | SALT | SAAO
--- | --- | --- | ---
id | internal id | internal id | internal id
dimension | number of measurements (pixels) on the energy axis | see below | see below
resolvingPower | median spectral resolving power per pixel | see below | see below
sampleSize | median pixel size | see below | see below

The calculation of the dimension, resolving power and sample size is explained in the section on spectral properties.

### EnergyInterval

An energy interval.

Column | Description | SALT | SAAO
--- | --- | --- | ---
energyId | id of the Energy entry to which this interval belongs | id of entry in the Energy table | id of entry in the Energy table
lower | lower energy bound, in Angstroms | see below | see below
upper | upper energy bound, in Angstroms | see below | see below

The calculation of the energy intervals is explained in the section on spectral properties.

### Polarization

A description of polarization measurements included in the data.

Column | Description | SALT | SAAO
--- | --- | --- | ---
id | internal id | internal id | internal id
states | comma-separated list of the polarization states (such as "Q,U") | see below |
dimension | number of polarization states included | see below |

SALT's polarization configurations are mapped as follows.

Configuration | States | Dimension
--- | --- | ---
Linear |
Linear Hi |
Circular |
All Stokes | 

### Position

The position to where the telescope was pointing when taking the data.

This table bears no resemblance at all to the Position model in the CAOM model and completely sidesteps its geometry aspects.

Column | Description | SALT | SAAO
--- | --- | --- | ---
id | internal id | internal id | internal id
equinox | equinox | from the FITS file | from the FITS file
ra | right ascension | from the FITS file | from the FITS file
dec| declination | from the FITS file | from the FITS file

## Calculating spectral properties

### RSS

RSS has three CCDs, each with 2048 pixels in the spectral direction. Hence we have

```
dimensions = 3 * 2048 = 6144
```

The wavelength for a CCD pixel depends on the grating angle, the camera angle, the grating frequency and the pixel's position. Its calculation is described by the following code.

```java
    /*
     * Returns the wavelength at the specified distance {@code x}
     * from the center of the middle CCD.
     *
     * See http://www.sal.wisc.edu/~khn/salt/Outgoing/3170AM0010_Spectrograph_Model_Draft_2.pdf
     * for the constants.
     *
     * @param x                distance (in spectral direction from center (in pixels)
     * @param gratingAngle     the grating angle (in degrees)
     * @param cameraAngle      the camera angle (in degrees)
     * @param gratingFrequency the grating frequency (in grooves/mm)
     * @return the wavelength (in Angstrom)
     */
    public static double getWavelength(double x, double gratingAngle, double cameraAngle, double gratingFrequency)
    {
        // What is the outgoing angle beta0 for the center of the middle chip?
        // (Normally, the camera angle will be twice the grating angle, so that
        // the incoming angle (i.e. the grating angle) alpha is equal to beta0.
        double alpha0 = 0; // grating rotation home error, in degrees
        double beta_ae = -0.063; // alignment error of the articulation home, in degrees
        double f_A = -4.2e-5;  // correction factor allowing for the mechanical error in placement of the articulation detent ring
        double Lambda = 1e7 / gratingFrequency;    // grating period
        double alpha = Math.toRadians(gratingAngle + alpha0);
        double beta0 = Math.toRadians((1 + f_A) * cameraAngle + beta_ae - (gratingAngle + alpha0));

        // The relevant distance for the optics is that from the optical axis
        // rather than that from the CCD center.
        x -= SaltData.RSS_OPTICAL_AXIS_ON_CCD.getX() / SaltData.RSS_PIXEL_SIZE;

        // "FUDGE FACTOR"
        x += 20.9;

        // The outgoing angle for a distance x is slightly different; the
        // correction dbeta is given by tan(dbeta) = x / f_cam with the focal
        // length f_cam of the imaging lens. Note that x must be converted from
        // pixels to a length.
        double dbeta = Math.atan((x * SaltData.RSS_PIXEL_SIZE) / SaltData.FOCAL_LENGTH_RSS_IMAGING_LENS);
        double beta = beta0 + dbeta;

        // The wavelength can now be obtained from the grating equation.
        return Lambda * (Math.sin(alpha) + Math.sin(beta));
    }
```

The following table lists the positions $x$ 
