-- =========================================================
-- Migration 005 — HIPAA_ADMIN role + llm_hipaa_review_log table
-- Run this against your EXISTING medflow database.
--   mysql -u root -p medflow < db/migration_005_hipaa_review.sql
-- =========================================================
USE medflow;

ALTER TABLE staff MODIFY COLUMN role ENUM(
    'PHYSICIAN','NURSE','PHARMACIST','ADMISSIONS','FINANCE','MANAGEMENT',
    'LEGAL','ADMIN','HIPAA_ADMIN'
) NOT NULL;

CREATE TABLE IF NOT EXISTS llm_hipaa_review_log (
    review_id             BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    staff_id              BIGINT UNSIGNED,
    actor_role             VARCHAR(30),
    chat_session_id        BIGINT UNSIGNED,
    purpose                 VARCHAR(500),
    http_method              VARCHAR(10),
    url                       VARCHAR(500),
    request_headers            LONGTEXT,
    request_params              LONGTEXT,
    request_body                 LONGTEXT,
    response_status                INT,
    response_body                   LONGTEXT,
    model                            VARCHAR(100),
    input_tokens                     INT,
    output_tokens                     INT,
    cost_usd                          DECIMAL(10,6),
    latency_ms                         INT,
    reviewed                           BOOLEAN NOT NULL DEFAULT FALSE,
    reviewed_by_staff_id                 BIGINT UNSIGNED,
    reviewed_at                          DATETIME,
    review_notes                          TEXT,
    created_at                             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_hipaa_staff FOREIGN KEY (staff_id) REFERENCES staff(staff_id),
    CONSTRAINT fk_hipaa_session FOREIGN KEY (chat_session_id) REFERENCES chat_sessions(session_id),
    CONSTRAINT fk_hipaa_reviewer FOREIGN KEY (reviewed_by_staff_id) REFERENCES staff(staff_id),
    INDEX idx_hipaa_created (created_at),
    INDEX idx_hipaa_reviewed (reviewed)
) ENGINE=InnoDB;

-- IMPORTANT: keycloak_user_id below is a PLACEHOLDER. If you create
-- hipaa.admin1 manually via the Keycloak admin console (rather than the
-- partial-import JSON), Keycloak generates its OWN random UUID and this
-- won't match -- same "No active MedFlow staff record" error finance1 hit.
-- After creating the user, verify/update:
--   UPDATE staff SET keycloak_user_id = '<real-id-from-keycloak>'
--   WHERE role = 'HIPAA_ADMIN';
INSERT INTO staff (staff_id, keycloak_user_id, hospital_id, first_name, last_name, role, npi_number, license_number, active) VALUES
(9, 'b1a1c2d3-1111-4a4a-8a8a-000000000009', 1, 'Diane', 'Marsh', 'HIPAA_ADMIN', NULL, NULL, TRUE);