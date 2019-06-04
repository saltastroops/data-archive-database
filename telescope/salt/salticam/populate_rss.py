import glob
import os

from astropy.io import fits
from dateutil import parser

from connection import ssda_connect
from util.get_information import *
from util.util import handle_missing_header, dms_degree, hms_degree


def populate_rss(date):
    # setting up a directory for rss from given date
    date = parser.parse(date)
    conn = ssda_connect()
    cursor = conn.cursor()
    # data_directory = '/salt/data/{year}/{monthday}/rss/raw'.format(year=date.strftime('%Y'), monthday=date.strftime('%m%d'))
    # print("DIR: ", data_directory)
    data_directory = '/home/nhlavu/nhlavu/da/database/data-archive-database/data/test_rss/one_file/'
    for filename in glob.iglob(data_directory + '**/*.fits', recursive=True):

        # Opening current fits file
        with fits.open(filename) as header_data_unit_list:
            headers = header_data_unit_list[0].header
            # Obtain the file sie
            file_size = os.path.getsize(filename)

            if handle_missing_header(headers, 'INSTRUME') == 'RSS':
                dms_degree(handle_missing_header(headers, 'DEC'))
                hms_degree(handle_missing_header(headers, 'RA'))

                # Observation-------------------------------------------------------------------Start
                observation_id = handle_missing_header(headers, 'BLOCKID') # TODO: BlockId is not in RSS
                telescope_id = get_telescope_id("SALT")
                telescope_observation_id = get_telescope_observation_id(observation_id)
                observation_date = handle_missing_header(headers, "DATE-OBS")
                observation_status_id = get_observation_status_id(observation_id)

                observation_sql = """
                                    INSERT INTO Observation(
                                        telescopeId,
                                        telescopeObservationId,
                                        startTime,
                                        observationStatusId
                                    )
                                    VALUES (%s,%s,%s,%s)
                                """
                observation_params = (telescope_id, telescope_observation_id, observation_date, observation_status_id)
                cursor.execute(observation_sql, observation_params)
                conn.commit()

                # Observation -------------------------------------------------------------------End

                # Target ------------------------------------------------------------------------Start
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
                    handle_missing_header(headers, 'OBJECT'),
                    hms_degree((handle_missing_header(headers, 'RA'))),
                    dms_degree((handle_missing_header(headers, 'DEC'))),
                    None,
                    1  # TODO TargetType still need to be defined
                )
                cursor.execute(target_sql, target_params)
                # Target ------------------------------------------------------------------------End

                # Data File ---------------------------------------------------------------------Start
                data_category_id = get_data_category_id(handle_missing_header(headers, 'OBJECT'))
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
                    observation_date,
                    filename,
                    get_last_target_id(),
                    file_size,
                    get_last_observation_id()
                )
                cursor.execute(data_files_sql, data_files_params)
                # Data File ---------------------------------------------------------------------End

                # Data File Preview -------------------------------------------------------------Start
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
                cursor.execute(data_preview_sql, data_preview_params)
                # Data File Preview -------------------------------------------------------------End
                # Main Rss input ----------------------------------------------------------------Start

                rss_data = {
                    'telescopeId': telescope_id,
                    'amplifierSection': handle_missing_header(headers, "AMPSEC"),
                    'amplifierTemperature': handle_missing_header(headers, "AMPTEM"),
                    'articulationAngle': handle_missing_header(headers, "AMPTEM"),
                    'articulationPitch': handle_missing_header(headers, "AR-PITCH"),
                    'articulationRoll': handle_missing_header(headers, "AR-ROLL"),
                    'articulationStation': handle_missing_header(headers, "AR_STA"),
                    'articulationStationEncoder': handle_missing_header(headers, "AR-STA-S"),
                    'articulationMachineState': handle_missing_header(headers, "AR-STATE"),
                    'amplifierReadoutX': handle_missing_header(headers, "ATM1_1"),
                    'amplifierReadoutY': handle_missing_header(headers, "ATM2_2"),
                    'biasSection': handle_missing_header(headers, "BIASSEC"),
                    'beamSplitterMachineState': handle_missing_header(headers, "BS-STATE"),
                    # TODO:  'beamSplitterScale': handle_missing_header(headers, "BSCALE"),
                    'beamSplitterZero': handle_missing_header(headers, "BZERO"),
                    'commandedArticulationStation': handle_missing_header(headers, "CAMANG"),
                    'detectorFocusPosition': handle_missing_header(headers, "CAMFOCUS"),
                    'cameraTemperature': handle_missing_header(headers, "CAMTEM"),
                    'numberOfAmplifiers': handle_missing_header(headers, "CCDNAMPS"),
                    'ccdSection': handle_missing_header(headers, "CCDSEC"),
                    'ccdSummation': handle_missing_header(headers, "CCDSUM"),
                    'ccdTemperature': handle_missing_header(headers, "CCDTEM"),
                    'ccdType': handle_missing_header(headers, "CCDTYPE"),
                    'transformationMatrix11': handle_missing_header(headers, "CD1_1"),
                    'transformationMatrix11A': handle_missing_header(headers, "CD1_1A"),
                    'transformationMatrix12': handle_missing_header(headers, "CD1_2"),
                    'transformationMatrix12A': handle_missing_header(headers, "CD1_2A"),
                    'transformationMatrix21': handle_missing_header(headers, "CD2_1"),
                    'transformationMatrix21A': handle_missing_header(headers, "CD2_1A"),
                    'transformationMatrix22': handle_missing_header(headers, "CD2_2"),
                    'transformationMatrix22A': handle_missing_header(headers, "CD2_2A"),
                    'coldEndTemperature': handle_missing_header(headers, "CENTEM"),
                    'configMachineState': handle_missing_header(headers, "CF-STATE"),
                    'collimatorTemperature': handle_missing_header(headers, "COLTEM"),
                    'pixelCoordinatePointX1': handle_missing_header(headers, "CRPIX1"),
                    'pixelCoordinatePointX1A': handle_missing_header(headers, "CRPIX1A"),

# CTYPE2
# CTYPE2A
# CUNIT1
# CUNIT2
# DATASEC
# DATE-OBS
# DEC
# DECPANGL
# DETMODE
# DETNAM
# DETSEC
                    'pixelCoordinatePointX2': handle_missing_header(headers, "CRPIX2"),
                    'pixelCoordinatePointX2A': handle_missing_header(headers, "CRPIX2A"),
                    'rightAscensionPoint1': handle_missing_header(headers, "CRVAL1"),
                    'spatialCoordinatePoint1A': handle_missing_header(headers, "CRVAL1A"),
                    'declinationPoint2': handle_missing_header(headers, "CRVAL2"),
                    'spacialCoordinatePoint2A': handle_missing_header(headers, "CRVAL2A"),
                    'gnomicProjection1': handle_missing_header(headers, "CTYPE1"),
                    'cartesianProjection1A': handle_missing_header(headers, "CTYPE1A"),
                    'gnomicProjection2': handle_missing_header(headers, ""),
                    'cartesianProjection2A': handle_missing_header(headers, ""),
                    'dataSection': handle_missing_header(headers, ""),
                    'dateOfObservation': handle_missing_header(headers, ""),
                    'detectorMode': handle_missing_header(headers, ""),
                    'detectorSection': handle_missing_header(headers, ""),
                    'detectorSize': handle_missing_header(headers, ""),
                    'detectorSoftwareVersion': handle_missing_header(headers, ""),
                    'coolerBoxTemperature': handle_missing_header(headers, ""),
                    'dispersionAxis': handle_missing_header(headers, ""),
                    'etalonMachineState': handle_missing_header(headers, ""),
                    'etalon1A': handle_missing_header(headers, ""),
                    'etalon1B': handle_missing_header(headers, ""),
                    'etalon1F': handle_missing_header(headers, ""),
                    'etalon1Mode': handle_missing_header(headers, ""),
                    'etalon1Wavelength': handle_missing_header(headers, ""),
                    'etalon1X': handle_missing_header(headers, ""),
                    'etalon1Y': handle_missing_header(headers, ""),
                    'etalon1Z': handle_missing_header(headers, ""),
                    'etalon2A': handle_missing_header(headers, ""),
                    'etalon2B': handle_missing_header(headers, ""),
                    'etalon2F': handle_missing_header(headers, ""),
                    'etalon2Mode': handle_missing_header(headers, ""),
                    'etalon2Wavelength': handle_missing_header(headers, ""),
                    'etalon2X': handle_missing_header(headers, ""),
                    'etalon2Y': handle_missing_header(headers, ""),
                    'etalon2Z': handle_missing_header(headers, ""),
                    'exposureTime': handle_missing_header(headers, ""),
                    'filterStation': handle_missing_header(headers, ""),
                    'filterMachineState': handle_missing_header(headers, ""),
                    'filterPosition': handle_missing_header(headers, ""),
                    'filterBarcode': handle_missing_header(headers, ""),
                    'filterStationSteps': handle_missing_header(headers, ""),
                    'filterStationVolts': handle_missing_header(headers, ""),
                    'filterMagazineSteps': handle_missing_header(headers, ""),
                    'filterMagazineVolts': handle_missing_header(headers, ""),
                    'focusPosition': handle_missing_header(headers, ""),
                    'focusPositionSteps': handle_missing_header(headers, ""),
                    'focusPositionVolts': handle_missing_header(headers, ""),
                    'focusMachineState': handle_missing_header(headers, ""),
                    'focusVolts': handle_missing_header(headers, ""),
                    'focusSteps': handle_missing_header(headers, ""),
                    'gain': handle_missing_header(headers, ""),
                    'gain1': handle_missing_header(headers, ""),
                    'gainSet': handle_missing_header(headers, ""),
                    'gratingMagazineSteps': handle_missing_header(headers, ""),
                    'gratingMagazineVolts': handle_missing_header(headers, ""),
                    'gratingRotationAngle': handle_missing_header(headers, ""),
                    'gratingStation': handle_missing_header(headers, ""),
                    'gratingStationSteps': handle_missing_header(headers, ""),
                    'gratingStationVolts': handle_missing_header(headers, ""),
                    'gratingMachineState': handle_missing_header(headers, ""),
                    'gratingRotationAngleSteps': handle_missing_header(headers, ""),
                    'grating': handle_missing_header(headers, ""),
                    'gratingAngle': handle_missing_header(headers, ""),
                    'halfWaveSteps': handle_missing_header(headers, ""),
                    'halfWaveAngle': handle_missing_header(headers, ""),
                    'halfWaveStation': handle_missing_header(headers, ""),
                    'halfWaveStationEncoder': handle_missing_header(headers, ""),
                    'imageId': handle_missing_header(headers, ""),
                    'instrumentName': handle_missing_header(headers, ""),
                    'julianDate': handle_missing_header(headers, ""),
                    'lstObservation': handle_missing_header(headers, ""),
                    'slitmaskBarcode': handle_missing_header(headers, ""),
                    'slitmaskType': handle_missing_header(headers, ""),
                    'numberOfCcds': handle_missing_header(headers, ""),
                    'numberOfExtensions': handle_missing_header(headers, ""),
                    'numberOfWindows': handle_missing_header(headers, ""),
                    'objectName': handle_missing_header(headers, ""),
                    'observationMode': handle_missing_header(headers, ""),
                    'observationType': handle_missing_header(headers, ""),
                    'pfsiControlSystemVersion': handle_missing_header(headers, ""),
                    'pixelScale': handle_missing_header(headers, ""),
                    'polarizationConfig': handle_missing_header(headers, ""),
                    'pfsiProcedure': handle_missing_header(headers, ""),
                    'pupilEnd': handle_missing_header(headers, ""),
                    'quaterWaveSteps': handle_missing_header(headers, ""),
                    'quaterWaveAngle': handle_missing_header(headers, ""),
                    'quaterWaveStation': handle_missing_header(headers, ""),
                    'quaterWaveStationEncoder': handle_missing_header(headers, ""),
                    'noiseReadout': handle_missing_header(headers, ""),
                    'ccdReadoutSpeed': handle_missing_header(headers, ""),
                    'pixelSaturation': handle_missing_header(headers, ""),
                    'shutterMachineState': handle_missing_header(headers, ""),
                    'slitmaskStation': handle_missing_header(headers, ""),
                    'slitmaskStationSteps': handle_missing_header(headers, ""),
                    'slitmaskStationVolts': handle_missing_header(headers, ""),
                    'slitmasMachineState': handle_missing_header(headers, ""),
                    'slitmaskMagazineSteps': handle_missing_header(headers, ""),
                    'slitmaskVolts': handle_missing_header(headers, ""),
                    'startOfObservationTime': handle_missing_header(headers, ""),
                    'systemTyme': handle_missing_header(headers, ""),
                    'fitsHeaderVersion': handle_missing_header(headers, ""),
                    'spatialCoordinate': handle_missing_header(headers, ""),
                    'waveplateMachineState': handle_missing_header(headers, ""),
                    'polarimetryProcedurePattern': handle_missing_header(headers, ""),
                    'crossTalk': handle_missing_header(headers, ""),
                }
                # Main Rss input ----------------------------------------------------------------End
                conn.commit()
                return


populate_rss("2019-05-10")
