-- MySQL dump 10.13  Distrib 5.7.26, for Linux (x86_64)
--
-- Host: 127.0.0.1    Database: ssda
-- ------------------------------------------------------
-- Server version	5.7.26-0ubuntu0.18.04.1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `DataCategory`
--

DROP TABLE IF EXISTS `DataCategory`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `DataCategory` (
  `dataCategoryId` int(11) NOT NULL AUTO_INCREMENT,
  `dataCategory` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`dataCategoryId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `DataFile`
--

DROP TABLE IF EXISTS `DataFile`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `DataFile` (
  `dataCategoryId` int(11) DEFAULT NULL,
  `startTime` varchar(45) DEFAULT NULL,
  `dataFileId` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) DEFAULT NULL,
  `targetId` int(11) DEFAULT NULL,
  `size` INT DEFAULT NULL,
  `observationId` int(11) DEFAULT NULL,
  PRIMARY KEY (`dataFileId`),
  KEY `fk_DataFileCategory_idx` (`dataCategoryId`),
  KEY `fk_DataFileTarget_idx` (`targetId`),
  KEY `fk_DataFileObservation_idx` (`observationId`),
  CONSTRAINT `fk_DataFileCategory` FOREIGN KEY (`dataCategoryId`) REFERENCES `DataCategory` (`dataCategoryId`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_DataFileObservation` FOREIGN KEY (`observationId`) REFERENCES `Observation` (`observationId`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_DataFileTarget` FOREIGN KEY (`targetId`) REFERENCES `Target` (`targetId`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `DataPreview`
--

DROP TABLE IF EXISTS `DataPreview`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `DataPreview` (
  `dataPreviewId` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) DEFAULT NULL,
  `dataFileId` int(11) DEFAULT NULL,
  `orders` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`dataPreviewId`),
  KEY `fk_DataPreviewDataFile_idx` (`dataFileId`),
  CONSTRAINT `fk_DataPreviewDataFile` FOREIGN KEY (`dataFileId`) REFERENCES `DataFile` (`dataFileId`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `HRS`
--

DROP TABLE IF EXISTS `HRS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `HRS` (
  `hrsId` int(11) NOT NULL AUTO_INCREMENT,
  `telescopeId` int(11) NOT NULL,
  `amplifierSection` VARCHAR(45) DEFAULT NULL,
  `amplifierTemperature` FLOAT DEFAULT NULL,
  `biasSection` VARCHAR(45) DEFAULT NULL,
  `numberOfAmplifiers` TINYINT DEFAULT NULL,
  `ccdSection` VARCHAR(45) DEFAULT NULL,
  `ccdSummation` VARCHAR(45) DEFAULT NULL,
  `ccdTemperature` FLOAT DEFAULT NULL,
  `ccdType` VARCHAR(45) DEFAULT NULL,
  `dataSection` VARCHAR(45) DEFAULT NULL,
  `dateOfObservation` VARCHAR(45) DEFAULT NULL,
  `detectorMode` VARCHAR(45) DEFAULT NULL,
  `detectorName` VARCHAR(45) DEFAULT NULL,
  `detectorSection` VARCHAR(45) DEFAULT NULL,
  `detectorSerialNumber` VARCHAR(45) DEFAULT NULL,
  `detectorSize` VARCHAR(45) DEFAULT NULL,
  `detectorSoftwareVersion` VARCHAR(45) DEFAULT NULL,
  `exposureMean` FLOAT DEFAULT NULL,
  `exposureMidPoint` FLOAT DEFAULT NULL,
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
  `numberOfAmplifiersUsed` TINYINT DEFAULT NULL,
  `numberOfCcdsInDetector` TINYINT DEFAULT NULL,
  `nodCount` TINYINT DEFAULT NULL,
  `nodPeriod` FLOAT DEFAULT NULL,
  `nodShuffle` TINYINT DEFAULT NULL,
  `observationMode` VARCHAR(45) DEFAULT NULL,
  `observationType` VARCHAR(45) DEFAULT NULL,
  `pressureDewar` FLOAT DEFAULT NULL,
  `pressureVacuum` FLOAT DEFAULT NULL,
  `prescan` TINYINT DEFAULT NULL,
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
  `startOfObservationTime` VARCHAR(45) DEFAULT NULL,
  `systemTime` VARCHAR(45) DEFAULT NULL,
  `fitsHeaderVersion` VARCHAR(45) DEFAULT NULL,
  PRIMARY KEY (`hrsId`),
  KEY `fk_HRSTelescope_idx` (`telescopeId`),
  CONSTRAINT `fk_HRSTelescope` FOREIGN KEY (`telescopeId`) REFERENCES `Telescope` (`telescopeId`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `RSS`
--

DROP TABLE IF EXISTS `RSS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `RSS` (
  `rssId` int(11) NOT NULL AUTO_INCREMENT,
  `telescopeId` int(11) NOT NULL,
  `amplifierSection` VARCHAR(45) DEFAULT NULL,
  `amplifierTemperature` FLOAT DEFAULT NULL,
  `articulationAngle` FLOAT DEFAULT NULL,
  `articulationPitch` FLOAT DEFAULT NULL,
  `articulationRoll` FLOAT DEFAULT NULL,
  `articulationStation` VARCHAR(45) DEFAULT NULL,
  `articulationStationEncoder` FLOAT DEFAULT NULL,
  `articulationMachineState` VARCHAR(45) DEFAULT NULL,
  `amplifierReadoutX` TINYINT DEFAULT NULL,
  `amplifierReadoutY` TINYINT DEFAULT NULL,
  `biasSection` VARCHAR(45) DEFAULT NULL,
  `beamSplitterMachineState` VARCHAR(45) DEFAULT NULL,
  `beamSplitterScale` FLOAT DEFAULT NULL,
  `beamSplitterZero` FLOAT DEFAULT NULL,
  `commandedArticulationStation` FLOAT DEFAULT NULL,
  `detectorFocusPosition` TINYINT DEFAULT NULL,
  `cameraTemperature` FLOAT DEFAULT NULL,
  `numberOfAmplifiers` TINYINT DEFAULT NULL,
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
  `configMachineState` VARCHAR(45) DEFAULT NULL,
  `collimatorTemperature` FLOAT DEFAULT NULL,
  `pixelCoordinatePointX1` FLOAT DEFAULT NULL,
  `pixelCoordinatePointX1A` FLOAT DEFAULT NULL,
  `pixelCoordinatePointX2` FLOAT DEFAULT NULL,
  `pixelCoordinatePointX2A` FLOAT DEFAULT NULL,
  `rightAsertionPoint1` FLOAT DEFAULT NULL,
  `spatialCoordinatePoint1A` FLOAT DEFAULT NULL,
  `declanationPoint2` FLOAT DEFAULT NULL,
  `spacialCoordinatePoint2A` FLOAT DEFAULT NULL,
  `gnomicProjection1` VARCHAR(45) DEFAULT NULL,
  `cartesianProjection1A` VARCHAR(45) DEFAULT NULL,
  `gnomicProjection2` VARCHAR(45) DEFAULT NULL,
  `cartesianProjection2A` VARCHAR(45) DEFAULT NULL,
  `dataSection` VARCHAR(45) DEFAULT NULL,
  `dateOfObservation` VARCHAR(45) DEFAULT NULL,
  `detectorMode` VARCHAR(45) DEFAULT NULL,
  `detectorSection` VARCHAR(45) DEFAULT NULL,
  `detectorSize` VARCHAR(45) DEFAULT NULL,
  `detectorSoftwareVersion` VARCHAR(45) DEFAULT NULL,
  `coolerBoxTemperature` FLOAT DEFAULT NULL,
  `dispersionAxis` TINYINT DEFAULT NULL,
  `etalonMachineState` VARCHAR(45) DEFAULT NULL,
  `etalon1A` FLOAT DEFAULT NULL,
  `etalon1B` FLOAT DEFAULT NULL,
  `etalon1F` FLOAT DEFAULT NULL,
  `etalon1Mode` VARCHAR(45) DEFAULT NULL,
  `etalon1Wavelength` FLOAT DEFAULT NULL,
  `etalon1X` FLOAT DEFAULT NULL,
  `etalon1Y` FLOAT DEFAULT NULL,
  `etalon1Z` FLOAT DEFAULT NULL,
  `etalon2A` FLOAT DEFAULT NULL,
  `etalon2B` FLOAT DEFAULT NULL,
  `etalon2F` FLOAT DEFAULT NULL,
  `etalon2Mode` VARCHAR(45) DEFAULT NULL,
  `etalon2Wavelength` FLOAT DEFAULT NULL,
  `etalon2X` FLOAT DEFAULT NULL,
  `etalon2Y` FLOAT DEFAULT NULL,
  `etalon2Z` FLOAT DEFAULT NULL,
  `exposureTime` FLOAT DEFAULT NULL,
  `filterStation` TINYINT DEFAULT NULL,
  `filterMachineState` VARCHAR(45) DEFAULT NULL,
  `filterPosition` TINYINT DEFAULT NULL,
  `filterBarcode` VARCHAR(45) DEFAULT NULL,
  `filterStationSteps` FLOAT DEFAULT NULL,
  `filterStationVolts` FLOAT DEFAULT NULL,
  `filterMagazineSteps` TINYINT DEFAULT NULL,
  `filterMagazineVolts` FLOAT DEFAULT NULL,
  `focusPosition` FLOAT DEFAULT NULL,
  `focusPositionSteps` FLOAT DEFAULT NULL,
  `focusPositionVolts` FLOAT DEFAULT NULL,
  `focusMachineState` VARCHAR(45) DEFAULT NULL,
  `focusVolts` FLOAT DEFAULT NULL,
  `focusSteps` TINYINT DEFAULT NULL,
  `gain` FLOAT DEFAULT NULL,
  `gain1` FLOAT DEFAULT NULL,
  `gainSet` VARCHAR(45) DEFAULT NULL,
  `gratingMagazineSteps` TINYINT DEFAULT NULL,
  `gratingMagazineVolts` FLOAT DEFAULT NULL,
  `gratingRotationAngle` FLOAT DEFAULT NULL,
  `gratingStation` VARCHAR(45) DEFAULT NULL,
  `gratingStationSteps` FLOAT DEFAULT NULL,
  `gratingStationVolts` FLOAT DEFAULT NULL,
  `gratingMachineState` VARCHAR(45) DEFAULT NULL,
  `gratingRotationAngleSteps` TINYINT DEFAULT NULL,
  `grating` VARCHAR(45) DEFAULT NULL,
  `gratingAngle` FLOAT DEFAULT NULL,
  `halfWaveSteps` TINYINT DEFAULT NULL,
  `halfWaveAngle` FLOAT DEFAULT NULL,
  `halfWaveStation` VARCHAR(45) DEFAULT NULL,
  `halfWaveStationEncoder` FLOAT DEFAULT NULL,
  `imageId` VARCHAR(45) DEFAULT NULL,
  `instrumentName` VARCHAR(45) DEFAULT NULL,
  `julianDate` FLOAT DEFAULT NULL,
  `lstObservation` VARCHAR(45) DEFAULT NULL,
  `slitmaskBarcode` VARCHAR(45) DEFAULT NULL,
  `slitmaskType` VARCHAR(45) DEFAULT NULL,
  `numberOfCcds` TINYINT DEFAULT NULL,
  `numberOfExtensions` TINYINT DEFAULT NULL,
  `numberOfWindows` INT DEFAULT NULL,
  `objectName` VARCHAR(45) DEFAULT NULL,
  `observationMode` VARCHAR(45) DEFAULT NULL,
  `observationType` VARCHAR(45) DEFAULT NULL,
  `pfsiControlSystemVersion` VARCHAR(45) DEFAULT NULL,
  `pixelScale` FLOAT DEFAULT NULL,
  `polarizationConfig` VARCHAR(45) DEFAULT NULL,
  `pfsiProcedure` VARCHAR(45) DEFAULT NULL,
  `pupilEnd` FLOAT DEFAULT NULL,
  `quaterWaveSteps` TINYINT DEFAULT NULL,
  `quaterWaveAngle` FLOAT DEFAULT NULL,
  `quaterWaveStation` VARCHAR(45) DEFAULT NULL,
  `quaterWaveStationEncoder` VARCHAR(45) DEFAULT NULL,
  `noiseReadout` FLOAT DEFAULT NULL,
  `ccdReadoutSpeed` VARCHAR(45) DEFAULT NULL,
  `pixelSaturation` TINYINT DEFAULT NULL,
  `shutterMachineState` VARCHAR(45) DEFAULT NULL,
  `slitmaskStation` FLOAT DEFAULT NULL,
  `slitmaskStationSteps` FLOAT DEFAULT NULL,
  `slitmaskStationVolts` FLOAT DEFAULT NULL,
  `slitmasMachineState` VARCHAR(45) DEFAULT NULL,
  `slitmaskMagazineSteps` TINYINT DEFAULT NULL,
  `slitmaskVolts` FLOAT DEFAULT NULL,
  `startOfObservationTime` VARCHAR(45) DEFAULT NULL,
  `systemTime` VARCHAR(45) DEFAULT NULL,
  `fitsHeaderVersion` VARCHAR(45) DEFAULT NULL,
  `spatialCoordinate` VARCHAR(45) DEFAULT NULL,
  `waveplateMachineState` VARCHAR(45) DEFAULT NULL,
  `polarimetryProcedurePattern` VARCHAR(45) DEFAULT NULL,
  `crossTalk` FLOAT DEFAULT NULL,
  PRIMARY KEY (`rssId`),
  KEY `fk_RSSTelescope_idx` (`telescopeId`),
  CONSTRAINT `fk_RSSTelescope` FOREIGN KEY (`telescopeId`) REFERENCES `Telescope` (`telescopeId`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `RSS`
--

DROP TABLE IF EXISTS `Salticam`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Salticam` (
  `salticamId` int(11) NOT NULL AUTO_INCREMENT,
  `telescopeId` int(11) NOT NULL,
  `amplifierSection` VARCHAR(45) DEFAULT NULL,
  `amplifierTemperature` FLOAT DEFAULT NULL,
  `amplifierReadoutX` TINYINT DEFAULT NULL,
  `amplifierReadoutY` TINYINT DEFAULT NULL,
  `biasSection` VARCHAR(45) DEFAULT NULL,
  `beamSplitterScale` FLOAT DEFAULT NULL,
  `beamSplitterZero` FLOAT DEFAULT NULL,
  `detectorFocusPosition` INT DEFAULT NULL,
  `numberOfAmplifiers` TINYINT DEFAULT NULL,
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
  `pixelCoordinatePointX1` FLOAT DEFAULT NULL,
  `pixelCoordinatePointX1A` FLOAT DEFAULT NULL,
  `pixelCoordinatePointX2` FLOAT DEFAULT NULL,
  `pixelCoordinatePointX2A` FLOAT DEFAULT NULL,
  `rightAsertionPoint1` FLOAT DEFAULT NULL,
  `spatialCoordinatePoint1A` FLOAT DEFAULT NULL,
  `declanationPoint2` FLOAT DEFAULT NULL,
  `spacialCoordinatePoint2A` FLOAT DEFAULT NULL,
  `gnomicProjection1` VARCHAR(45) DEFAULT NULL,
  `cartesianProjection1A` VARCHAR(45) DEFAULT NULL,
  `gnomicProjection2` VARCHAR(45) DEFAULT NULL,
  `cartesianProjection2A` VARCHAR(45) DEFAULT NULL,
  `anglesDegreesAlways1` VARCHAR(45) DEFAULT NULL,
  `anglesDegreesAlways2` VARCHAR(45) DEFAULT NULL,
  `dataSection` VARCHAR(45) DEFAULT NULL,
  `dateOfObservation` VARCHAR(45) DEFAULT NULL,
  `detectorMode` VARCHAR(45) DEFAULT NULL,
  `detectorSection` VARCHAR(45) DEFAULT NULL,
  `detectorSize` VARCHAR(45) DEFAULT NULL,
  `detectorSoftwareVersion` VARCHAR(45) DEFAULT NULL,
  `coolerBoxTemperature` FLOAT DEFAULT NULL,
  `exposureTime` FLOAT DEFAULT NULL,
  `filterPosition` TINYINT DEFAULT NULL,
  `filterName` VARCHAR(45) DEFAULT NULL,
  `gain` FLOAT DEFAULT NULL,
  `gain1` FLOAT DEFAULT NULL,
  `gainSet` VARCHAR(45) DEFAULT NULL,
  `imageId` VARCHAR(45) DEFAULT NULL,
  `instrumentName` VARCHAR(45) DEFAULT NULL,
  `julianDate` FLOAT DEFAULT NULL,
  `lstObservation` VARCHAR(45) DEFAULT NULL,
  `numberOfCcds` TINYINT DEFAULT NULL,
  `numberOfExtensions` TINYINT DEFAULT NULL,
  `numberOfWindows` INT DEFAULT NULL,
  `objectName` VARCHAR(45) DEFAULT NULL,
  `observationMode` VARCHAR(45) DEFAULT NULL,
  `observationType` VARCHAR(45) DEFAULT NULL,
  `pixelScale` FLOAT DEFAULT NULL,
  `pupilEnd` FLOAT DEFAULT NULL,
  `noiseReadout` FLOAT DEFAULT NULL,
  `ccdReadoutSpeed` VARCHAR(45) DEFAULT NULL,
  `pixelSaturation` TINYINT DEFAULT NULL,
  `startOfObservationTime` VARCHAR(45) DEFAULT NULL,
  `systemTime` VARCHAR(45) DEFAULT NULL,
  `fitsHeaderVersion` VARCHAR(45) DEFAULT NULL,
  `spatialCoordinate` VARCHAR(45) DEFAULT NULL,
  `crossTalk` FLOAT DEFAULT NULL,
  PRIMARY KEY (`salticamId`),
  KEY `fk_SalticamTelescope_idx` (`telescopeId`),
  CONSTRAINT `fk_SalticamTelescope` FOREIGN KEY (`telescopeId`) REFERENCES `Telescope` (`telescopeId`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Institution`
--

DROP TABLE IF EXISTS `Institution`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Institution` (
  `institutionId` int(11) NOT NULL AUTO_INCREMENT,
  `institutionName` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`institutionId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Observation`
--

DROP TABLE IF EXISTS `Observation`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Observation` (
  `observationId` int(11) NOT NULL AUTO_INCREMENT,
  `telescopeId` int(11) DEFAULT NULL,
  `telescopeObservationId` varchar(45) DEFAULT NULL,
  `startTime` varchar(45) DEFAULT NULL,
  `observationStatusId` int(11) DEFAULT NULL,
  PRIMARY KEY (`observationId`),
  KEY `fk_observationStatus_idx` (`observationStatusId`),
  KEY `fk_ObservationTelescope_idx` (`telescopeId`),
  CONSTRAINT `fk_ObservationTelescope` FOREIGN KEY (`telescopeId`) REFERENCES `Telescope` (`telescopeId`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_observationStatus` FOREIGN KEY (`observationStatusId`) REFERENCES `ObservationStatus` (`observationStatusId`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ObservationStatus`
--

DROP TABLE IF EXISTS `ObservationStatus`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ObservationStatus` (
  `observationStatusId` int(11) NOT NULL,
  `status` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`observationStatusId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Proposal`
--

DROP TABLE IF EXISTS `Proposal`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Proposal` (
  `proposalId` int(11) NOT NULL AUTO_INCREMENT,
  `proposalCode` varchar(45) DEFAULT NULL,
  `date` varchar(45) DEFAULT NULL,
  `principalInvestigatorGivenName` varchar(45) DEFAULT NULL,
  `principalInvestigatorFamilyName` varchar(45) DEFAULT NULL,
  `title` varchar(255) DEFAULT NULL,
  `lastUpdated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`proposalId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ProposalInvestigator`
--

DROP TABLE IF EXISTS `ProposalInvestigator`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ProposalInvestigator` (
  `proposalId` int(11) NOT NULL,
  `userId` int(11) DEFAULT NULL,
  PRIMARY KEY (`proposalId`),
  KEY `fk_ProposalInvestigatorUser_idx` (`userId`),
  CONSTRAINT `fk_ProposalInvestigatorProposal` FOREIGN KEY (`proposalId`) REFERENCES `Proposal` (`proposalId`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_ProposalInvestigatorUser` FOREIGN KEY (`userId`) REFERENCES `User` (`userId`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Target`
--

DROP TABLE IF EXISTS `Target`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Target` (
  `targetId` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) DEFAULT NULL,
  `rightAscension` float DEFAULT NULL,
  `declination` float DEFAULT NULL,
  `position` point DEFAULT NULL,
  `targetTypeId` int(11) DEFAULT NULL,
  PRIMARY KEY (`targetId`),
  KEY `fk_TargetType_idx` (`targetTypeId`),
  CONSTRAINT `fk_TargetType` FOREIGN KEY (`targetTypeId`) REFERENCES `TargetType` (`targetTypeId`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `TargetType`
--

DROP TABLE IF EXISTS `TargetType`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `TargetType` (
  `targetTypeId` int(11) NOT NULL AUTO_INCREMENT,
  `numericValue` varchar(45) DEFAULT NULL,
  `explanation` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`targetTypeId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Telescope`
--

DROP TABLE IF EXISTS `Telescope`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Telescope` (
  `telescopeId` int(11) NOT NULL AUTO_INCREMENT,
  `telescopeName` varchar(45) NOT NULL,
  `ownerId` int(11) DEFAULT NULL,
  PRIMARY KEY (`telescopeId`),
  KEY `fk_TelescopeInstitute_idx` (`ownerId`),
  CONSTRAINT `fk_TelescopeInstitute` FOREIGN KEY (`ownerId`) REFERENCES `Institution` (`institutionId`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `User`
--

DROP TABLE IF EXISTS `User`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `User` (
  `userId` int(11) NOT NULL AUTO_INCREMENT,
  `institutionId` int(11) DEFAULT NULL,
  `institutionUserId` varchar(45) DEFAULT NULL,
  `givenName` varchar(45) DEFAULT NULL,
  `familyName` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`userId`),
  KEY `fk_UserInstitution_idx` (`institutionId`),
  CONSTRAINT `fk_UserInstitution` FOREIGN KEY (`institutionId`) REFERENCES `Institution` (`institutionId`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2019-05-24  9:58:50
