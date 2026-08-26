from langchain_core.tools import tool

from agent.api_client import api_get, api_post
from agent.context import current_staff_id, current_role


@tool
def get_active_medication_requests(encounter_id: int) -> dict:
    """Get active medication requests for an encounter, for pharmacy review."""
    status, data = api_get(
        f"/api/encounters/{encounter_id}/medication-requests",
        current_staff_id.get(), current_role.get(),
        params={"status": "ACTIVE"},
    )
    return {"status": status, "data": data}


@tool
def check_drug_interactions(drug_a: str, drug_b: str) -> dict:
    """Check whether two drug names have a known interaction before a med is
    dispensed."""
    status, data = api_get(
        "/api/medication-requests/interactions", current_staff_id.get(), current_role.get(),
        params={"drug_a": drug_a, "drug_b": drug_b},
    )
    return {"status": status, "data": data}


@tool
def get_inventory(hospital_id: int, low_stock_only: bool = False) -> dict:
    """Get pharmacy/medical inventory for a hospital. Set low_stock_only=True
    to see only items at or below their reorder threshold."""
    status, data = api_get(
        f"/api/hospitals/{hospital_id}/inventory", current_staff_id.get(), current_role.get(),
        params={"low_stock": str(low_stock_only).lower()},
    )
    return {"status": status, "data": data}


@tool
def dispense_medication(inventory_item_id: int, quantity: int, related_medication_request_id: int = None) -> dict:
    """Record a DISPENSE inventory transaction -- reduces quantity_on_hand for
    the given inventory item."""
    status, data = api_post(
        "/api/inventory-transactions", current_staff_id.get(), current_role.get(),
        json_body={
            "inventory_item_id": inventory_item_id,
            "transaction_type": "DISPENSE",
            "quantity": quantity,
            "related_medication_request_id": related_medication_request_id,
        },
    )
    return {"status": status, "data": data}


PHARMACY_TOOLS = [get_active_medication_requests, check_drug_interactions, get_inventory, dispense_medication]

PHARMACY_SYSTEM_PROMPT = """You are MedFlow's pharmacy assistant. You help
pharmacists review active medication orders, check drug interactions before
dispensing, monitor inventory (especially controlled substances and low-stock
items), and record dispenses. Always run check_drug_interactions before
recommending a dispense if two or more drugs are involved. Flag controlled
substances explicitly in your answer."""
