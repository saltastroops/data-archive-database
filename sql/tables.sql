-- MySQL dump 10.13  Distrib 5.7.17, for macos10.12 (x86_64)
--
-- Host: 127.0.0.1    Database: ssda
-- ------------------------------------------------------
-- Server version	5.7.17

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
  `id` int(11) NOT NULL,
  `dataCategory` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `DataFile`
--

DROP TABLE IF EXISTS `DataFile`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `DataFile` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) DEFAULT NULL,
  `dataCategoryId` varchar(45) DEFAULT NULL,
  `observationId` int(11) DEFAULT NULL,
  `targetID` varchar(45) DEFAULT NULL,
  `startTime` varchar(45) DEFAULT NULL,
  `size` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `observationId_idx` (`observationId`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `DataPreview`
--

DROP TABLE IF EXISTS `DataPreview`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `DataPreview` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) DEFAULT NULL,
  `dataFieldId` varchar(45) DEFAULT NULL,
  `orders` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `FileData`
--

DROP TABLE IF EXISTS `FileData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `FileData` (
  `dataCategoryId` varchar(45) DEFAULT NULL,
  `startTime` varchar(45) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `FitsHeaderImage`
--

DROP TABLE IF EXISTS `FitsHeaderImage`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `FitsHeaderImage` (
  `fileID` int(11) NOT NULL,
  `object` varchar(45) DEFAULT NULL,
  `detectormode` varchar(45) DEFAULT NULL,
  `ra` varchar(45) DEFAULT NULL,
  `dec` varchar(45) DEFAULT NULL,
  `date` varchar(45) DEFAULT NULL,
  `exptime` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`fileID`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `HIPPO`
--

DROP TABLE IF EXISTS `HIPPO`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `HIPPO` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `telescopeName` varchar(45) DEFAULT NULL,
  `date` varchar(45) DEFAULT NULL,
  `observer` varchar(45) DEFAULT NULL,
  `objectName` varchar(45) DEFAULT NULL,
  `exposureMode` varchar(45) DEFAULT NULL,
  `filter` varchar(45) DEFAULT NULL,
  `humidity` varchar(45) DEFAULT NULL,
  `rotater` varchar(45) DEFAULT NULL,
  `telFocus` varchar(45) DEFAULT NULL,
  `wheelA` varchar(45) DEFAULT NULL,
  `wheelB` varchar(45) DEFAULT NULL,
  `zenith` varchar(45) DEFAULT NULL,
  `headModel` varchar(45) DEFAULT NULL,
  `acquisitionMode` varchar(45) DEFAULT NULL,
  `readMode` varchar(45) DEFAULT NULL,
  `imageRect` varchar(45) DEFAULT NULL,
  `hbin` varchar(45) DEFAULT NULL,
  `vbin` varchar(45) DEFAULT NULL,
  `exposure` varchar(45) DEFAULT NULL,
  `serialNumber` varchar(45) DEFAULT NULL,
  `filterA` varchar(45) DEFAULT NULL,
  `filterB` varchar(45) DEFAULT NULL,
  `hourAngle` varchar(45) DEFAULT NULL,
  `instrumentAngle` varchar(45) DEFAULT NULL,
  `triggers` varchar(45) DEFAULT NULL,
  `instrumentName` varchar(45) DEFAULT NULL,
  `Observation_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_SHOC_Observation1_idx` (`Observation_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `HRS`
--

DROP TABLE IF EXISTS `HRS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `HRS` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `objectName` varchar(45) DEFAULT NULL,
  `date` varchar(45) DEFAULT NULL,
  `ra` varchar(45) DEFAULT NULL,
  `declination` varchar(45) DEFAULT NULL,
  `telescope` varchar(45) DEFAULT NULL,
  `imageType` varchar(45) DEFAULT NULL,
  `filter` varchar(45) DEFAULT NULL,
  `exposure` varchar(45) DEFAULT NULL,
  `instrument` varchar(45) DEFAULT NULL,
  `mode` varchar(45) DEFAULT NULL,
  `prismpos` varchar(45) DEFAULT NULL,
  `trimsec` varchar(45) DEFAULT NULL,
  `biassec` varchar(45) DEFAULT NULL,
  `bscale` varchar(45) DEFAULT NULL,
  `bzero` varchar(45) DEFAULT NULL,
  `targetInfo_target_ID` int(11) NOT NULL,
  PRIMARY KEY (`id`,`targetInfo_target_ID`),
  KEY `fk_GIRAFFE_header_targetInfo1_idx` (`targetInfo_target_ID`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `HippoTech`
--

DROP TABLE IF EXISTS `HippoTech`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `HippoTech` (
  `id` int(11) NOT NULL,
  `BZERO` varchar(45) DEFAULT NULL,
  `BSCALE` varchar(45) DEFAULT NULL,
  `HEAD` varchar(45) DEFAULT NULL,
  `IMGRECT` varchar(45) DEFAULT NULL,
  `HBIN` varchar(45) DEFAULT NULL,
  `VBIN` varchar(45) DEFAULT NULL,
  `SUBRECT` varchar(45) DEFAULT NULL,
  `DATATYPE` varchar(45) DEFAULT NULL,
  `XTYPE` varchar(45) DEFAULT NULL,
  `XUNIT` varchar(45) DEFAULT NULL,
  `RAYWAVE` varchar(45) DEFAULT NULL,
  `CALBWVNM` varchar(45) DEFAULT NULL,
  `TRIGGER` varchar(45) DEFAULT NULL,
  `CALIB` varchar(45) DEFAULT NULL,
  `DLLVER` varchar(45) DEFAULT NULL,
  `EXPOSURE` varchar(45) DEFAULT NULL,
  `TEMP` varchar(45) DEFAULT NULL,
  `READTIME` varchar(45) DEFAULT NULL,
  `OPERATN` varchar(45) DEFAULT NULL,
  `GAIN` varchar(45) DEFAULT NULL,
  `EMREALGN` varchar(45) DEFAULT NULL,
  `VCLKAMP` varchar(45) DEFAULT NULL,
  `VSHIFT` varchar(45) DEFAULT NULL,
  `OUTPTAMP` varchar(45) DEFAULT NULL,
  `PREAMP` varchar(45) DEFAULT NULL,
  `SERNO` varchar(45) DEFAULT NULL,
  `UNSTTEMP` varchar(45) DEFAULT NULL,
  `BLCLAMP` varchar(45) DEFAULT NULL,
  `PRECAN` varchar(45) DEFAULT NULL,
  `FLIPX` varchar(45) DEFAULT NULL,
  `FLIPY` varchar(45) DEFAULT NULL,
  `CNTCVTMD` varchar(45) DEFAULT NULL,
  `CNTCVT` varchar(45) DEFAULT NULL,
  `DTNWLGTH` varchar(45) DEFAULT NULL,
  `SNTVTY` varchar(45) DEFAULT NULL,
  `SPSNFLTR` varchar(45) DEFAULT NULL,
  `THRSHLD` varchar(45) DEFAULT NULL,
  `PCNTENLD` varchar(45) DEFAULT NULL,
  `NSETHSLD` varchar(45) DEFAULT NULL,
  `AVGFTRMD` varchar(45) DEFAULT NULL,
  `AVGFCTR` varchar(45) DEFAULT NULL,
  `FRMCNT` varchar(45) DEFAULT NULL,
  `PORTMODE` varchar(45) DEFAULT NULL,
  `LSHEIGHT` varchar(45) DEFAULT NULL,
  `LSSPEED` varchar(45) DEFAULT NULL,
  `LSALTDIR` varchar(45) DEFAULT NULL,
  `LSCTRL` varchar(45) DEFAULT NULL,
  `LSDIR` varchar(45) DEFAULT NULL,
  `FKSMODE` varchar(45) DEFAULT NULL,
  `FKTMODE` varchar(45) DEFAULT NULL,
  `DATE` varchar(45) DEFAULT NULL,
  `FRAME` varchar(45) DEFAULT NULL,
  `ESHTMODE` varchar(45) DEFAULT NULL,
  `IRIGDATA` varchar(45) DEFAULT NULL,
  `AIRMASS` varchar(45) DEFAULT NULL,
  `DATE-OBS` varchar(45) DEFAULT NULL,
  `DOMEPOS` varchar(45) DEFAULT NULL,
  `FILTERA` varchar(45) DEFAULT NULL,
  `FILTERB` varchar(45) DEFAULT NULL,
  `GPS-INT` varchar(45) DEFAULT NULL,
  `GPSSTART` varchar(45) DEFAULT NULL,
  `HA` varchar(45) DEFAULT NULL,
  `HUMIDIT` varchar(45) DEFAULT NULL,
  `INSTANGL` varchar(45) DEFAULT NULL,
  `INSTRUME` varchar(45) DEFAULT NULL,
  `INSTSWV` varchar(45) DEFAULT NULL,
  `OBJDEC` varchar(45) DEFAULT NULL,
  `OBJECT` varchar(45) DEFAULT NULL,
  `OBJEPOCH` varchar(45) DEFAULT NULL,
  `OBJEQUIN` varchar(45) DEFAULT NULL,
  `OBJRA` varchar(45) DEFAULT NULL,
  `OBSERVER` varchar(45) DEFAULT NULL,
  `OBSTYPE` varchar(45) DEFAULT NULL,
  `POSA` varchar(45) DEFAULT NULL,
  `POSB` varchar(45) DEFAULT NULL,
  `RELSKYT` varchar(45) DEFAULT NULL,
  `SEEING` varchar(45) DEFAULT NULL,
  `TELDEC` varchar(45) DEFAULT NULL,
  `TELESCOP` varchar(45) DEFAULT NULL,
  `TELFOCUS` varchar(45) DEFAULT NULL,
  `TELRA` varchar(45) DEFAULT NULL,
  `TMTDEW` varchar(45) DEFAULT NULL,
  `WHEELA` varchar(45) DEFAULT NULL,
  `WHEELB` varchar(45) DEFAULT NULL,
  `WIND` varchar(45) DEFAULT NULL,
  `ZD` varchar(45) DEFAULT NULL,
  `SHOC_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_SHOC_TECH_SHOC1_idx` (`SHOC_id`),
  CONSTRAINT `fk_SHOC_TECH_SHOC12` FOREIGN KEY (`SHOC_id`) REFERENCES `SHOC` (`id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Institution`
--

DROP TABLE IF EXISTS `Institution`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Institution` (
  `id` int(11) NOT NULL,
  `institutionName` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Instruments`
--

DROP TABLE IF EXISTS `Instruments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Instruments` (
  `instrument_id` int(11) NOT NULL AUTO_INCREMENT,
  `instrumentName` varchar(45) DEFAULT NULL,
  `Telescopes_telescope_id` int(11) NOT NULL,
  PRIMARY KEY (`instrument_id`),
  KEY `instrument_idx` (`instrumentName`),
  KEY `fk_Instruments_Telescopes1_idx` (`Telescopes_telescope_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Observation`
--

DROP TABLE IF EXISTS `Observation`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Observation` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `telescopeId` varchar(45) DEFAULT NULL,
  `telescopeObservationId` varchar(45) DEFAULT NULL,
  `startTime` varchar(45) DEFAULT NULL,
  `statusId` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ObservationStatus`
--

DROP TABLE IF EXISTS `ObservationStatus`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ObservationStatus` (
  `id` int(11) NOT NULL,
  `status` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Observatories`
--

DROP TABLE IF EXISTS `Observatories`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Observatories` (
  `observatory_id` int(11) NOT NULL AUTO_INCREMENT,
  `observatoryName` varchar(45) DEFAULT NULL,
  `latitude` varchar(45) DEFAULT NULL,
  `longitude` varchar(45) DEFAULT NULL,
  `altitude` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`observatory_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Proposal`
--

DROP TABLE IF EXISTS `Proposal`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Proposal` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `proposalCode` varchar(45) DEFAULT NULL,
  `date` varchar(45) DEFAULT NULL,
  `principalInvestigatorGivenName` varchar(45) DEFAULT NULL,
  `principalInvestigatorFamilyName` varchar(45) DEFAULT NULL,
  `title` varchar(255) DEFAULT NULL,
  `lastUpdated` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ProposalInvestigator`
--

DROP TABLE IF EXISTS `ProposalInvestigator`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ProposalInvestigator` (
  `proposalId` int(11) NOT NULL,
  `userId` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`proposalId`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Proposal_Status`
--

DROP TABLE IF EXISTS `Proposal_Status`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Proposal_Status` (
  `id` int(11) NOT NULL,
  `status` varchar(45) DEFAULT NULL,
  `Proposal_Statuscol` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `SHOC`
--

DROP TABLE IF EXISTS `SHOC`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `SHOC` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `telescopeName` varchar(45) DEFAULT NULL,
  `date` varchar(45) DEFAULT NULL,
  `observer` varchar(45) DEFAULT NULL,
  `objectName` varchar(45) DEFAULT NULL,
  `exposureMode` varchar(45) DEFAULT NULL,
  `filter` varchar(45) DEFAULT NULL,
  `humidity` varchar(45) DEFAULT NULL,
  `rotater` varchar(45) DEFAULT NULL,
  `telFocus` varchar(45) DEFAULT NULL,
  `wheelA` varchar(45) DEFAULT NULL,
  `wheelB` varchar(45) DEFAULT NULL,
  `zenith` varchar(45) DEFAULT NULL,
  `headModel` varchar(45) DEFAULT NULL,
  `acquisitionMode` varchar(45) DEFAULT NULL,
  `readMode` varchar(45) DEFAULT NULL,
  `imageRect` varchar(45) DEFAULT NULL,
  `hbin` varchar(45) DEFAULT NULL,
  `vbin` varchar(45) DEFAULT NULL,
  `exposure` varchar(45) DEFAULT NULL,
  `serialNumber` varchar(45) DEFAULT NULL,
  `filterA` varchar(45) DEFAULT NULL,
  `filterB` varchar(45) DEFAULT NULL,
  `hourAngle` varchar(45) DEFAULT NULL,
  `instrumentAngle` varchar(45) DEFAULT NULL,
  `triggers` varchar(45) DEFAULT NULL,
  `instrumentName` varchar(45) DEFAULT NULL,
  `Observation_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_SHOC_Observation1_idx` (`Observation_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `SIRIUS`
--

DROP TABLE IF EXISTS `SIRIUS`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `SIRIUS` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `telescopeName` varchar(45) DEFAULT NULL,
  `date` varchar(45) DEFAULT NULL,
  `observer` varchar(45) DEFAULT NULL,
  `objectName` varchar(45) DEFAULT NULL,
  `exposureMode` varchar(45) DEFAULT NULL,
  `filter` varchar(45) DEFAULT NULL,
  `humidity` varchar(45) DEFAULT NULL,
  `rotater` varchar(45) DEFAULT NULL,
  `telFocus` varchar(45) DEFAULT NULL,
  `wheelA` varchar(45) DEFAULT NULL,
  `wheelB` varchar(45) DEFAULT NULL,
  `zenith` varchar(45) DEFAULT NULL,
  `headModel` varchar(45) DEFAULT NULL,
  `acquisitionMode` varchar(45) DEFAULT NULL,
  `readMode` varchar(45) DEFAULT NULL,
  `imageRect` varchar(45) DEFAULT NULL,
  `hbin` varchar(45) DEFAULT NULL,
  `vbin` varchar(45) DEFAULT NULL,
  `exposure` varchar(45) DEFAULT NULL,
  `serialNumber` varchar(45) DEFAULT NULL,
  `filterA` varchar(45) DEFAULT NULL,
  `filterB` varchar(45) DEFAULT NULL,
  `hourAngle` varchar(45) DEFAULT NULL,
  `instrumentAngle` varchar(45) DEFAULT NULL,
  `triggers` varchar(45) DEFAULT NULL,
  `instrumentName` varchar(45) DEFAULT NULL,
  `Observation_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_SHOC_Observation1_idx` (`Observation_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `SPUPNIC`
--

DROP TABLE IF EXISTS `SPUPNIC`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `SPUPNIC` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `object` varchar(45) DEFAULT NULL,
  `observer` varchar(45) DEFAULT NULL,
  `telescope` varchar(45) DEFAULT NULL,
  `instrument` varchar(45) DEFAULT NULL,
  `date_obs` varchar(45) DEFAULT NULL,
  `grating` varchar(45) DEFAULT NULL,
  `grating_angle` varchar(45) DEFAULT NULL,
  `filter` varchar(45) DEFAULT NULL,
  `exposure` varchar(45) DEFAULT NULL,
  `exposure_type` varchar(45) DEFAULT NULL,
  `arc_lamp` varchar(45) DEFAULT NULL,
  `ra` varchar(45) DEFAULT NULL,
  `declination` varchar(45) DEFAULT NULL,
  `Observation_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_SPUPNIC_Observation1_idx` (`Observation_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `STE`
--

DROP TABLE IF EXISTS `STE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `STE` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `telescopeName` varchar(45) DEFAULT NULL,
  `date` varchar(45) DEFAULT NULL,
  `observer` varchar(45) DEFAULT NULL,
  `objectName` varchar(45) DEFAULT NULL,
  `exposureTime` varchar(45) DEFAULT NULL,
  `filter` varchar(45) DEFAULT NULL,
  `rotater` varchar(45) DEFAULT NULL,
  `telFocus` varchar(45) DEFAULT NULL,
  `wheelA` varchar(45) DEFAULT NULL,
  `wheelB` varchar(45) DEFAULT NULL,
  `zenith` varchar(45) DEFAULT NULL,
  `headModel` varchar(45) DEFAULT NULL,
  `acquisitionMode` varchar(45) DEFAULT NULL,
  `readMode` varchar(45) DEFAULT NULL,
  `imageRect` varchar(45) DEFAULT NULL,
  `hbin` varchar(45) DEFAULT NULL,
  `vbin` varchar(45) DEFAULT NULL,
  `exposure` varchar(45) DEFAULT NULL,
  `serialNumber` varchar(45) DEFAULT NULL,
  `filterA` varchar(45) DEFAULT NULL,
  `filterB` varchar(45) DEFAULT NULL,
  `hourAngle` varchar(45) DEFAULT NULL,
  `instrumentAngle` varchar(45) DEFAULT NULL,
  `triggers` varchar(45) DEFAULT NULL,
  `instrumentName` varchar(45) DEFAULT NULL,
  `Observation_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_SHOC_Observation1_idx` (`Observation_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Salticam`
--

DROP TABLE IF EXISTS `Salticam`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Salticam` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `telescopeName` varchar(45) DEFAULT NULL,
  `dateObserved` varchar(45) DEFAULT NULL,
  `observer` varchar(45) DEFAULT NULL,
  `objectName` varchar(45) DEFAULT NULL,
  `obsMode` varchar(45) DEFAULT NULL,
  `instrumentName` varchar(45) DEFAULT NULL,
  `rightAscension` varchar(45) DEFAULT NULL,
  `declination` varchar(45) DEFAULT NULL,
  `exposureTime` varchar(45) DEFAULT NULL,
  `airMass` varchar(45) DEFAULT NULL,
  `detectorMode` varchar(45) DEFAULT NULL,
  `observationType` varchar(45) DEFAULT NULL,
  `ccdType` varchar(45) DEFAULT NULL,
  `projectID` varchar(45) DEFAULT NULL,
  `siteLatitude` varchar(45) DEFAULT NULL,
  `siteLongitude` varchar(45) DEFAULT NULL,
  `detectorSoftwareVersion` varchar(45) DEFAULT NULL,
  `julianDay` varchar(45) DEFAULT NULL,
  `moonAngle` varchar(45) DEFAULT NULL,
  `gainSet` varchar(45) DEFAULT NULL,
  `readOutSpeed` varchar(45) DEFAULT NULL,
  `filter` varchar(45) DEFAULT NULL,
  `filterPosition` varchar(45) DEFAULT NULL,
  `cameraFocus` varchar(45) DEFAULT NULL,
  `telescopeFocus` varchar(45) DEFAULT NULL,
  `photometry` varchar(45) DEFAULT NULL,
  `seeing` varchar(45) DEFAULT NULL,
  `transparency` varchar(45) DEFAULT NULL,
  `blockID` varchar(45) DEFAULT NULL,
  `telescopeRightAscension` varchar(45) DEFAULT NULL,
  `telescopeDeclination` varchar(45) DEFAULT NULL,
  `equinox` varchar(45) DEFAULT NULL,
  `epoch` varchar(45) DEFAULT NULL,
  `timeObserved` varchar(45) DEFAULT NULL,
  `Observation_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_SHOC_Observation1_idx` (`Observation_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `SalticamTech`
--

DROP TABLE IF EXISTS `SalticamTech`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `SalticamTech` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `properMotionRA` varchar(45) DEFAULT NULL,
  `properMotionDEC` varchar(45) DEFAULT NULL,
  `observer` varchar(45) DEFAULT NULL,
  `objectName` varchar(45) DEFAULT NULL,
  `obsMode` varchar(45) DEFAULT NULL,
  `instrumentName` varchar(45) DEFAULT NULL,
  `rightAscension` varchar(45) DEFAULT NULL,
  `declination` varchar(45) DEFAULT NULL,
  `exposureTime` varchar(45) DEFAULT NULL,
  `airMass` varchar(45) DEFAULT NULL,
  `detectorMode` varchar(45) DEFAULT NULL,
  `observationType` varchar(45) DEFAULT NULL,
  `ccdType` varchar(45) DEFAULT NULL,
  `imageRect` varchar(45) DEFAULT NULL,
  `hbin` varchar(45) DEFAULT NULL,
  `vbin` varchar(45) DEFAULT NULL,
  `exposure` varchar(45) DEFAULT NULL,
  `serialNumber` varchar(45) DEFAULT NULL,
  `filterA` varchar(45) DEFAULT NULL,
  `filterB` varchar(45) DEFAULT NULL,
  `hourAngle` varchar(45) DEFAULT NULL,
  `instrumentAngle` varchar(45) DEFAULT NULL,
  `triggers` varchar(45) DEFAULT NULL,
  `projectID` varchar(45) DEFAULT NULL,
  `Observation_id` int(11) NOT NULL,
  `siteLatitude` varchar(45) DEFAULT NULL,
  `siteLongitude` varchar(45) DEFAULT NULL,
  `detectorSoftwareVersion` varchar(45) DEFAULT NULL,
  `julianDay` varchar(45) DEFAULT NULL,
  `moonAngle` varchar(45) DEFAULT NULL,
  `gainSet` varchar(45) DEFAULT NULL,
  `readOutSpeed` varchar(45) DEFAULT NULL,
  `filter` varchar(45) DEFAULT NULL,
  `filterPosition` varchar(45) DEFAULT NULL,
  `cameraFocus` varchar(45) DEFAULT NULL,
  `telescopeFocus` varchar(45) DEFAULT NULL,
  `photometry` varchar(45) DEFAULT NULL,
  `seeing` varchar(45) DEFAULT NULL,
  `transparancy` varchar(45) DEFAULT NULL,
  `blockID` varchar(45) DEFAULT NULL,
  `imageID` varchar(45) DEFAULT NULL,
  `telescopeRightAscension` varchar(45) DEFAULT NULL,
  `telescopeDeclination` varchar(45) DEFAULT NULL,
  `pupilStart` varchar(45) DEFAULT NULL,
  `pupilEnd` varchar(45) DEFAULT NULL,
  `pixelScale` varchar(45) DEFAULT NULL,
  `numberOfAmplifiers` varchar(45) DEFAULT NULL,
  `numberOfCCD` varchar(45) DEFAULT NULL,
  `ccdSum` varchar(45) DEFAULT NULL,
  `telescopePositionAngle` varchar(45) DEFAULT NULL,
  `pelliclePosition` varchar(45) DEFAULT NULL,
  `instrumentPort` varchar(45) DEFAULT NULL,
  `telescopeEquinox` varchar(45) DEFAULT NULL,
  `telescopeEpoch` varchar(45) DEFAULT NULL,
  `telescopeHourAngle` varchar(45) DEFAULT NULL,
  `telescopeAltitude` varchar(45) DEFAULT NULL,
  `telescope` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_SHOC_Observation1_idx` (`Observation_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ShocTech`
--

DROP TABLE IF EXISTS `ShocTech`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ShocTech` (
  `id` int(11) NOT NULL,
  `BZERO` varchar(45) DEFAULT NULL,
  `BSCALE` varchar(45) DEFAULT NULL,
  `HEAD` varchar(45) DEFAULT NULL,
  `IMGRECT` varchar(45) DEFAULT NULL,
  `HBIN` varchar(45) DEFAULT NULL,
  `VBIN` varchar(45) DEFAULT NULL,
  `SUBRECT` varchar(45) DEFAULT NULL,
  `DATATYPE` varchar(45) DEFAULT NULL,
  `XTYPE` varchar(45) DEFAULT NULL,
  `XUNIT` varchar(45) DEFAULT NULL,
  `RAYWAVE` varchar(45) DEFAULT NULL,
  `CALBWVNM` varchar(45) DEFAULT NULL,
  `TRIGGER` varchar(45) DEFAULT NULL,
  `CALIB` varchar(45) DEFAULT NULL,
  `DLLVER` varchar(45) DEFAULT NULL,
  `EXPOSURE` varchar(45) DEFAULT NULL,
  `TEMP` varchar(45) DEFAULT NULL,
  `READTIME` varchar(45) DEFAULT NULL,
  `OPERATN` varchar(45) DEFAULT NULL,
  `GAIN` varchar(45) DEFAULT NULL,
  `EMREALGN` varchar(45) DEFAULT NULL,
  `VCLKAMP` varchar(45) DEFAULT NULL,
  `VSHIFT` varchar(45) DEFAULT NULL,
  `OUTPTAMP` varchar(45) DEFAULT NULL,
  `PREAMP` varchar(45) DEFAULT NULL,
  `SERNO` varchar(45) DEFAULT NULL,
  `UNSTTEMP` varchar(45) DEFAULT NULL,
  `BLCLAMP` varchar(45) DEFAULT NULL,
  `PRECAN` varchar(45) DEFAULT NULL,
  `FLIPX` varchar(45) DEFAULT NULL,
  `FLIPY` varchar(45) DEFAULT NULL,
  `CNTCVTMD` varchar(45) DEFAULT NULL,
  `CNTCVT` varchar(45) DEFAULT NULL,
  `DTNWLGTH` varchar(45) DEFAULT NULL,
  `SNTVTY` varchar(45) DEFAULT NULL,
  `SPSNFLTR` varchar(45) DEFAULT NULL,
  `THRSHLD` varchar(45) DEFAULT NULL,
  `PCNTENLD` varchar(45) DEFAULT NULL,
  `NSETHSLD` varchar(45) DEFAULT NULL,
  `AVGFTRMD` varchar(45) DEFAULT NULL,
  `AVGFCTR` varchar(45) DEFAULT NULL,
  `FRMCNT` varchar(45) DEFAULT NULL,
  `PORTMODE` varchar(45) DEFAULT NULL,
  `LSHEIGHT` varchar(45) DEFAULT NULL,
  `LSSPEED` varchar(45) DEFAULT NULL,
  `LSALTDIR` varchar(45) DEFAULT NULL,
  `LSCTRL` varchar(45) DEFAULT NULL,
  `LSDIR` varchar(45) DEFAULT NULL,
  `FKSMODE` varchar(45) DEFAULT NULL,
  `FKTMODE` varchar(45) DEFAULT NULL,
  `DATE` varchar(45) DEFAULT NULL,
  `FRAME` varchar(45) DEFAULT NULL,
  `ESHTMODE` varchar(45) DEFAULT NULL,
  `IRIGDATA` varchar(45) DEFAULT NULL,
  `AIRMASS` varchar(45) DEFAULT NULL,
  `DATE-OBS` varchar(45) DEFAULT NULL,
  `DOMEPOS` varchar(45) DEFAULT NULL,
  `FILTERA` varchar(45) DEFAULT NULL,
  `FILTERB` varchar(45) DEFAULT NULL,
  `GPS-INT` varchar(45) DEFAULT NULL,
  `GPSSTART` varchar(45) DEFAULT NULL,
  `HA` varchar(45) DEFAULT NULL,
  `HUMIDIT` varchar(45) DEFAULT NULL,
  `INSTANGL` varchar(45) DEFAULT NULL,
  `INSTRUME` varchar(45) DEFAULT NULL,
  `INSTSWV` varchar(45) DEFAULT NULL,
  `OBJDEC` varchar(45) DEFAULT NULL,
  `OBJECT` varchar(45) DEFAULT NULL,
  `OBJEPOCH` varchar(45) DEFAULT NULL,
  `OBJEQUIN` varchar(45) DEFAULT NULL,
  `OBJRA` varchar(45) DEFAULT NULL,
  `OBSERVER` varchar(45) DEFAULT NULL,
  `OBSTYPE` varchar(45) DEFAULT NULL,
  `POSA` varchar(45) DEFAULT NULL,
  `POSB` varchar(45) DEFAULT NULL,
  `RELSKYT` varchar(45) DEFAULT NULL,
  `SEEING` varchar(45) DEFAULT NULL,
  `TELDEC` varchar(45) DEFAULT NULL,
  `TELESCOP` varchar(45) DEFAULT NULL,
  `TELFOCUS` varchar(45) DEFAULT NULL,
  `TELRA` varchar(45) DEFAULT NULL,
  `TMTDEW` varchar(45) DEFAULT NULL,
  `WHEELA` varchar(45) DEFAULT NULL,
  `WHEELB` varchar(45) DEFAULT NULL,
  `WIND` varchar(45) DEFAULT NULL,
  `ZD` varchar(45) DEFAULT NULL,
  `SHOC_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_SHOC_TECH_SHOC1_idx` (`SHOC_id`),
  CONSTRAINT `fk_SHOC_TECH_SHOC1` FOREIGN KEY (`SHOC_id`) REFERENCES `SHOC` (`id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `SimbadClassification`
--

DROP TABLE IF EXISTS `SimbadClassification`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `SimbadClassification` (
  `numericCode` varchar(45) DEFAULT NULL,
  `standardName` varchar(45) DEFAULT NULL,
  `condition` varchar(45) DEFAULT NULL,
  `extendedExplanation` varchar(45) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `SiriusTech`
--

DROP TABLE IF EXISTS `SiriusTech`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `SiriusTech` (
  `id` int(11) NOT NULL,
  `BZERO` varchar(45) DEFAULT NULL,
  `BSCALE` varchar(45) DEFAULT NULL,
  `HEAD` varchar(45) DEFAULT NULL,
  `IMGRECT` varchar(45) DEFAULT NULL,
  `HBIN` varchar(45) DEFAULT NULL,
  `VBIN` varchar(45) DEFAULT NULL,
  `SUBRECT` varchar(45) DEFAULT NULL,
  `DATATYPE` varchar(45) DEFAULT NULL,
  `XTYPE` varchar(45) DEFAULT NULL,
  `XUNIT` varchar(45) DEFAULT NULL,
  `RAYWAVE` varchar(45) DEFAULT NULL,
  `CALBWVNM` varchar(45) DEFAULT NULL,
  `TRIGGER` varchar(45) DEFAULT NULL,
  `CALIB` varchar(45) DEFAULT NULL,
  `DLLVER` varchar(45) DEFAULT NULL,
  `EXPOSURE` varchar(45) DEFAULT NULL,
  `TEMP` varchar(45) DEFAULT NULL,
  `READTIME` varchar(45) DEFAULT NULL,
  `OPERATN` varchar(45) DEFAULT NULL,
  `GAIN` varchar(45) DEFAULT NULL,
  `EMREALGN` varchar(45) DEFAULT NULL,
  `VCLKAMP` varchar(45) DEFAULT NULL,
  `VSHIFT` varchar(45) DEFAULT NULL,
  `OUTPTAMP` varchar(45) DEFAULT NULL,
  `PREAMP` varchar(45) DEFAULT NULL,
  `SERNO` varchar(45) DEFAULT NULL,
  `UNSTTEMP` varchar(45) DEFAULT NULL,
  `BLCLAMP` varchar(45) DEFAULT NULL,
  `PRECAN` varchar(45) DEFAULT NULL,
  `FLIPX` varchar(45) DEFAULT NULL,
  `FLIPY` varchar(45) DEFAULT NULL,
  `CNTCVTMD` varchar(45) DEFAULT NULL,
  `CNTCVT` varchar(45) DEFAULT NULL,
  `DTNWLGTH` varchar(45) DEFAULT NULL,
  `SNTVTY` varchar(45) DEFAULT NULL,
  `SPSNFLTR` varchar(45) DEFAULT NULL,
  `THRSHLD` varchar(45) DEFAULT NULL,
  `PCNTENLD` varchar(45) DEFAULT NULL,
  `NSETHSLD` varchar(45) DEFAULT NULL,
  `AVGFTRMD` varchar(45) DEFAULT NULL,
  `AVGFCTR` varchar(45) DEFAULT NULL,
  `FRMCNT` varchar(45) DEFAULT NULL,
  `PORTMODE` varchar(45) DEFAULT NULL,
  `LSHEIGHT` varchar(45) DEFAULT NULL,
  `LSSPEED` varchar(45) DEFAULT NULL,
  `LSALTDIR` varchar(45) DEFAULT NULL,
  `LSCTRL` varchar(45) DEFAULT NULL,
  `LSDIR` varchar(45) DEFAULT NULL,
  `FKSMODE` varchar(45) DEFAULT NULL,
  `FKTMODE` varchar(45) DEFAULT NULL,
  `DATE` varchar(45) DEFAULT NULL,
  `FRAME` varchar(45) DEFAULT NULL,
  `ESHTMODE` varchar(45) DEFAULT NULL,
  `IRIGDATA` varchar(45) DEFAULT NULL,
  `AIRMASS` varchar(45) DEFAULT NULL,
  `DATE-OBS` varchar(45) DEFAULT NULL,
  `DOMEPOS` varchar(45) DEFAULT NULL,
  `FILTERA` varchar(45) DEFAULT NULL,
  `FILTERB` varchar(45) DEFAULT NULL,
  `GPS-INT` varchar(45) DEFAULT NULL,
  `GPSSTART` varchar(45) DEFAULT NULL,
  `HA` varchar(45) DEFAULT NULL,
  `HUMIDIT` varchar(45) DEFAULT NULL,
  `INSTANGL` varchar(45) DEFAULT NULL,
  `INSTRUME` varchar(45) DEFAULT NULL,
  `INSTSWV` varchar(45) DEFAULT NULL,
  `OBJDEC` varchar(45) DEFAULT NULL,
  `OBJECT` varchar(45) DEFAULT NULL,
  `OBJEPOCH` varchar(45) DEFAULT NULL,
  `OBJEQUIN` varchar(45) DEFAULT NULL,
  `OBJRA` varchar(45) DEFAULT NULL,
  `OBSERVER` varchar(45) DEFAULT NULL,
  `OBSTYPE` varchar(45) DEFAULT NULL,
  `POSA` varchar(45) DEFAULT NULL,
  `POSB` varchar(45) DEFAULT NULL,
  `RELSKYT` varchar(45) DEFAULT NULL,
  `SEEING` varchar(45) DEFAULT NULL,
  `TELDEC` varchar(45) DEFAULT NULL,
  `TELESCOP` varchar(45) DEFAULT NULL,
  `TELFOCUS` varchar(45) DEFAULT NULL,
  `TELRA` varchar(45) DEFAULT NULL,
  `TMTDEW` varchar(45) DEFAULT NULL,
  `WHEELA` varchar(45) DEFAULT NULL,
  `WHEELB` varchar(45) DEFAULT NULL,
  `WIND` varchar(45) DEFAULT NULL,
  `ZD` varchar(45) DEFAULT NULL,
  `SHOC_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_SHOC_TECH_SHOC1_idx` (`SHOC_id`),
  CONSTRAINT `fk_SHOC_TECH_SHOC10` FOREIGN KEY (`SHOC_id`) REFERENCES `SHOC` (`id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `SpupnicTech`
--

DROP TABLE IF EXISTS `SpupnicTech`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `SpupnicTech` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `u-start` varchar(45) DEFAULT NULL,
  `lc-start` varchar(45) DEFAULT NULL,
  `hbin` varchar(45) DEFAULT NULL,
  `vbin` varchar(45) DEFAULT NULL,
  `slitpos` varchar(45) DEFAULT NULL,
  `slitwid` varchar(45) DEFAULT NULL,
  `frame` varchar(45) DEFAULT NULL,
  `binning` varchar(45) DEFAULT NULL,
  `ccd-sum` varchar(45) DEFAULT NULL,
  `sgain` varchar(45) DEFAULT NULL,
  `srd-noise` varchar(45) DEFAULT NULL,
  `ccd-temp` varchar(45) DEFAULT NULL,
  `cf-temp` varchar(45) DEFAULT NULL,
  `focus-pos` varchar(45) DEFAULT NULL,
  `hart-pos` varchar(45) DEFAULT NULL,
  `hart-seq` varchar(45) DEFAULT NULL,
  `SPUPNIC_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_SPUPNIC_TECH_SPUPNIC1_idx` (`SPUPNIC_id`),
  CONSTRAINT `fk_SPUPNIC_TECH_SPUPNIC1` FOREIGN KEY (`SPUPNIC_id`) REFERENCES `SPUPNIC` (`id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `SteTech`
--

DROP TABLE IF EXISTS `SteTech`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `SteTech` (
  `id` int(11) NOT NULL,
  `BZERO` varchar(45) DEFAULT NULL,
  `BSCALE` varchar(45) DEFAULT NULL,
  `HEAD` varchar(45) DEFAULT NULL,
  `IMGRECT` varchar(45) DEFAULT NULL,
  `HBIN` varchar(45) DEFAULT NULL,
  `VBIN` varchar(45) DEFAULT NULL,
  `SUBRECT` varchar(45) DEFAULT NULL,
  `DATATYPE` varchar(45) DEFAULT NULL,
  `XTYPE` varchar(45) DEFAULT NULL,
  `XUNIT` varchar(45) DEFAULT NULL,
  `RAYWAVE` varchar(45) DEFAULT NULL,
  `CALBWVNM` varchar(45) DEFAULT NULL,
  `TRIGGER` varchar(45) DEFAULT NULL,
  `CALIB` varchar(45) DEFAULT NULL,
  `DLLVER` varchar(45) DEFAULT NULL,
  `EXPOSURE` varchar(45) DEFAULT NULL,
  `TEMP` varchar(45) DEFAULT NULL,
  `READTIME` varchar(45) DEFAULT NULL,
  `OPERATN` varchar(45) DEFAULT NULL,
  `GAIN` varchar(45) DEFAULT NULL,
  `EMREALGN` varchar(45) DEFAULT NULL,
  `VCLKAMP` varchar(45) DEFAULT NULL,
  `VSHIFT` varchar(45) DEFAULT NULL,
  `OUTPTAMP` varchar(45) DEFAULT NULL,
  `PREAMP` varchar(45) DEFAULT NULL,
  `SERNO` varchar(45) DEFAULT NULL,
  `UNSTTEMP` varchar(45) DEFAULT NULL,
  `BLCLAMP` varchar(45) DEFAULT NULL,
  `PRECAN` varchar(45) DEFAULT NULL,
  `FLIPX` varchar(45) DEFAULT NULL,
  `FLIPY` varchar(45) DEFAULT NULL,
  `CNTCVTMD` varchar(45) DEFAULT NULL,
  `CNTCVT` varchar(45) DEFAULT NULL,
  `DTNWLGTH` varchar(45) DEFAULT NULL,
  `SNTVTY` varchar(45) DEFAULT NULL,
  `SPSNFLTR` varchar(45) DEFAULT NULL,
  `THRSHLD` varchar(45) DEFAULT NULL,
  `PCNTENLD` varchar(45) DEFAULT NULL,
  `NSETHSLD` varchar(45) DEFAULT NULL,
  `AVGFTRMD` varchar(45) DEFAULT NULL,
  `AVGFCTR` varchar(45) DEFAULT NULL,
  `FRMCNT` varchar(45) DEFAULT NULL,
  `PORTMODE` varchar(45) DEFAULT NULL,
  `LSHEIGHT` varchar(45) DEFAULT NULL,
  `LSSPEED` varchar(45) DEFAULT NULL,
  `LSALTDIR` varchar(45) DEFAULT NULL,
  `LSCTRL` varchar(45) DEFAULT NULL,
  `LSDIR` varchar(45) DEFAULT NULL,
  `FKSMODE` varchar(45) DEFAULT NULL,
  `FKTMODE` varchar(45) DEFAULT NULL,
  `DATE` varchar(45) DEFAULT NULL,
  `FRAME` varchar(45) DEFAULT NULL,
  `ESHTMODE` varchar(45) DEFAULT NULL,
  `IRIGDATA` varchar(45) DEFAULT NULL,
  `AIRMASS` varchar(45) DEFAULT NULL,
  `DATE-OBS` varchar(45) DEFAULT NULL,
  `DOMEPOS` varchar(45) DEFAULT NULL,
  `FILTERA` varchar(45) DEFAULT NULL,
  `FILTERB` varchar(45) DEFAULT NULL,
  `GPS-INT` varchar(45) DEFAULT NULL,
  `GPSSTART` varchar(45) DEFAULT NULL,
  `HA` varchar(45) DEFAULT NULL,
  `HUMIDIT` varchar(45) DEFAULT NULL,
  `INSTANGL` varchar(45) DEFAULT NULL,
  `INSTRUME` varchar(45) DEFAULT NULL,
  `INSTSWV` varchar(45) DEFAULT NULL,
  `OBJDEC` varchar(45) DEFAULT NULL,
  `OBJECT` varchar(45) DEFAULT NULL,
  `OBJEPOCH` varchar(45) DEFAULT NULL,
  `OBJEQUIN` varchar(45) DEFAULT NULL,
  `OBJRA` varchar(45) DEFAULT NULL,
  `OBSERVER` varchar(45) DEFAULT NULL,
  `OBSTYPE` varchar(45) DEFAULT NULL,
  `POSA` varchar(45) DEFAULT NULL,
  `POSB` varchar(45) DEFAULT NULL,
  `RELSKYT` varchar(45) DEFAULT NULL,
  `SEEING` varchar(45) DEFAULT NULL,
  `TELDEC` varchar(45) DEFAULT NULL,
  `TELESCOP` varchar(45) DEFAULT NULL,
  `TELFOCUS` varchar(45) DEFAULT NULL,
  `TELRA` varchar(45) DEFAULT NULL,
  `TMTDEW` varchar(45) DEFAULT NULL,
  `WHEELA` varchar(45) DEFAULT NULL,
  `WHEELB` varchar(45) DEFAULT NULL,
  `WIND` varchar(45) DEFAULT NULL,
  `ZD` varchar(45) DEFAULT NULL,
  `SHOC_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_SHOC_TECH_SHOC1_idx` (`SHOC_id`),
  CONSTRAINT `fk_SHOC_TECH_SHOC13` FOREIGN KEY (`SHOC_id`) REFERENCES `SHOC` (`id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Target`
--

DROP TABLE IF EXISTS `Target`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Target` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) DEFAULT NULL,
  `rightAscension` varchar(255) DEFAULT NULL,
  `declination` varchar(255) DEFAULT NULL,
  `position` varchar(255) DEFAULT NULL,
  `targetTypeId` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `TargetType`
--

DROP TABLE IF EXISTS `TargetType`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `TargetType` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `numericValue` varchar(45) DEFAULT NULL,
  `explanation` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Telescope`
--

DROP TABLE IF EXISTS `Telescope`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Telescope` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `telescopeName` varchar(45) NOT NULL,
  `ownerId` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `User`
--

DROP TABLE IF EXISTS `User`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `User` (
  `id` int(11) NOT NULL,
  `institutionId` varchar(45) DEFAULT NULL,
  `institutionUserId` varchar(45) DEFAULT NULL,
  `givenName` varchar(45) DEFAULT NULL,
  `familyName` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `WINCAM`
--

DROP TABLE IF EXISTS `WINCAM`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `WINCAM` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `telescopeName` varchar(45) DEFAULT NULL,
  `date` varchar(45) DEFAULT NULL,
  `observer` varchar(45) DEFAULT NULL,
  `objectName` varchar(45) DEFAULT NULL,
  `exposureMode` varchar(45) DEFAULT NULL,
  `filter` varchar(45) DEFAULT NULL,
  `humidity` varchar(45) DEFAULT NULL,
  `rotater` varchar(45) DEFAULT NULL,
  `telFocus` varchar(45) DEFAULT NULL,
  `wheelA` varchar(45) DEFAULT NULL,
  `wheelB` varchar(45) DEFAULT NULL,
  `zenith` varchar(45) DEFAULT NULL,
  `headModel` varchar(45) DEFAULT NULL,
  `acquisitionMode` varchar(45) DEFAULT NULL,
  `readMode` varchar(45) DEFAULT NULL,
  `imageRect` varchar(45) DEFAULT NULL,
  `hbin` varchar(45) DEFAULT NULL,
  `vbin` varchar(45) DEFAULT NULL,
  `exposure` varchar(45) DEFAULT NULL,
  `serialNumber` varchar(45) DEFAULT NULL,
  `filterA` varchar(45) DEFAULT NULL,
  `filterB` varchar(45) DEFAULT NULL,
  `hourAngle` varchar(45) DEFAULT NULL,
  `instrumentAngle` varchar(45) DEFAULT NULL,
  `triggers` varchar(45) DEFAULT NULL,
  `instrumentName` varchar(45) DEFAULT NULL,
  `Observation_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_SHOC_Observation1_idx` (`Observation_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `WINCAM_TECH`
--

DROP TABLE IF EXISTS `WINCAM_TECH`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `WINCAM_TECH` (
  `id` int(11) NOT NULL,
  `BZERO` varchar(45) DEFAULT NULL,
  `BSCALE` varchar(45) DEFAULT NULL,
  `HEAD` varchar(45) DEFAULT NULL,
  `IMGRECT` varchar(45) DEFAULT NULL,
  `HBIN` varchar(45) DEFAULT NULL,
  `VBIN` varchar(45) DEFAULT NULL,
  `SUBRECT` varchar(45) DEFAULT NULL,
  `DATATYPE` varchar(45) DEFAULT NULL,
  `XTYPE` varchar(45) DEFAULT NULL,
  `XUNIT` varchar(45) DEFAULT NULL,
  `RAYWAVE` varchar(45) DEFAULT NULL,
  `CALBWVNM` varchar(45) DEFAULT NULL,
  `TRIGGER` varchar(45) DEFAULT NULL,
  `CALIB` varchar(45) DEFAULT NULL,
  `DLLVER` varchar(45) DEFAULT NULL,
  `EXPOSURE` varchar(45) DEFAULT NULL,
  `TEMP` varchar(45) DEFAULT NULL,
  `READTIME` varchar(45) DEFAULT NULL,
  `OPERATN` varchar(45) DEFAULT NULL,
  `GAIN` varchar(45) DEFAULT NULL,
  `EMREALGN` varchar(45) DEFAULT NULL,
  `VCLKAMP` varchar(45) DEFAULT NULL,
  `VSHIFT` varchar(45) DEFAULT NULL,
  `OUTPTAMP` varchar(45) DEFAULT NULL,
  `PREAMP` varchar(45) DEFAULT NULL,
  `SERNO` varchar(45) DEFAULT NULL,
  `UNSTTEMP` varchar(45) DEFAULT NULL,
  `BLCLAMP` varchar(45) DEFAULT NULL,
  `PRECAN` varchar(45) DEFAULT NULL,
  `FLIPX` varchar(45) DEFAULT NULL,
  `FLIPY` varchar(45) DEFAULT NULL,
  `CNTCVTMD` varchar(45) DEFAULT NULL,
  `CNTCVT` varchar(45) DEFAULT NULL,
  `DTNWLGTH` varchar(45) DEFAULT NULL,
  `SNTVTY` varchar(45) DEFAULT NULL,
  `SPSNFLTR` varchar(45) DEFAULT NULL,
  `THRSHLD` varchar(45) DEFAULT NULL,
  `PCNTENLD` varchar(45) DEFAULT NULL,
  `NSETHSLD` varchar(45) DEFAULT NULL,
  `AVGFTRMD` varchar(45) DEFAULT NULL,
  `AVGFCTR` varchar(45) DEFAULT NULL,
  `FRMCNT` varchar(45) DEFAULT NULL,
  `PORTMODE` varchar(45) DEFAULT NULL,
  `LSHEIGHT` varchar(45) DEFAULT NULL,
  `LSSPEED` varchar(45) DEFAULT NULL,
  `LSALTDIR` varchar(45) DEFAULT NULL,
  `LSCTRL` varchar(45) DEFAULT NULL,
  `LSDIR` varchar(45) DEFAULT NULL,
  `FKSMODE` varchar(45) DEFAULT NULL,
  `FKTMODE` varchar(45) DEFAULT NULL,
  `DATE` varchar(45) DEFAULT NULL,
  `FRAME` varchar(45) DEFAULT NULL,
  `ESHTMODE` varchar(45) DEFAULT NULL,
  `IRIGDATA` varchar(45) DEFAULT NULL,
  `AIRMASS` varchar(45) DEFAULT NULL,
  `DATE-OBS` varchar(45) DEFAULT NULL,
  `DOMEPOS` varchar(45) DEFAULT NULL,
  `FILTERA` varchar(45) DEFAULT NULL,
  `FILTERB` varchar(45) DEFAULT NULL,
  `GPS-INT` varchar(45) DEFAULT NULL,
  `GPSSTART` varchar(45) DEFAULT NULL,
  `HA` varchar(45) DEFAULT NULL,
  `HUMIDIT` varchar(45) DEFAULT NULL,
  `INSTANGL` varchar(45) DEFAULT NULL,
  `INSTRUME` varchar(45) DEFAULT NULL,
  `INSTSWV` varchar(45) DEFAULT NULL,
  `OBJDEC` varchar(45) DEFAULT NULL,
  `OBJECT` varchar(45) DEFAULT NULL,
  `OBJEPOCH` varchar(45) DEFAULT NULL,
  `OBJEQUIN` varchar(45) DEFAULT NULL,
  `OBJRA` varchar(45) DEFAULT NULL,
  `OBSERVER` varchar(45) DEFAULT NULL,
  `OBSTYPE` varchar(45) DEFAULT NULL,
  `POSA` varchar(45) DEFAULT NULL,
  `POSB` varchar(45) DEFAULT NULL,
  `RELSKYT` varchar(45) DEFAULT NULL,
  `SEEING` varchar(45) DEFAULT NULL,
  `TELDEC` varchar(45) DEFAULT NULL,
  `TELESCOP` varchar(45) DEFAULT NULL,
  `TELFOCUS` varchar(45) DEFAULT NULL,
  `TELRA` varchar(45) DEFAULT NULL,
  `TMTDEW` varchar(45) DEFAULT NULL,
  `WHEELA` varchar(45) DEFAULT NULL,
  `WHEELB` varchar(45) DEFAULT NULL,
  `WIND` varchar(45) DEFAULT NULL,
  `ZD` varchar(45) DEFAULT NULL,
  `SHOC_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_SHOC_TECH_SHOC1_idx` (`SHOC_id`),
  CONSTRAINT `fk_SHOC_TECH_SHOC11` FOREIGN KEY (`SHOC_id`) REFERENCES `SHOC` (`id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `testdata`
--

DROP TABLE IF EXISTS `testdata`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE testdata (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `filename` varchar(45) DEFAULT NULL,
  `categoryID` varchar(45) DEFAULT NULL,
  `targetID` varchar(45) DEFAULT NULL,
  `startTime` varchar(45) DEFAULT NULL,
  `filesize` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping events for database 'ssda'
--
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2019-05-10  9:57:43
