from langchain_core.tools import tool

from agent.api_client import api_get, api_post
from agent.context import current_staff_id, current_role


@tool
def get_patient_chart(encounter_id: int) -> dict:
    """Get a combined view of an encounter: encounter details, patient
    demographics, diagnoses, active medications, and lab orders/results.
    Use this before recording a new diagnosis or prescribing a medication."""
    status, data = api_get(f"/api/encounters/{encounter_id}/chart", current_staff_id.get(), current_role.get())
    return {"status": status, "data": data}


@tool
def create_diagnosis(encounter_id: int, icd10_code: str, description: str = "") -> dict:
    """Record a new diagnosis for an encounter. icd10_code should be a valid
    ICD-10-CM code (e.g. 'J18.9' for pneumonia, unspecified organism)."""
    status, data = api_post(
        f"/api/encounters/{encounter_id}/diagnoses", current_staff_id.get(), current_role.get(),
        json_body={"icd10_code": icd10_code, "description": description},
    )
    return {"status": status, "data": data}


@tool
def create_lab_order(encounter_id: int, test_code: str, test_name: str) -> dict:
    """Order a new lab test for an encounter."""
    status, data = api_post(
        f"/api/encounters/{encounter_id}/lab-orders", current_staff_id.get(), current_role.get(),
        json_body={"test_code": test_code, "test_name": test_name},
    )
    return {"status": status, "data": data}


@tool
def get_lab_results(encounter_id: int, status: str = "") -> dict:
    """Get lab orders/results for an encounter. Optionally filter by status
    (ORDERED, COLLECTED, IN_LAB, RESULTED, CANCELLED)."""
    params = {"status": status} if status else None
    resp_status, data = api_get(
        f"/api/encounters/{encounter_id}/lab-orders", current_staff_id.get(), current_role.get(), params=params
    )
    return {"status": resp_status, "data": data}


@tool
def create_medication_request(encounter_id: int, patient_id: int, drug_name: str,
                               dose: str = "", route: str = "", frequency: str = "",
                               controlled_substance_flag: bool = False) -> dict:
    """Prescribe a new medication for a patient's encounter."""
    status, data = api_post(
        "/api/medication-requests", current_staff_id.get(), current_role.get(),
        json_body={
            "encounter_id": encounter_id,
            "patient_id": patient_id,
            "drug_name": drug_name,
            "dose": dose,
            "route": route,
            "frequency": frequency,
            "controlled_substance_flag": controlled_substance_flag,
        },
    )
    return {"status": status, "data": data}


PHYSICIAN_TOOLS = [
    get_patient_chart,
    create_diagnosis,
    create_lab_order,
    get_lab_results,
    create_medication_request,
]

PHYSICIAN_SYSTEM_PROMPT = """You are MedFlow's physician assistant. You help
physicians review a patient's full chart (diagnoses, active medications, lab
orders/results), record new diagnoses, order labs, and prescribe medications.

Always call get_patient_chart before recording a new diagnosis or
prescribing a medication, so you're acting on current information rather
than assuming.

If asked to draft a discharge summary: first call get_patient_chart to
gather the encounter's diagnoses, medications, and lab results, then write
the summary yourself directly in your response -- this is a generation
task, not a tool call, since there is no discharge-summary API endpoint.
Structure it with clear sections: Diagnosis, Hospital Course, Medications at
Discharge, and Follow-up. Do not fabricate any clinical detail that isn't
present in the chart data you actually retrieved -- if information is
missing (e.g. no discharge_datetime set yet), say so rather than inventing
it."""