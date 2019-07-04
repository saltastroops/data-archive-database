/**
 * SQL for creating the MySQL database for the SAAO/SALT data archive.
 */

-- Create (and use) the database.

CREATE DATABASE IF NOT EXISTS `ssda`;

USE `ssda`;

-- Avoid foreign key issues caused solely by the order of the CREATE statements below.

SET FOREIGN_KEY_CHECKS=0;

/**
 * Spatial reference system for target positions
 */
CREATE OR REPLACE SPATIAL REFERENCE SYSTEM 123456 NAME 'Perfect Unit Sphere' DEFINITION 'GEOGCS["Unit Sphere",DATUM["Unit Sphere",SPHEROID["Unit Sphere",1,0]],PRIMEM["Greenwich",0],UNIT["degree",0.017453292519943278],AXIS["Lon",EAST],AXIS["Lat",NORTH]]';

/**
 * DataCategory
 *
 * The data category such as Science, Arcs, etc.
 */
DROP TABLE IF EXISTS `DataCategory`;
CREATE TABLE `DataCategory` (
     `dataCategoryId` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'Primary key.',
     `dataCategory` VARCHAR(255) UNIQUE NOT NULL COMMENT 'Data category.',
     PRIMARY KEY (`dataCategoryId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

/**
 * Instruments
 *
 * Instrument names for SAAO telescopes and SALT
 */
DROP TABLE IF EXISTS `Instrument`;
CREATE TABLE `Instrument` (
     `instrumentId` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'Primary key for this table(Instrument).',
     `instrumentName` VARCHAR(255) NOT NULL COMMENT 'Name given to an instrument.',
    PRIMARY KEY (`instrumentId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

/**
 * DataFile
 *
 * Metadata for (raw) data files. The data file usually is a (raw) FITS file, but it may also be a text file containing
 * documentation. There are no entries for reduced data.
 */
DROP TABLE IF EXISTS `DataFile`;
CREATE TABLE `DataFile` (
    `dataFileId` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'Primary key.',
    `dataCategoryId` INT(11) UNSIGNED NOT NULL COMMENT 'Category of data contained in the data file.',
    `startTime` DATETIME NOT NULL COMMENT 'The observation start time recorded in the data file.',
    `dataFileName` VARCHAR(255) NOT NULL COMMENT 'Filename, such as R20190203000023.fits.',
    `path` VARCHAR(255) UNIQUE NOT NULL COMMENT 'File path, including the filename, such as /home/path/to/raw/R20190203000023.fits.',
    `targetId` INT(11) UNSIGNED COMMENT 'Target which was observed.',
    `size` FLOAT NOT NULL COMMENT 'File size in bytes.',
    `observationId` INT(11) UNSIGNED NOT NULL COMMENT 'Observation to which the data file belongs.',
    `instrumentId` INT(11) UNSIGNED NOT NULL COMMENT 'Instrument used for this data file',
    INDEX(startTime),
    PRIMARY KEY (`dataFileId`),
    KEY `fk_DataFileDataCategory_idx` (`dataCategoryId`),
    KEY `fk_DataFileTarget_idx` (`targetId`),
    KEY `fk_DataFileObservation_idx` (`observationId`),
    KEY `fk_DataPreviewInstrument_idx` (`instrumentId`),
    CONSTRAINT `fk_DataFileDataCategory` FOREIGN KEY (`dataCategoryId`) REFERENCES `DataCategory` (`dataCategoryId`) ON DELETE NO ACTION ON UPDATE NO ACTION,
    CONSTRAINT `fk_DataFileObservation` FOREIGN KEY (`observationId`) REFERENCES `Observation` (`observationId`) ON DELETE NO ACTION ON UPDATE NO ACTION,
    CONSTRAINT `fk_DataFileTarget` FOREIGN KEY (`targetId`) REFERENCES `Target` (`targetId`) ON DELETE NO ACTION ON UPDATE NO ACTION,
    CONSTRAINT `fk_DataPreviewInstrument` FOREIGN KEY (`instrumentId`) REFERENCES `Instrument` (`instrumentId`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

/**
 * DataPreview
 *
 * Preview file for a data file.
 */
DROP TABLE IF EXISTS `DataPreview`;
CREATE TABLE `DataPreview` (
    `dataPreviewFileName` VARCHAR(255) NOT NULL COMMENT 'Filename of the file containing the preview image, such as R20190203000023-1.png.',
    `path` VARCHAR(255) UNIQUE NOT NULL COMMENT 'File path of the file containing the preview image, such as /home/path/to/preview/R20190203000023-1.png.',
    `dataFileId` INT(11) UNSIGNED NOT NULL COMMENT 'Id of the data file to which the preview image belongs.',
    `dataPreviewOrder` INT(11) UNSIGNED NOT NULL COMMENT 'Defines an order within multiple preview files for the same data file.',
    `dataPreviewTypeId` INT(11) UNSIGNED NOT NULL COMMENT 'Type of data preview file',
    PRIMARY KEY (`dataFileId`, `dataPreviewOrder`),
    KEY `fk_DataPreviewDataFile_idx` (`dataFileId`),
    KEY `fk_DataPreviewDataPreviewType_idx` (`dataPreviewTypeId`),
    CONSTRAINT `fk_DataPreviewDataFile` FOREIGN KEY (`dataFileId`) REFERENCES `DataFile` (`dataFileId`) ON DELETE NO ACTION ON UPDATE NO ACTION,
    CONSTRAINT `fk_DataPreviewDataPreviewType` FOREIGN KEY (`dataPreviewTypeId`) REFERENCES `DataPreviewType` (`dataPreviewTypeId`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

/**
 * DataPreviewType
 *
 * Type of a preview file, such as "Header" or "Image".
 */
DROP TABLE IF EXISTS `DataPreviewType`;
CREATE TABLE `DataPreviewType` (
    `dataPreviewTypeId` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'Primary key.',
    `dataPreviewType` VARCHAR(32) UNIQUE NOT NULL COMMENT 'Type of data preview file/',
    PRIMARY KEY (`dataPreviewTypeId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

/**
 * HRS
 *
 * HRS setup, as described in the primary header of the corresponding FITS data file.
 */
DROP TABLE IF EXISTS `HRS`;
CREATE TABLE `HRS` (
    `hrsId` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'Primary key for this table(HRS).',
    `dataFileId` INT(11) UNSIGNED NOT NULL COMMENT 'A foreign key linking to data file, see table DataFile',
    `amplifierSection` VARCHAR(255) DEFAULT NULL,
    `amplifierTemperature` FLOAT DEFAULT NULL,
    `biasSection` VARCHAR(255) DEFAULT NULL,
    `numberOfAmplifiers` INT(11) DEFAULT NULL,
    `ccdSection` VARCHAR(255) DEFAULT NULL,
    `ccdSummation` VARCHAR(255) DEFAULT NULL,
    `ccdTemperature` FLOAT DEFAULT NULL,
    `ccdType` VARCHAR(255) DEFAULT NULL,
    `dataSection` VARCHAR(255) DEFAULT NULL,
    `dateOfObservation` VARCHAR(255) DEFAULT NULL,
    `detectorMode` VARCHAR(255) DEFAULT NULL,
    `detectorName` VARCHAR(255) DEFAULT NULL,
    `detectorSection` VARCHAR(255) DEFAULT NULL,
    `detectorSerialNumber` VARCHAR(255) DEFAULT NULL,
    `detectorSize` VARCHAR(255) DEFAULT NULL,
    `detectorSoftwareVersion` VARCHAR(255) DEFAULT NULL,
    `exposureMean` FLOAT DEFAULT NULL,
    `exposureMidPoint` FLOAT DEFAULT NULL,
    `exposureTotal` FLOAT DEFAULT NULL,
    `exposureTime` FLOAT DEFAULT NULL,
    `fifCentering` VARCHAR(255) DEFAULT NULL,
    `fifCenteringOffset` VARCHAR(255) DEFAULT NULL,
    `fifPortOffset` VARCHAR(255) DEFAULT NULL,
    `fifPort` VARCHAR(255) DEFAULT NULL,
    `fifSeparation` VARCHAR(255) DEFAULT NULL,
    `focusBlueArm` FLOAT DEFAULT NULL,
    `focusRedArm` FLOAT DEFAULT NULL,
    `gain` FLOAT DEFAULT NULL COMMENT 'An average of gain values',
    `gainSet` VARCHAR(255) DEFAULT NULL,
    `iodenStagePosition` VARCHAR(255) DEFAULT NULL,
    `instrumentName` VARCHAR(255) DEFAULT NULL,
    `lstObservation` VARCHAR(255) DEFAULT NULL,
    `numberOfAmplifiersUsed` INT(11) DEFAULT NULL,
    `numberOfCcdsInDetector` INT(11) DEFAULT NULL,
    `nodCount` INT(11) DEFAULT NULL,
    `nodPeriod` FLOAT DEFAULT NULL,
    `nodShuffle` INT(11) DEFAULT NULL,
    `observationMode` VARCHAR(255) DEFAULT NULL,
    `observationType` VARCHAR(255) DEFAULT NULL,
    `pressureDewar` FLOAT DEFAULT NULL,
    `pressureVacuum` FLOAT DEFAULT NULL,
    `prescan` INT(11) DEFAULT NULL,
    `ccdReadoutSpeed` VARCHAR(255) DEFAULT NULL,
    `airTemperature` FLOAT DEFAULT NULL,
    `blueCameraTemperature` FLOAT DEFAULT NULL,
    `collimatorTemperature` FLOAT DEFAULT NULL,
    `echelle` FLOAT DEFAULT NULL,
    `iodineTemperature` FLOAT DEFAULT NULL,
    `opticalBenchTemperature` FLOAT DEFAULT NULL,
    `redCameraTemperature` FLOAT DEFAULT NULL,
    `redMirrorTemperature` FLOAT DEFAULT NULL,
    `vacuumTemperature` FLOAT DEFAULT NULL,
    `startOfObservationTime` VARCHAR(255) DEFAULT NULL,
    `systemTime` VARCHAR(255) DEFAULT NULL,
    `fitsHeaderVersion` VARCHAR(255) DEFAULT NULL,
    PRIMARY KEY (`hrsId`),
    KEY `fk_HRSDataFile_idx` (`dataFileId`),
    CONSTRAINT `fk_HRSDataFile` FOREIGN KEY (`dataFileId`) REFERENCES `DataFile` (`dataFileId`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

/**
 * Institution
 *
 * An institution, such as SAAO or SALT, accepting proposals.
 */
DROP TABLE IF EXISTS `Institution`;
CREATE TABLE `Institution` (
    `institutionId` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'Primary key.',
    `institutionName` VARCHAR(255) UNIQUE NOT NULL COMMENT 'Name of the institution.',
    PRIMARY KEY (`institutionId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

/**
 * Observation
 *
 * An observation which has been made. Observations that have been scheduled but not done
 * yet are not included in the database. Observations are included in the database irrespective
 * of whether they have been accepted or rejected.
 */

DROP TABLE IF EXISTS `Observation`;
CREATE TABLE `Observation` (
    `observationId` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'Primary key.',
    `proposalId` INT(11) UNSIGNED COMMENT 'Proposal to which the observation belongs.',
    `telescopeId` INT(11) UNSIGNED NOT NULL  COMMENT 'Telescope used for taking the data.',
    `telescopeObservationId` VARCHAR(255) COMMENT 'Identifier used by the telescope for the observsation,',
    `night` DATE NOT NULL COMMENT 'Date an observation was taken',
    `availableFrom` DATE NOT NULL COMMENT 'A date observation is available to the public',
    `observationStatusId` INT(11) UNSIGNED NOT NULL COMMENT 'A foreign key linking to observation status, see table ObservationStatus',
    PRIMARY KEY (`observationId`),
    KEY `fk_ObservationProposal_idx` (`proposalId`),
    KEY `fk_ObservationObservationStatus_idx` (`observationStatusId`),
    KEY `fk_ObservationTelescope_idx` (`telescopeId`),
    CONSTRAINT `fk_ObservationProposal` FOREIGN KEY (`proposalId`) REFERENCES `Proposal` (`proposalId`) ON DELETE NO ACTION ON UPDATE NO ACTION,
    CONSTRAINT `fk_ObservationTelescope` FOREIGN KEY (`telescopeId`) REFERENCES `Telescope` (`telescopeId`) ON DELETE NO ACTION ON UPDATE NO ACTION,
    CONSTRAINT `fk_ObservationObservationStatus` FOREIGN KEY (`observationStatusId`) REFERENCES `ObservationStatus` (`observationStatusId`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

/**
 * ObservationStatus
 *
 * The status of an observation, i.e. whether the observation has been accepted or rejected.
 */

DROP TABLE IF EXISTS `ObservationStatus`;
CREATE TABLE `ObservationStatus` (
    `observationStatusId` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'Primary key.',
    `status` VARCHAR(255) UNIQUE NOT NULL COMMENT 'Observation status.',
    PRIMARY KEY (`observationStatusId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

/**
 * Proposal
 *
 * A proposal is the request for observing time made to the relevant TAC(s). There may be
 * multiple observations for a proposal. The database doesn't necessarily contain proposals
  if no data have been taken for them.
 */
DROP TABLE IF EXISTS `Proposal`;
CREATE TABLE `Proposal` (
    `proposalId` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'Primary key.',
    `proposalCode` VARCHAR(255) NOT NULL COMMENT 'Code used for referring to a proposal, such as 2018-2-SCI-042.',
    `principalInvestigatorGivenName` VARCHAR(255) COMMENT 'Principal investigator\'s given name.',
    `principalInvestigatorFamilyName` VARCHAR(255) COMMENT 'The principal investigator\'s family name.',
    `title` VARCHAR(255) COMMENT 'Proposal title',
    `institutionId` INT(11) UNSIGNED NOT NULL COMMENT 'Institution to which the proposal was submitted.',
    PRIMARY KEY (`proposalId`),
    KEY `fk_ProposalInstitution_idx` (`institutionId`),
    CONSTRAINT `fk_ProposalInstitution` FOREIGN KEY (`institutionId`) REFERENCES `Institution` (`institutionId`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

/**
 * ProposalInvestigator
 *
 * A join table joining proposals and user accounts of investigators on the proposals. This table
 * is not guaranteed to give the full list of investigators for a proposal, and it should only be
 * used for checking whether a given user may access proposal content,
 */
DROP TABLE IF EXISTS `ProposalInvestigator`;
CREATE TABLE `ProposalInvestigator` (
     `proposalId` INT(11) UNSIGNED NOT NULL COMMENT 'A foreign key linking to proposal, see Proposal table',
     `institutionUserId` VARCHAR(255) NOT NULL  COMMENT 'A user identifier on the institute database. Not a ssda key',
     PRIMARY KEY (`proposalId`, `institutionUserId`),
     CONSTRAINT `fk_ProposalInvestigatorProposal` FOREIGN KEY (`proposalId`) REFERENCES `Proposal` (`proposalId`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

/**
 * RSS
 *
 * RSS setup, as described in the primary header of the corresponding FITS data file.
 */
DROP TABLE IF EXISTS `RSS`;
CREATE TABLE `RSS` (
    `rssId` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'Primary key for this table(RSS).',
    `dataFileId` INT(11) UNSIGNED NOT NULL COMMENT 'A foreign key linking to DataFile table.',
    `amplifierSection` VARCHAR(255) DEFAULT NULL,
    `amplifierTemperature` FLOAT DEFAULT NULL,
    `articulationAngle` FLOAT DEFAULT NULL,
    `articulationPitch` FLOAT DEFAULT NULL,
    `articulationRoll` FLOAT DEFAULT NULL,
    `articulationStation` VARCHAR(255) DEFAULT NULL,
    `articulationStationEncoder` FLOAT DEFAULT NULL,
    `articulationMachineState` VARCHAR(255) DEFAULT NULL,
    `amplifierReadoutX` INT(11) DEFAULT NULL,
    `amplifierReadoutY` INT(11) DEFAULT NULL,
    `biasSection` VARCHAR(255) DEFAULT NULL,
    `beamSplitterMachineState` VARCHAR(255) DEFAULT NULL,
    `beamSplitterScale` FLOAT DEFAULT NULL,
    `beamSplitterZero` FLOAT DEFAULT NULL,
    `commandedArticulationStation` FLOAT DEFAULT NULL,
    `detectorFocusPosition` INT(11) DEFAULT NULL,
    `cameraTemperature` FLOAT DEFAULT NULL,
    `numberOfAmplifiers` INT(11) DEFAULT NULL,
    `ccdSection` VARCHAR(255) DEFAULT NULL,
    `ccdSummation` VARCHAR(255) DEFAULT NULL,
    `ccdTemperature` FLOAT DEFAULT NULL,
    `ccdType` VARCHAR(255) DEFAULT NULL,
    `transformationMatrix11` FLOAT DEFAULT NULL,
    `transformationMatrix11A` FLOAT DEFAULT NULL,
    `transformationMatrix12` FLOAT DEFAULT NULL,
    `transformationMatrix12A` FLOAT DEFAULT NULL,
    `transformationMatrix21` FLOAT DEFAULT NULL,
    `transformationMatrix21A` FLOAT DEFAULT NULL,
    `transformationMatrix22` FLOAT DEFAULT NULL,
    `transformationMatrix22A` FLOAT DEFAULT NULL,
    `coldEndTemperature` FLOAT DEFAULT NULL,
    `configMachineState` VARCHAR(255) DEFAULT NULL,
    `collimatorTemperature` FLOAT DEFAULT NULL,
    `pixelCoordinatePointX1` FLOAT DEFAULT NULL,
    `pixelCoordinatePointX1A` FLOAT DEFAULT NULL,
    `pixelCoordinatePointX2` FLOAT DEFAULT NULL,
    `pixelCoordinatePointX2A` FLOAT DEFAULT NULL,
    `rightAscensionPoint1` FLOAT DEFAULT NULL,
    `spatialCoordinatePoint1A` FLOAT DEFAULT NULL,
    `declinationPoint2` FLOAT DEFAULT NULL,
    `spacialCoordinatePoint2A` FLOAT DEFAULT NULL,
    `gnomicProjection1` VARCHAR(255) DEFAULT NULL,
    `cartesianProjection1A` VARCHAR(255) DEFAULT NULL,
    `gnomicProjection2` VARCHAR(255) DEFAULT NULL,
    `cartesianProjection2A` VARCHAR(255) DEFAULT NULL,
    `dataSection` VARCHAR(255) DEFAULT NULL,
    `dateOfObservation` VARCHAR(255) DEFAULT NULL,
    `detectorMode` VARCHAR(255) DEFAULT NULL,
    `detectorSection` VARCHAR(255) DEFAULT NULL,
    `detectorSize` VARCHAR(255) DEFAULT NULL,
    `detectorSoftwareVersion` VARCHAR(255) DEFAULT NULL,
    `coolerBoxTemperature` FLOAT DEFAULT NULL,
    `dispersionAxis` INT(11) DEFAULT NULL,
    `etalonMachineState` VARCHAR(255) DEFAULT NULL,
    `etalon1A` FLOAT DEFAULT NULL,
    `etalon1B` FLOAT DEFAULT NULL,
    `etalon1F` FLOAT DEFAULT NULL,
    `etalon1Mode` VARCHAR(255) DEFAULT NULL,
    `etalon1Wavelength` FLOAT DEFAULT NULL,
    `etalon1X` FLOAT DEFAULT NULL,
    `etalon1Y` FLOAT DEFAULT NULL,
    `etalon1Z` FLOAT DEFAULT NULL,
    `etalon2A` FLOAT DEFAULT NULL,
    `etalon2B` FLOAT DEFAULT NULL,
    `etalon2F` FLOAT DEFAULT NULL,
    `etalon2Mode` VARCHAR(255) DEFAULT NULL,
    `etalon2Wavelength` FLOAT DEFAULT NULL,
    `etalon2X` FLOAT DEFAULT NULL,
    `etalon2Y` FLOAT DEFAULT NULL,
    `etalon2Z` FLOAT DEFAULT NULL,
    `exposureTime` FLOAT DEFAULT NULL,
    `filterStation` INT(11) DEFAULT NULL,
    `filterMachineState` VARCHAR(255) DEFAULT NULL,
    `filterPosition` INT(11) DEFAULT NULL,
    `filterBarcode` VARCHAR(255) DEFAULT NULL,
    `filterStationSteps` FLOAT DEFAULT NULL,
    `filterStationVolts` FLOAT DEFAULT NULL,
    `filterMagazineSteps` INT(11) DEFAULT NULL,
    `filterMagazineVolts` FLOAT DEFAULT NULL,
    `focusPosition` FLOAT DEFAULT NULL,
    `focusPositionSteps` FLOAT DEFAULT NULL,
    `focusPositionVolts` FLOAT DEFAULT NULL,
    `focusMachineState` VARCHAR(255) DEFAULT NULL,
    `focusVolts` FLOAT DEFAULT NULL,
    `focusSteps` INT(11) DEFAULT NULL,
    `gain` FLOAT DEFAULT NULL COMMENT 'An average of gain values',
    `gain1` VARCHAR(255) DEFAULT NULL,
    `gainSet` VARCHAR(255) DEFAULT NULL,
    `gratingMagazineSteps` INT(11) DEFAULT NULL,
    `gratingMagazineVolts` FLOAT DEFAULT NULL,
    `gratingRotationAngle` FLOAT DEFAULT NULL,
    `gratingStation` VARCHAR(255) DEFAULT NULL,
    `gratingStationSteps` FLOAT DEFAULT NULL,
    `gratingStationVolts` FLOAT DEFAULT NULL,
    `gratingMachineState` VARCHAR(255) DEFAULT NULL,
    `gratingRotationAngleSteps` INT(11) DEFAULT NULL,
    `grating` VARCHAR(255) DEFAULT NULL,
    `gratingAngle` FLOAT DEFAULT NULL,
    `halfWaveSteps` INT(11) DEFAULT NULL,
    `halfWaveAngle` FLOAT DEFAULT NULL,
    `halfWaveStation` VARCHAR(255) DEFAULT NULL,
    `halfWaveStationEncoder` FLOAT DEFAULT NULL,
    `imageId` VARCHAR(255) DEFAULT NULL,
    `instrumentName` VARCHAR(255) DEFAULT NULL,
    `julianDate` FLOAT DEFAULT NULL,
    `lstObservation` VARCHAR(255) DEFAULT NULL,
    `slitmaskBarcode` VARCHAR(255) DEFAULT NULL,
    `slitmaskType` VARCHAR(255) DEFAULT NULL,
    `numberOfCcds` INT(11) DEFAULT NULL,
    `numberOfExtensions` INT(11) DEFAULT NULL,
    `numberOfWindows` INT(11) DEFAULT NULL,
    `objectName` VARCHAR(255) DEFAULT NULL,
    `observationMode` VARCHAR(255) DEFAULT NULL,
    `observationType` VARCHAR(255) DEFAULT NULL,
    `pfsiControlSystemVersion` VARCHAR(255) DEFAULT NULL,
    `pixelScale` FLOAT DEFAULT NULL,
    `polarizationConfig` VARCHAR(255) DEFAULT NULL,
    `pfsiProcedure` VARCHAR(255) DEFAULT NULL,
    `pupilEnd` FLOAT DEFAULT NULL,
    `quaterWaveSteps` INT(11) DEFAULT NULL,
    `quaterWaveAngle` FLOAT DEFAULT NULL,
    `quaterWaveStation` VARCHAR(255) DEFAULT NULL,
    `quaterWaveStationEncoder` VARCHAR(255) DEFAULT NULL,
    `noiseReadout` FLOAT DEFAULT NULL,
    `ccdReadoutSpeed` VARCHAR(255) DEFAULT NULL,
    `pixelSaturation` INT(11) DEFAULT NULL,
    `shutterMachineState` VARCHAR(255) DEFAULT NULL,
    `slitmaskStation` VARCHAR(255) DEFAULT NULL,
    `slitmaskStationSteps` FLOAT DEFAULT NULL,
    `slitmaskStationVolts` FLOAT DEFAULT NULL,
    `slitmasMachineState` VARCHAR(255) DEFAULT NULL,
    `slitmaskMagazineSteps` INT(11) DEFAULT NULL,
    `slitmaskVolts` FLOAT DEFAULT NULL,
    `startOfObservationTime` VARCHAR(255) DEFAULT NULL,
    `systemTime` VARCHAR(255) DEFAULT NULL,
    `fitsHeaderVersion` VARCHAR(255) DEFAULT NULL,
    `spatialCoordinate` VARCHAR(255) DEFAULT NULL,
    `waveplateMachineState` VARCHAR(255) DEFAULT NULL,
    `polarimetryProcedurePattern` VARCHAR(255) DEFAULT NULL,
    `crossTalk` FLOAT DEFAULT NULL,
    PRIMARY KEY (`rssId`),
    KEY `fk_RSSDataFile_idx` (`dataFileId`),
    CONSTRAINT `fk_RSSDataFile` FOREIGN KEY (`dataFileId`) REFERENCES `DataFile` (`dataFileId`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

/**
 * Salticam
 *
 * Salticam setup, as described in the primary header of the corresponding FITS data file.
 */
DROP TABLE IF EXISTS `Salticam`;
CREATE TABLE `Salticam` (
    `salticamId` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'Primary key for this table(Salticam).',
    `dataFileId` INT(11) UNSIGNED NOT NULL COMMENT 'A foreign key linking to Datafile table.',
    `amplifierSection` VARCHAR(255) DEFAULT NULL,
    `amplifierTemperature` FLOAT DEFAULT NULL,
    `amplifierReadoutX` INT(11) DEFAULT NULL,
    `amplifierReadoutY` INT(11) DEFAULT NULL,
    `biasSection` VARCHAR(255) DEFAULT NULL,
    `beamSplitterScale` FLOAT DEFAULT NULL,
    `beamSplitterZero` FLOAT DEFAULT NULL,
    `detectorFocusPosition` INT(11) DEFAULT NULL,
    `numberOfAmplifiers` INT(11) DEFAULT NULL,
    `ccdSection` VARCHAR(255) DEFAULT NULL,
    `ccdSummation` VARCHAR(255) DEFAULT NULL,
    `ccdTemperature` FLOAT DEFAULT NULL,
    `ccdType` VARCHAR(255) DEFAULT NULL,
    `transformationMatrix11` FLOAT DEFAULT NULL,
    `transformationMatrix11A` FLOAT DEFAULT NULL,
    `transformationMatrix12` FLOAT DEFAULT NULL,
    `transformationMatrix12A` FLOAT DEFAULT NULL,
    `transformationMatrix21` FLOAT DEFAULT NULL,
    `transformationMatrix21A` FLOAT DEFAULT NULL,
    `transformationMatrix22` FLOAT DEFAULT NULL,
    `transformationMatrix22A` FLOAT DEFAULT NULL,
    `coldEndTemperature` FLOAT DEFAULT NULL,
    `pixelCoordinatePointX1` FLOAT DEFAULT NULL,
    `pixelCoordinatePointX1A` FLOAT DEFAULT NULL,
    `pixelCoordinatePointX2` FLOAT DEFAULT NULL,
    `pixelCoordinatePointX2A` FLOAT DEFAULT NULL,
    `rightAsertionPoint1` FLOAT DEFAULT NULL,
    `spatialCoordinatePoint1A` FLOAT DEFAULT NULL,
    `declanationPoint2` FLOAT DEFAULT NULL,
    `spacialCoordinatePoint2A` FLOAT DEFAULT NULL,
    `gnomicProjection1` VARCHAR(255) DEFAULT NULL,
    `cartesianProjection1A` VARCHAR(255) DEFAULT NULL,
    `gnomicProjection2` VARCHAR(255) DEFAULT NULL,
    `cartesianProjection2A` VARCHAR(255) DEFAULT NULL,
    `anglesDegreesAlways1` VARCHAR(255) DEFAULT NULL,
    `anglesDegreesAlways2` VARCHAR(255) DEFAULT NULL,
    `dataSection` VARCHAR(255) DEFAULT NULL,
    `dateOfObservation` VARCHAR(255) DEFAULT NULL,
    `detectorMode` VARCHAR(255) DEFAULT NULL,
    `detectorSection` VARCHAR(255) DEFAULT NULL,
    `detectorSize` VARCHAR(255) DEFAULT NULL,
    `detectorSoftwareVersion` VARCHAR(255) DEFAULT NULL,
    `coolerBoxTemperature` FLOAT DEFAULT NULL,
    `exposureTime` FLOAT DEFAULT NULL,
    `filterPosition` INT(11) DEFAULT NULL,
    `filterName` VARCHAR(255) DEFAULT NULL,
    `gain` FLOAT DEFAULT NULL COMMENT 'An average of gain values',
    `gain1` VARCHAR(255) DEFAULT NULL,
    `gainSet` VARCHAR(255) DEFAULT NULL,
    `imageId` VARCHAR(255) DEFAULT NULL,
    `instrumentName` VARCHAR(255) DEFAULT NULL,
    `julianDate` FLOAT DEFAULT NULL,
    `lstObservation` VARCHAR(255) DEFAULT NULL,
    `numberOfCcds` INT(11) DEFAULT NULL,
    `numberOfExtensions` INT(11) DEFAULT NULL,
    `numberOfWindows` INT(11) DEFAULT NULL,
    `objectName` VARCHAR(255) DEFAULT NULL,
    `observationMode` VARCHAR(255) DEFAULT NULL,
    `observationType` VARCHAR(255) DEFAULT NULL,
    `pixelScale` FLOAT DEFAULT NULL,
    `pupilEnd` FLOAT DEFAULT NULL,
    `noiseReadout` FLOAT DEFAULT NULL,
    `ccdReadoutSpeed` VARCHAR(255) DEFAULT NULL,
    `pixelSaturation` INT(11) DEFAULT NULL,
    `startOfObservationTime` VARCHAR(255) DEFAULT NULL,
    `systemTime` VARCHAR(255) DEFAULT NULL,
    `fitsHeaderVersion` VARCHAR(255) DEFAULT NULL,
    `spatialCoordinate` VARCHAR(255) DEFAULT NULL,
    `crossTalk` FLOAT DEFAULT NULL,
    PRIMARY KEY (`salticamId`),
    KEY `fk_SalticamDataFile_idx` (`dataFileId`),
    CONSTRAINT `fk_SalticamDataFile` FOREIGN KEY (`dataFileId`) REFERENCES `DataFile` (`dataFileId`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

/**
 * Target
 *
 * An observed target.
 */
DROP TABLE IF EXISTS `Target`;
CREATE TABLE `Target` (
      `targetId` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'Primary key.',
      `targetName` VARCHAR(255) NOT NULL COMMENT 'Target name',
      `rightAscension` FLOAT NOT NULL COMMENT 'Right ascension, in degrees from 0 to 360.',
      `declination` FLOAT NOT NULL COMMENT 'Declination, indegrees from -90 to 90.',
      `position` POINT SRID 123456 NOT NULL COMMENT 'Right ascension and declination. The right ascension is offset by -180 deg so that it falls into [-180, 180].',
      `targetTypeId` INT(11) UNSIGNED COMMENT 'Id of the target type.',
      PRIMARY KEY (`targetId`),
      KEY `fk_TargetTargetType_idx` (`targetTypeId`),
      CONSTRAINT `fk_TargetTargetType` FOREIGN KEY (`targetTypeId`) REFERENCES `TargetType` (`targetTypeId`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

/**
 * TargetType
 *
 * The target type according to the SIMBAD object classification.
 */
DROP TABLE IF EXISTS `TargetType`;
CREATE TABLE `TargetType` (
    `targetTypeId` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'Primary key.',
    `numericCode` VARCHAR(255) UNIQUE NOT NULL COMMENT 'The numeric code for the target type, such as “14.06.16.01”.',
    `explanation` VARCHAR(255) NOT NULL COMMENT 'An explanation of the target type, such as “pulsating white dwarf”.',
    PRIMARY KEY (`targetTypeId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

/**
 * Telescope
 *
 * A telescope.
 */
DROP TABLE IF EXISTS `Telescope`;
CREATE TABLE `Telescope` (
     `telescopeId` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'Primary key.',
     `telescopeName` VARCHAR(255) UNIQUE NOT NULL  COMMENT 'Telescope name.',
     `institutionId` INT(11) UNSIGNED NOT NULL COMMENT 'Id of the institution owning the telescope.',
     PRIMARY KEY (`telescopeId`),
     KEY `fk_TelescopeInstitution_idx` (`institutionId`),
     CONSTRAINT `fk_TelescopeInstitution` FOREIGN KEY (`institutionId`) REFERENCES `Institution` (`institutionId`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- Now that all tables have been created, foreign key constraints should be honoured again.

SET FOREIGN_KEY_CHECKS=1;

-- Add the data categories.

INSERT INTO DataCategory (dataCategory) VALUES ('Arc'), ('Bias'), ('Flat'), ('Science');

-- Add the data preview types.

INSERT INTO DataPreviewType (dataPreviewType) VALUES ('Header'), ('Image');

-- Add the institutions.

INSERT INTO Institution (institutionId, institutionName) VALUES (1, 'SAAO'), (2, 'SALT');

-- Add the observation status values.

INSERT INTO ObservationStatus (`status`) VALUES ('Accepted'), ('Rejected');

-- Add the target types.

INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('15.00.51.00', 'spiral galaxy') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('12.05.05.00', 'interacting galaxies') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('15.00.50.00', 'elliptical galaxy') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('14.06.50.00', 'neutron star') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('12.13.11.00', 'cataclysmic variable star') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('00.00.00.00', 'object of unknown nature') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('50.02.01.00', 'Pluto') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('12.13.01.00', 'eclipsing binary') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('14.09.04.03', 'pulsar') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('12.03.00.00', 'cluster of galaxies') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('12.11.01.00', 'globular cluster') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('12.11.00.00', 'cluster of stars') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('14.06.18.00', 'brown dwarf (M<0.08solMass)') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('15.15.00.00', 'active galactic nucleus') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('12.11.02.00', 'open (galactic) cluster') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('06.50.00.00', 'supersoft source') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('14.06.25.00', 'pre-main sequence star') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('14.09.00.00', 'variable star') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('14.00.00.00', 'star') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('15.15.04.00', 'quasar') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('14.06.16.00', 'white dwarf') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('12.13.00.00', 'double, binary or multiple star') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('15.00.53.00', 'irregular galaxy') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('14.09.01.00', 'variable star of irregular type') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('50.01.07.00', 'Uranus') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('12.13.11.06', 'nova') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('51.01.02.00', 'photometric standard') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('15.15.03.00', 'blazar') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('13.08.50.00', 'bipolar nebula') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('51.01.01.00', 'astrometric standard') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('51.02.02.00', 'dome flat') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('51.01.06.00', 'guide star') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('51.01.04.00', 'polarimetric standard') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('51.01.05.00', 'radial velocity standard') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('51.02.01.00', 'sky flat') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('51.01.04.01', 'spectropolarimetric standard') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('51.01.03.00', 'spectroscopic standard') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('15.00.52.00', 'dwarf galaxy') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('15.00.00.00', 'galaxy') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('15.14.00.00', 'gravitationally lensed image') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('15.15.02.00', 'Seyfert galaxy') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('15.12.00.00', 'starburst galaxy') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('15.50.00.00', 'galaxy with supernova') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('12.50.00.00', 'star field') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('13.08.06.00', 'dark cloud (nebula)') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('13.08.51.00', 'gaseous nebula') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('13.14.50.00', 'outflow or jet') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('13.08.07.00', 'reflection nebula') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('13.13.00.00', 'supernova remnant') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('50.03.02.00', 'asteroid') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('50.03.01.00', 'comet') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('50.01.03.00', 'Earth') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('50.03.03.00', 'Trans-Neptunian object') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('50.01.05.00', 'Jupiter') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('50.01.04.00', 'Mars') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('50.01.01.00', 'Mercury') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('50.01.03.01', 'Moon') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('50.01.08.00', 'Neptune') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('50.04.00.00', 'planetary moon') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('50.05.00.00', 'planetary ring') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('50.01.06.00', 'Saturn') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('50.01.02.00', 'Venus') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('14.06.51.00', 'black hole') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('14.09.05.03', 'Cepheid variable star') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('07.03.00.00', 'gamma-ray burst') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('09.03.00.00', '(micro)lensing event') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('14.07.50.00', 'nearby star') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('14.07.00.00', 'high proper-motion star') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('14.09.08.00', 'supernova') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('14.06.30.00', 'Wolf-Rayet star') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('01.00.00.00', 'radio-source') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('01.14.00.00', 'maser') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('06.00.00.00', 'X-ray source') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('07.00.00.00', 'gamma-ray source') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('08.00.00.00', 'inexistent objects') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('08.03.00.00', 'not an object (artefact)') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('09.00.00.00', 'gravitational source') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('09.07.00.00', 'possible gravitational lens') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('09.08.00.00', 'possible gravitationally lensed image') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('09.09.00.00', 'gravitational lens') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('09.11.00.00', 'gravitational lens system (lens+images)') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('10.00.00.00', 'candidate objects') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('10.02.00.00', 'possible supercluster of galaxies') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('10.03.00.00', 'possible cluster of galaxies') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('10.04.00.00', 'possible Group of galaxies') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('10.11.00.00', 'physical binary candidate') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('10.11.01.00', 'eclipsing binary candidate') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('10.11.11.00', 'cataclysmic binary candidate') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('10.11.12.00', 'X-ray binary candidate') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('10.11.12.02', 'low-mass X-ray binary candidate') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('10.11.12.03', 'high-mass X-ray binary candidate') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('10.12.00.00', 'possible peculiar star') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('10.12.01.00', 'young stellar object candidate') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('10.12.02.00', 'pre-main sequence star candidate') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('10.12.02.03', 'T Tau star candidate') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('10.12.03.00', 'possible carbon Star') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('10.12.04.00', 'possible S Star') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('10.12.05.00', 'possible star with envelope of OH/IR type') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('10.12.06.00', 'possible star with envelope of CH type') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('10.12.07.00', 'possible Wolf-Rayet star') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('10.12.08.00', 'possible Be star') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('10.12.11.00', 'possible horizontal branch star') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('10.12.12.00', 'possible red giant Branch star') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('10.12.13.00', 'possible red supergiant star') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('10.12.14.00', 'possible asymptotic giant branch star') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('10.12.15.00', 'post-AGB star candidate') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('10.12.16.00', 'candidate blue straggler Star') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('10.12.18.00', 'white dwarf candidate') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('10.12.20.00', 'neutron star candidate') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('10.12.22.00', 'black hole candidate') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('10.12.23.00', 'supernova candidate') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('10.12.24.00', 'low-mass star candidate') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('10.12.26.00', 'brown dwarf candidate') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('12.00.00.00', 'composite object') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('12.01.00.00', 'region defined in the sky') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('12.01.05.00', 'underdense region of the Universe') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('12.02.00.00', 'supercluster of galaxies') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('12.04.00.00', 'group of galaxies') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('12.04.05.00', 'compact group of galaxies') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('12.04.50.00', 'group of quasars') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('12.05.00.00', 'pair of galaxies') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('12.10.00.00', 'possible globular cluster') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('12.12.00.00', 'association of stars') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('12.13.01.01', 'eclipsing binary of Algol type') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('12.13.01.02', 'eclipsing binary of beta Lyr type') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('12.13.01.03', 'eclipsing binary of W UMa type') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('12.13.01.08', 'star showing eclipses by its planet') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('12.13.02.00', 'spectroscopic binary') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('12.13.11.02', 'cataclysmic var. DQ Her type') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('12.13.11.03', 'cataclysmic var. AM Her type') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('12.13.11.05', 'nova-like Star') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('12.13.11.07', 'dwarf nova') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('12.13.12.00', 'X-ray binary') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('12.13.12.02', 'low mass X-ray binary') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('12.13.12.03', 'high mass X-ray binary') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('13.00.00.00', 'insterstellar matter') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('13.01.00.00', 'part of cloud') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('13.02.00.00', 'possible planetary nebula') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('13.03.00.00', 'cometary globule') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('13.04.00.00', 'bubble') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('13.06.00.00', 'emission object') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('13.08.00.00', 'cloud or nebula') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('13.08.03.00', 'galactic nebula') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('13.08.04.00', 'bright nebula') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('13.08.12.00', 'molecular cloud') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('13.08.12.03', 'globule (low-mass dark cloud)') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('13.08.12.06', 'dense core inside a molecular cloud') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('13.08.13.00', 'high-velocity cloud') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('13.09.00.00', 'HII (ionized) region') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('13.10.00.00', 'planetary nebula') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('13.11.00.00', 'HI shell') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('13.12.00.00', 'supernova remnant candidate') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('13.14.00.00', 'circumstellar matter') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('13.14.01.00', 'outflow candidate') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('13.14.15.00', 'outflow') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('13.14.16.00', 'Herbig-Haro object') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('14.01.00.00', 'star in cluster') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('14.02.00.00', 'star in nebula') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('14.03.00.00', 'star in association') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('14.04.00.00', 'star in double system') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('14.05.00.00', 'star suspected of variability') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('14.06.00.00', 'peculiar star') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('14.06.01.00', 'horizontal branch star') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('14.06.02.00', 'young stellar object') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('14.06.05.00', 'emission-line star') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('14.06.05.03', 'Be star') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('14.06.06.00', 'blue straggler star') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('14.06.10.00', 'red giant branch star') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('14.06.12.00', 'asymptotic giant branch star (He-burning)') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('14.06.12.03', 'carbon star') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('14.06.12.06', 'S star') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('14.06.13.00', 'red supergiant star') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('14.06.15.00', 'post-AGB star (proto-PN)') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('14.06.16.01', 'pulsating white dwarf') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('14.06.17.00', 'low-mass star (M<1solMass)') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('14.06.23.00', 'star with envelope of OH/IR type') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('14.06.24.00', 'star with envelope of CH type') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('14.06.25.03', 'T Tau-type star') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('14.08.00.00', 'high-velocity star') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('14.09.01.01', 'variable star of Orion type') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('14.09.01.02', 'variable star with rapid variations') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('14.09.03.00', 'eruptive variable star') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('14.09.03.01', 'flare star') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('14.09.03.02', 'variable star of FU Ori type') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('14.09.03.04', 'variable star of R CrB type') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('14.09.04.00', 'rotationally variable star') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('14.09.04.01', 'variable star of alpha2 CVn type') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('14.09.04.02', 'ellipsoidal variable star') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('14.09.04.04', 'variable of BY Dra type') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('14.09.04.05', 'variable of RS CVn type') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('14.09.05.00', 'pulsating variable star') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('14.09.05.02', 'variable star of RR Lyr type') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('14.09.05.05', 'variable star of delta Sct type') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('14.09.05.06', 'variable star of RV Tau type') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('14.09.05.07', 'variable star of W Vir type') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('14.09.05.08', 'variable star of beta Cep type') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('14.09.05.09', 'classical Cepheid (delta Cep type)') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('14.09.05.10', 'variable star of gamma Dor type') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('14.09.06.00', 'long-period variable star') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('14.09.06.01', 'variable Star of Mira Cet type') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('14.09.06.04', 'semi-regular pulsating star') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('14.09.09.00', 'symbiotic star') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('14.14.00.00', 'sub-stellar object') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('14.14.02.00', 'extra-solar planet candidate') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('14.50.00.00', 'isolated star (not a member of a particular galaxy)') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('15.01.00.00', 'part of a galaxy') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('15.02.00.00', 'galaxy in cluster of galaxies') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('15.02.02.00', 'brightest galaxy in a cluster (BCG)') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('15.03.00.00', 'galaxy in group of galaxies') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('15.04.00.00', 'galaxy in Pair of galaxies') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('15.05.00.00', 'galaxy with high redshift') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('15.06.00.00', 'absorption line system') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('15.06.01.00', 'Ly alpha absorption line system') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('15.06.02.00', 'damped Ly-alpha absorption line system') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('15.06.03.00', 'metallic absorption line system') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('15.06.05.00', 'Lyman limit system') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('15.06.08.00', 'broad absorption line system') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('15.07.00.00', 'radio galaxy') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('15.08.00.00', 'HII galaxy') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('15.09.00.00', 'low surface brightness galaxy') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('15.10.00.00', 'possible active galactic nucleus') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('15.10.07.00', 'possible quasar') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('15.10.11.00', 'possible blazar') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('15.10.17.00', 'possible BL Lac') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('15.11.00.00', 'emission-line galaxy') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('15.13.00.00', 'blue compact galaxy') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('15.14.01.00', 'gravitationally lensed image of a galaxy') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('15.14.07.00', 'gravitationally lensed image of a quasar') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('15.15.01.00', 'LINER-type active galactic nucleus') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('15.15.02.01', 'Seyfert 1 galaxy') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('15.15.02.02', 'Seyfert 2 galaxy') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('15.15.03.01', 'BL Lac - type object') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('15.15.03.02', 'optically violently variable object') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('50.00.00.00', 'solar system object') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('50.01.00.00', 'planet') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('50.02.00.00', 'dwarf planet') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('50.02.02.00', 'Ceres') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('50.02.03.00', 'Haumea') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('50.02.04.00', 'MakeMake') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('50.02.05.00', 'Eris') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('50.03.00.00', 'small Solar System body') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('51.00.00.00', 'calibration') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('51.01.00.00', 'standard') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('51.02.00.00', 'flat') ;
INSERT INTO `TargetType` (`numericCode`, `explanation`) VALUES ('52.00.00.00', 'man-made object') ;

-- Add the telescopes.

INSERT INTO Telescope (telescopeName, institutionId) VALUE ('SALT', 1), ('1.9 m', 1), ('1.0 m', 1), ('Lesedi', 1);
INSERT INTO Instrument (instrumentName, instrumentId) VALUE ('RSS', 1), ('HRS', 2), ('Salticam', 3), ('SHOC', 4);
