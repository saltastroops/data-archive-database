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
  `dataCategory` VARCHAR(255) DEFAULT NULL,
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
  `dataFileId` int(11) NOT NULL AUTO_INCREMENT,
  `dataCategoryId` int(11) DEFAULT NULL,
  `startTime` DATETIME DEFAULT NULL,
  `name` VARCHAR(255) DEFAULT NULL,
  `path` VARCHAR(255) DEFAULT NULL,
  `targetId` int(11) DEFAULT NULL,
  `size` FLOAT DEFAULT NULL,
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
  `name` VARCHAR(255) DEFAULT NULL,
  `path` VARCHAR(255) DEFAULT NULL,
  `dataFileId` int(11) DEFAULT NULL,
  `order` VARCHAR(255) DEFAULT NULL,
  PRIMARY KEY (`dataPreviewId`),
  KEY `fk_DataPreviewDataFile_idx` (`dataFileId`),
  CONSTRAINT `fk_DataPreviewDataFile` FOREIGN KEY (`dataFileId`) REFERENCES `DataFile` (`dataFileId`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `HRS`
--

DROP TABLE IF EXISTS `HRS`;
CREATE TABLE `HRS` (
  `hrsId` int(11) NOT NULL AUTO_INCREMENT,
  `dataFileId` int(11) NOT NULL,
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

--
-- Table structure for table `RSS`
--

DROP TABLE IF EXISTS `RSS`;
CREATE TABLE `RSS` (
  `rssId` INT(11) NOT NULL AUTO_INCREMENT,
  `dataFileId` INT(11) NOT NULL,
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

--
-- Table structure for table `RSS`
--

DROP TABLE IF EXISTS `Salticam`;
CREATE TABLE `Salticam` (
  `salticamId` int(11) NOT NULL AUTO_INCREMENT,
  `dataFileId` int(11) NOT NULL,
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
-- Table structure for table `Institution`
--

DROP TABLE IF EXISTS `Institution`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Institution` (
  `institutionId` int(11) NOT NULL AUTO_INCREMENT,
  `institutionName` VARCHAR(255) DEFAULT NULL,
  PRIMARY KEY (`institutionId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Observation`
--

DROP TABLE IF EXISTS `Observation`;
CREATE TABLE `Observation` (
  `observationId` int(11) NOT NULL AUTO_INCREMENT,
  `proposalId` int(11),
  `telescopeId` int(11) DEFAULT NULL,
  `telescopeObservationId` VARCHAR(255) DEFAULT NULL,
  `night` VARCHAR(255) DEFAULT NULL,
  `observationStatusId` int(11) DEFAULT NULL,
  PRIMARY KEY (`observationId`),
  KEY `fk_proposal_idx` (`proposalId`),
  KEY `fk_observationStatus_idx` (`observationStatusId`),
  KEY `fk_ObservationTelescope_idx` (`telescopeId`),
  CONSTRAINT `fk_proposal` FOREIGN KEY (`proposalId`) REFERENCES `Proposal` (`proposalId`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_ObservationTelescope` FOREIGN KEY (`telescopeId`) REFERENCES `Telescope` (`telescopeId`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk_observationStatus` FOREIGN KEY (`observationStatusId`) REFERENCES `ObservationStatus` (`observationStatusId`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Table structure for table `ObservationStatus`
--

DROP TABLE IF EXISTS `ObservationStatus`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ObservationStatus` (
  `observationStatusId` int(11) NOT NULL,
  `status` VARCHAR(255) DEFAULT NULL,
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
  `proposalCode` VARCHAR(255) NOT NULL,
  `principalInvestigatorGivenName` VARCHAR(255) NOT NULL,
  `principalInvestigatorFamilyName` VARCHAR(255) NOT NULL,
  `title` VARCHAR(255) NOT NULL,
  `institutionId` INT(11) NOT NULL,
  `lastUpdated` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`proposalId`),
  KEY `fk_institution_idx` (`institutionId`),
  CONSTRAINT `fk_ProposalInstitution` FOREIGN KEY (`institutionId`) REFERENCES `Institution` (`institutionId`) ON DELETE NO ACTION ON UPDATE NO ACTION
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
  `institutionUserId` varchar(255) NOT NULL,
  PRIMARY KEY (`proposalId`, `institutionUserId`),
  CONSTRAINT `fk_ProposalInvestigatorProposal` FOREIGN KEY (`proposalId`) REFERENCES `Proposal` (`proposalId`) ON DELETE NO ACTION ON UPDATE NO ACTION,
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;


--
-- Spatial reference system for target positions
--
CREATE OR REPLACE SPATIAL REFERENCE SYSTEM 123456 NAME 'Perfect Unit Sphere' DEFINITION 'GEOGCS["Unit Sphere",DATUM["Unit Sphere",SPHEROID["Unit Sphere",1,0]],PRIMEM["Greenwich",0],UNIT["degree",0.017453292519943278],AXIS["Lon",EAST],AXIS["Lat",NORTH]]';

--
-- Table structure for table `Target`
--

DROP TABLE IF EXISTS `Target`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Target` (
  `targetId` int(11) NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(255) DEFAULT NULL,
  `rightAscension` float DEFAULT NULL,
  `declination` float DEFAULT NULL,
  `position` point SRID 123456 DEFAULT NULL COMMENT 'RA is offset by -180 deg so that it falls into [-180, 180]',
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
  `numericValue` VARCHAR(255) DEFAULT NULL,
  `explanation` VARCHAR(100) DEFAULT NULL,
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
  `telescopeName` VARCHAR(255) NOT NULL,
  `ownerId` int(11) DEFAULT NULL,
  PRIMARY KEY (`telescopeId`),
  KEY `fk_TelescopeInstitute_idx` (`ownerId`),
  CONSTRAINT `fk_TelescopeInstitute` FOREIGN KEY (`ownerId`) REFERENCES `Institution` (`institutionId`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
