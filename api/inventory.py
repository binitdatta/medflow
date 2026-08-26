from datetime import datetime

from flask import Blueprint, jsonify, request

from auth.decorators import require_role, current_staff_id, current_role
from extensions import db
from models.inventory import InventoryItem, InventoryTransaction
from ._audit_helper import write_audit

inventory_bp = Blueprint("inventory", __name__)


@inventory_bp.route("/hospitals/<int:hospital_id>/inventory", methods=["GET"])
@require_role("PHARMACIST", "MANAGEMENT")
def get_inventory(hospital_id):
    """No PHI — item/stock levels only."""
    low_stock_only = request.args.get("low_stock", "false").lower() == "true"
    items = InventoryItem.query.filter_by(hospital_id=hospital_id).all()
    results = [i.to_dict() for i in items]
    if low_stock_only:
        results = [r for r in results if r["low_stock"]]
    return jsonify(results)


@inventory_bp.route("/inventory-transactions", methods=["POST"])
@require_role("PHARMACIST")
def create_inventory_transaction():
    payload = request.get_json(force=True)
    required = ["inventory_item_id", "transaction_type", "quantity"]
    missing = [f for f in required if f not in payload]
    if missing:
        return jsonify({"error": "missing fields", "fields": missing}), 400

    item = InventoryItem.query.get(payload["inventory_item_id"])
    if not item:
        return jsonify({"error": "inventory item not found"}), 404

    txn_type = payload["transaction_type"]
    quantity = int(payload["quantity"])

    if txn_type in ("RECEIPT",):
        item.quantity_on_hand += quantity
    elif txn_type in ("DISPENSE",):
        if item.quantity_on_hand < quantity:
            return jsonify({"error": "insufficient stock"}), 409
        item.quantity_on_hand -= quantity
    elif txn_type == "ADJUSTMENT":
        item.quantity_on_hand += quantity  # quantity may be negative for downward adjustments
    # TRANSFER handled in Phase 2 (cross-hospital logic)

    transaction = InventoryTransaction(
        inventory_item_id=payload["inventory_item_id"],
        transaction_type=txn_type,
        quantity=quantity,
        related_medication_request_id=payload.get("related_medication_request_id"),
        performed_by_staff_id=current_staff_id(),
        transaction_at=datetime.utcnow(),
    )
    db.session.add(transaction)
    db.session.commit()

    write_audit(
        actor_staff_id=current_staff_id(),
        actor_role=current_role(),
        action="CREATE",
        resource_type="inventory_transaction",
        resource_id=transaction.transaction_id,
        intent_text=payload.get("intent", f"{txn_type} of {quantity}"),
        phi_accessed=False,
    )
    return jsonify(transaction.to_dict()), 201
