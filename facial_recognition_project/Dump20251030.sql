-- MySQL dump 10.13  Distrib 8.0.41, for Win64 (x86_64)
--
-- Host: 127.0.0.1    Database: face_recognition_db
-- ------------------------------------------------------
-- Server version	8.0.41

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `contacts`
--

DROP TABLE IF EXISTS `contacts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `contacts` (
  `contact_id` int NOT NULL AUTO_INCREMENT,
  `personal_id` int NOT NULL,
  `phone_number` varchar(20) DEFAULT NULL,
  `email` text,
  PRIMARY KEY (`contact_id`),
  KEY `personal_id` (`personal_id`),
  CONSTRAINT `contacts_ibfk_1` FOREIGN KEY (`personal_id`) REFERENCES `patients` (`personal_id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `contacts`
--

LOCK TABLES `contacts` WRITE;
/*!40000 ALTER TABLE `contacts` DISABLE KEYS */;
INSERT INTO `contacts` VALUES (1,1003,'N/A','N/A');
/*!40000 ALTER TABLE `contacts` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `health_issues`
--

DROP TABLE IF EXISTS `health_issues`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `health_issues` (
  `issue_id` int NOT NULL AUTO_INCREMENT,
  `personal_id` int NOT NULL,
  `issue_name` varchar(100) DEFAULT NULL,
  `diagnosed_date` date DEFAULT NULL,
  `status` enum('Active','Resolved','Chronic') DEFAULT NULL,
  `description` text,
  PRIMARY KEY (`issue_id`),
  KEY `personal_id` (`personal_id`),
  CONSTRAINT `health_issues_ibfk_1` FOREIGN KEY (`personal_id`) REFERENCES `patients` (`personal_id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `health_issues`
--

LOCK TABLES `health_issues` WRITE;
/*!40000 ALTER TABLE `health_issues` DISABLE KEYS */;
INSERT INTO `health_issues` VALUES (1,1003,'Healthy','2025-09-02','Active','Initial record');
/*!40000 ALTER TABLE `health_issues` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `medication`
--

DROP TABLE IF EXISTS `medication`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `medication` (
  `medication_id` int NOT NULL AUTO_INCREMENT,
  `personal_id` int NOT NULL,
  `medication_name` varchar(100) DEFAULT NULL,
  `dosage` varchar(50) DEFAULT NULL,
  `frequency` varchar(50) DEFAULT NULL,
  `start_date` date DEFAULT NULL,
  `end_date` date DEFAULT NULL,
  `status` enum('ongoing','completed','discontinued') DEFAULT NULL,
  `type` enum('taken','prescribed') DEFAULT NULL,
  `notes` text,
  PRIMARY KEY (`medication_id`),
  KEY `personal_id` (`personal_id`),
  CONSTRAINT `medication_ibfk_1` FOREIGN KEY (`personal_id`) REFERENCES `patients` (`personal_id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `medication`
--

LOCK TABLES `medication` WRITE;
/*!40000 ALTER TABLE `medication` DISABLE KEYS */;
INSERT INTO `medication` VALUES (1,1003,'None','N/A','N/A',NULL,NULL,'ongoing','prescribed','Initial record');
/*!40000 ALTER TABLE `medication` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `patients`
--

DROP TABLE IF EXISTS `patients`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `patients` (
  `personal_id` int NOT NULL AUTO_INCREMENT,
  `first_name` varchar(100) NOT NULL,
  `middle_name` varchar(100) DEFAULT NULL,
  `last_name` varchar(100) NOT NULL,
  `age` int NOT NULL,
  `sex` enum('Male','Female','Other') NOT NULL,
  `sex_other` varchar(50) DEFAULT NULL,
  `last_login` datetime DEFAULT NULL,
  PRIMARY KEY (`personal_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1004 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `patients`
--

LOCK TABLES `patients` WRITE;
/*!40000 ALTER TABLE `patients` DISABLE KEYS */;
INSERT INTO `patients` VALUES (1003,'Phuc','','Nguyen',0,'Other',NULL,NULL);
/*!40000 ALTER TABLE `patients` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `relatives_contacts`
--

DROP TABLE IF EXISTS `relatives_contacts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `relatives_contacts` (
  `relative_id` int NOT NULL AUTO_INCREMENT,
  `personal_id` int NOT NULL,
  `relative_first_name` varchar(100) DEFAULT NULL,
  `relative_last_name` varchar(100) DEFAULT NULL,
  `relationship_type` varchar(50) DEFAULT NULL,
  `phone_number` varchar(20) DEFAULT NULL,
  `email` text,
  `thumbnail` blob,
  `full_image_path` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`relative_id`),
  KEY `fk_personal` (`personal_id`),
  CONSTRAINT `fk_personal` FOREIGN KEY (`personal_id`) REFERENCES `patients` (`personal_id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `relatives_contacts`
--

LOCK TABLES `relatives_contacts` WRITE;
/*!40000 ALTER TABLE `relatives_contacts` DISABLE KEYS */;
INSERT INTO `relatives_contacts` VALUES (1,1003,'N/A','N/A','N/A','N/A','N/A',NULL,NULL);
/*!40000 ALTER TABLE `relatives_contacts` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `symptom_table`
--

DROP TABLE IF EXISTS `symptom_table`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `symptom_table` (
  `symptom_id` int NOT NULL AUTO_INCREMENT,
  `personal_id` int NOT NULL,
  `symptom_name` varchar(50) DEFAULT NULL,
  `start_date` date DEFAULT NULL,
  `status` enum('ongoing','resolved') DEFAULT NULL,
  `notes` text,
  PRIMARY KEY (`symptom_id`),
  KEY `personal_id` (`personal_id`),
  CONSTRAINT `symptom_table_ibfk_1` FOREIGN KEY (`personal_id`) REFERENCES `patients` (`personal_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `symptom_table`
--

LOCK TABLES `symptom_table` WRITE;
/*!40000 ALTER TABLE `symptom_table` DISABLE KEYS */;
/*!40000 ALTER TABLE `symptom_table` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-10-30 22:31:15
