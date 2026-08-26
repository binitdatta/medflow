#!/usr/bin/env bash
# =========================================================
# MedFlow — confidential client test script
#
# Exercises the "Path 2" auth flow from auth/middleware.py: obtains a Bearer
# access token from Keycloak via the medflow-service confidential client
# using the Resource Owner Password Credentials grant, then calls a handful
# of Flask REST endpoints with different role users to prove RBAC is
# enforced independently at the API layer.
#
# Requires: curl, jq
# Usage:    ./test_confidential_client.sh
# =========================================================
set -euo pipefail

KEYCLOAK_BASE_URL="${KEYCLOAK_BASE_URL:-http://localhost:8080}"
REALM="${KEYCLOAK_REALM:-medflow}"
CLIENT_ID="${KEYCLOAK_CONFIDENTIAL_CLIENT_ID:-medflow-service}"
CLIENT_SECRET="${KEYCLOAK_CONFIDENTIAL_CLIENT_SECRET:-JbngaAmvYvn0oU7imiZ1YfmJiVV7iwkX}"
API_BASE_URL="${API_BASE_URL:-http://localhost:5000}"

TOKEN_URL="${KEYCLOAK_BASE_URL}/realms/${REALM}/protocol/openid-connect/token"

get_token() {
  local username="$1"
  local password="$2"
  curl -s -X POST "$TOKEN_URL" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "grant_type=password" \
    -d "client_id=${CLIENT_ID}" \
    -d "client_secret=${CLIENT_SECRET}" \
    -d "username=${username}" \
    -d "password=${password}" \
    -d "scope=openid" \
  | jq -r '.access_token'
}

echo "== 1. Nurse (nurse1) — should succeed on bed status, fail on patients endpoint scoped to other roles =="
NURSE_TOKEN=$(get_token "nurse1" "Nurse123!")
echo "--- GET /api/hospitals/1/beds ---"
curl -s -X GET "${API_BASE_URL}/api/hospitals/1/beds" \
  -H "Authorization: Bearer ${NURSE_TOKEN}" | jq .

echo
echo "== 2. Pharmacist (pharm1) — inventory + drug interaction check =="
PHARM_TOKEN=$(get_token "pharm1" "Pharm123!")
echo "--- GET /api/hospitals/1/inventory?low_stock=true ---"
curl -s -X GET "${API_BASE_URL}/api/hospitals/1/inventory?low_stock=true" \
  -H "Authorization: Bearer ${PHARM_TOKEN}" | jq .

echo "--- GET /api/medication-requests/interactions?drug_a=warfarin&drug_b=aspirin ---"
curl -s -X GET "${API_BASE_URL}/api/medication-requests/interactions?drug_a=warfarin&drug_b=aspirin" \
  -H "Authorization: Bearer ${PHARM_TOKEN}" | jq .

echo
echo "== 3. Admissions (admissions1) — patient lookup =="
ADMISSIONS_TOKEN=$(get_token "admissions1" "Admissions123!")
echo "--- GET /api/patients/MRN-100234 ---"
curl -s -X GET "${API_BASE_URL}/api/patients/MRN-100234" \
  -H "Authorization: Bearer ${ADMISSIONS_TOKEN}" | jq .

echo
echo "== 4. Negative test — Nurse token calling an Admissions-only endpoint (expect 403) =="
echo "--- POST /api/patients (as nurse1) ---"
curl -s -o /dev/null -w "HTTP %{http_code}\n" -X POST "${API_BASE_URL}/api/patients" \
  -H "Authorization: Bearer ${NURSE_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"mrn":"MRN-999999","first_name":"Test","last_name":"Patient","dob":"2000-01-01","primary_hospital_id":1}'

echo
echo "== 5. Admin/tester (svc.tester) — audit log read =="
ADMIN_TOKEN=$(get_token "svc.tester" "TesterPass123!")
echo "--- GET /api/audit-log ---"
curl -s -X GET "${API_BASE_URL}/api/audit-log" \
  -H "Authorization: Bearer ${ADMIN_TOKEN}" | jq .

echo
echo "Done."
