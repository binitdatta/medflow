from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request

from auth.decorators import require_role, current_staff_id, current_role
from models.audit import AuditLog
from ._audit_helper import write_audit

audit_bp = Blueprint("audit", __name__)


@audit_bp.route("/audit-log", methods=["POST"])
def post_audit_log():
    """
    Called by the LangGraph audit_writer node after every PHI-touching tool
    result. Intentionally open to any authenticated session (not role-gated)
    because every role's subgraph needs to be able to log its own actions —
    but the actor_staff_id must match the caller's own session, enforced below.
    """
    payload = request.get_json(force=True)
    if payload.get("actor_staff_id") != current_staff_id():
        return jsonify({"error": "actor_staff_id must match authenticated session"}), 403

    entry = write_audit(
        actor_staff_id=payload["actor_staff_id"],
        actor_role=payload.get("actor_role", current_role()),
        action=payload["action"],
        resource_type=payload["resource_type"],
        resource_id=payload.get("resource_id"),
        intent_text=payload.get("intent_text"),
        phi_accessed=payload.get("phi_accessed", False),
    )
    return jsonify(entry.to_dict()), 201


@audit_bp.route("/audit-log", methods=["GET"])
@require_role("LEGAL", "ADMIN")
def get_audit_log():
    query = AuditLog.query

    resource_type = request.args.get("resource_type")
    resource_id = request.args.get("resource_id")
    staff_id = request.args.get("staff_id")
    since_days = request.args.get("since_days")

    if resource_type:
        query = query.filter_by(resource_type=resource_type)
    if resource_id:
        query = query.filter_by(resource_id=resource_id)
    if staff_id:
        query = query.filter_by(actor_staff_id=staff_id)
    if since_days:
        cutoff = datetime.utcnow() - timedelta(days=int(since_days))
        query = query.filter(AuditLog.occurred_at >= cutoff)

    limit = min(int(request.args.get("limit", 200)), 500)
    rows = query.order_by(AuditLog.occurred_at.desc()).limit(limit).all()

    write_audit(
        actor_staff_id=current_staff_id(),
        actor_role=current_role(),
        action="READ",
        resource_type="audit_log",
        resource_id=resource_id,
        intent_text=request.args.get("intent", "audit trail query"),
        phi_accessed=bool(resource_type == "patient" or resource_id),
    )
    return jsonify([r.to_dict() for r in rows])