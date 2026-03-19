-- ============================================================
-- Alzheimer Care - Face Recognition Database Schema
-- Run this script once to set up the database
-- ============================================================

CREATE DATABASE IF NOT EXISTS face_recognition_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE face_recognition_db;

-- ── Patients table ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS patients (
    personal_id   INT           NOT NULL AUTO_INCREMENT,
    first_name    VARCHAR(50)   NOT NULL,
    middle_name   VARCHAR(50)   DEFAULT NULL,
    last_name     VARCHAR(50)   NOT NULL,
    age           TINYINT       UNSIGNED NOT NULL,
    sex           ENUM('M','F','Other') NOT NULL DEFAULT 'M',
    sex_other     VARCHAR(100)  DEFAULT NULL,
    last_login    DATETIME      DEFAULT CURRENT_TIMESTAMP,
    created_at    DATETIME      DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (personal_id)
) ENGINE=InnoDB;

-- ── Contacts table ─────────────────────────────────────────
-- FIX: personal_id is a FK to patients, not an auto-increment
CREATE TABLE IF NOT EXISTS contacts (
    contact_id    INT           NOT NULL AUTO_INCREMENT,
    personal_id   INT           NOT NULL,
    phone_number  VARCHAR(25)   DEFAULT NULL,
    email         VARCHAR(120)  DEFAULT NULL,
    PRIMARY KEY (contact_id),
    CONSTRAINT fk_contacts_patient
        FOREIGN KEY (personal_id) REFERENCES patients(personal_id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ── Relatives/Contacts table ────────────────────────────────
-- FIX: relative_id is AUTO_INCREMENT (do NOT pass it from Python)
CREATE TABLE IF NOT EXISTS relatives_contacts (
    relative_id           INT            NOT NULL AUTO_INCREMENT,
    personal_id           INT            NOT NULL,           -- FK to patients
    relative_first_name   VARCHAR(50)    NOT NULL,
    relative_last_name    VARCHAR(50)    NOT NULL,
    relationship_type     VARCHAR(60)    NOT NULL,
    phone_number          VARCHAR(25)    DEFAULT NULL,
    email                 VARCHAR(120)   DEFAULT NULL,
    thumbnail             MEDIUMBLOB     DEFAULT NULL,       -- 100×100 JPEG bytes
    full_image_path       VARCHAR(300)   DEFAULT NULL,
    added_at              DATETIME       DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (relative_id),
    CONSTRAINT fk_relative_patient
        FOREIGN KEY (personal_id) REFERENCES patients(personal_id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ── Optional: sample data (comment out for production) ─────
/*
INSERT INTO patients (first_name, last_name, age, sex, last_login)
VALUES ('John', 'Doe', 78, 'M', NOW());

INSERT INTO contacts (personal_id, phone_number, email)
VALUES (1, '+1-555-0100', 'john.doe@example.com');

INSERT INTO relatives_contacts (personal_id, relative_first_name, relative_last_name, relationship_type, phone_number)
VALUES (1, 'Jane', 'Doe', 'Spouse', '+1-555-0101');
*/

SELECT 'Database schema created successfully.' AS status;
