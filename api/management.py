from flask import Blueprint, jsonify

from auth.decorators import require_role, current_staff_id, current_role
from extensions import db
from models.hospital import Bed, Unit, Department
from models.encounter import Encounter
from ._audit_helper import write_audit

management_bp = Blueprint("management", __name__)


@management_bp.route("/hospitals/<int:hospital_id>/occupancy-summary", methods=["GET"])
@require_role("MANAGEMENT")
def get_occupancy_summary(hospital_id):
    """Aggregated bed counts by status -- no bed-to-patient linkage exposed
    here, unlike GET /hospitals/<id>/beds which Nurse/Admissions use."""
    beds = (
        db.session.query(Bed)
        .join(Unit, Bed.unit_id == Unit.unit_id)
        .join(Department, Unit.department_id == Department.department_id)
        .filter(Department.hospital_id == hospital_id)
        .all()
    )
    total = len(beds)
    count_by_status = {}
    for b in beds:
        count_by_status[b.status] = count_by_status.get(b.status, 0) + 1
    occupied = count_by_status.get("OCCUPIED", 0)
    occupancy_pct = round((occupied / total) * 100, 1) if total else 0.0

    write_audit(
        actor_staff_id=current_staff_id(),
        actor_role=current_role(),
        action="READ",
        resource_type="occupancy_summary",
        resource_id=None,
        intent_text=f"occupancy summary for hospital {hospital_id}",
        phi_accessed=False,
    )
    return jsonify({
        "hospital_id": hospital_id,
        "total_beds": total,
        "count_by_status": count_by_status,
        "occupancy_pct": occupancy_pct,
    })


@management_bp.route("/hospitals/<int:hospital_id>/encounter-volume", methods=["GET"])
@require_role("MANAGEMENT")
def get_encounter_volume(hospital_id):
    """Aggregated encounter counts by type/status -- no patient identifiers
    or clinical detail returned, just volume."""
    rows = Encounter.query.filter_by(hospital_id=hospital_id).all()
    count_by_type = {}
    count_by_status = {}
    for e in rows:
        count_by_type[e.encounter_type] = count_by_type.get(e.encounter_type, 0) + 1
        count_by_status[e.status] = count_by_status.get(e.status, 0) + 1

    write_audit(
        actor_staff_id=current_staff_id(),
        actor_role=current_role(),
        action="READ",
        resource_type="encounter_volume",
        resource_id=None,
        intent_text=f"encounter volume for hospital {hospital_id}",
        phi_accessed=False,
    )
    return jsonify({
        "hospital_id": hospital_id,
        "total_encounters": len(rows),
        "count_by_type": count_by_type,
        "count_by_status": count_by_status,
    })