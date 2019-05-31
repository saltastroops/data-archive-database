import os.path
from astropy.io import fits
import glob
from connection import ssda_connect
from telescope.salt.salticam.get_information import get_telescope_id, \
    get_observation_status_id, \
    get_telescope_observation_id, get_data_category_id, get_last_observation_id, get_last_data_file_id, \
    get_last_target_id
from util.util import handle_missing_header, convert_time_to_float


def populate_scam(data_directory):
    """
    Defining the function for populating the salticam table.
    The data is obtained from the fit files
    
    :param data_directory: The directory where the fit files are located
    """
    # Connecting to the ssda database server and database
    ssda_con = ssda_connect()
    
    # Database cursor
    cursor = ssda_con.cursor()

    # Recursively traverse through the data_directory search for fits file to import
    for filename in glob.iglob(data_directory + '**/*.fits', recursive=True):
        print(filename)
        # Obtain the file sie
        file_size = os.path.getsize(filename)
        
        # Obtaining th header data unit list with open() as context manager.
        # Helps to avoid forgetting closing the file after it opened.
        with fits.open(filename) as header_data_unit_list:
            # Obtaining the primary header data unit
            primary_header_data_unit = header_data_unit_list[0].header

            # Import data, check which instrument file it is to determine which table to populate.
            if handle_missing_header(primary_header_data_unit, 'INSTRUME') == 'SALTICAM':
                ra = handle_missing_header(primary_header_data_unit, 'RA')
                dec = handle_missing_header(primary_header_data_unit, 'DEC')
                
                # position = SkyCoord(ra=ra, dec=dec, unit=(u.hourangle, u.deg))

                start_time = handle_missing_header(primary_header_data_unit, 'DATE-OBS')
                
                # Get the telescope id from th sdda
                telescope_id = 1  # get_telescope_id('SALT')
                
                # Obtaining the block id from the fit header
                block_id = handle_missing_header(primary_header_data_unit, 'BLOCKID')
                
                # Get the observation status id from the sdb
                observation_status_id = get_observation_status_id(block_id)
                
                # Get the telescope observation id from the sdb
                telescope_observation_id = get_telescope_observation_id(block_id)
                
                # Get the dat category from the fit header
                data_category = handle_missing_header(primary_header_data_unit, 'OBJECT')
                
                # Get the data category id from the ssda
                data_category_id = get_data_category_id(data_category)
                
                # Sql for entering observation table entries.
                observation_sql = """
                    INSERT INTO Observation(
                        telescopeId,
                        telescopeObservationId,
                        startTime,
                        observationStatusId
                    )
                    VALUES (%s,%s,%s,%s)
                """
                observation_params = (telescope_id, telescope_observation_id, start_time, observation_status_id)

                salticam_sql = """
                    INSERT INTO Salticam(
                        telescopeId,
                        amplifierSection,
                        amplifierTemperature,
                        amplifierReadoutX,
                        amplifierReadoutY,
                        biasSection,
                        beamSplitterScale,
                        beamSplitterZero,
                        detectorFocusPosition,
                        numberOfAmplifiers,
                        ccdSection,
                        ccdSummation,
                        ccdTemperature,
                        ccdType,
                        transformationMatrix11,
                        transformationMatrix11A,
                        transformationMatrix12,
                        transformationMatrix12A,
                        transformationMatrix21,
                        transformationMatrix21A,
                        transformationMatrix22,
                        transformationMatrix22A,
                        coldEndTemperature,
                        pixelCoordinatePointX1,
                        pixelCoordinatePointX1A,
                        pixelCoordinatePointX2,
                        pixelCoordinatePointX2A,
                        rightAsertionPoint1,
                        spatialCoordinatePoint1A,
                        declanationPoint2,
                        spacialCoordinatePoint2A,
                        gnomicProjection1,
                        cartesianProjection1A,
                        gnomicProjection2,
                        cartesianProjection2A,
                        anglesDegreesAlways1,
                        anglesDegreesAlways2,
                        dataSection,
                        dateOfObservation,
                        detectorMode,
                        detectorSection,
                        detectorSize,
                        detectorSoftwareVersion,
                        coolerBoxTemperature,
                        exposureTime,
                        filterPosition,
                        filterName,
                        gain,
                        gain1,
                        gainSet,
                        imageId,
                        instrumentName,
                        julianDate,
                        lstObservation,
                        numberOfCcds,
                        numberOfExtensions,
                        numberOfWindows,
                        objectName,
                        observationMode,
                        observationType,
                        pixelScale,
                        pupilEnd,
                        noiseReadout,
                        ccdReadoutSpeed,
                        pixelSaturation,
                        startOfObservationTime,
                        systemTyme,
                        fitsHeaderVersion,
                        spatialCoordinate,
                        crossTalk
                    )
                    VALUES (
                        %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                        %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                        %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                        %s,%s,%s,%s,%s,%s,%s,%s,%s,%s
                    )
                """
                salticam_params = (
                    telescope_id,
                    handle_missing_header(primary_header_data_unit, 'AMPSEC'),
                    handle_missing_header(primary_header_data_unit, 'AMPTEM'),
                    handle_missing_header(primary_header_data_unit, 'ATM1_1'),
                    handle_missing_header(primary_header_data_unit, 'ATM1_2'),
                    handle_missing_header(primary_header_data_unit, 'BIASSEC'),
                    handle_missing_header(primary_header_data_unit, 'BSCALE'),
                    handle_missing_header(primary_header_data_unit, 'BZERO'),
                    handle_missing_header(primary_header_data_unit, 'CAMFOCUS'),
                    handle_missing_header(primary_header_data_unit, 'CCDNAMPS'),
                    handle_missing_header(primary_header_data_unit, 'CCDSEC'),
                    handle_missing_header(primary_header_data_unit, 'CCDSUM'),
                    handle_missing_header(primary_header_data_unit, 'CCDTEM'),
                    handle_missing_header(primary_header_data_unit, 'CCDTYPE'),
                    handle_missing_header(primary_header_data_unit, 'CD1_1'),
                    handle_missing_header(primary_header_data_unit, 'CD1_1A'),
                    handle_missing_header(primary_header_data_unit, 'CD1_2'),
                    handle_missing_header(primary_header_data_unit, 'CD1_2A'),
                    handle_missing_header(primary_header_data_unit, 'CD2_1'),
                    handle_missing_header(primary_header_data_unit, 'CD2_1A'),
                    handle_missing_header(primary_header_data_unit, 'CD2_2'),
                    handle_missing_header(primary_header_data_unit, 'CD2_2A'),
                    handle_missing_header(primary_header_data_unit, 'CENTEM'),
                    handle_missing_header(primary_header_data_unit, 'CRPIX1'),
                    handle_missing_header(primary_header_data_unit, 'CRPIX1A'),
                    handle_missing_header(primary_header_data_unit, 'CRPIX2'),
                    handle_missing_header(primary_header_data_unit, 'CRPIX2A'),
                    handle_missing_header(primary_header_data_unit, 'CRVAL1'),
                    handle_missing_header(primary_header_data_unit, 'CRVAL1A'),
                    handle_missing_header(primary_header_data_unit, 'CRVAL2'),
                    handle_missing_header(primary_header_data_unit, 'CRVAL2A'),
                    handle_missing_header(primary_header_data_unit, 'CTYPE1'),
                    handle_missing_header(primary_header_data_unit, 'CTYPE1A'),
                    handle_missing_header(primary_header_data_unit, 'CTYPE2'),
                    handle_missing_header(primary_header_data_unit, 'CTYPE2A'),
                    handle_missing_header(primary_header_data_unit, 'CUNIT1'),
                    handle_missing_header(primary_header_data_unit, 'CUNIT2'),
                    handle_missing_header(primary_header_data_unit, 'DATASEC'),
                    handle_missing_header(primary_header_data_unit, 'DATE-OBS'),
                    handle_missing_header(primary_header_data_unit, 'DETMODE'),
                    handle_missing_header(primary_header_data_unit, 'DETSEC'),
                    handle_missing_header(primary_header_data_unit, 'DETSIZE'),
                    handle_missing_header(primary_header_data_unit, 'DETSWV'),
                    handle_missing_header(primary_header_data_unit, 'DEWTEM'),
                    handle_missing_header(primary_header_data_unit, 'EXPTIME'),
                    handle_missing_header(primary_header_data_unit, 'FILPOS'),
                    handle_missing_header(primary_header_data_unit, 'FILTER'),
                    handle_missing_header(primary_header_data_unit, 'GAIN'),
                    handle_missing_header(primary_header_data_unit, 'GAIN1'),
                    handle_missing_header(primary_header_data_unit, 'GAINSET'),
                    handle_missing_header(primary_header_data_unit, 'IMAGEID'),
                    handle_missing_header(primary_header_data_unit, 'INSTRUME'),
                    handle_missing_header(primary_header_data_unit, 'JD'),
                    handle_missing_header(primary_header_data_unit, 'LST-OBS'),
                    handle_missing_header(primary_header_data_unit, 'NCCDS'),
                    handle_missing_header(primary_header_data_unit, 'NEXTEND'),
                    handle_missing_header(primary_header_data_unit, 'NWINDOW'),
                    handle_missing_header(primary_header_data_unit, 'OBJECT'),
                    handle_missing_header(primary_header_data_unit, 'OBSMODE'),
                    handle_missing_header(primary_header_data_unit, 'OBSTYPE'),
                    handle_missing_header(primary_header_data_unit, 'PIXSCALE'),
                    handle_missing_header(primary_header_data_unit, 'PUPEND'),
                    handle_missing_header(primary_header_data_unit, 'RDNOISE'),
                    handle_missing_header(primary_header_data_unit, 'ROSPEED'),
                    handle_missing_header(primary_header_data_unit, 'SATURATE'),
                    handle_missing_header(primary_header_data_unit, 'TIME-OBS'),
                    handle_missing_header(primary_header_data_unit, 'TIMESYS'),
                    handle_missing_header(primary_header_data_unit, 'VERFITS'),
                    handle_missing_header(primary_header_data_unit, 'WCSNAMEA'),
                    handle_missing_header(primary_header_data_unit, 'XTALK')
                )
                print(salticam_params)

                target_sql = """
                    INSERT INTO Target(
                        name,
                        rightAscension,
                        declination,
                        position,
                        targetTypeId
                    )
                    VALUES (%s,%s,%s,%s,%s)
                """
                
                target_params = (
                    handle_missing_header(primary_header_data_unit, 'OBJECT'),
                    convert_time_to_float((handle_missing_header(primary_header_data_unit, 'RA'))),
                    convert_time_to_float((handle_missing_header(primary_header_data_unit, 'DEC'))),
                    None,
                    1
                )
                
                data_files_sql = """
                    INSERT INTO DataFile(
                        dataCategoryId,
                        startTime,
                        name,
                        targetId,
                        size,
                        observationId
                    )
                    VALUES (%s,%s,%s,%s,%s,%s)
                """
                
                data_files_params = (
                    data_category_id,
                    start_time,
                    filename,
                    get_last_target_id(),
                    file_size,
                    get_last_observation_id()
                )
                
                data_preview_sql = """
                    INSERT INTO DataPreview(
                        name,
                        dataFileId,
                        orders
                    )
                    VALUES (%s,%s,%s)
                """
                data_preview_params = (
                    filename,
                    get_last_data_file_id(),
                    "DESC"
                )

                cursor.execute(observation_sql, observation_params)
                cursor.execute(salticam_sql, salticam_params)
                cursor.execute(target_sql, target_params)
                cursor.execute(data_files_sql, data_files_params)
                cursor.execute(data_preview_sql, data_preview_params)
                ssda_con.commit()
                
            else:
                print("Not importing any other and OBJECT at this moment")
                exit(1)
                # c.close()
                ssda_con.commit()

    print("XXX....")
    ssda_con.close()


populate_scam("/home/nhlavu/nhlavu/da/database/data-archive-database/data/")
