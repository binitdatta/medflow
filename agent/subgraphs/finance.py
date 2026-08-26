from langchain_core.tools import tool

from agent.api_client import api_get
from agent.context import current_staff_id, current_role


@tool
def get_claims_by_status(hospital_id: int, status: str = "") -> dict:
    """Get billing claims for a hospital. Optionally filter by status
    (SUBMITTED, PAID, DENIED, APPEALED). Returns claim amount, payer, and
    status -- no clinical/diagnosis detail is included."""
    params = {"status": status} if status else None
    resp_status, data = api_get(
        f"/api/hospitals/{hospital_id}/claims", current_staff_id.get(), current_role.get(), params=params
    )
    return {"status": resp_status, "data": data}


@tool
def get_revenue_summary(hospital_id: int) -> dict:
    """Get an aggregated revenue summary for a hospital: total submitted,
    paid, and denied amounts, plus a claim count broken down by status."""
    resp_status, data = api_get(
        f"/api/hospitals/{hospital_id}/revenue-summary", current_staff_id.get(), current_role.get()
    )
    return {"status": resp_status, "data": data}


FINANCE_TOOLS = [get_claims_by_status, get_revenue_summary]

FINANCE_SYSTEM_PROMPT = """You are MedFlow's finance assistant. You help
billing/revenue-cycle staff review claims and revenue summaries for a
hospital. You only have access to billing data -- claim amounts, payer
names, and claim status -- and no clinical detail (diagnoses, medications,
lab results) is available to you or ever included in the data you can
retrieve. If asked about clinical information, explain plainly that
Finance's tools don't have access to that and it would need to come from
clinical staff, rather than guessing or inferring it from claim data."""