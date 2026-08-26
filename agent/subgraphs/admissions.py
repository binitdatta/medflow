from langchain_core.tools import tool

from agent.api_client import api_get, api_post
from agent.context import current_staff_id, current_role


@tool
def search_patient_by_mrn(mrn: str) -> dict:
    """Look up an existing patient by their MRN (medical record number)."""
    status, data = api_get(f"/api/patients/{mrn}", current_staff_id.get(), current_role.get())
    return {"status": status, "data": data}


@tool
def create_patient(mrn: str, first_name: str, last_name: str, dob: str,
                    primary_hospital_id: int, sex: str = "U",
                    address: str = "", phone: str = "") -> dict:
    """Register a new patient. dob must be YYYY-MM-DD. sex is one of M, F, O, U."""
    status, data = api_post(
        "/api/patients", current_staff_id.get(), current_role.get(),
        json_body={
            "mrn": mrn, "first_name": first_name, "last_name": last_name, "dob": dob,
            "primary_hospital_id": primary_hospital_id, "sex": sex, "address": address, "phone": phone,
        },
    )
    return {"status": status, "data": data}


@tool
def create_encounter(patient_id: int, hospital_id: int, encounter_type: str,
                      chief_complaint: str = "") -> dict:
    """Create a new encounter for a patient. encounter_type is one of
    INPATIENT, OUTPATIENT, ER."""
    status, data = api_post(
        "/api/encounters", current_staff_id.get(), current_role.get(),
        json_body={
            "patient_id": patient_id, "hospital_id": hospital_id,
            "encounter_type": encounter_type, "chief_complaint": chief_complaint,
        },
    )
    return {"status": status, "data": data}


@tool
def get_available_beds(hospital_id: int) -> dict:
    """Get all currently AVAILABLE beds for a hospital."""
    status, data = api_get(
        f"/api/hospitals/{hospital_id}/beds", current_staff_id.get(), current_role.get(),
        params={"status": "AVAILABLE"},
    )
    return {"status": status, "data": data}


@tool
def assign_bed(bed_id: int, encounter_id: int) -> dict:
    """Assign an available bed to an encounter -- marks the bed OCCUPIED and
    the encounter IN_PROGRESS."""
    status, data = api_post(
        "/api/bed-assignments", current_staff_id.get(), current_role.get(),
        json_body={"bed_id": bed_id, "encounter_id": encounter_id},
    )
    return {"status": status, "data": data}


ADMISSIONS_TOOLS = [search_patient_by_mrn, create_patient, create_encounter, get_available_beds, assign_bed]

ADMISSIONS_SYSTEM_PROMPT = """You are MedFlow's admissions assistant. You help
admissions staff search for existing patients, register new patients, open new
encounters, and assign beds. Always search_patient_by_mrn first before
creating a new patient, to avoid duplicate records. Confirm the MRN,
encounter_id, and bed assignment clearly in your final answer."""
