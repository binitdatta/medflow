from datetime import datetime

from flask import Blueprint, jsonify, request

from auth.decorators import require_role, current_staff_id, current_role
from extensions import db
from models.encounter import Encounter
from models.patient import Patient
from models.bed_assignment import BedAssignment
from models.hospital import Bed
from ._audit_helper import write_audit

from datetime import datetime

from flask import Blueprint, jsonify, request

from auth.decorators import require_role, current_staff_id, current_role
from extensions import db
from models.encounter import Encounter, Diagnosis
from models.patient import Patient
from models.bed_assignment import BedAssignment
from models.hospital import Bed
from models.medication import MedicationRequest
from models.lab import LabOrder
from ._audit_helper import write_audit

encounters_bp = Blueprint("encounters", __name__)


@encounters_bp.route("/encounters/<int:encounter_id>", methods=["GET"])
@require_role("PHYSICIAN", "NURSE", "ADMISSIONS")
def get_encounter(encounter_id):
    encounter = Encounter.query.get(encounter_id)
    if not encounter:
        return jsonify({"error": "not found"}), 404

    write_audit(
        actor_staff_id=current_staff_id(),
        actor_role=current_role(),
        action="READ",
        resource_type="encounter",
        resource_id=encounter.encounter_id,
        intent_text=request.args.get("intent"),
        phi_accessed=True,
    )
    return jsonify(encounter.to_dict())


@encounters_bp.route("/encounters", methods=["POST"])
@require_role("ADMISSIONS")
def create_encounter():
    payload = request.get_json(force=True)
    required = ["patient_id", "hospital_id", "encounter_type"]
    missing = [f for f in required if f not in payload]
    if missing:
        return jsonify({"error": "missing fields", "fields": missing}), 400

    encounter = Encounter(
        patient_id=payload["patient_id"],
        hospital_id=payload["hospital_id"],
        encounter_type=payload["encounter_type"],
        status=payload.get("status", "ARRIVED"),
        admit_datetime=datetime.utcnow(),
        chief_complaint=payload.get("chief_complaint"),
    )
    db.session.add(encounter)
    db.session.commit()

    write_audit(
        actor_staff_id=current_staff_id(),
        actor_role=current_role(),
        action="CREATE",
        resource_type="encounter",
        resource_id=encounter.encounter_id,
        intent_text=payload.get("intent", "register new encounter"),
        phi_accessed=True,
    )
    return jsonify(encounter.to_dict()), 201


@encounters_bp.route("/units/<int:unit_id>/encounters", methods=["GET"])
@require_role("NURSE", "PHYSICIAN")
def get_unit_encounters(unit_id):
    """Nurse-facing: active encounters for patients currently in beds on this unit."""
    rows = (
        db.session.query(Encounter, Patient, Bed)
        .join(Patient, Encounter.patient_id == Patient.patient_id)
        .join(Bed, Encounter.bed_id == Bed.bed_id)
        .filter(Bed.unit_id == unit_id, Encounter.status == "IN_PROGRESS")
        .all()
    )
    results = []
    for encounter, patient, bed in rows:
        item = encounter.to_dict()
        item["patient"] = patient.to_dict(full=False)
        item["bed_number"] = bed.bed_number
        results.append(item)

    write_audit(
        actor_staff_id=current_staff_id(),
        actor_role=current_role(),
        action="READ",
        resource_type="encounter",
        resource_id=None,
        intent_text=f"unit {unit_id} patient list",
        phi_accessed=True,
    )
    return jsonify(results)

@encounters_bp.route("/encounters/<int:encounter_id>/chart", methods=["GET"])
@require_role("PHYSICIAN", "NURSE")
def get_encounter_chart(encounter_id):
    """Combined view for a physician reviewing a patient: encounter details,
    demographics, diagnoses, active medications, and lab orders/results in
    one call, rather than four separate tool round-trips."""
    encounter = Encounter.query.get(encounter_id)
    if not encounter:
        return jsonify({"error": "not found"}), 404

    patient = Patient.query.get(encounter.patient_id)
    diagnoses = (
        Diagnosis.query.filter_by(encounter_id=encounter_id)
        .order_by(Diagnosis.diagnosed_at.desc()).all()
    )
    active_meds = MedicationRequest.query.filter_by(encounter_id=encounter_id, status="ACTIVE").all()
    labs = LabOrder.query.filter_by(encounter_id=encounter_id).order_by(LabOrder.ordered_at.desc()).all()

    write_audit(
        actor_staff_id=current_staff_id(),
        actor_role=current_role(),
        action="READ",
        resource_type="encounter_chart",
        resource_id=encounter.encounter_id,
        intent_text=request.args.get("intent", "full chart view"),
        phi_accessed=True,
    )
    return jsonify({
        "encounter": encounter.to_dict(),
        "patient": patient.to_dict(full=False) if patient else None,
        "diagnoses": [d.to_dict() for d in diagnoses],
        "active_medications": [m.to_dict() for m in active_meds],
        "lab_orders": [l.to_dict() for l in labs],
    })