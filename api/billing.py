from flask import Blueprint, jsonify, request

from auth.decorators import require_role, current_staff_id, current_role
from models.billing import BillingClaim
from ._audit_helper import write_audit

billing_bp = Blueprint("billing", __name__)


@billing_bp.route("/hospitals/<int:hospital_id>/claims", methods=["GET"])
@require_role("FINANCE", "MANAGEMENT")
def get_claims(hospital_id):
    """No PHI -- billing_claims only links to encounter_id, never joined to
    diagnoses/clinical detail at this endpoint. That's what lets Finance see
    claim amounts and denial reasons while structurally having no path to
    clinical information, not just a policy saying it shouldn't look."""
    status_filter = request.args.get("status")
    query = BillingClaim.query.filter_by(hospital_id=hospital_id)
    if status_filter:
        query = query.filter_by(status=status_filter)
    rows = query.order_by(BillingClaim.submitted_at.desc()).all()

    write_audit(
        actor_staff_id=current_staff_id(),
        actor_role=current_role(),
        action="READ",
        resource_type="billing_claim",
        resource_id=None,
        intent_text=f"claims for hospital {hospital_id}" + (f" status={status_filter}" if status_filter else ""),
        phi_accessed=False,
    )
    return jsonify([r.to_dict() for r in rows])


@billing_bp.route("/hospitals/<int:hospital_id>/revenue-summary", methods=["GET"])
@require_role("FINANCE", "MANAGEMENT")
def get_revenue_summary(hospital_id):
    rows = BillingClaim.query.filter_by(hospital_id=hospital_id).all()

    summary = {
        "hospital_id": hospital_id,
        "total_claims": len(rows),
        "total_submitted_amount": 0.0,
        "total_paid_amount": 0.0,
        "total_denied_amount": 0.0,
        "count_by_status": {},
    }
    for claim in rows:
        amount = float(claim.claim_amount) if claim.claim_amount is not None else 0.0
        summary["total_submitted_amount"] += amount
        if claim.status == "PAID":
            summary["total_paid_amount"] += amount
        elif claim.status == "DENIED":
            summary["total_denied_amount"] += amount
        summary["count_by_status"][claim.status] = summary["count_by_status"].get(claim.status, 0) + 1

    write_audit(
        actor_staff_id=current_staff_id(),
        actor_role=current_role(),
        action="READ",
        resource_type="revenue_summary",
        resource_id=None,
        intent_text=f"revenue summary for hospital {hospital_id}",
        phi_accessed=False,
    )
    return jsonify(summary)