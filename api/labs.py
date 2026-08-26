from datetime import datetime

from flask import Blueprint, jsonify, request

from auth.decorators import require_role, current_staff_id, current_role
from extensions import db
from models.lab import LabOrder
from ._audit_helper import write_audit

labs_bp = Blueprint("labs", __name__)


@labs_bp.route("/encounters/<int:encounter_id>/lab-orders", methods=["GET"])
@require_role("PHYSICIAN", "NURSE")
def get_lab_orders(encounter_id):
    status_filter = request.args.get("status")
    query = LabOrder.query.filter_by(encounter_id=encounter_id)
    if status_filter:
        query = query.filter_by(status=status_filter)
    rows = query.order_by(LabOrder.ordered_at.desc()).all()

    write_audit(
        actor_staff_id=current_staff_id(),
        actor_role=current_role(),
        action="READ",
        resource_type="lab_order",
        resource_id=None,
        intent_text=f"lab orders for encounter {encounter_id}",
        phi_accessed=True,
    )
    return jsonify([r.to_dict() for r in rows])


@labs_bp.route("/encounters/<int:encounter_id>/lab-orders", methods=["POST"])
@require_role("PHYSICIAN")
def create_lab_order(encounter_id):
    payload = request.get_json(force=True)
    required = ["test_code", "test_name"]
    missing = [f for f in required if f not in payload]
    if missing:
        return jsonify({"error": "missing fields", "fields": missing}), 400

    lab_order = LabOrder(
        encounter_id=encounter_id,
        ordered_by_staff_id=current_staff_id(),
        test_code=payload["test_code"],
        test_name=payload["test_name"],
        status=payload.get("status", "ORDERED"),
        ordered_at=datetime.utcnow(),
    )
    db.session.add(lab_order)
    db.session.commit()

    write_audit(
        actor_staff_id=current_staff_id(),
        actor_role=current_role(),
        action="CREATE",
        resource_type="lab_order",
        resource_id=lab_order.lab_order_id,
        intent_text=payload.get("intent", "new lab order"),
        phi_accessed=True,
    )
    return jsonify(lab_order.to_dict()), 201