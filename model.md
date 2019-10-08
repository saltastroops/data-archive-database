# Database model

The database model is designed to be compliant with the [Common Archive Observation Model (CAOM)](http://www.opencadc.org/caom2/#caom2) as much as possible. In the following sections the tables are described.

## Tables

### Observation

A single top-level entry in the data archive. This generally corresponds to a single data file.

Column | Description | SALT | SAAO
--- | --- | --- | ---
observationId | internal id | internal id | internal id
observationGroup | identifier for the group of observations to which this observation belongs | block visit id
metaRelease | timestamp after which metadata for the observation instance is public | the date after which the data is public | 
type | the type of observation (FITS OBSTYPE keyword); usually OBJECT for intent = science | FITS OBSTYPE keyword |
intent | the intent of the original observer in acquiring this data, such as "SCIENCE" or "ARC" | See below |
statusId | id of the Status table entry | id in Status table | id in Status table
algorithmId | id of the Algorithm table entry | id in Algorithm table | id in Algorithm table
instrumentId | id of the instrument used to acquire the data | id in Instrument table | id in Instrument table
proposalId | id of the proposal to which the observation belongs | id in Proposal table | id in Proposal table
targetId | id of the observed target | id in Target table | id in Target table
telescopeId | id of the telescope used for taking the data | id in Telescope table | id in Telescope table

The observationID value for SALT depends on whether the observation forms part of a proposal. If it does, the proposal code, the block visit id and a running number are concatenated with a dash. An example would be 2019-1-SCI-042-21563-7.

### Status

The status of the observation.

Column | Description
--- | ---
statusId | internal id
status | status

The possible values for `status` are `Accepted` (the observation meets the requirements) and `Rejected` (the observation does not meet the requirements).

### Instrument

An instrument taking observation data, such as RSS or SHOC.

Column | Description
--- | ---
instrumentId | internal id
name | instrument name

### InstrumentKeyword

A lookup table for the instrument keywords.

Keywords should be all upper case. They should also be as general as possible.

Column | Description
--- | ---
instrumentKeywordId | internal id
instrumentKeyword | instrument keyword

### InstrumentKeywordValue

Instrument keywords and corresponding values.

Column | Description
--- | ---
id | internal id
instrumentId | id of the instrument entry
instrumentKeywordId | id of the instrument keyword entry
value | value (as a string)

### Proposal

A description of the science proposal or programme that initiated an observation.

Column | Description | SALT | SAAO
--- | --- | --- | ---
proposalId | internal id | internal id | internal id
proposalIdentifier | collection-specific identifier for the proposal | proposal code |
pi | proper name of the principal investigator | first name and surname of the PI |
title | title of the proposal | title of the proposal |
institutionId | id of the Institution entry for this proposal | id for "SALT" | id for "SAAO"

### Telescope

A telescope used to acquire the data for an observation.

Column | Description
--- | ---
telescopeId | internal id
name | telescope name
geoLocationX | x-coordinate of the geocentric location of the telescope at the time of observation (see FITS WCS Paper III)
geoLocationY | y-coordinate of the geocentric location of the telescope at the time of observation (see FITS WCS Paper III)
geoLocationZ | z-coordinate of the geocentric location of the telescope at the time of observation (see FITS WCS Paper III)

### Target

A target of an observation.

Column | Description
--- | ---
targetId | internal id 
name | proper name of the target
targetTypeId | id of numeric SIMBAD target type code
standard | indicates that the target is typically used as a standard (astrometric, photometric, etc)
moving | indicates that the target is a moving object; used for solar system objects but not high proper motion stars

For SALT, `moving` is set to true if the target is a Horizons target.

[TODO: Can we figure out the type?]

### TargetType

A target type, as defined by the [SIMBAD object classification](http://simbad.u-strasbg.fr/simbad/sim-display?data=otypes&option=display+numeric+codes).

Column | Description
--- | ---
targetTypeId | internal id
numericCode | numeric code for the target type
description | human-friendly description of the target type

### Institution

An institution to which proposals can be sent.

Column | Description
--- | ---
institutionId | internal id
name | name of the institution

The name is `SALT` or `SAAO`.

### Algorithm

Algorithm or process that created the observation.

Column | Description
--- | ---
algorithmId | internal id
algorithm | algorithm

For simple observations the value of `algorithm` should be `exposure`.

### Plane

A component of an observation that describes one product of the observation.

The table does not include the calibration level.

Column | Description | SALT | SAAO
--- | --- | --- | ---
planeId | internal id | internal id | internal id
productIdentifier | collection- and observationIdentifier-specific identifier for this product | FITS filename without the file extension |
metaRelease | timestamp after which metadata for the plane is public; this metaRelease timestamp applies to all children of the plane and to artifacts with releaseType=meta | the date after which the data is public |
dataRelease | timestamp after which data for the plane is public; this dataRelease timestamp applies to all children of the plane and to artifacts with releaseType=data | the date after which the data is public |
dataProductTypeId | id of the DataProductType table entry | id in DataProductType table | id in ProductDataTypeEntry
energyId | id of energy description | id in Energy table | id in Energy table
polarizationId | id of polarization description | id in Polarization table
positionId | id of the position description | id in Position table | id in Position table
qualityId | id of the quality | id of entry in Quality table | id of entry in Quality table
timeId | id of the time description | id of entry in Time table | id of entry in Time table

### DataProductType

Standard classification of the type of data product; describes the logical data type for the main artifacts.

Column | Description
--- | ---
dataProductTypeId | internal id
dataProductType | data product type

For SALT, the data product type is `image` for Salticam and RSS imaging and Fabry-Perot, `spectrum` otherwise.

### Energy

A description of the energy coverage and sampling of the data.

Column | Description
--- | ---
energyId | internal id
lowerBound | lower energy bound, in metres
upperBound | upper energy bound, in metres
dimension | number of measurements (pixels) on the energy axis
resolvingPower | median spectral resolving power per pixel
sampleSize | median pixel size

The calculation of the dimension, resolving power and sample size is explained in the section on calculating energy properties.

### EnergyInterval

An energy interval.

Column | Description
--- | ---
energyId | id of the Energy entry to which this interval belongs
lower | lower energy bound, in metres
upper | upper energy bound, in metres

The calculation of the energy intervals is explained in the section on calculating energy properties.

### Polarization

A junction table for linking planes and Stokes parameters.

Column | Description
--- | ---
id | internal id
planeId | id of a Plane entry
stokesParameterId | id of a StokesParameter entry

SALT's polarization configurations are mapped as follows to Stokes parameters.

Configuration | Stokes parameters
--- | ---
Linear | Q, U
Linear Hi | Q, U
Circular | V
All Stokes | Q, U, V

### StokesParameter

The Stokes parameters.

Column | Description
stokesParameterId | internal id
stokesParameter | Stokes parameter

### Position

The position to where the telescope was pointing when taking the data.

This table bears no resemblance at all to the Position model in the CAOM model and completely sidesteps its geometry aspects.

Column | Description
--- | ---
positionId | internal id
equinox | equinox
ra | right ascension
dec| declination

### Time

A description of the time coverage and sampling of the data.

Column | Description | SALT | SAAO
--- | --- | --- | ---
timeId | internal id | internal id | internal id
resolution | median temporal resolution per pixel, in seconds | exposure time from the FITS file
start | start time, as UTC | start of observation from the FITS file |
end | end time, as UTC | start time + exposure time from the FITS file |
exposure | median exposure time per pixel, in seconds | exposure time from the FITS file

### Artifact

A physical product (typically a file).

Column | Description
--- | ---
artifactId | internal id
planeId | id of the Plane entry to which this artifact belongs
artifactIdentifier | a UUID
artifactName | name of the artifact
path | file path
productType | the primary product type of the artifact; for multi-part artifacts where the parts have different types, this is the primary type; for example, if an artifact has a science part and an auxiliary part, the artifact should have type science
contentLength | the size of the resolved artifact; typically file size in bytes
contentChecksum | the checksum of the artifact data; the URI must conform to the pattern {algorithm}:{value}, for example: md5:4be91751541fd804e7207663a0822f56

`artifactName` is taken to be the filename of the FITS file. `path` id taken to be the location of the FITS file. `contentLength` is the file size in bytes.
`contentChecksum` is the MD5 checksum of the FITS file.

The following algorithm is used to determine the product type for SALT.

1. If the observation type is "OBJECT" or "SCIENCE", the product type is science.

2. If the observation type contains "BIAS" or the object name is "BIAS", the product type is bias.

3. If the observation type contains "FLAT", the product type is flat.

4. The product type is calibration in all other cases.

Note that the CAOM does not define a product type specifically for arcs.

### ProductType

The primary product type of the artifact; for multi-part artifacts where the parts have different types, this is the primary type; for example, if an artifact has a science part and an auxiliary part, the artifact should have type science.
id | internal id

Column | Description
--- | ---
productTypeId | internal id
productType | product type

The product type must be chosen from the [list of defined product types](http://www.opencadc.org/caom2/ProductType/).

## Calculating energy properties

### Imaging with a filter

Let T be the transmission of the filter used. Define lambda1 and lambda2 as follows:

lambda1: T(lambda1) = p && T(lambda) < p for all lambda < lambda1

lambda2: T(lambda2) = p && T(lambda) < p for all lambda > lambda2

Here p = 0.5, i.e. lambda2 - lambda1 is the FWHM.

If there are no such values lambda1 and lambda2, no energy properties are defined.

If there are such values lambda1 and lambda2, there is a single energy interval, taken to be bounded by lambda1 and lambda2:

```
energy intervals = [[lambda1, lambda2]]
```

The resolving power then is taken to be

```
resolving power = 0.5 * (lambda1 + lambda2) / (lambda2 - lambda1)
```

The dimension is just 1.

For a practical calculation, the filter transmission is given as an array `t` of pairs of wavelengths and corresponding transmissions. Then the following algorithm is used for getting lambda1 and lambda2.

1. Sort `t` so that `t[i][0] > t[i - 1][0]` for all array index values `i` greater than 0.

2. Loop over the array and find the first index value `i` for which `t[i][1] < p` and `t[i + 1][1]` >= p.

3. Let `x1 = t[i][0]`, `x2 = t[i + 1][0]`, `t1 = t[i][1]` and `t2 = t[i + 1][1]`. Let f be the line through (x1, t1) and (x2, t2). Then lambda1 is defined by f(lambda1) = p.

4. Loop over the array and find the last index value `i` for which `t[i][1] >= p` and `t[i + 1][1]` < p.

5. Again let `x1 = t[i][0]`, `x2 = t[i + 1][0]`, `t1 = t[i][1]` and `t2 = t[i + 1][1]`. Let g be the line through (x1, t1) and (x2, t2). Then lambda2 is defined by g(lambda1) = p.

In steps 3 and 5 the value of lambda1 or lambda2 can be calculated by means of the formula `lambda = (p + m * x1 - t1) / m`, where m is the gradient of the line, `m = (t2 - t1) / (x2 - x1)`.

### Imaging without a filter

No energy properties are defined for this case.

### Salticam

The energy properties are obtained as described in the section on imaging with a filter.

### RSS (imaging)

The energy properties are obtained as described in the section on imaging with a filter.

### RSS (longslit spectroscopy)

RSS has three CCDs, each with 2048 pixels in the spectral direction. However, effectively only 2032 can be used, so that we have

```
dimension = 3 * 2032 / spectral binning = 6096 / spectral binning
```

The binning in spectral and spatial direction is given by the `CCDSUM` keyword in the FITS header, with the spectral ome coming first. For example, if the FITS header contains the line

```
CCDSUM  = '2 4     '           / On chip summation                              
```

the spectral binning is 2.

The wavelength for a CCD pixel depends on the grating angle, the camera angle, the grating frequency and the pixel's position. Its calculation is described by the following code.

```
/*
 * the focal length of the RSS imaging lens (in mm)
 */
double FOCAL_LENGTH_RSS_IMAGING_LENS = 328;

/*
 * the location (in x direction) of the intersection between the center CCD
 * and the optical axis in mm
 *
 * Note: the sign convention differs from that used by the
 * PySpectrograph package.
 */
double RSS_OPTICAL_AXIS_ON_CCD = 0.3066;

/*
 * the size of a pixel on the RSS CCD chips (in millimeters)
 */
double RSS_PIXEL_SIZE = 0.015;

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
 * @return the wavelength (in metres)
 */
double getWavelength(double x, double gratingAngle, double cameraAngle, double gratingFrequency)
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
    x -= RSS_OPTICAL_AXIS_ON_CCD.getX() / RSS_PIXEL_SIZE;

    // "FUDGE FACTOR"
    x += 20.9;

    // The outgoing angle for a distance x is slightly different; the
    // correction dbeta is given by tan(dbeta) = x / f_cam with the focal
    // length f_cam of the imaging lens. Note that x must be converted from
    // pixels to a length.
    double dbeta = Math.atan((x * RSS_PIXEL_SIZE) / SaltData.FOCAL_LENGTH_RSS_IMAGING_LENS);
    double beta = beta0 + dbeta;

    // The wavelength can now be obtained from the grating equation.
    double wavelength = Lambda * (Math.sin(alpha) + Math.sin(beta));
    
    // The CAOM expects the wavelength to be in metres, not Angstroms.
    return wavelength / 1e10;
}
```

The following table lists the positions x for the CCD edges. Edge 1 abd 2 correspond to the smallest and largest wavelength detected by the CCD, respectively.

CCD | x(edge 1) | x(edge 2)
--- | --- | ---
1 | -3162 | -1130
2 | -1016 | 1016
3 | 1130 | 3162

The energy intervals are the wavelength intervals for these values of x:

```
energy intervals = [[getWavelength(x(edge 1 of CCD i), gratingAngle, cameraAngle, gratingFrequency), getWavelength(x(edge 2 of CCD i), gratingAngle, cameraAngle, gratingFrequency)] for i in (1, 2, 3)]
```

However, as the Common Archive Observation Model limits the number of energy intervals to one per plane, we ignore chip gaps and just use

```
energy interval = [getWavelength(3162, gratingAngle, cameraAngle, gratingFrequency), getWavelength(-3162, gratingAngle, cameraAngle, gratingFrequency)]
```

We estimate the sample size to be

```
sampleSize = getWavelength(spectral binning, gratingAngle, cameraAngle, gratingFrequency) - getWavelength(0, gratingAngle, cameraAngle, gratingFrequency)
```

The calculation of the resolving power is described by the following code.

```
/*
 * the focal length of the telescope (in mm)
 */
double FOCAL_LENGTH_TELESCOPE = 46200;

/*
 * the focal length of the RSS collimator (in mm)
 */
double FOCAL_LENGTH_RSS_COLLIMATOR = 630;

/*
 * Returns the resolution element for the given grating frequency, grating angle and slit width.
 *
 * @param gratingFrequency the grating frequence (in grooves/mm)
 * @param gratingAngle     the grating angle (in degrees)
 * @param slitWidth        the slit width (in arcseconds)
 * @return the resolution element
 */
double getResolutionElement(double gratingFrequency, double gratingAngle, double slitWidth)
{
    double Lambda = 1e7 / gratingFrequency;
    return Math.toRadians(slitWidth / 3600) * Lambda * Math.cos(Math.toRadians(gratingAngle)) * (
            FOCAL_LENGTH_TELESCOPE / FOCAL_LENGTH_RSS_COLLIMATOR);
}

/*
 * Returns the resolution at the center of the middle CCD. This is the ratio
 * of the resolution element and the wavelength at the CD's center.
 *
 * @param gratingAngle     the grating angle (in degrees)
 * @param cameraAngle      the camera angle (in degrees)
 * @param gratingFrequency the grating frequency (in grooves/mm)
 * @param slitWidth        the slit width (in arcseconds)
 * @return the resolution
 */
double getWavelengthResolution(double gratingAngle,
                               double cameraAngle,
                               double gratingFrequency,
                               double slitWidth)
{
    double wavelength = getWavelength(0, gratingAngle, cameraAngle, gratingFrequency);
    double wavelengthResolutionElement = getResolutionElement(gratingFrequency, gratingAngle, slitWidth);
    return wavelength / wavelengthResolutionElement;
}
```

The camera angle, grating angle and slit barcode can be obtained directly from the FITS header; their keywords are `AR-ANGLE`, `GR-ANGLE` and `MASKID`, respectively. The slit width can be obtained from the barcode, as shown in the following code.

```
/**
 * Returns the slit width for the given barcode.
 *
 * @param barcode barcode
 * @return the slit width (in arcseconds)
 */
public static Double slitWidthFromBarcode(String barcode)
{
    if (barcode.equals("P000000N02")) {
        return 0.333333;
    }
    if (barcode.equals("P000000P08") || barcode.equals("P000000P09")) {
        return 1.5;
    }
    return Double.parseDouble(barcode.substring(2, 6)) / 100;
}
```

The values for the grating frequency are collected in the following table.

Grating | Grating frequency
--- | ---
pg0300 | 300
pg0900 | 903.89
pg1300 | 1299.6
pg1800 | 1801.89
pg2300 | 2302.60
pg3000 | 3000.55

### RSS (MOS)

No energy properties are defined for this case.

### RSS (Fabry-Perot)

The FITS header contains two fields for wavelengths, `ET1WAVE0` and `ET2WAVE0`. Which of these is the approximate wavelength depends on the etalon state, as recorded by the `ET-STATE` keyword. The following table lists the wavelength values to ue:

Value for ET_STATE | Keyword to use for wavelength
--- | ---
S1 - Etalon Open | n/a
S2 - Etalon 1 | ET1WAVE0
S3 - Etalon 2 | ET2WAVE0
S4 - Etalon 1 & 2 | ET1WAVE0

As these wavelength values are not calibrated, they are approximations only.

The FWHM values are given for all modes (TF, LR, MR, HR) and a list of wavelengths in Table 1 of in the paper [An Imaging Fabry-Pérot system for the Robert Stobie Spectrograph on the Southern African Large Telescope](https://iopscience.iop.org/article/10.1088/0004-6256/135/5/1825/meta) by Naseem Rangwala, Ted Williams and their collaborators (2008).

Linear interpolation is used to get the FWHM for the observation's wavelength from these values. Then the (single) energy interval is taken to be

```
energy intervals = [[lambda - FWHM / 2, lambda + FWHM / 2]]
```

The resolving power is

```
resolving power = lambda / FWHM
```

The sample size is

```
sample size = FWHM
```

It should be noted that these values are rough approximations as the etalons' FWHM has degraded since the measurements taken in 2008.

The dimension is just 1.

### HRS

The wavelength range and resolving power for the two detector arms and the various modes are given in the following table.

Arm | Mode | Wavelength range (nm) | Resolving power
--- | --- | --- | ---
Blue | Low Resolution | 370 - 555 | 15000
Blue | Medium Resolution | 370 - 555 | 43400
Blue | High Resolution | 370 - 555 | 66700
Blue | High Stability (P) | 370 - 555 | 66900
Blue | High Stability (O) | 370 - 555 | 94600
Red | Low Resolution | 555 - 890 | 14000
Red | Medium Resolution | 555 - 890 | 39600
Red | High Resolution | 555 - 890 | 73700
Red | High Stability (P) | 555 - 890 | 64600
Red | High Stability (O) | 555 - 890 | 84200

The sample size is given in the following table.

Arm | Sample size (A)
--- | ---
Blue | 0.032 A
Red | 0.043 A

The dimension is calculated as the ratio of the wavelength range and sample size.

Arm | Dimension
--- | ---
Blue | 57812
Red | 77906

these values have to be corrected with the spectral binning, which is the first of the two numbers in the value for the `CCDSUM` keyword in the FITS header.

### BVIT

The energy properties are obtained as described in the section on imaging with a filter.

