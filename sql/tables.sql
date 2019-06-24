/**
 * DataCategory
 *
 * The data Category such as Science, Arcs, etc.
 */

DROP TABLE IF EXISTS `DataCategory`;
CREATE TABLE `DataCategory` (
  `dataCategoryId` int(11) NOT NULL AUTO_INCREMENT,  -- Primary key.
  `dataCategory` VARCHAR(255) DEFAULT NULL,  -- The  data  category.  Possible  values  are Science, Flat, Dark, Arc, Bias, Engineering and Documentation
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
  `dataFileId` int(11) NOT NULL AUTO_INCREMENT,     -- Unique key
  `dataCategoryId` int(11) DEFAULT NULL,            -- A foreign key linking to data category see table `DataCategory`
  `startTime` DATETIME DEFAULT NULL,                -- Fits file "observation time" recorded on file
  `name` VARCHAR(255) DEFAULT NULL,                 -- Filename i.e R20190203000023.fits
  `path` VARCHAR(255) DEFAULT NULL,                 -- A file's paths i.e /home/path/to/file/raw/R20190203000023.fits
  `targetId` int(11) DEFAULT NULL,                  -- A foreign key linking target see table Target
  `size` FLOAT DEFAULT NULL,                        -- File size in kilobytes
  `observationId` int(11) DEFAULT NULL,             -- A foreign key linking to observation, see table Observation
  PRIMARY KEY (`dataFileId`),
  KEY `fk_DataFileCategory_idx` (`dataCategoryId`),
  KEY `fk_DataFileTarget_idx` (`targetId`),
  KEY `fk_DataFileObservation_idx` (`observationId`),
  CONSTRAINT `fk_DataFileCategory` FOREIGN KEY (`dataCategoryId`) REFERENCES `DataCategory` (`dataCategoryId`) ON DELETE NO ACTION ON UPDATE NO ACTION,
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
  `dataPreviewId` int(11) NOT NULL AUTO_INCREMENT,  -- Primary key.
  `name` VARCHAR(255) DEFAULT NULL,
  `path` VARCHAR(255) DEFAULT NULL,                 -- Path to preview path
  `dataFileId` int(11) DEFAULT NULL,                -- A foreign key linking to data file, see table DataFile
  `order` VARCHAR(255) DEFAULT NULL,                -- Defines an order within multiple preview files for the same data file
  PRIMARY KEY (`dataPreviewId`),
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
  `hrsId` int(11) NOT NULL AUTO_INCREMENT,       -- Primary key for this table(HRS).
  `dataFileId` int(11) NOT NULL,                -- A foreign key linking to data file, see table DataFile
  `amplifierSection` VARCHAR(255) DEFAULT NULL,
  `amplifierTemperature` FLOAT DEFAULT NULL,
  `biasSection` VARCHAR(255) DEFAULT NULL,
  `numberOfAmplifiers` INT DEFAULT NULL,
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
  `gain` VARCHAR(255) DEFAULT NULL,
  `gainSet` VARCHAR(255) DEFAULT NULL,
  `iodenStagePosition` VARCHAR(255) DEFAULT NULL,
  `instrumentName` VARCHAR(255) DEFAULT NULL,
  `lstObservation` VARCHAR(255) DEFAULT NULL,
  `numberOfAmplifiersUsed` INT DEFAULT NULL,
  `numberOfCcdsInDetector` INT DEFAULT NULL,
  `nodCount` INT DEFAULT NULL,
  `nodPeriod` FLOAT DEFAULT NULL,
  `nodShuffle` INT DEFAULT NULL,
  `observationMode` VARCHAR(255) DEFAULT NULL,
  `observationType` VARCHAR(255) DEFAULT NULL,
  `pressureDewar` FLOAT DEFAULT NULL,
  `pressureVacuum` FLOAT DEFAULT NULL,
  `prescan` INT DEFAULT NULL,
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
  `rssId` INT(11) NOT NULL AUTO_INCREMENT,  -- Primary key for this table(RSS).
  `dataFileId` INT(11) NOT NULL,  -- A foreign key linking to DataFile table. 
  `amplifierSection` VARCHAR(255) DEFAULT NULL,
  `amplifierTemperature` FLOAT DEFAULT NULL,
  `articulationAngle` FLOAT DEFAULT NULL,
  `articulationPitch` FLOAT DEFAULT NULL,
  `articulationRoll` FLOAT DEFAULT NULL,
  `articulationStation` VARCHAR(255) DEFAULT NULL,
  `articulationStationEncoder` FLOAT DEFAULT NULL,
  `articulationMachineState` VARCHAR(255) DEFAULT NULL,
  `amplifierReadoutX` INT DEFAULT NULL,
  `amplifierReadoutY` INT DEFAULT NULL,
  `biasSection` VARCHAR(255) DEFAULT NULL,
  `beamSplitterMachineState` VARCHAR(255) DEFAULT NULL,
  `beamSplitterScale` FLOAT DEFAULT NULL,
  `beamSplitterZero` FLOAT DEFAULT NULL,
  `commandedArticulationStation` FLOAT DEFAULT NULL,
  `detectorFocusPosition` INT DEFAULT NULL,
  `cameraTemperature` FLOAT DEFAULT NULL,
  `numberOfAmplifiers` INT DEFAULT NULL,
  `ccdSection` VARCHAR(255) DEFAULT NULL,
  `ccdSummation` VARCHAR(255) DEFAULT NULL,
  `ccdTemperature` FLOAT DEFAULT NULL,
  `ccdType` VARCHAR(255) DEFAULT NULL,
  `transfromationMatrix11` FLOAT DEFAULT NULL,
  `transfromationMatrix11A` FLOAT DEFAULT NULL,
  `transfromationMatrix12` FLOAT DEFAULT NULL,
  `transfromationMatrix12A` FLOAT DEFAULT NULL,
  `transfromationMatrix21` FLOAT DEFAULT NULL,
  `transfromationMatrix21A` FLOAT DEFAULT NULL,
  `transfromationMatrix22` FLOAT DEFAULT NULL,
  `transfromationMatrix22A` FLOAT DEFAULT NULL,
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
  `dispersionAxis` INT DEFAULT NULL,
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
  `filterStation` INT DEFAULT NULL,
  `filterMachineState` VARCHAR(255) DEFAULT NULL,
  `filterPosition` INT DEFAULT NULL,
  `filterBarcode` VARCHAR(255) DEFAULT NULL,
  `filterStationSteps` FLOAT DEFAULT NULL,
  `filterStationVolts` FLOAT DEFAULT NULL,
  `filterMagazineSteps` INT DEFAULT NULL,
  `filterMagazineVolts` FLOAT DEFAULT NULL,
  `focusPosition` FLOAT DEFAULT NULL,
  `focusPositionSteps` FLOAT DEFAULT NULL,
  `focusPositionVolts` FLOAT DEFAULT NULL,
  `focusMachineState` VARCHAR(255) DEFAULT NULL,
  `focusVolts` FLOAT DEFAULT NULL,
  `focusSteps` INT DEFAULT NULL,
  `gain` VARCHAR(255) DEFAULT NULL,
  `gain1` VARCHAR(255) DEFAULT NULL,
  `gainSet` VARCHAR(255) DEFAULT NULL,
  `gratingMagazineSteps` INT DEFAULT NULL,
  `gratingMagazineVolts` FLOAT DEFAULT NULL,
  `gratingRotationAngle` FLOAT DEFAULT NULL,
  `gratingStation` VARCHAR(255) DEFAULT NULL,
  `gratingStationSteps` FLOAT DEFAULT NULL,
  `gratingStationVolts` FLOAT DEFAULT NULL,
  `gratingMachineState` VARCHAR(255) DEFAULT NULL,
  `gratingRotationAngleSteps` INT DEFAULT NULL,
  `grating` VARCHAR(255) DEFAULT NULL,
  `gratingAngle` FLOAT DEFAULT NULL,
  `halfWaveSteps` INT DEFAULT NULL,
  `halfWaveAngle` FLOAT DEFAULT NULL,
  `halfWaveStation` VARCHAR(255) DEFAULT NULL,
  `halfWaveStationEncoder` FLOAT DEFAULT NULL,
  `imageId` VARCHAR(255) DEFAULT NULL,
  `instrumentName` VARCHAR(255) DEFAULT NULL,
  `julianDate` FLOAT DEFAULT NULL,
  `lstObservation` VARCHAR(255) DEFAULT NULL,
  `slitmaskBarcode` VARCHAR(255) DEFAULT NULL,
  `slitmaskType` VARCHAR(255) DEFAULT NULL,
  `numberOfCcds` INT DEFAULT NULL,
  `numberOfExtensions` INT DEFAULT NULL,
  `numberOfWindows` INT DEFAULT NULL,
  `objectName` VARCHAR(255) DEFAULT NULL,
  `observationMode` VARCHAR(255) DEFAULT NULL,
  `observationType` VARCHAR(255) DEFAULT NULL,
  `pfsiControlSystemVersion` VARCHAR(255) DEFAULT NULL,
  `pixelScale` FLOAT DEFAULT NULL,
  `polarizationConfig` VARCHAR(255) DEFAULT NULL,
  `pfsiProcedure` VARCHAR(255) DEFAULT NULL,
  `pupilEnd` FLOAT DEFAULT NULL,
  `quaterWaveSteps` INT DEFAULT NULL,
  `quaterWaveAngle` FLOAT DEFAULT NULL,
  `quaterWaveStation` VARCHAR(255) DEFAULT NULL,
  `quaterWaveStationEncoder` VARCHAR(255) DEFAULT NULL,
  `noiseReadout` FLOAT DEFAULT NULL,
  `ccdReadoutSpeed` VARCHAR(255) DEFAULT NULL,
  `pixelSaturation` INT DEFAULT NULL,
  `shutterMachineState` VARCHAR(255) DEFAULT NULL,
  `slitmaskStation` FLOAT DEFAULT NULL,
  `slitmaskStationSteps` FLOAT DEFAULT NULL,
  `slitmaskStationVolts` FLOAT DEFAULT NULL,
  `slitmasMachineState` VARCHAR(255) DEFAULT NULL,
  `slitmaskMagazineSteps` INT DEFAULT NULL,
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
  `salticamId` int(11) NOT NULL AUTO_INCREMENT,      -- Primary key for this table(Salticam).
  `dataFileId` int(11) NOT NULL,                    -- A foreign key linking to Datafile table.
  `amplifierSection` VARCHAR(255) DEFAULT NULL,
  `amplifierTemperature` FLOAT DEFAULT NULL,
  `amplifierReadoutX` INT DEFAULT NULL,
  `amplifierReadoutY` INT DEFAULT NULL,
  `biasSection` VARCHAR(255) DEFAULT NULL,
  `beamSplitterScale` FLOAT DEFAULT NULL,
  `beamSplitterZero` FLOAT DEFAULT NULL,
  `detectorFocusPosition` INT DEFAULT NULL,
  `numberOfAmplifiers` INT DEFAULT NULL,
  `ccdSection` VARCHAR(255) DEFAULT NULL,
  `ccdSummation` VARCHAR(255) DEFAULT NULL,
  `ccdTemperature` FLOAT DEFAULT NULL,
  `ccdType` VARCHAR(255) DEFAULT NULL,
  `transfromationMatrix11` FLOAT DEFAULT NULL,
  `transfromationMatrix11A` FLOAT DEFAULT NULL,
  `transfromationMatrix12` FLOAT DEFAULT NULL,
  `transfromationMatrix12A` FLOAT DEFAULT NULL,
  `transfromationMatrix21` FLOAT DEFAULT NULL,
  `transfromationMatrix21A` FLOAT DEFAULT NULL,
  `transfromationMatrix22` FLOAT DEFAULT NULL,
  `transfromationMatrix22A` FLOAT DEFAULT NULL,
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
  `filterPosition` INT DEFAULT NULL,
  `filterName` VARCHAR(255) DEFAULT NULL,
  `gain` VARCHAR(255) DEFAULT NULL,
  `gain1` VARCHAR(255) DEFAULT NULL,
  `gainSet` VARCHAR(255) DEFAULT NULL,
  `imageId` VARCHAR(255) DEFAULT NULL,
  `instrumentName` VARCHAR(255) DEFAULT NULL,
  `julianDate` FLOAT DEFAULT NULL,
  `lstObservation` VARCHAR(255) DEFAULT NULL,
  `numberOfCcds` INT DEFAULT NULL,
  `numberOfExtensions` INT DEFAULT NULL,
  `numberOfWindows` INT DEFAULT NULL,
  `objectName` VARCHAR(255) DEFAULT NULL,
  `observationMode` VARCHAR(255) DEFAULT NULL,
  `observationType` VARCHAR(255) DEFAULT NULL,
  `pixelScale` FLOAT DEFAULT NULL,
  `pupilEnd` FLOAT DEFAULT NULL,
  `noiseReadout` FLOAT DEFAULT NULL,
  `ccdReadoutSpeed` VARCHAR(255) DEFAULT NULL,
  `pixelSaturation` INT DEFAULT NULL,
  `startOfObservationTime` VARCHAR(255) DEFAULT NULL,
  `systemTime` VARCHAR(255) DEFAULT NULL,
  `fitsHeaderVersion` VARCHAR(255) DEFAULT NULL,
  `spatialCoordinate` VARCHAR(255) DEFAULT NULL,
  `crossTalk` FLOAT DEFAULT NULL,
  PRIMARY KEY (`salticamId`),
  KEY `fk_SalticamDataFile_idx` (`dataFileId`),
  CONSTRAINT `fk_SalticamDataFile` FOREIGN KEY (`dataFileId`) REFERENCES `DataFile` (`dataFileId`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Table structure from table `Institution`
--

DROP TABLE IF EXISTS `Institution`;
CREATE TABLE `Institution` (
  `institutionId` int(11) NOT NULL AUTO_INCREMENT,  -- Primary key.
  `institutionName` VARCHAR(255) DEFAULT NULL,      -- Institute name like SAAO, SALT
  PRIMARY KEY (`institutionId`)
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
  `observationId` int(11) NOT NULL AUTO_INCREMENT,      -- Primary key.
  `proposalId` int(11),                                 -- A foreign key linking to proposal, see table Proposal
  `telescopeId` int(11) DEFAULT NULL,                   -- A foreign key linking to telescope, see table Telescope
  `telescopeObservationId` VARCHAR(255) DEFAULT NULL,   -- Same as a block id for SALT, it is not a key of ssda
  `night` VARCHAR(255) DEFAULT NULL,                    -- date an observation was taken
  `observationStatusId` int(11) DEFAULT NULL,           -- A foreign key linking to observation status, see table ObservationStatus
  PRIMARY KEY (`observationId`),
  KEY `fk_proposal_idx` (`proposalId`),
  KEY `fk_observationStatus_idx` (`observationStatusId`),
  KEY `fk_ObservationTelescope_idx` (`telescopeId`),
  CONSTRAINT `fk_proposal` FOREIGN KEY (`proposalId`) REFERENCES `Proposal` (`proposalId`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_ObservationTelescope` FOREIGN KEY (`telescopeId`) REFERENCES `Telescope` (`telescopeId`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_observationStatus` FOREIGN KEY (`observationStatusId`) REFERENCES `ObservationStatus` (`observationStatusId`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

/**
 * ObservationStatus
 *
 * The status of an observation, i.e. whether the observation has been accepted or rejected
 */

DROP TABLE IF EXISTS `ObservationStatus`;
CREATE TABLE `ObservationStatus` (
  `observationStatusId` int(11) NOT NULL,   -- Primary key.
  `status` VARCHAR(255) DEFAULT NULL,       --The observation status. The possible values are Accepted, Rejected and Unknown
  PRIMARY KEY (`observationStatusId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

/**
 * Proposal
 * A  proposal  is  the  request  for  observing  time  made  to  the  relevant  TAC(s).  There  may  be
 * multiple  observations  for  a  proposal.  The  database  contains  all  proposals  irrespective  of
 * whether data have been taken for them.
 */

DROP TABLE IF EXISTS `Proposal`;
CREATE TABLE `Proposal` (
  `proposalId` int(11) NOT NULL AUTO_INCREMENT,     -- Primary key.
  `proposalCode` VARCHAR(255) NOT NULL,             -- The code used for referring to a proposal, such as 2018-2-SCI-042.
  `principalInvestigatorGivenName` VARCHAR(255) NOT NULL,   -- The principal investigator’s given name.
  `principalInvestigatorFamilyName` VARCHAR(255) NOT NULL,  -- The principal investigator’s family name.
  `title` VARCHAR(255) NOT NULL,                            -- The proposal title
  `institutionId` INT(11) NOT NULL,                         -- A foreign key linking to Institute table
  `lastUpdated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, -- timestamp of when it was last updated
  PRIMARY KEY (`proposalId`),
  KEY `fk_institution_idx` (`institutionId`),
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
  `proposalId` int(11) NOT NULL,                -- A foreign key linking to proposal, see Proposal table
  `institutionUserId` varchar(255) NOT NULL,    -- A user identifier on the institute database. Not a ssda key
  PRIMARY KEY (`proposalId`, `institutionUserId`),
  CONSTRAINT `fk_ProposalInvestigatorProposal` FOREIGN KEY (`proposalId`) REFERENCES `Proposal` (`proposalId`) ON DELETE NO ACTION ON UPDATE NO ACTION,
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


--
-- Spatial reference system for target positions
--
CREATE OR REPLACE SPATIAL REFERENCE SYSTEM 123456 NAME 'Perfect Unit Sphere' DEFINITION 'GEOGCS["Unit Sphere",DATUM["Unit Sphere",SPHEROID["Unit Sphere",1,0]],PRIMEM["Greenwich",0],UNIT["degree",0.017453292519943278],AXIS["Lon",EAST],AXIS["Lat",NORTH]]';

/**
 * Target
 * An observed target.
 */

DROP TABLE IF EXISTS `Target`;
CREATE TABLE `Target` (
  `targetId` int(11) NOT NULL AUTO_INCREMENT,   -- Primary key.
  `name` VARCHAR(255) DEFAULT NULL,             -- target name
  `rightAscension` float DEFAULT NULL,          -- target's right ascension
  `declination` float DEFAULT NULL,             -- target's declination
  `position` point SRID 123456 DEFAULT NULL COMMENT 'RA is offset by -180 deg so that it falls into [-180, 180]',
  `targetTypeId` int(11) DEFAULT NULL,          -- A foreign key linking to target type, see targetType table
  PRIMARY KEY (`targetId`),
  KEY `fk_TargetType_idx` (`targetTypeId`),
  CONSTRAINT `fk_TargetType` FOREIGN KEY (`targetTypeId`) REFERENCES `TargetType` (`targetTypeId`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

/**
 * TargetType
 * The target type according to the SIMBAD object classification.
 */

DROP TABLE IF EXISTS `TargetType`;
CREATE TABLE `TargetType` (
  `targetTypeId` int(11) NOT NULL AUTO_INCREMENT,   -- Primary key.
  `numericValue` VARCHAR(255) DEFAULT NULL,         -- The numeric code for the target type, such as “14.06.16.01”.
  `explanation` VARCHAR(100) DEFAULT NULL,          -- An explanation of the target type, such as “Pulsating White Dwarf”.
  PRIMARY KEY (`targetTypeId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

/**
 * Telescope
 */

DROP TABLE IF EXISTS `Telescope`;
CREATE TABLE `Telescope` (
  `telescopeId` int(11) NOT NULL AUTO_INCREMENT,  -- Primary key.
  `telescopeName` VARCHAR(255) NOT NULL,    -- Name given to a telescope
  `ownerId` int(11) DEFAULT NULL,           -- The  id  of  the  institution  owning  the  telescope.  This  links  to  the Institution table.
  PRIMARY KEY (`telescopeId`),
  KEY `fk_TelescopeInstitute_idx` (`ownerId`),
  CONSTRAINT `fk_TelescopeInstitute` FOREIGN KEY (`ownerId`) REFERENCES `Institution` (`institutionId`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
