-- MySQL dump 10.13  Distrib 5.7.30, for Linux (x86_64)
--
-- Host: localhost    Database: django_db
-- ------------------------------------------------------
-- Server version	5.7.30-0ubuntu0.18.04.1

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
-- Table structure for table `EMA_answer`
--

DROP TABLE IF EXISTS `EMA_answer`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `EMA_answer` (
  `ID` varchar(36) NOT NULL,
  `AnswerKey` varchar(36) NOT NULL,
  `Question_id` varchar(36) NOT NULL,
  `Questionnaire_id` varchar(36) NOT NULL,
  PRIMARY KEY (`ID`),
  KEY `EMA_answer_Question_id_a292b94d_fk_EMA_question_ID` (`Question_id`),
  KEY `EMA_answer_Questionnaire_id_dd28145f_fk_EMA_questionnaire_ID` (`Questionnaire_id`),
  CONSTRAINT `EMA_answer_Question_id_a292b94d_fk_EMA_question_ID` FOREIGN KEY (`Question_id`) REFERENCES `EMA_question` (`ID`),
  CONSTRAINT `EMA_answer_Questionnaire_id_dd28145f_fk_EMA_questionnaire_ID` FOREIGN KEY (`Questionnaire_id`) REFERENCES `EMA_questionnaire` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `EMA_authorization`
--

DROP TABLE IF EXISTS `EMA_authorization`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `EMA_authorization` (
  `ID` varchar(36) NOT NULL,
  `AllowRead` tinyint(1) NOT NULL,
  `AllowWrite` tinyint(1) NOT NULL,
  `Feature_id` varchar(36) NOT NULL,
  `UserGroup_id` varchar(36) NOT NULL,
  PRIMARY KEY (`ID`),
  KEY `EMA_authorization_Feature_id_3c65a007_fk_EMA_feature_ID` (`Feature_id`),
  KEY `EMA_authorization_UserGroup_id_ddda967e_fk_EMA_usergroup_ID` (`UserGroup_id`),
  CONSTRAINT `EMA_authorization_Feature_id_3c65a007_fk_EMA_feature_ID` FOREIGN KEY (`Feature_id`) REFERENCES `EMA_feature` (`ID`),
  CONSTRAINT `EMA_authorization_UserGroup_id_ddda967e_fk_EMA_usergroup_ID` FOREIGN KEY (`UserGroup_id`) REFERENCES `EMA_usergroup` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `EMA_datachunk`
--

DROP TABLE IF EXISTS `EMA_datachunk`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `EMA_datachunk` (
  `ID` varchar(36) NOT NULL,
  `Subject` varchar(36) NOT NULL,
  `Start` datetime(6) NOT NULL,
  `End` datetime(6) NOT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `EMA_feature`
--

DROP TABLE IF EXISTS `EMA_feature`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `EMA_feature` (
  `ID` varchar(36) NOT NULL,
  `Name` varchar(255) NOT NULL,
  `Description` varchar(2048) NOT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `EMA_feature_FileTypes`
--

DROP TABLE IF EXISTS `EMA_feature_FileTypes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `EMA_feature_FileTypes` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `feature_id` varchar(36) NOT NULL,
  `filetype_id` varchar(36) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `EMA_feature_FileTypes_feature_id_filetype_id_973b7cb3_uniq` (`feature_id`,`filetype_id`),
  KEY `EMA_feature_FileTypes_filetype_id_4c06dbe4_fk_EMA_filetype_ID` (`filetype_id`),
  CONSTRAINT `EMA_feature_FileTypes_feature_id_d440804f_fk_EMA_feature_ID` FOREIGN KEY (`feature_id`) REFERENCES `EMA_feature` (`ID`),
  CONSTRAINT `EMA_feature_FileTypes_filetype_id_4c06dbe4_fk_EMA_filetype_ID` FOREIGN KEY (`filetype_id`) REFERENCES `EMA_filetype` (`ID`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `EMA_featurevalue`
--

DROP TABLE IF EXISTS `EMA_featurevalue`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `EMA_featurevalue` (
  `ID` varchar(36) NOT NULL,
  `Start` datetime(6) NOT NULL,
  `End` datetime(6) NOT NULL,
  `LastUpdate` datetime(6) NOT NULL,
  `Side` varchar(36) NOT NULL,
  `Value` double NOT NULL,
  `isValid` tinyint(1) NOT NULL,
  `DataChunk_id` varchar(36) NOT NULL,
  `Feature_id` varchar(36) NOT NULL,
  PRIMARY KEY (`ID`),
  KEY `EMA_featurevalue_DataChunk_id_3f24cf80_fk_EMA_datachunk_ID` (`DataChunk_id`),
  KEY `EMA_featurevalue_Feature_id_7d92e786_fk_EMA_feature_ID` (`Feature_id`),
  CONSTRAINT `EMA_featurevalue_DataChunk_id_3f24cf80_fk_EMA_datachunk_ID` FOREIGN KEY (`DataChunk_id`) REFERENCES `EMA_datachunk` (`ID`),
  CONSTRAINT `EMA_featurevalue_Feature_id_7d92e786_fk_EMA_feature_ID` FOREIGN KEY (`Feature_id`) REFERENCES `EMA_feature` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `EMA_file`
--

DROP TABLE IF EXISTS `EMA_file`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `EMA_file` (
  `ID` varchar(36) NOT NULL,
  `Filename` varchar(255) NOT NULL,
  `LastUpdate` datetime(6) NOT NULL,
  `isValid` tinyint(1) NOT NULL,
  `DataChunk_id` varchar(36) NOT NULL,
  `FileType_id` varchar(36) NOT NULL,
  PRIMARY KEY (`ID`),
  KEY `EMA_file_DataChunk_id_d48164c7_fk_EMA_datachunk_ID` (`DataChunk_id`),
  KEY `EMA_file_FileType_id_78bbe6eb_fk_EMA_filetype_ID` (`FileType_id`),
  CONSTRAINT `EMA_file_DataChunk_id_d48164c7_fk_EMA_datachunk_ID` FOREIGN KEY (`DataChunk_id`) REFERENCES `EMA_datachunk` (`ID`),
  CONSTRAINT `EMA_file_FileType_id_78bbe6eb_fk_EMA_filetype_ID` FOREIGN KEY (`FileType_id`) REFERENCES `EMA_filetype` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `EMA_filetype`
--

DROP TABLE IF EXISTS `EMA_filetype`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `EMA_filetype` (
  `ID` varchar(36) NOT NULL,
  `FileExtension` varchar(255) NOT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `EMA_question`
--

DROP TABLE IF EXISTS `EMA_question`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `EMA_question` (
  `ID` varchar(36) NOT NULL,
  `QuestionKey` varchar(36) NOT NULL,
  PRIMARY KEY (`ID`),
  UNIQUE KEY `QuestionKey` (`QuestionKey`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `EMA_questionnaire`
--

DROP TABLE IF EXISTS `EMA_questionnaire`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `EMA_questionnaire` (
  `ID` varchar(36) NOT NULL,
  `Motivation` varchar(255) NOT NULL,
  `Filename` varchar(255) NOT NULL,
  `SurveyFile` varchar(255) NOT NULL,
  `Start` datetime(6) NOT NULL,
  `End` datetime(6) NOT NULL,
  `device` varchar(255) NOT NULL,
  `app_version` varchar(255) NOT NULL,
  `DataChunk_id` varchar(36) NOT NULL,
  PRIMARY KEY (`ID`),
  KEY `EMA_questionnaire_DataChunk_id_e0e3ca07_fk_EMA_datachunk_ID` (`DataChunk_id`),
  CONSTRAINT `EMA_questionnaire_DataChunk_id_e0e3ca07_fk_EMA_datachunk_ID` FOREIGN KEY (`DataChunk_id`) REFERENCES `EMA_datachunk` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `EMA_user`
--

DROP TABLE IF EXISTS `EMA_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `EMA_user` (
  `ID` varchar(36) NOT NULL,
  `Lastname` varchar(255) NOT NULL,
  `Forename` varchar(255) NOT NULL,
  `eMail` varchar(255) NOT NULL,
  `IsActive` tinyint(1) NOT NULL,
  `Login` varchar(255) NOT NULL,
  `Password` varchar(255) NOT NULL,
  `Allow_FileUpload` tinyint(1) NOT NULL,
  `UserGroup_id` varchar(36) NOT NULL,
  PRIMARY KEY (`ID`),
  UNIQUE KEY `Login` (`Login`),
  KEY `EMA_user_UserGroup_id_c34ea9e5_fk_EMA_usergroup_ID` (`UserGroup_id`),
  CONSTRAINT `EMA_user_UserGroup_id_c34ea9e5_fk_EMA_usergroup_ID` FOREIGN KEY (`UserGroup_id`) REFERENCES `EMA_usergroup` (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `EMA_usergroup`
--

DROP TABLE IF EXISTS `EMA_usergroup`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `EMA_usergroup` (
  `ID` varchar(36) NOT NULL,
  `Title` varchar(255) NOT NULL,
  `IsActive` tinyint(1) NOT NULL,
  PRIMARY KEY (`ID`),
  UNIQUE KEY `Title` (`Title`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2020-07-09 13:27:53
