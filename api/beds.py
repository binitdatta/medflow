from datetime import datetime

from flask import Blueprint, jsonify, request

from auth.decorators import require_role, current_staff_id, current_role
from extensions import db
from models.hospital import Bed, Unit, Department
from models.bed_assignment import BedAssignment
from models.encounter import Encounter
from ._audit_helper import write_audit

beds_bp = Blueprint("beds", __name__)


@beds_bp.route("/hospitals/<int:hospital_id>/beds", methods=["GET"])
@require_role("ADMISSIONS", "NURSE", "MANAGEMENT")
def get_beds(hospital_id):
    """No PHI in this payload — bed status only, no patient/MRN attached."""
    status_filter = request.args.get("status")
    query = (
        db.session.query(Bed, Unit)
        .join(Unit, Bed.unit_id == Unit.unit_id)
        .join(Department, Unit.department_id == Department.department_id)
        .filter(Department.hospital_id == hospital_id)
    )
    if status_filter:
        query = query.filter(Bed.status == status_filter)

    results = []
    for bed, unit in query.all():
        item = bed.to_dict()
        item["unit_name"] = unit.name
        results.append(item)
    return jsonify(results)


@beds_bp.route("/bed-assignments", methods=["POST"])
@require_role("ADMISSIONS")
def create_bed_assignment():
    payload = request.get_json(force=True)
    required = ["bed_id", "encounter_id"]
    missing = [f for f in required if f not in payload]
    if missing:
        return jsonify({"error": "missing fields", "fields": missing}), 400

    bed = Bed.query.get(payload["bed_id"])
    if not bed:
        return jsonify({"error": "bed not found"}), 404
    if bed.status != "AVAILABLE":
        return jsonify({"error": f"bed is {bed.status}, not AVAILABLE"}), 409

    assignment = BedAssignment(
        bed_id=payload["bed_id"],
        encounter_id=payload["encounter_id"],
        assigned_at=datetime.utcnow(),
    )
    bed.status = "OCCUPIED"

    encounter = Encounter.query.get(payload["encounter_id"])
    if encounter:
        encounter.bed_id = bed.bed_id
        encounter.status = "IN_PROGRESS"

    db.session.add(assignment)
    db.session.commit()

    write_audit(
        actor_staff_id=current_staff_id(),
        actor_role=current_role(),
        action="CREATE",
        resource_type="bed_assignment",
        resource_id=assignment.assignment_id,
        intent_text=payload.get("intent", "assign bed to encounter"),
        phi_accessed=True,  # links a bed to a specific patient encounter
    )
    return jsonify(assignment.to_dict()), 201
