-- =========================================================
-- MedFlow — MySQL 8.x DDL (Phase 1)
-- Run as a user with CREATE privileges on the target schema.
-- This file is DBA-owned: the app connects with ddl-auto=validate
-- equivalent behavior (SQLAlchemy never creates/alters tables at runtime).
-- =========================================================

CREATE DATABASE IF NOT EXISTS medflow CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE medflow;

-- Dedicated app user (adjust host/password before running in a real environment)
-- CREATE USER 'medflow_app'@'%' IDENTIFIED BY 'change-me';
-- GRANT SELECT, INSERT, UPDATE, DELETE ON medflow.* TO 'medflow_app'@'%';
-- FLUSH PRIVILEGES;

-- =========================================================
CREATE TABLE hospitals (
    hospital_id     BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name            VARCHAR(150) NOT NULL,
    address         VARCHAR(255),
    timezone        VARCHAR(50) NOT NULL DEFAULT 'America/Chicago',
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE departments (
    department_id   BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    hospital_id     BIGINT UNSIGNED NOT NULL,
    name            VARCHAR(150) NOT NULL,
    dept_type       ENUM('INPATIENT','OUTPATIENT','PHARMACY','INVENTORY','ADMISSIONS','ER') NOT NULL,
    CONSTRAINT fk_dept_hospital FOREIGN KEY (hospital_id) REFERENCES hospitals(hospital_id)
) ENGINE=InnoDB;

CREATE TABLE units (
    unit_id         BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    department_id   BIGINT UNSIGNED NOT NULL,
    name            VARCHAR(100) NOT NULL,
    floor           VARCHAR(20),
    capacity        INT NOT NULL DEFAULT 0,
    CONSTRAINT fk_unit_dept FOREIGN KEY (department_id) REFERENCES departments(department_id)
) ENGINE=InnoDB;

CREATE TABLE beds (
    bed_id          BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    unit_id         BIGINT UNSIGNED NOT NULL,
    bed_number      VARCHAR(20) NOT NULL,
    status          ENUM('AVAILABLE','OCCUPIED','CLEANING','OUT_OF_SERVICE') NOT NULL DEFAULT 'AVAILABLE',
    CONSTRAINT fk_bed_unit FOREIGN KEY (unit_id) REFERENCES units(unit_id),
    UNIQUE KEY uq_bed_per_unit (unit_id, bed_number)
) ENGINE=InnoDB;

CREATE TABLE staff (
    staff_id            BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    keycloak_user_id    VARCHAR(64) NOT NULL UNIQUE,
    hospital_id         BIGINT UNSIGNED NOT NULL,
    first_name          VARCHAR(100) NOT NULL,
    last_name            VARCHAR(100) NOT NULL,
    role                ENUM('PHYSICIAN','NURSE','PHARMACIST','ADMISSIONS','FINANCE','MANAGEMENT','LEGAL','ADMIN') NOT NULL,
    npi_number          VARCHAR(20),
    license_number      VARCHAR(50),
    active              BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT fk_staff_hospital FOREIGN KEY (hospital_id) REFERENCES hospitals(hospital_id)
) ENGINE=InnoDB;

CREATE TABLE patients (
    patient_id          BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    mrn                 VARCHAR(20) NOT NULL UNIQUE,
    first_name          VARCHAR(100) NOT NULL,
    last_name           VARCHAR(100) NOT NULL,
    dob                 DATE NOT NULL,
    sex                 ENUM('M','F','O','U') NOT NULL DEFAULT 'U',
    ssn_last4           VARCHAR(4),
    address             VARCHAR(255),
    phone               VARCHAR(30),
    primary_hospital_id BIGINT UNSIGNED NOT NULL,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_patient_hospital FOREIGN KEY (primary_hospital_id) REFERENCES hospitals(hospital_id)
) ENGINE=InnoDB;

CREATE TABLE encounters (
    encounter_id            BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    patient_id              BIGINT UNSIGNED NOT NULL,
    hospital_id             BIGINT UNSIGNED NOT NULL,
    encounter_type          ENUM('INPATIENT','OUTPATIENT','ER') NOT NULL,
    status                  ENUM('PLANNED','ARRIVED','IN_PROGRESS','DISCHARGED','CANCELLED') NOT NULL DEFAULT 'PLANNED',
    admit_datetime          DATETIME,
    discharge_datetime      DATETIME,
    attending_physician_id  BIGINT UNSIGNED,
    chief_complaint         VARCHAR(255),
    bed_id                  BIGINT UNSIGNED,
    CONSTRAINT fk_enc_patient FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
    CONSTRAINT fk_enc_hospital FOREIGN KEY (hospital_id) REFERENCES hospitals(hospital_id),
    CONSTRAINT fk_enc_physician FOREIGN KEY (attending_physician_id) REFERENCES staff(staff_id),
    CONSTRAINT fk_enc_bed FOREIGN KEY (bed_id) REFERENCES beds(bed_id)
) ENGINE=InnoDB;

CREATE TABLE diagnoses (
    diagnosis_id          BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    encounter_id          BIGINT UNSIGNED NOT NULL,
    icd10_code            VARCHAR(10) NOT NULL,
    description           VARCHAR(255),
    diagnosed_by_staff_id BIGINT UNSIGNED NOT NULL,
    diagnosed_at          DATETIME NOT NULL,
    CONSTRAINT fk_dx_encounter FOREIGN KEY (encounter_id) REFERENCES encounters(encounter_id),
    CONSTRAINT fk_dx_staff FOREIGN KEY (diagnosed_by_staff_id) REFERENCES staff(staff_id)
) ENGINE=InnoDB;

CREATE TABLE lab_orders (
    lab_order_id         BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    encounter_id         BIGINT UNSIGNED NOT NULL,
    ordered_by_staff_id  BIGINT UNSIGNED NOT NULL,
    test_code            VARCHAR(20) NOT NULL,
    test_name            VARCHAR(150) NOT NULL,
    status               ENUM('ORDERED','COLLECTED','IN_LAB','RESULTED','CANCELLED') NOT NULL DEFAULT 'ORDERED',
    ordered_at           DATETIME NOT NULL,
    resulted_at          DATETIME,
    result_value         VARCHAR(100),
    result_units         VARCHAR(30),
    abnormal_flag        BOOLEAN DEFAULT FALSE,
    CONSTRAINT fk_lab_encounter FOREIGN KEY (encounter_id) REFERENCES encounters(encounter_id),
    CONSTRAINT fk_lab_staff FOREIGN KEY (ordered_by_staff_id) REFERENCES staff(staff_id)
) ENGINE=InnoDB;

CREATE TABLE medication_requests (
    medication_request_id    BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    encounter_id             BIGINT UNSIGNED NOT NULL,
    patient_id               BIGINT UNSIGNED NOT NULL,
    prescribed_by_staff_id   BIGINT UNSIGNED NOT NULL,
    drug_name                VARCHAR(150) NOT NULL,
    ndc_code                 VARCHAR(20),
    dose                     VARCHAR(50),
    route                    VARCHAR(30),
    frequency                VARCHAR(50),
    status                   ENUM('DRAFT','ACTIVE','COMPLETED','CANCELLED','ON_HOLD') NOT NULL DEFAULT 'DRAFT',
    controlled_substance_flag BOOLEAN DEFAULT FALSE,
    start_datetime           DATETIME,
    end_datetime             DATETIME,
    CONSTRAINT fk_mr_encounter FOREIGN KEY (encounter_id) REFERENCES encounters(encounter_id),
    CONSTRAINT fk_mr_patient FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
    CONSTRAINT fk_mr_staff FOREIGN KEY (prescribed_by_staff_id) REFERENCES staff(staff_id)
) ENGINE=InnoDB;

CREATE TABLE medication_administrations (
    administration_id         BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    medication_request_id     BIGINT UNSIGNED NOT NULL,
    administered_by_staff_id  BIGINT UNSIGNED NOT NULL,
    administered_at           DATETIME NOT NULL,
    dose_given                VARCHAR(50),
    notes                     VARCHAR(255),
    CONSTRAINT fk_admin_mr FOREIGN KEY (medication_request_id) REFERENCES medication_requests(medication_request_id),
    CONSTRAINT fk_admin_staff FOREIGN KEY (administered_by_staff_id) REFERENCES staff(staff_id)
) ENGINE=InnoDB;

CREATE TABLE inventory_items (
    inventory_item_id       BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    hospital_id             BIGINT UNSIGNED NOT NULL,
    sku                     VARCHAR(50) NOT NULL,
    item_name               VARCHAR(150) NOT NULL,
    category                ENUM('DRUG','MEDICAL_SUPPLY','EQUIPMENT') NOT NULL,
    unit_of_measure         VARCHAR(20),
    quantity_on_hand        INT NOT NULL DEFAULT 0,
    reorder_threshold       INT NOT NULL DEFAULT 0,
    is_controlled_substance BOOLEAN DEFAULT FALSE,
    CONSTRAINT fk_inv_hospital FOREIGN KEY (hospital_id) REFERENCES hospitals(hospital_id),
    UNIQUE KEY uq_sku_per_hospital (hospital_id, sku)
) ENGINE=InnoDB;

CREATE TABLE inventory_transactions (
    transaction_id                 BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    inventory_item_id              BIGINT UNSIGNED NOT NULL,
    transaction_type               ENUM('RECEIPT','DISPENSE','ADJUSTMENT','TRANSFER') NOT NULL,
    quantity                       INT NOT NULL,
    related_medication_request_id  BIGINT UNSIGNED,
    performed_by_staff_id          BIGINT UNSIGNED NOT NULL,
    transaction_at                 DATETIME NOT NULL,
    CONSTRAINT fk_txn_item FOREIGN KEY (inventory_item_id) REFERENCES inventory_items(inventory_item_id),
    CONSTRAINT fk_txn_mr FOREIGN KEY (related_medication_request_id) REFERENCES medication_requests(medication_request_id),
    CONSTRAINT fk_txn_staff FOREIGN KEY (performed_by_staff_id) REFERENCES staff(staff_id)
) ENGINE=InnoDB;

CREATE TABLE bed_assignments (
    assignment_id   BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    bed_id          BIGINT UNSIGNED NOT NULL,
    encounter_id    BIGINT UNSIGNED NOT NULL,
    assigned_at     DATETIME NOT NULL,
    released_at     DATETIME,
    CONSTRAINT fk_ba_bed FOREIGN KEY (bed_id) REFERENCES beds(bed_id),
    CONSTRAINT fk_ba_encounter FOREIGN KEY (encounter_id) REFERENCES encounters(encounter_id)
) ENGINE=InnoDB;

CREATE TABLE billing_claims (
    claim_id         BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    encounter_id     BIGINT UNSIGNED NOT NULL,
    hospital_id      BIGINT UNSIGNED NOT NULL,
    payer_name       VARCHAR(150),
    claim_amount     DECIMAL(12,2) NOT NULL,
    status           ENUM('SUBMITTED','PAID','DENIED','APPEALED') NOT NULL DEFAULT 'SUBMITTED',
    submitted_at     DATETIME,
    adjudicated_at   DATETIME,
    denial_reason    VARCHAR(255),
    CONSTRAINT fk_claim_encounter FOREIGN KEY (encounter_id) REFERENCES encounters(encounter_id),
    CONSTRAINT fk_claim_hospital FOREIGN KEY (hospital_id) REFERENCES hospitals(hospital_id)
) ENGINE=InnoDB;

CREATE TABLE audit_log (
    audit_id        BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    actor_staff_id  BIGINT UNSIGNED NOT NULL,
    actor_role      VARCHAR(30) NOT NULL,
    action          ENUM('READ','CREATE','UPDATE','DELETE') NOT NULL,
    resource_type   VARCHAR(50) NOT NULL,
    resource_id     BIGINT UNSIGNED,
    intent_text     VARCHAR(255),
    phi_accessed    BOOLEAN NOT NULL DEFAULT FALSE,
    occurred_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address      VARCHAR(45),
    CONSTRAINT fk_audit_staff FOREIGN KEY (actor_staff_id) REFERENCES staff(staff_id),
    INDEX idx_audit_resource (resource_type, resource_id),
    INDEX idx_audit_actor (actor_staff_id, occurred_at)
) ENGINE=InnoDB;

CREATE TABLE chat_sessions (
    session_id   BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    staff_id     BIGINT UNSIGNED NOT NULL,
    role_context VARCHAR(30) NOT NULL,
    started_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_chat_staff FOREIGN KEY (staff_id) REFERENCES staff(staff_id)
) ENGINE=InnoDB;

CREATE TABLE chat_messages (
    message_id   BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    session_id   BIGINT UNSIGNED NOT NULL,
    sender       ENUM('USER','ASSISTANT','TOOL') NOT NULL,
    content      TEXT NOT NULL,
    tool_name    VARCHAR(100),
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_msg_session FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id)
) ENGINE=InnoDB;

-- =========================================================
-- Migration 002 — add http_call_log + llm_call_log
--
-- Run this against your EXISTING medflow database (you already ran
-- db/ddl.sql once, so re-running the full file will fail on duplicate
-- table errors). This file only adds the two new tables.
--
-- Usage:
--   mysql -u root -p medflow < db/migration_002_add_logging_tables.sql
-- =========================================================
USE medflow;

CREATE TABLE IF NOT EXISTS http_call_log (
    log_id            BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    staff_id          BIGINT UNSIGNED,
    actor_role        VARCHAR(30),
    method            VARCHAR(10) NOT NULL,
    path              VARCHAR(255) NOT NULL,
    query_string      VARCHAR(500),
    request_body      LONGTEXT,
    response_status   INT,
    response_body     LONGTEXT,
    duration_ms       INT,
    ip_address        VARCHAR(45),
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_httplog_staff FOREIGN KEY (staff_id) REFERENCES staff(staff_id),
    INDEX idx_httplog_created (created_at),
    INDEX idx_httplog_path (path)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS llm_call_log (
    log_id            BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    staff_id          BIGINT UNSIGNED,
    actor_role        VARCHAR(30),
    chat_session_id   BIGINT UNSIGNED,
    model             VARCHAR(100) NOT NULL,
    request_json      LONGTEXT,
    response_json     LONGTEXT,
    input_tokens      INT,
    output_tokens     INT,
    cost_usd          DECIMAL(10,6),
    latency_ms        INT,
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_llmlog_staff FOREIGN KEY (staff_id) REFERENCES staff(staff_id),
    CONSTRAINT fk_llmlog_session FOREIGN KEY (chat_session_id) REFERENCES chat_sessions(session_id),
    INDEX idx_llmlog_created (created_at)
) ENGINE=InnoDB;
