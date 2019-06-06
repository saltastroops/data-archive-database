--
-- Table structure for table `Telescope`
--

DROP TABLE IF EXISTS `Telescope`;
CREATE TABLE `Telescope` (
  `telescopeId` INT(11) NOT NULL AUTO_INCREMENT,
  `telescopeName` VARCHAR(45) NOT NULL,
  `ownerId` INT(11) DEFAULT NULL,
  PRIMARY KEY (`telescopeId`),
  KEY `fk_TelescopeInstitute_idx` (`ownerId`),
  CONSTRAINT `fk_TelescopeInstitute` FOREIGN KEY (`ownerId`) REFERENCES `Institution` (`institutionId`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Table structure for table `Observation`
--

DROP TABLE IF EXISTS `Observation`;
CREATE TABLE `Observation` (
  `observationId` INT(11) NOT NULL AUTO_INCREMENT,
  `telescopeId` INT(11) DEFAULT NULL,
  `telescopeObservationId` INT(45) DEFAULT NULL,
  `observationStatusId` INT(11) DEFAULT NULL,
  PRIMARY KEY (`observationId`),
  KEY `fk_observationStatus_idx` (`observationStatusId`),
  KEY `fk_ObservationTelescope_idx` (`telescopeId`),
  CONSTRAINT `fk_ObservationTelescope` FOREIGN KEY (`telescopeId`) REFERENCES `Telescope` (`telescopeId`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_observationStatus` FOREIGN KEY (`observationStatusId`) REFERENCES `ObservationStatus` (`observationStatusId`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Table structure for table `ObservationStatus`
--

DROP TABLE IF EXISTS `ObservationStatus`;
CREATE TABLE `ObservationStatus` (
  `observationStatusId` INT(11) NOT NULL AUTO_INCREMENT,
  `status` VARCHAR(45) DEFAULT NULL,
  PRIMARY KEY (`observationStatusId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Table structure for table `Proposal`
--

--
-- Table structure for table `DataCategory`
--

DROP TABLE IF EXISTS `DataCategory`;
CREATE TABLE `DataCategory` (
  `dataCategoryId` INT(11) NOT NULL AUTO_INCREMENT,
  `dataCategory` VARCHAR(255) DEFAULT NULL,
  PRIMARY KEY (`dataCategoryId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Table structure for table `DataFile`
--

DROP TABLE IF EXISTS `DataFile`;
CREATE TABLE `DataFile` (
  `dataFileId` INT(11) NOT NULL AUTO_INCREMENT,
  `dataCategoryId` INT(11) DEFAULT NULL,
  `startTime` DATETIME DEFAULT NULL,
  `name` VARCHAR(255) DEFAULT NULL,
  `directory` VARCHAR(255) DEFAULT NULL,
  `targetId` INT(11) DEFAULT NULL,
  `size` FLOAT DEFAULT NULL,
  `observationId` INT(11) DEFAULT NULL,
  PRIMARY KEY (`dataFileId`),
  KEY `fk_DataFileCategory_idx` (`dataCategoryId`),
  KEY `fk_DataFileTarget_idx` (`targetId`),
  KEY `fk_DataFileObservation_idx` (`observationId`),
  CONSTRAINT `fk_DataFileCategory` FOREIGN KEY (`dataCategoryId`) REFERENCES `DataCategory` (`dataCategoryId`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_DataFileObservation` FOREIGN KEY (`observationId`) REFERENCES `Observation` (`observationId`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_DataFileTarget` FOREIGN KEY (`targetId`) REFERENCES `Target` (`targetId`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Table structure for table `DataPreview`
--

DROP TABLE IF EXISTS `DataPreview`;
CREATE TABLE `DataPreview` (
  `dataPreviewId` INT(11) NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(255) DEFAULT NULL,
  `dataFileId` INT(11) DEFAULT NULL,
  `orders` VARCHAR(45) DEFAULT NULL,
  PRIMARY KEY (`dataPreviewId`),
  KEY `fk_DataPreviewDataFile_idx` (`dataFileId`),
  CONSTRAINT `fk_DataPreviewDataFile` FOREIGN KEY (`dataFileId`) REFERENCES `DataFile` (`dataFileId`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Table structure for table `HRS`
--

DROP TABLE IF EXISTS `HRS`;
CREATE TABLE `HRS` (
  `hrsId` INT(11) NOT NULL AUTO_INCREMENT,
  `dataFileId` INT(11) NOT NULL,
  `observationId` INT(11) NOT NULL,
  `amplifierSection` VARCHAR(45) DEFAULT NULL,
  `amplifierTemperature` FLOAT DEFAULT NULL,
  `biasSection` VARCHAR(45) DEFAULT NULL,
  `numberOfAmplifiers` INT DEFAULT NULL,
  `ccdSection` VARCHAR(45) DEFAULT NULL,
  `ccdSummation` VARCHAR(45) DEFAULT NULL,
  `ccdTemperature` FLOAT DEFAULT NULL,
  `ccdType` VARCHAR(45) DEFAULT NULL,
  `dataSection` VARCHAR(45) DEFAULT NULL,
  `detectorMode` VARCHAR(45) DEFAULT NULL,
  `detectorName` VARCHAR(45) DEFAULT NULL,
  `detectorSection` VARCHAR(45) DEFAULT NULL,
  `detectorSerialNumber` VARCHAR(45) DEFAULT NULL,
  `detectorSize` VARCHAR(45) DEFAULT NULL,
  `detectorSoftwareVersion` VARCHAR(45) DEFAULT NULL,
  `exposureMean` FLOAT DEFAULT NULL,
  `exposureMidPoINT` FLOAT DEFAULT NULL,
  `exposureTotal` FLOAT DEFAULT NULL,
  `exposureTime` FLOAT DEFAULT NULL,
  `fifCentering` VARCHAR(45) DEFAULT NULL,
  `fifCenteringOffset` FLOAT DEFAULT NULL,
  `fifPortOffset` FLOAT DEFAULT NULL,
  `fifPort` VARCHAR(45) DEFAULT NULL,
  `fifSeparation` FLOAT DEFAULT NULL,
  `focusBlueArm` FLOAT DEFAULT NULL,
  `focusRedArm` FLOAT DEFAULT NULL,
  `gain` FLOAT DEFAULT NULL,
  `gainSet` VARCHAR(45) DEFAULT NULL,
  `iodenStagePosition` VARCHAR(45) DEFAULT NULL,
  `instrumentName` VARCHAR(45) DEFAULT NULL,
  `lstObservation` VARCHAR(45) DEFAULT NULL,
  `numberOfAmplifiersUsed` INT DEFAULT NULL,
  `numberOfCcdsInDetector` INT DEFAULT NULL,
  `nodCount` INT DEFAULT NULL,
  `nodPeriod` FLOAT DEFAULT NULL,
  `nodShuffle` INT DEFAULT NULL,
  `observationMode` VARCHAR(45) DEFAULT NULL,
  `observationType` VARCHAR(45) DEFAULT NULL,
  `pressureDewar` FLOAT DEFAULT NULL,
  `pressureVacuum` FLOAT DEFAULT NULL,
  `prescan` INT DEFAULT NULL,
  `ccdReadoutSpeed` VARCHAR(45) DEFAULT NULL,
  `airTemperature` FLOAT DEFAULT NULL,
  `blueCameraTemperature` FLOAT DEFAULT NULL,
  `collimatorTemperature` FLOAT DEFAULT NULL,
  `echelle` FLOAT DEFAULT NULL,
  `iodineTemperature` FLOAT DEFAULT NULL,
  `opticalBenchTemperature` FLOAT DEFAULT NULL,
  `redCameraTemperature` FLOAT DEFAULT NULL,
  `redMirrorTemperature` FLOAT DEFAULT NULL,
  `vacuumTemperature` FLOAT DEFAULT NULL,
  `fitsHeaderVersion` VARCHAR(45) DEFAULT NULL,
  PRIMARY KEY (`hrsId`),
  KEY `fk_HRSObservation_idx` (`observationId`),
  KEY `fk_HRSDataFile_idx` (`dataFileId`),
  CONSTRAINT `fk_HRSObservation` FOREIGN KEY (`ObservationId`) REFERENCES `Observation` (`ObservationId`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_HRSDataFile` FOREIGN KEY (`dataFileId`) REFERENCES `DataFile` (`dataFileId`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Table structure for table `RSS`
--

DROP TABLE IF EXISTS `RSS`;
CREATE TABLE `RSS` (
  `rssId` INT(11) NOT NULL AUTO_INCREMENT,
  `dataFileId` INT(11) NOT NULL,
  `observationId` INT(11) NOT NULL,
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
  `pixelCoordinatePoINTX1` FLOAT DEFAULT NULL,
  `pixelCoordinatePoINTX1A` FLOAT DEFAULT NULL,
  `pixelCoordinatePoINTX2` FLOAT DEFAULT NULL,
  `pixelCoordinatePoINTX2A` FLOAT DEFAULT NULL,
  `rightAscensionPoINT1` FLOAT DEFAULT NULL,
  `spatialCoordinatePoINT1A` FLOAT DEFAULT NULL,
  `declinationPoINT2` FLOAT DEFAULT NULL,
  `spacialCoordinatePoINT2A` FLOAT DEFAULT NULL,
  `gnomicProjection1` VARCHAR(255) DEFAULT NULL,
  `cartesianProjection1A` VARCHAR(255) DEFAULT NULL,
  `gnomicProjection2` VARCHAR(255) DEFAULT NULL,
  `cartesianProjection2A` VARCHAR(255) DEFAULT NULL,
  `dataSection` VARCHAR(255) DEFAULT NULL,
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
  `gain` FLOAT DEFAULT NULL,
  `gain1` FLOAT DEFAULT NULL,
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
  `fitsHeaderVersion` VARCHAR(45) DEFAULT NULL,
  `spatialCoordinate` VARCHAR(45) DEFAULT NULL,
  `waveplateMachineState` VARCHAR(45) DEFAULT NULL,
  `polarimetryProcedurePattern` VARCHAR(45) DEFAULT NULL,
  `crossTalk` FLOAT DEFAULT NULL,
  PRIMARY KEY (`rssId`),
  KEY `fk_RSSObservation_idx` (`observationId`),
  KEY `fk_RSSDataFile_idx` (`dataFileId`),
  CONSTRAINT `fk_RSSObservation` FOREIGN KEY (`ObservationId`) REFERENCES `Observation` (`ObservationId`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_RSSDataFile` FOREIGN KEY (`dataFileId`) REFERENCES `DataFile` (`dataFileId`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Table structure for table `RSS`
--

DROP TABLE IF EXISTS `Salticam`;
CREATE TABLE `Salticam` (
  `salticamId` INT(11) NOT NULL AUTO_INCREMENT,
  `observationId` INT(11) NOT NULL,
  `dataFileId` INT(11) NOT NULL,
  `amplifierSection` VARCHAR(45) DEFAULT NULL,
  `amplifierTemperature` FLOAT DEFAULT NULL,
  `amplifierReadoutX` INT DEFAULT NULL,
  `amplifierReadoutY` INT DEFAULT NULL,
  `biasSection` VARCHAR(45) DEFAULT NULL,
  `beamSplitterScale` FLOAT DEFAULT NULL,
  `beamSplitterZero` FLOAT DEFAULT NULL,
  `detectorFocusPosition` INT DEFAULT NULL,
  `numberOfAmplifiers` INT DEFAULT NULL,
  `ccdSection` VARCHAR(45) DEFAULT NULL,
  `ccdSummation` VARCHAR(45) DEFAULT NULL,
  `ccdTemperature` FLOAT DEFAULT NULL,
  `ccdType` VARCHAR(45) DEFAULT NULL,
  `transformationMatrix11` FLOAT DEFAULT NULL,
  `transformationMatrix11A` FLOAT DEFAULT NULL,
  `transformationMatrix12` FLOAT DEFAULT NULL,
  `transformationMatrix12A` FLOAT DEFAULT NULL,
  `transformationMatrix21` FLOAT DEFAULT NULL,
  `transformationMatrix21A` FLOAT DEFAULT NULL,
  `transformationMatrix22` FLOAT DEFAULT NULL,
  `transformationMatrix22A` FLOAT DEFAULT NULL,
  `coldEndTemperature` FLOAT DEFAULT NULL,
  `pixelCoordinatePoINTX1` FLOAT DEFAULT NULL,
  `pixelCoordinatePoINTX1A` FLOAT DEFAULT NULL,
  `pixelCoordinatePoINTX2` FLOAT DEFAULT NULL,
  `pixelCoordinatePoINTX2A` FLOAT DEFAULT NULL,
  `rightAsertionPoINT1` FLOAT DEFAULT NULL,
  `spatialCoordinatePoINT1A` FLOAT DEFAULT NULL,
  `declanationPoINT2` FLOAT DEFAULT NULL,
  `spacialCoordinatePoINT2A` FLOAT DEFAULT NULL,
  `gnomicProjection1` VARCHAR(45) DEFAULT NULL,
  `cartesianProjection1A` VARCHAR(45) DEFAULT NULL,
  `gnomicProjection2` VARCHAR(45) DEFAULT NULL,
  `cartesianProjection2A` VARCHAR(45) DEFAULT NULL,
  `anglesDegreesAlways1` VARCHAR(45) DEFAULT NULL,
  `anglesDegreesAlways2` VARCHAR(45) DEFAULT NULL,
  `dataSection` VARCHAR(45) DEFAULT NULL,
  `detectorMode` VARCHAR(45) DEFAULT NULL,
  `detectorSection` VARCHAR(45) DEFAULT NULL,
  `detectorSize` VARCHAR(45) DEFAULT NULL,
  `detectorSoftwareVersion` VARCHAR(45) DEFAULT NULL,
  `coolerBoxTemperature` FLOAT DEFAULT NULL,
  `exposureTime` FLOAT DEFAULT NULL,
  `filterPosition` INT DEFAULT NULL,
  `filterName` VARCHAR(45) DEFAULT NULL,
  `gain` FLOAT DEFAULT NULL,
  `gain1` FLOAT DEFAULT NULL,
  `gainSet` VARCHAR(45) DEFAULT NULL,
  `imageId` VARCHAR(45) DEFAULT NULL,
  `instrumentName` VARCHAR(45) DEFAULT NULL,
  `julianDate` FLOAT DEFAULT NULL,
  `lstObservation` VARCHAR(45) DEFAULT NULL,
  `numberOfCcds` INT DEFAULT NULL,
  `numberOfExtensions` INT DEFAULT NULL,
  `numberOfWindows` INT DEFAULT NULL,
  `objectName` VARCHAR(45) DEFAULT NULL,
  `observationMode` VARCHAR(45) DEFAULT NULL,
  `observationType` VARCHAR(45) DEFAULT NULL,
  `pixelScale` FLOAT DEFAULT NULL,
  `pupilEnd` FLOAT DEFAULT NULL,
  `noiseReadout` FLOAT DEFAULT NULL,
  `ccdReadoutSpeed` VARCHAR(45) DEFAULT NULL,
  `pixelSaturation` INT DEFAULT NULL,
  `fitsHeaderVersion` VARCHAR(45) DEFAULT NULL,
  `spatialCoordinate` VARCHAR(45) DEFAULT NULL,
  `crossTalk` FLOAT DEFAULT NULL,
  PRIMARY KEY (`salticamId`),
  KEY `fk_SalticamObservation_idx` (`observationId`),
  KEY `fk_SalticamDataFile_idx` (`dataFileId`),
  CONSTRAINT `fk_SalticamObservation` FOREIGN KEY (`ObservationId`) REFERENCES `Observation` (`ObservationId`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_SalticamDataFile` FOREIGN KEY (`dataFileId`) REFERENCES `DataFile` (`dataFileId`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Table structure for table `Institution`
--

DROP TABLE IF EXISTS `Institution`;
CREATE TABLE `Institution` (
  `institutionId` INT(11) NOT NULL AUTO_INCREMENT,
  `institutionName` VARCHAR(45) DEFAULT NULL,
  PRIMARY KEY (`institutionId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


DROP TABLE IF EXISTS `Proposal`;
CREATE TABLE `Proposal` (
  `proposalId` INT(11) NOT NULL AUTO_INCREMENT,
  `proposalCode` VARCHAR(45) DEFAULT NULL,
  `date` VARCHAR(45) DEFAULT NULL,
  `principalInvestigatorGivenName` VARCHAR(45) DEFAULT NULL,
  `principalInvestigatorFamilyName` VARCHAR(45) DEFAULT NULL,
  `title` VARCHAR(255) DEFAULT NULL,
  `lastUpdated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`proposalId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Table structure for table `ProposalInvestigator`
--

DROP TABLE IF EXISTS `ProposalInvestigator`;
CREATE TABLE `ProposalInvestigator` (
  `proposalId` INT(11) NOT NULL,
  `userId` INT(11) DEFAULT NULL,
  PRIMARY KEY (`proposalId`),
  KEY `fk_ProposalInvestigatorUser_idx` (`userId`),
  CONSTRAINT `fk_ProposalInvestigatorProposal` FOREIGN KEY (`proposalId`) REFERENCES `Proposal` (`proposalId`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_ProposalInvestigatorUser` FOREIGN KEY (`userId`) REFERENCES `User` (`userId`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Table structure for table `Target`
--

DROP TABLE IF EXISTS `Target`;
CREATE TABLE `Target` (
  `targetId` INT(11) NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(255) DEFAULT NULL,
  `rightAscension` FLOAT DEFAULT NULL,
  `declination` FLOAT DEFAULT NULL,
  `position` POINT DEFAULT NULL,
  `targetTypeId` INT(11) DEFAULT NULL,
  PRIMARY KEY (`targetId`),
  KEY `fk_TargetType_idx` (`targetTypeId`),
  CONSTRAINT `fk_TargetType` FOREIGN KEY (`targetTypeId`) REFERENCES `TargetType` (`targetTypeId`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Table structure for table `TargetType`
--

DROP TABLE IF EXISTS `TargetType`;
CREATE TABLE `TargetType` (
  `targetTypeId` INT(11) NOT NULL AUTO_INCREMENT,
  `numericValue` VARCHAR(255) DEFAULT NULL,
  `explanation` VARCHAR(255) DEFAULT NULL,
  PRIMARY KEY (`targetTypeId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Table structure for table `Telescope`
--

DROP TABLE IF EXISTS `Telescope`;
CREATE TABLE `Telescope` (
  `telescopeId` INT(11) NOT NULL AUTO_INCREMENT,
  `telescopeName` VARCHAR(45) NOT NULL,
  `ownerId` INT(11) DEFAULT NULL,
  PRIMARY KEY (`telescopeId`),
  KEY `fk_TelescopeInstitute_idx` (`ownerId`),
  CONSTRAINT `fk_TelescopeInstitute` FOREIGN KEY (`ownerId`) REFERENCES `Institution` (`institutionId`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Table structure for table `User`
--

DROP TABLE IF EXISTS `User`;
CREATE TABLE `User` (
  `userId` INT(11) NOT NULL AUTO_INCREMENT,
  `institutionId` INT(11) DEFAULT NULL,
  `institutionUserId` VARCHAR(45) DEFAULT NULL,
  `givenName` VARCHAR(45) DEFAULT NULL,
  `familyName` VARCHAR(45) DEFAULT NULL,
  PRIMARY KEY (`userId`),
  KEY `fk_UserInstitution_idx` (`institutionId`),
  CONSTRAINT `fk_UserInstitution` FOREIGN KEY (`institutionId`) REFERENCES `Institution` (`institutionId`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
