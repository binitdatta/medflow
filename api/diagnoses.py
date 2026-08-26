from datetime import datetime

from flask import Blueprint, jsonify, request

from auth.decorators import require_role, current_staff_id, current_role
from extensions import db
from models.encounter import Diagnosis
from ._audit_helper import write_audit

diagnoses_bp = Blueprint("diagnoses", __name__)


@diagnoses_bp.route("/encounters/<int:encounter_id>/diagnoses", methods=["GET"])
@require_role("PHYSICIAN", "NURSE")
def get_diagnoses(encounter_id):
    rows = Diagnosis.query.filter_by(encounter_id=encounter_id).order_by(Diagnosis.diagnosed_at.desc()).all()

    write_audit(
        actor_staff_id=current_staff_id(),
        actor_role=current_role(),
        action="READ",
        resource_type="diagnosis",
        resource_id=None,
        intent_text=f"diagnoses for encounter {encounter_id}",
        phi_accessed=True,
    )
    return jsonify([r.to_dict() for r in rows])


@diagnoses_bp.route("/encounters/<int:encounter_id>/diagnoses", methods=["POST"])
@require_role("PHYSICIAN")
def create_diagnosis(encounter_id):
    payload = request.get_json(force=True)
    required = ["icd10_code"]
    missing = [f for f in required if f not in payload]
    if missing:
        return jsonify({"error": "missing fields", "fields": missing}), 400

    diagnosis = Diagnosis(
        encounter_id=encounter_id,
        icd10_code=payload["icd10_code"],
        description=payload.get("description"),
        diagnosed_by_staff_id=current_staff_id(),
        diagnosed_at=datetime.utcnow(),
    )
    db.session.add(diagnosis)
    db.session.commit()

    write_audit(
        actor_staff_id=current_staff_id(),
        actor_role=current_role(),
        action="CREATE",
        resource_type="diagnosis",
        resource_id=diagnosis.diagnosis_id,
        intent_text=payload.get("intent", "new diagnosis"),
        phi_accessed=True,
    )
    return jsonify(diagnosis.to_dict()), 201