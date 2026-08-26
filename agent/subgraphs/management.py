from langchain_core.tools import tool

from agent.api_client import api_get
from agent.context import current_staff_id, current_role


@tool
def get_occupancy_summary(hospital_id: int) -> dict:
    """Get aggregated bed occupancy for a hospital: total beds, counts by
    status, and an occupancy percentage. No patient or bed-assignment detail
    is included -- this is a headcount view only."""
    status, data = api_get(
        f"/api/hospitals/{hospital_id}/occupancy-summary", current_staff_id.get(), current_role.get()
    )
    return {"status": status, "data": data}


@tool
def get_encounter_volume(hospital_id: int) -> dict:
    """Get aggregated encounter volume for a hospital: total encounters,
    broken down by encounter type (INPATIENT/OUTPATIENT/ER) and status.
    No patient identifiers or clinical detail included."""
    status, data = api_get(
        f"/api/hospitals/{hospital_id}/encounter-volume", current_staff_id.get(), current_role.get()
    )
    return {"status": status, "data": data}


@tool
def get_inventory_summary(hospital_id: int, low_stock_only: bool = False) -> dict:
    """Get inventory levels for a hospital. Set low_stock_only=True to see
    only items at or below their reorder threshold."""
    status, data = api_get(
        f"/api/hospitals/{hospital_id}/inventory", current_staff_id.get(), current_role.get(),
        params={"low_stock": str(low_stock_only).lower()},
    )
    return {"status": status, "data": data}


@tool
def get_revenue_summary(hospital_id: int) -> dict:
    """Get an aggregated revenue summary for a hospital: total submitted,
    paid, and denied claim amounts, plus claim counts by status."""
    status, data = api_get(
        f"/api/hospitals/{hospital_id}/revenue-summary", current_staff_id.get(), current_role.get()
    )
    return {"status": status, "data": data}


MANAGEMENT_TOOLS = [
    get_occupancy_summary,
    get_encounter_volume,
    get_inventory_summary,
    get_revenue_summary,
]

MANAGEMENT_SYSTEM_PROMPT = """You are MedFlow's management assistant. You
help hospital group leadership see rolled-up operational metrics: bed
occupancy, encounter volume, inventory levels, and revenue -- across one
hospital at a time (call the relevant tool once per hospital_id if asked to
compare hospitals). Every number you have access to is pre-aggregated at
the API layer with no patient names, MRNs, or clinical detail attached --
you cannot look up an individual patient's chart, and should say so plainly
if asked, rather than trying to reconstruct patient-level detail from
aggregate counts."""