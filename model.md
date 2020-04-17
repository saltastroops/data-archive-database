# Database model

The database model is designed to be compliant with the [Common Archive Observation Model (CAOM)](http://www.opencadc.org/caom2/#caom2) as much as possible. In the following sections the tables are described.

## Tables
Tables are well defined [here](sql)

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

