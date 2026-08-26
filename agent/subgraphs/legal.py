from langchain_core.tools import tool

from agent.api_client import api_get
from agent.context import current_staff_id, current_role


@tool
def get_audit_trail_for_patient(patient_id: int, since_days: int = 30) -> dict:
    """Get the audit trail of who accessed a specific patient's records
    (by patient_id, matching audit_log.resource_id for resource_type='patient')
    within the last N days (default 30)."""
    status, data = api_get(
        "/api/audit-log", current_staff_id.get(), current_role.get(),
        params={"resource_type": "patient", "resource_id": patient_id, "since_days": since_days},
    )
    return {"status": status, "data": data}


@tool
def get_audit_trail_for_staff(staff_id: int, since_days: int = 30) -> dict:
    """Get the audit trail of everything a specific staff member (by
    staff_id) has done within the last N days (default 30)."""
    status, data = api_get(
        "/api/audit-log", current_staff_id.get(), current_role.get(),
        params={"staff_id": staff_id, "since_days": since_days},
    )
    return {"status": status, "data": data}


@tool
def browse_audit_trail(resource_type: str = "", since_days: int = 30) -> dict:
    """Browse the audit trail generally, optionally filtered by
    resource_type (e.g. 'patient', 'encounter', 'medication_request',
    'inventory_transaction', 'billing_claim', 'audit_log') within the last N
    days (default 30). Use this for open-ended questions that aren't about
    one specific patient or staff member."""
    params = {"since_days": since_days}
    if resource_type:
        params["resource_type"] = resource_type
    status, data = api_get("/api/audit-log", current_staff_id.get(), current_role.get(), params=params)
    return {"status": status, "data": data}


LEGAL_TOOLS = [get_audit_trail_for_patient, get_audit_trail_for_staff, browse_audit_trail]

LEGAL_SYSTEM_PROMPT = """You are MedFlow's legal/compliance assistant. You
help legal and compliance staff answer questions like "who accessed patient
X's chart in the last 30 days" or "what has staff member Y done recently"
by querying the audit trail. You are strictly read-only -- you have no
tools that create, update, or delete anything, only tools that query the
audit_log table.

When reporting results, state exactly what the audit trail shows -- who
(actor_role/actor_staff_id), what action, what resource, and when -- without
speculating about intent or drawing conclusions about whether an access was
appropriate. That judgment belongs to the human reviewing the report. If the
audit trail shows no matching entries, say so plainly rather than assuming
that means nothing happened (the app has only been logging since this
system went live -- it has no visibility into anything before that)."""