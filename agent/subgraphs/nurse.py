from langchain_core.tools import tool

from agent.api_client import api_get, api_post
from agent.context import current_staff_id, current_role


@tool
def get_unit_patients(unit_id: int) -> dict:
    """Get the list of patients currently admitted to a given nursing unit,
    including their encounter status and bed number."""
    status, data = api_get(f"/api/units/{unit_id}/encounters", current_staff_id.get(), current_role.get())
    return {"status": status, "data": data}


@tool
def get_medication_schedule(encounter_id: int) -> dict:
    """Get the active medication requests for a specific encounter, i.e. what's
    due to be administered."""
    status, data = api_get(
        f"/api/encounters/{encounter_id}/medication-requests",
        current_staff_id.get(), current_role.get(),
        params={"status": "ACTIVE"},
    )
    return {"status": status, "data": data}


@tool
def record_medication_administration(medication_request_id: int, dose_given: str, notes: str = "") -> dict:
    """Record that a medication was administered to a patient for a given
    medication_request_id. Use this only after confirming the order and dose."""
    status, data = api_post(
        "/api/medication-administrations", current_staff_id.get(), current_role.get(),
        json_body={"medication_request_id": medication_request_id, "dose_given": dose_given, "notes": notes},
    )
    return {"status": status, "data": data}


@tool
def get_bed_status(hospital_id: int, status: str = "") -> dict:
    """Get bed availability for a hospital. Optionally filter by status
    (AVAILABLE, OCCUPIED, CLEANING, OUT_OF_SERVICE)."""
    params = {"status": status} if status else None
    resp_status, data = api_get(
        f"/api/hospitals/{hospital_id}/beds", current_staff_id.get(), current_role.get(), params=params
    )
    return {"status": resp_status, "data": data}


NURSE_TOOLS = [get_unit_patients, get_medication_schedule, record_medication_administration, get_bed_status]

NURSE_SYSTEM_PROMPT = """You are MedFlow's nursing assistant. You help nurses check
on their unit's patients, see what medications are due, record medication
administrations, and check bed status. You only have access to nursing-scoped
tools -- you cannot see billing, legal, or other hospitals' data. Be concise
and clinical in tone. Always confirm the encounter/medication_request_id you
acted on in your final answer so the nurse can double check it."""
