from datetime import datetime

from flask import Blueprint, jsonify, request

from auth.decorators import require_role, current_staff_id, current_role
from extensions import db
from models.medication import MedicationRequest, MedicationAdministration
from ._audit_helper import write_audit

medications_bp = Blueprint("medications", __name__)


@medications_bp.route("/encounters/<int:encounter_id>/medication-requests", methods=["GET"])
@require_role("PHYSICIAN", "NURSE", "PHARMACIST")
def get_medication_requests(encounter_id):
    status_filter = request.args.get("status")
    query = MedicationRequest.query.filter_by(encounter_id=encounter_id)
    if status_filter:
        query = query.filter_by(status=status_filter)
    results = [m.to_dict() for m in query.all()]

    write_audit(
        actor_staff_id=current_staff_id(),
        actor_role=current_role(),
        action="READ",
        resource_type="medication_request",
        resource_id=None,
        intent_text=f"medication requests for encounter {encounter_id}",
        phi_accessed=True,
    )
    return jsonify(results)


@medications_bp.route("/medication-requests", methods=["POST"])
@require_role("PHYSICIAN")
def create_medication_request():
    payload = request.get_json(force=True)
    required = ["encounter_id", "patient_id", "drug_name"]
    missing = [f for f in required if f not in payload]
    if missing:
        return jsonify({"error": "missing fields", "fields": missing}), 400

    med_request = MedicationRequest(
        encounter_id=payload["encounter_id"],
        patient_id=payload["patient_id"],
        prescribed_by_staff_id=current_staff_id(),
        drug_name=payload["drug_name"],
        ndc_code=payload.get("ndc_code"),
        dose=payload.get("dose"),
        route=payload.get("route"),
        frequency=payload.get("frequency"),
        status=payload.get("status", "ACTIVE"),
        controlled_substance_flag=payload.get("controlled_substance_flag", False),
        start_datetime=datetime.utcnow(),
    )
    db.session.add(med_request)
    db.session.commit()

    write_audit(
        actor_staff_id=current_staff_id(),
        actor_role=current_role(),
        action="CREATE",
        resource_type="medication_request",
        resource_id=med_request.medication_request_id,
        intent_text=payload.get("intent", "new medication order"),
        phi_accessed=True,
    )
    return jsonify(med_request.to_dict()), 201


@medications_bp.route("/medication-requests/interactions", methods=["GET"])
@require_role("PHARMACIST")
def check_drug_interactions():
    """
    Phase 1 stub: returns a static rules-based interaction check for two drug
    names so the Pharmacy subgraph has a real tool to call end-to-end.
    Phase 2: replace body with a call to a real interaction-checking service/API.
    """
    drug_a = request.args.get("drug_a", "").strip().lower()
    drug_b = request.args.get("drug_b", "").strip().lower()

    known_interactions = {
        frozenset(["warfarin", "aspirin"]): "Increased bleeding risk — major interaction.",
        frozenset(["warfarin", "ibuprofen"]): "Increased bleeding risk — major interaction.",
        frozenset(["lisinopril", "potassium"]): "Risk of hyperkalemia — monitor levels.",
        frozenset(["metformin", "contrast dye"]): "Risk of lactic acidosis — hold metformin around imaging.",
    }
    key = frozenset([drug_a, drug_b])
    interaction = known_interactions.get(key)

    write_audit(
        actor_staff_id=current_staff_id(),
        actor_role=current_role(),
        action="READ",
        resource_type="drug_interaction_check",
        intent_text=f"{drug_a} + {drug_b}",
        phi_accessed=False,
    )
    return jsonify({
        "drug_a": drug_a,
        "drug_b": drug_b,
        "interaction_found": interaction is not None,
        "detail": interaction or "No known interaction in reference set.",
    })


@medications_bp.route("/medication-administrations", methods=["POST"])
@require_role("NURSE")
def create_medication_administration():
    payload = request.get_json(force=True)
    required = ["medication_request_id"]
    missing = [f for f in required if f not in payload]
    if missing:
        return jsonify({"error": "missing fields", "fields": missing}), 400

    administration = MedicationAdministration(
        medication_request_id=payload["medication_request_id"],
        administered_by_staff_id=current_staff_id(),
        administered_at=datetime.utcnow(),
        dose_given=payload.get("dose_given"),
        notes=payload.get("notes"),
    )
    db.session.add(administration)
    db.session.commit()

    write_audit(
        actor_staff_id=current_staff_id(),
        actor_role=current_role(),
        action="CREATE",
        resource_type="medication_administration",
        resource_id=administration.administration_id,
        intent_text=payload.get("intent", "medication administered"),
        phi_accessed=True,
    )
    return jsonify(administration.to_dict()), 201
