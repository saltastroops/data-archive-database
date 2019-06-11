import os.path
from astropy.io import fits
import glob
from connection import ssda_connect
from util.get_information import get_telescope_id, \
    get_observation_status_id, \
    get_telescope_observation_id, get_data_category_id, get_last_observation_id, get_last_data_file_id, \
    get_last_target_id
from util.util import handle_missing_header, convert_time_to_float


def populate_hrs(data_directory):
    """
    Defining the function for populating the hrs table.
    The data is obtained from the fit files
    
    :param data_directory: The directory where the fit files are located
    """
    # Connecting to the ssda database server and database
    ssda_con = ssda_connect()
    
    # Database cursor
    cursor = ssda_con.cursor()
    
    # Recursively traverse through the data_directory search for fits file to import
    for filename in glob.iglob(data_directory + '**/**/raw/*.fits', recursive=True):
        # Obtain the file sie
        file_size = os.path.getsize(filename)

        # Obtaining th header data unit list with open() as context manager.
        # Helps to avoid forgetting closing the file after it opened.
        with fits.open(filename) as header_data_unit_list:
            # Obtaining the primary header data unit
            primary_header_data_unit = header_data_unit_list[0].header
    
            # Import data, check which instrument file it is to determine which table to populate.
            if handle_missing_header(primary_header_data_unit, 'INSTRUME') == 'HRS':
                ra = handle_missing_header(primary_header_data_unit, 'RA')
                dec = handle_missing_header(primary_header_data_unit, 'DEC')

                start_time = handle_missing_header(primary_header_data_unit, 'DATE-OBS')

                # Get the telescope id from th sdda
                telescope_id = get_telescope_id('SALT')

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
                
                hrs_sql_dictionary = {
                    "telescopeId": telescope_id,
                    "amplifierSection": handle_missing_header(primary_header_data_unit, 'AMPSEC'),
                    "amplifierTemperature": handle_missing_header(primary_header_data_unit, 'AMPTEM'),
                    "biasSection": handle_missing_header(primary_header_data_unit, 'BIASSEC'),
                    "numberOfAmplifiers": handle_missing_header(primary_header_data_unit, 'CCDNAMPS'),
                    "ccdSection": handle_missing_header(primary_header_data_unit, 'CCDSEC'),
                    "ccdSummation": handle_missing_header(primary_header_data_unit, 'CCDSUM'),
                    "ccdTemperature": handle_missing_header(primary_header_data_unit, 'CCDTEMP'),
                    "ccdType": handle_missing_header(primary_header_data_unit, 'CCDTYPE'),
                    "dataSection": handle_missing_header(primary_header_data_unit, 'DATASEC'),
                    "dateOfObservation": handle_missing_header(primary_header_data_unit, 'DATE-OBS'),
                    "detectorMode": handle_missing_header(primary_header_data_unit, 'DETMODE'),
                    "detectorName": handle_missing_header(primary_header_data_unit, 'DETNAM'),
                    "detectorSection": handle_missing_header(primary_header_data_unit, 'DETSEC'),
                    "detectorSerialNumber": handle_missing_header(primary_header_data_unit, 'DETSER'),
                    "detectorSize": handle_missing_header(primary_header_data_unit, 'DETSIZE'),
                    "detectorSoftwareVersion": handle_missing_header(primary_header_data_unit, 'DETSWV'),
                    "exposureMean": handle_missing_header(primary_header_data_unit, 'EXP-MEAN'),
                    "exposureMidPoint": handle_missing_header(primary_header_data_unit, 'EXP-MID'),
                    "exposureTotal": handle_missing_header(primary_header_data_unit, 'EXP-TOT'),
                    "exposureTime": handle_missing_header(primary_header_data_unit, 'EXPTIME'),
                    "fifCentering": handle_missing_header(primary_header_data_unit, 'FIFCEN'),
                    "fifCenteringOffset": handle_missing_header(primary_header_data_unit, 'FIFCOFF'),
                    "fifPortOffset": handle_missing_header(primary_header_data_unit, 'FIFPOFF'),
                    "fifPort": handle_missing_header(primary_header_data_unit, 'FIFPORT'),
                    "fifSeparation": handle_missing_header(primary_header_data_unit, 'FIFSEP'),
                    "focusBlueArm": handle_missing_header(primary_header_data_unit, 'FOC-BMIR'),
                    "focusRedArm": handle_missing_header(primary_header_data_unit, 'FOC-RMIR'),
                    "gain": gain_average(handle_missing_header(primary_header_data_unit, 'GAIN')),
                    "gainSet": handle_missing_header(primary_header_data_unit, 'GAINSET'),
                    "iodenStagePosition": handle_missing_header(primary_header_data_unit, 'I2STAGE'),
                    "instrumentName": handle_missing_header(primary_header_data_unit, 'INSTRUME'),
                    "lstObservation": handle_missing_header(primary_header_data_unit, 'LST-OBS'),
                    "numberOfAmplifiersUsed": handle_missing_header(primary_header_data_unit, 'NAMPS'),
                    "numberOfCcdsInDetector": handle_missing_header(primary_header_data_unit, 'NCCDS'),
                    "nodCount": handle_missing_header(primary_header_data_unit, 'NODCOUNT'),
                    "nodPeriod": handle_missing_header(primary_header_data_unit, 'NODPER'),
                    "nodShuffle": handle_missing_header(primary_header_data_unit, 'NODSHUFF'),
                    "observationMode": handle_missing_header(primary_header_data_unit, 'OBSMODE'),
                    "observationType": handle_missing_header(primary_header_data_unit, 'OBSTYPE'),
                    "pressureDewar": handle_missing_header(primary_header_data_unit, 'PRE-DEW'),
                    "pressureVacuum": handle_missing_header(primary_header_data_unit, 'PRE-VAC'),
                    "prescan": handle_missing_header(primary_header_data_unit, 'PRESCAN'),
                    "ccdReadoutSpeed": handle_missing_header(primary_header_data_unit, 'ROSPEED'),
                    "airTemperature": handle_missing_header(primary_header_data_unit, 'TEM-AIR'),
                    "blueCameraTemperature": handle_missing_header(primary_header_data_unit, 'TEM-BCAM'),
                    "collimatorTemperature": handle_missing_header(primary_header_data_unit, 'TEM-COLL'),
                    "echelle": handle_missing_header(primary_header_data_unit, 'TEM-ECH'),
                    "iodineTemperature": handle_missing_header(primary_header_data_unit, 'TEM-IOD'),
                    "opticalBenchTemperature": handle_missing_header(primary_header_data_unit, 'TEM-OB'),
                    "redCameraTemperature": handle_missing_header(primary_header_data_unit, 'TEM-RCAM'),
                    "redMirrorTemperature": handle_missing_header(primary_header_data_unit, 'TEM-RMIR'),
                    "vacuumTemperature": handle_missing_header(primary_header_data_unit, 'TEM-VAC'),
                    "startOfObservationTime": handle_missing_header(primary_header_data_unit, 'TIME-OBS'),
                    "systemTime": handle_missing_header(primary_header_data_unit, 'TIMESYS'),
                    "fitsHeaderVersion": handle_missing_header(primary_header_data_unit, 'VERFITS')
                }
                
                hrs_sql_params = create_insert_sql("HRS", hrs_sql_dictionary)
                
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
                cursor.execute(hrs_sql_params['sql'], hrs_sql_params['sql_params'])
                cursor.execute(target_sql, target_params)
                cursor.execute(data_files_sql, data_files_params)
                cursor.execute(data_preview_sql, data_preview_params)
                ssda_con.commit()

            else:
                print("Not importing any other and OBJECT at this moment")
                exit(1)
                ssda_con.commit()

    ssda_con.close()
    
    
def gain_average(gain):
    gain_values = gain.split(' ')
    total = 0
    
    for i in gain_values:
        total += float(i)
    
    average = total/len(gain_values)
    
    return average


def create_insert_sql(table, dictionary_sql):
    placeholders = ', '.join(['%s'] * len(dictionary_sql))
    columns = ', '.join(dictionary_sql.keys())
    sql = "INSERT INTO {} ( {} ) VALUES ( {} )".format(table, columns, placeholders)
    
    return {
        "sql": sql,
        "sql_params": tuple(dictionary_sql.values())
    }


populate_hrs("/home/sifiso/Downloads/salt_data/hrs")
