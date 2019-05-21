
import os.path
from astropy.io import fits
import glob
from astropy import units as u
from astropy.coordinates import SkyCoord

############################################################################################
# Specify the directory to the FITS files on disk                                          #
############################################################################################
from connection import ssda_connect

path_to_data = input("Enter the path to the raw fits data:")
data_directory = path_to_data

#
############################################################################################
# Connecting to the database server and database                                           #
############################################################################################
mydb = ssda_connect()

############################################################################################
# Recursively traverse through the data_directory search for fits file to import           #
############################################################################################

# def getCategory(category):
#    cursor = mydb.cursor()
#
#    cursor.execute("select id from DataCategory where dataCategory =%s",(category,))
#    record = cursor.fetchone()
#
#    value = record[0]
#
#    print (connect(**sdb_config)value)
#    mydb.close()
#    return  ;

for filename in glob.iglob(data_directory + '*.fits', recursive=True):
    print(filename)
    filesize = os.path.getsize(filename)

    hdulist = fits.open(filename)
    prihdr = hdulist[0].header

    c = mydb.cursor()

    # Import data, check which instrument file it is to determine which table to populate.
    if prihdr['INSTRUME'] == 'SALTICAM' and prihdr['OBJECT'] != 'BIAS':
        startTime = prihdr['DATE-OBS']

        positionCoords = SkyCoord(prihdr['RA'] + "" + prihdr['DEC'], unit=(u.hour, u.deg), frame='icrs').to_string('decimal')
        print("Position Coordinates")
        print(positionCoords)

        c.execute("SELECT * FROM Telescope where telescopeName= 'SALT'")
        myresult = [(0, "SALT", "1")]
        print("results: \n", myresult)
        for x in myresult:
            telescopeId = x[0]
            startTime = prihdr['DATE-OBS']
            observation = """INSERT INTO Observation(telescopeId,telescopeObservationId,startTime,statusId)
                             VALUES (%s,%s,%s,%s) """, (x[0], 2, prihdr['DATE-OBS'], 2)

            # Closing sirius_observation
            scam = ("""
INSERT INTO Salticam(
    telescopeName,
    dateObserved,
    observer,
    objectName,
    obsMode,
    instrumentName,
    rightAscension,
    declination,
    exposureTime,
    airMass,
    detectorMode,
    observationType,
    ccdType,
    projectID,
    siteLatitude,
    siteLongitude,
    detectorSoftwareVersion,
    julianDay,
    moonAngle,
    gainSet,
    readOutSpeed,
    filter,
    filterPosition,
    cameraFocus,
    telescopeFocus,
    photometry,
    seeing,
    transparency,
    blockId,
    telescopeRightAscension,
    telescopeDeclination,
    equinox,
    epoch,
    timeObserved)VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
        %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """,
                    (
                              prihdr['OBSERVAT'],
                              prihdr['DATE-OBS'],
                              prihdr['PROPOSER'],
                              prihdr['OBJECT'],
                              prihdr['OBSMODE'],
                              prihdr['INSTRUME'],
                              prihdr['RA'],
                              prihdr['DEC'],
                              prihdr['EXPTIME'],
                              prihdr['AIRMASS'],
                              prihdr['DETMODE'],
                              prihdr['OBSTYPE'],
                              prihdr['CCDTYPE'],
                              prihdr['PROPID'],
                              prihdr['SITELAT'],
                              prihdr['SITELONG'],
                              prihdr['DETSWV'],
                              prihdr['JD'],
                              prihdr['MOONANG'],
                              prihdr['GAINSET'],
                              prihdr['ROSPEED'],
                              prihdr['FILTER'],
                              prihdr['FILPOS'],
                              prihdr['CAMFOCUS'],
                              prihdr['TELFOCUS'],
                              prihdr['PHOTOMET'],
                              prihdr['SEEING'],
                              prihdr['TRANSPAR'],
                              prihdr['BLOCKID'],
                              # prihdr['IMAGEID'],
                              prihdr['TELRA'],
                              prihdr['TELDEC'],
                              prihdr['EQUINOX'],
                              prihdr['EPOCH'],
                              prihdr['TIME-OBS']
                    )
                    )  # Closing scam
            datafiles = ("""
INSERT INTO DataFile (name, datacategoryId, targetID,startTime,size)
    VALUES (%s,%s,%s,%s,%s)""", (filename, 1, 1, prihdr['TIME-OBS'], filesize)
                         )

            dataPreview = ("""
INSERT INTO DataPreview (name, dataFieldId,orders)
    VALUES (%s,%s,%s)""", (filename, 1, 1)
                           )

            target = ("""
INSERT INTO Target(name,rightAscension,declination,position,targetTypeId)
    VALUES (%s,%s,%s,%s,%s)
    """, (
                           prihdr['OBJECT'],
                           prihdr['RA'],
                           prihdr['DEC'],
                           positionCoords,
                           200
            )
                      )
            c.execute(*observation)
            c.execute(*scam)
            c.execute(*datafiles)
            c.execute(*target)
            c.execute(*dataPreview)
            mydb.commit()
            print("DOne with all...")
    else:
        print("Not importing any other and OBJECT at this moment")
        exit(1)
        # c.close()
        mydb.commit()
mydb.close()
