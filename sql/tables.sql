SET FOREIGN_KEY_CHECKS=0 COMMENT 'Since tables are not in other this must be disable and enabled at the end';

/**
 * Spatial reference system for target positions
 */
CREATE OR REPLACE SPATIAL REFERENCE SYSTEM 123456 NAME 'Perfect Unit Sphere' DEFINITION 'GEOGCS["Unit Sphere",DATUM["Unit Sphere",SPHEROID["Unit Sphere",1,0]],PRIMEM["Greenwich",0],UNIT["degree",0.017453292519943278],AXIS["Lon",EAST],AXIS["Lat",NORTH]]';

/**
 * TargetType
 * The target type according to the SIMBAD object classification.
 */
DROP TABLE IF EXISTS `TargetType`;
CREATE TABLE `TargetType` (
  `targetTypeId` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'Primary key.',
  `numericValue` VARCHAR(255) UNIQUE NOT NULL COMMENT 'The numeric code for the target type, such as “14.06.16.01”.',
  `explanation` VARCHAR(255) NOT NULL COMMENT 'An explanation of the target type, such as “Pulsating White Dwarf”.',
 PRIMARY KEY (`targetTypeId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

/**
 * Target
 * An observed target.
 */
DROP TABLE IF EXISTS `Target`;
CREATE TABLE `Target` (
  `targetId` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'Primary key.',
  `name` VARCHAR(255) NOT NULL COMMENT 'target name',
  `rightAscension` FLOAT NOT NULL COMMENT 'target right ascension',
  `declination` FLOAT NOT NULL COMMENT 'target declination',
  `position` point SRID 123456 NOT NULL COMMENT 'RA is offset by -180 deg so that it falls into [-180, 180]',
  `targetTypeId` INT(11) UNSIGNED COMMENT 'A foreign key linking to target type, see targetType table',
 PRIMARY KEY (`targetId`),
 KEY `fk_TargetTargetType_idx` (`targetTypeId`),
 CONSTRAINT `fk_TargetTargetType` FOREIGN KEY (`targetTypeId`) REFERENCES `TargetType` (`targetTypeId`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

/**
 * Table structure from table `Institution`
 */
DROP TABLE IF EXISTS `Institution`;
CREATE TABLE `Institution` (
  `institutionId` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'Primary key.',
  `institutionName` VARCHAR(255) UNIQUE NOT NULL COMMENT 'Institution name like SAAO, SALT',
 PRIMARY KEY (`institutionId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

/**
 * Telescope
 */
DROP TABLE IF EXISTS `Telescope`;
CREATE TABLE `Telescope` (
  `telescopeId` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'Primary key.',
  `telescopeName` VARCHAR(255) UNIQUE NOT NULL  COMMENT 'Name given to a telescope',
  `institutionId` INT(11) UNSIGNED NOT NULL COMMENT 'The id of the institution owning the telescope. This links to the Institution table.',
 PRIMARY KEY (`telescopeId`),
 KEY `fk_TelescopeInstitution_idx` (`institutionId`),
 CONSTRAINT `fk_TelescopeInstitution` FOREIGN KEY (`institutionId`) REFERENCES `Institution` (`institutionId`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

/**
 * Proposal
 * A proposal is the request for observing time made to the relevant TAC(s). There may be
 * multiple observations for a proposal. The database contains all proposals irrespective of
 * whether data have been taken for them.
 */
DROP TABLE IF EXISTS `Proposal`;
CREATE TABLE `Proposal` (
  `proposalId` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'Primary key.',
  `proposalCode` VARCHAR(255) NOT NULL COMMENT 'The code used for referring to a proposal, such as 2018-2-SCI-042.',
  `principalInvestigatorGivenName` VARCHAR(255) COMMENT 'The principal investigator’s given name.',
  `principalInvestigatorFamilyName` VARCHAR(255) COMMENT 'The principal investigator’s family name.',
  `title` VARCHAR(255) COMMENT 'The proposal title',
  `institutionId` INT(11) UNSIGNED NOT NULL COMMENT 'A foreign key linking to Institution table',
 PRIMARY KEY (`proposalId`),
 KEY `fk_ProposalInstitution_idx` (`institutionId`),
 CONSTRAINT `fk_ProposalInstitution` FOREIGN KEY (`institutionId`) REFERENCES `Institution` (`institutionId`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

/**
 * ObservationStatus
 *
 * The status of an observation, i.e. whether the observation has been accepted or rejected
 */

DROP TABLE IF EXISTS `ObservationStatus`;
CREATE TABLE `ObservationStatus` (
  `observationStatusId` INT(11) UNSIGNED NOT NULL COMMENT 'Primary key.',
  `status` VARCHAR(255) UNIQUE NOT NULL COMMENT 'The observation status. The possible values are Accepted, Rejected and Unknown',
 PRIMARY KEY (`observationStatusId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

/**
 * Observation
 *
 * An observation which has been made. Observations that have been scheduled but not done
 * yet are not included in the database. Observations are included in the database irrespective
 * of whether they have been accepted or rejected
 */

DROP TABLE IF EXISTS `Observation`;
CREATE TABLE `Observation` (
  `observationId` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'Primary key.',
  `proposalId` INT(11) UNSIGNED COMMENT 'A foreign key linking to proposal, see table Proposal',
  `telescopeId` INT(11) UNSIGNED NOT NULL  COMMENT 'A foreign key linking to telescope, see table Telescope',
  `telescopeObservationId` VARCHAR(255) COMMENT 'Same as a block visit id for SALT, it is not a key of ssda',
  `night` DATE NOT NULL COMMENT 'date an observation was taken',
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
 * DataCategory
 *
 * The data Category such as Science, Arcs, etc.
 */
 DROP TABLE IF EXISTS `DataCategory`;
 CREATE TABLE `DataCategory` (
   `dataCategoryId` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'Primary key.',
   `dataCategory` VARCHAR(255) UNIQUE NOT NULL COMMENT 'The data category. Possible values are Science, Flat, Dark, Arc, Bias, Engineering and Documentation',
  PRIMARY KEY (`dataCategoryId`)
 ) ENGINE=InnoDB DEFAULT CHARSET=utf8;

/**
 * DataFile
 *
 * Metadata for (raw) data files. The data file usually is a (raw) FITS file, but it may also be a text file containing
 * documentation. There are no entries for reduced data.
 */

DROP TABLE IF EXISTS `DataFile`;
CREATE TABLE `DataFile` (
  `dataFileId` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'Unique key',
  `dataCategoryId` INT(11) UNSIGNED NOT NULL COMMENT 'A foreign key linking to data category see table `DataCategory`',
  `startTime` DATETIME NOT NULL COMMENT 'Fits file "observation time" recorded on file',
  `name` VARCHAR(255) NOT NULL COMMENT 'Filename i.e R20190203000023.fits',
  `path` VARCHAR(255) UNIQUE NOT NULL COMMENT 'A file paths i.e /home/path/to/file/raw/R20190203000023.fits',
  `targetId` INT(11) UNSIGNED COMMENT 'A foreign key linking target see table Target',
  `size` FLOAT NOT NULL COMMENT 'File size in bytes',
  `observationId` INT(11) UNSIGNED NOT NULL COMMENT 'A foreign key linking to observation, see table Observation',
 PRIMARY KEY (`dataFileId`),
 KEY `fk_DataFileDataCategory_idx` (`dataCategoryId`),
 KEY `fk_DataFileTarget_idx` (`targetId`),
 KEY `fk_DataFileObservation_idx` (`observationId`),
 CONSTRAINT `fk_DataFileDataCategory` FOREIGN KEY (`dataCategoryId`) REFERENCES `DataCategory` (`dataCategoryId`) ON DELETE NO ACTION ON UPDATE NO ACTION,
 CONSTRAINT `fk_DataFileObservation` FOREIGN KEY (`observationId`) REFERENCES `Observation` (`observationId`) ON DELETE NO ACTION ON UPDATE NO ACTION,
 CONSTRAINT `fk_DataFileTarget` FOREIGN KEY (`targetId`) REFERENCES `Target` (`targetId`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

/**
 * DataPreview
 *
 * Preview images for a data file.
 */
DROP TABLE IF EXISTS `DataPreview`;
CREATE TABLE `DataPreview` (
  `name` VARCHAR(255),
  `path` VARCHAR(255) UNIQUE NOT NULL COMMENT 'Path to preview path',
  `dataFileId` INT(11) UNSIGNED NOT NULL COMMENT 'A foreign key linking to data file, see table DataFile',
  `previewOrder` INT(11) UNSIGNED NOT NULL COMMENT 'Defines an order within multiple preview files for the same data file',
 PRIMARY KEY (`dataFileId`, `previewOrder`),
 KEY `fk_DataPreviewDataFile_idx` (`dataFileId`),
 CONSTRAINT `fk_DataPreviewDataFile` FOREIGN KEY (`dataFileId`) REFERENCES `DataFile` (`dataFileId`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

/**
 * HRS
 *
 * Columns below are HRS specific
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
 * RSS
 *
 * Columns below are RSS specific
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
  `slitmaskStation` FLOAT DEFAULT NULL,
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
 * Columns below are Salticam specific
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

SET FOREIGN_KEY_CHECKS=1 COMMENT 'Make sure that this is ran';;
