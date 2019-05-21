import os.path
from astropy.io import fits
import glob
from astropy import units as u
from astropy.coordinates import SkyCoord
from connection import ssda_connect
from telescope.salt.salticam.get_information import get_telescope_id


def populate_scam(data_directory):
    """
    Defining the function for populating the salticam table.
    The data is obtained from the fit files
    
    :param data_directory: The directory where the fit files are located
    """
    
    # Connecting to the database server and database
    ssda_con = ssda_connect()
    
    # Database cursor
    cursor = ssda_con.cursor()
    
    # Recursively traverse through the data_directory search for fits file to import
    for filename in glob.iglob(data_directory + '**/raw/*.fits', recursive=True):
        # Obtain the file sie
        file_size = os.path.getsize(filename)
        
        # Obtaining th header data unit list with open() as context manager.
        # Helps to avoid forgetting closing the file after it opened.
        with fits.open(filename) as header_data_unit_list:
            # Obtaining the primary header data unit
            primary_header_data_unit = header_data_unit_list[0].header

            # Import data, check which instrument file it is to determine which table to populate.
            if primary_header_data_unit['INSTRUME'] == 'SALTICAM' and primary_header_data_unit['OBJECT'] != 'BIAS':
                position_coords = SkyCoord(
                    primary_header_data_unit['RA'] + "" + primary_header_data_unit['DEC'],
                    unit=(u.hour, u.deg),
                    frame='icrs'
                ).to_string('decimal')

                telescope_id = get_telescope_id('SALT')
                
                print(telescope_id)
                start_time = primary_header_data_unit['DATE-OBS']
                
                observation = (
                    """
                        INSERT INTO Observation(
                            telescopeId,
                            telescopeObservationId,
                            startTime,
                            statusId
                        )
                        VALUES (%s,%s,%s,%s)
                    """,
                    (
                        telescope_id,
                        2,
                        start_time,
                        2
                    )
                )

                scam = (
                    """
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
                            timeObserved
                        )
                        VALUES (
                            %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                            %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s
                        )
                    """,
                    (
                        primary_header_data_unit['OBSERVAT'],
                        primary_header_data_unit['DATE-OBS'],
                        primary_header_data_unit['PROPOSER'],
                        primary_header_data_unit['OBJECT'],
                        primary_header_data_unit['OBSMODE'],
                        primary_header_data_unit['INSTRUME'],
                        primary_header_data_unit['RA'],
                        primary_header_data_unit['DEC'],
                        primary_header_data_unit['EXPTIME'],
                        primary_header_data_unit['AIRMASS'],
                        primary_header_data_unit['DETMODE'],
                        primary_header_data_unit['OBSTYPE'],
                        primary_header_data_unit['CCDTYPE'],
                        primary_header_data_unit['PROPID'],
                        primary_header_data_unit['SITELAT'],
                        primary_header_data_unit['SITELONG'],
                        primary_header_data_unit['DETSWV'],
                        primary_header_data_unit['JD'],
                        primary_header_data_unit['MOONANG'],
                        primary_header_data_unit['GAINSET'],
                        primary_header_data_unit['ROSPEED'],
                        primary_header_data_unit['FILTER'],
                        primary_header_data_unit['FILPOS'],
                        primary_header_data_unit['CAMFOCUS'],
                        primary_header_data_unit['TELFOCUS'],
                        primary_header_data_unit['PHOTOMET'],
                        primary_header_data_unit['SEEING'],
                        primary_header_data_unit['TRANSPAR'],
                        primary_header_data_unit['BLOCKID'],
                        # primary_header_data_unit['IMAGEID'],
                        primary_header_data_unit['TELRA'],
                        primary_header_data_unit['TELDEC'],
                        primary_header_data_unit['EQUINOX'],
                        primary_header_data_unit['EPOCH'],
                        primary_header_data_unit['TIME-OBS']
                    )
                )

                datafiles = (
                    """
                        INSERT INTO DataFile(
                            name,
                            datacategoryId,
                            targetID,
                            startTime,
                            size
                        )
                        VALUES (%s,%s,%s,%s,%s)
                    """,
                    (
                        filename,
                        1,
                        1,
                        start_time,
                        file_size
                    )
                )

                dataPreview = (
                    """
                        INSERT INTO DataPreview(
                            name,
                            dataFieldId,
                            orders
                        )
                        VALUES (%s,%s,%s)
                    """,
                    (
                        filename,
                        1,
                        1
                    )
                )

                target = (
                    """
                        INSERT INTO Target(
                            name,
                            rightAscension,
                            declination,
                            position,
                            targetTypeId
                        )
                        VALUES (%s,%s,%s,%s,%s)
                    """,
                    (
                        primary_header_data_unit['OBJECT'],
                        primary_header_data_unit['RA'],
                        primary_header_data_unit['DEC'],
                        position_coords,
                        200
                    )
                )

                cursor.execute(*observation)
                cursor.execute(*scam)
                cursor.execute(*datafiles)
                cursor.execute(*target)
                cursor.execute(*dataPreview)
                ssda_con.commit()
                
            else:
                print("Not importing any other and OBJECT at this moment")
                exit(1)
                # c.close()
                ssda_con.commit()
                
        ssda_con.close()


populate_scam("/home/sifiso/Downloads/salt_data")
