from datetime import datetime

from flask import Blueprint, jsonify, request

from auth.decorators import require_role, current_staff_id, current_role
from extensions import db
from models.patient import Patient
from ._audit_helper import write_audit

patients_bp = Blueprint("patients", __name__)


@patients_bp.route("/patients/<string:mrn>", methods=["GET"])
@require_role("PHYSICIAN", "NURSE", "ADMISSIONS", "LEGAL", "PHARMACIST")
def get_patient_by_mrn(mrn):
    patient = Patient.query.filter_by(mrn=mrn).first()
    if not patient:
        return jsonify({"error": "not found"}), 404

    write_audit(
        actor_staff_id=current_staff_id(),
        actor_role=current_role(),
        action="READ",
        resource_type="patient",
        resource_id=patient.patient_id,
        intent_text=request.args.get("intent", "lookup by mrn"),
        phi_accessed=True,
    )
    return jsonify(patient.to_dict())


@patients_bp.route("/patients", methods=["POST"])
@require_role("ADMISSIONS")
def create_patient():
    payload = request.get_json(force=True)
    required = ["mrn", "first_name", "last_name", "dob", "primary_hospital_id"]
    missing = [f for f in required if f not in payload]
    if missing:
        return jsonify({"error": "missing fields", "fields": missing}), 400

    patient = Patient(
        mrn=payload["mrn"],
        first_name=payload["first_name"],
        last_name=payload["last_name"],
        dob=datetime.strptime(payload["dob"], "%Y-%m-%d").date(),
        sex=payload.get("sex", "U"),
        ssn_last4=payload.get("ssn_last4"),
        address=payload.get("address"),
        phone=payload.get("phone"),
        primary_hospital_id=payload["primary_hospital_id"],
    )
    db.session.add(patient)
    db.session.commit()

    write_audit(
        actor_staff_id=current_staff_id(),
        actor_role=current_role(),
        action="CREATE",
        resource_type="patient",
        resource_id=patient.patient_id,
        intent_text=payload.get("intent", "register new patient"),
        phi_accessed=True,
    )
    return jsonify(patient.to_dict()), 201
