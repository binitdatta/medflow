-- =========================================================
-- MedFlow — Seed Data (Phase 1)
-- Load AFTER db/ddl.sql.
-- staff.keycloak_user_id values MUST match the `id` field of the
-- corresponding user in keycloak/medflow-realm.json — that's how a logged-in
-- Keycloak identity resolves to a local staff/role record.
-- =========================================================
USE medflow;

-- ---------- Hospitals ----------
INSERT INTO hospitals (hospital_id, name, address, timezone) VALUES
(1, 'Riverside General Hospital', '100 Riverside Ave, Springfield, IL', 'America/Chicago'),
(2, 'Lakeside Medical Center', '200 Lakeside Dr, Springfield, IL', 'America/Chicago');

-- ---------- Departments ----------
INSERT INTO departments (department_id, hospital_id, name, dept_type) VALUES
(1, 1, 'Riverside Inpatient Medicine', 'INPATIENT'),
(2, 1, 'Riverside Pharmacy', 'PHARMACY'),
(3, 1, 'Riverside Admissions', 'ADMISSIONS'),
(4, 2, 'Lakeside Inpatient Medicine', 'INPATIENT'),
(5, 2, 'Lakeside Pharmacy', 'PHARMACY');

-- ---------- Units ----------
INSERT INTO units (unit_id, department_id, name, floor, capacity) VALUES
(1, 1, 'Unit 3 - Medical/Surgical', '3', 20),
(2, 1, 'Unit 4 - Telemetry', '4', 16),
(3, 4, 'Unit 2 - Medical/Surgical', '2', 18);

-- ---------- Beds ----------
INSERT INTO beds (bed_id, unit_id, bed_number, status) VALUES
(1, 1, '301', 'OCCUPIED'),
(2, 1, '302', 'AVAILABLE'),
(3, 1, '303', 'AVAILABLE'),
(4, 2, '401', 'OCCUPIED'),
(5, 2, '402', 'CLEANING'),
(6, 3, '201', 'AVAILABLE');

-- ---------- Staff ----------
-- keycloak_user_id values match keycloak/medflow-realm.json user "id" fields exactly.
INSERT INTO staff (staff_id, keycloak_user_id, hospital_id, first_name, last_name, role, npi_number, license_number, active) VALUES
(1, 'b1a1c2d3-1111-4a4a-8a8a-000000000001', 1, 'Angela',  'Reyes',    'NURSE',      NULL,          'RN-IL-88213', TRUE),
(2, 'b1a1c2d3-1111-4a4a-8a8a-000000000002', 1, 'Marcus',  'Chen',     'PHARMACIST', NULL,          'RPH-IL-44120', TRUE),
(3, 'b1a1c2d3-1111-4a4a-8a8a-000000000003', 1, 'Denise',  'Walker',   'ADMISSIONS', NULL,          NULL,          TRUE),
(4, 'b1a1c2d3-1111-4a4a-8a8a-000000000004', 1, 'Sanjay',  'Patel',    'PHYSICIAN',  '1922334455',  'MD-IL-10982', TRUE),
(5, 'b1a1c2d3-1111-4a4a-8a8a-000000000005', 1, 'System',  'Tester',   'ADMIN',      NULL,          NULL,          TRUE);

-- ---------- Patients ----------
INSERT INTO patients (patient_id, mrn, first_name, last_name, dob, sex, ssn_last4, address, phone, primary_hospital_id) VALUES
(1, 'MRN-100234', 'Harold', 'Jennings', '1958-03-11', 'M', '1234', '45 Oak St, Springfield, IL', '217-555-0110', 1),
(2, 'MRN-100235', 'Priya',  'Nair',     '1990-07-22', 'F', '5678', '12 Elm St, Springfield, IL', '217-555-0111', 1);

-- ---------- Encounters ----------
INSERT INTO encounters (encounter_id, patient_id, hospital_id, encounter_type, status, admit_datetime, attending_physician_id, chief_complaint, bed_id) VALUES
(1, 1, 1, 'INPATIENT', 'IN_PROGRESS', '2026-07-18 08:30:00', 4, 'Shortness of breath', 1),
(2, 2, 1, 'INPATIENT', 'IN_PROGRESS', '2026-07-19 14:10:00', 4, 'Post-op monitoring', 4);

-- ---------- Medication Requests ----------
INSERT INTO medication_requests (medication_request_id, encounter_id, patient_id, prescribed_by_staff_id, drug_name, ndc_code, dose, route, frequency, status, controlled_substance_flag, start_datetime) VALUES
(1, 1, 1, 4, 'Warfarin', '00056-0169-70', '5mg', 'oral', 'daily', 'ACTIVE', FALSE, '2026-07-18 09:00:00'),
(2, 1, 1, 4, 'Aspirin', '00536-1017-01', '81mg', 'oral', 'daily', 'ACTIVE', FALSE, '2026-07-18 09:00:00'),
(3, 2, 2, 4, 'Morphine', '00409-1234-01', '2mg', 'IV', 'q4h PRN', 'ACTIVE', TRUE, '2026-07-19 15:00:00');

-- ---------- Inventory ----------
INSERT INTO inventory_items (inventory_item_id, hospital_id, sku, item_name, category, unit_of_measure, quantity_on_hand, reorder_threshold, is_controlled_substance) VALUES
(1, 1, 'DRUG-WARF-5MG', 'Warfarin 5mg tablet', 'DRUG', 'tablet', 500, 100, FALSE),
(2, 1, 'DRUG-ASA-81MG', 'Aspirin 81mg tablet', 'DRUG', 'tablet', 800, 150, FALSE),
(3, 1, 'DRUG-MORPH-2MG', 'Morphine 2mg/mL vial', 'DRUG', 'vial', 40, 50, TRUE),
(4, 1, 'SUPP-GLOVE-M', 'Nitrile Gloves (M)', 'MEDICAL_SUPPLY', 'box', 200, 40, FALSE);

-- =========================================================
-- Seed additions for Phase 2 — Physician subgraph
-- Run AFTER db/ddl.sql and db/seed.sql (the diagnoses and lab_orders
-- tables already exist from Phase 1's ddl.sql -- this just adds rows).
--
-- Usage:
--   mysql -u root -p medflow < db/seed_002_physician_data.sql
-- =========================================================
USE medflow;

-- Diagnosis for encounter 1 (Harold Jennings — shortness of breath)
INSERT INTO diagnoses (diagnosis_id, encounter_id, icd10_code, description, diagnosed_by_staff_id, diagnosed_at) VALUES
(1, 1, 'J18.9', 'Pneumonia, unspecified organism', 4, '2026-07-18 10:15:00');

-- Lab orders for encounter 1 — one resulted (abnormal), one still pending
INSERT INTO lab_orders (lab_order_id, encounter_id, ordered_by_staff_id, test_code, test_name, status, ordered_at, resulted_at, result_value, result_units, abnormal_flag) VALUES
(1, 1, 4, 'CBC', 'Complete Blood Count', 'RESULTED', '2026-07-18 09:00:00', '2026-07-18 10:30:00', 'WBC 14.2', 'x10^9/L', TRUE),
(2, 1, 4, 'CXR', 'Chest X-Ray', 'ORDERED', '2026-07-18 09:05:00', NULL, NULL, NULL, FALSE);


-- =========================================================
-- Seed additions for Phase 2 — Finance subgraph
-- Run AFTER db/ddl.sql and db/seed.sql (billing_claims table already
-- exists from Phase 1's ddl.sql -- this adds a Finance staff row and
-- sample claims).
--
-- Requires the finance1 Keycloak user to exist first (see step 1 above),
-- or the keycloak_user_id below won't resolve to anything at login time.
--
-- Usage:
--   mysql -u root -p medflow < db/seed_003_finance_data.sql
-- =========================================================
USE medflow;

INSERT INTO staff (staff_id, keycloak_user_id, hospital_id, first_name, last_name, role, npi_number, license_number, active) VALUES
(6, 'b1a1c2d3-1111-4a4a-8a8a-000000000006', 1, 'Renee', 'Castillo', 'FINANCE', NULL, NULL, TRUE);

-- Mix of statuses across both existing encounters so there's something to
-- query: one paid, one denied (with a reason), one still submitted/pending.
INSERT INTO billing_claims (claim_id, encounter_id, hospital_id, payer_name, claim_amount, status, submitted_at, adjudicated_at, denial_reason) VALUES
(1, 1, 1, 'BlueCross Illinois', 4250.00, 'PAID',      '2026-07-19 09:00:00', '2026-07-25 00:00:00', NULL),
(2, 2, 1, 'Medicare',           1875.50, 'DENIED',    '2026-07-20 09:00:00', '2026-07-26 00:00:00', 'Missing prior authorization'),
(3, 1, 1, 'Aetna',               980.00, 'SUBMITTED', '2026-07-21 09:00:00', NULL,                  NULL);


USE medflow;

INSERT INTO staff (staff_id, keycloak_user_id, hospital_id, first_name, last_name, role, npi_number, license_number, active) VALUES
(7, 'b1a1c2d3-1111-4a4a-8a8a-000000000007', 1, 'Marcus',  'Okafor', 'MANAGEMENT', NULL, NULL, TRUE),
(8, 'b1a1c2d3-1111-4a4a-8a8a-000000000008', 1, 'Priya',   'Shah',   'LEGAL',      NULL, NULL, TRUE);