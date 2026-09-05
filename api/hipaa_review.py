"""
HIPAA compliance review API. Every route here is gated to HIPAA_ADMIN only
-- deliberately not ADMIN, and not shared with the Usage & Cost dashboard's
gate. The whole point of a dedicated role is that fewer people can see raw
PHI-laden LLM payloads than can see aggregate cost numbers.
"""
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request

from auth.decorators import require_role, current_staff_id
from extensions import db
from models.llm_hipaa_review import LlmHipaaReviewLog

hipaa_review_bp = Blueprint("hipaa_review", __name__)


def _parse_date_range():
    end_str = request.args.get("end_date")
    start_str = request.args.get("start_date")
    end = (datetime.strptime(end_str, "%Y-%m-%d") + timedelta(days=1)) if end_str else (
        datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    )
    start = datetime.strptime(start_str, "%Y-%m-%d") if start_str else (end - timedelta(days=8))
    return start, end


@hipaa_review_bp.route("/hipaa/review/summary", methods=["GET"])
@require_role("HIPAA_ADMIN")
def review_summary():
    start, end = _parse_date_range()
    base_query = LlmHipaaReviewLog.query.filter(
        LlmHipaaReviewLog.created_at >= start, LlmHipaaReviewLog.created_at < end
    )
    total = base_query.count()
    unreviewed = base_query.filter(LlmHipaaReviewLog.reviewed == False).count()  # noqa: E712
    return jsonify({
        "start_date": start.strftime("%Y-%m-%d"),
        "end_date": (end - timedelta(days=1)).strftime("%Y-%m-%d"),
        "total_calls": total,
        "unreviewed_calls": unreviewed,
        "reviewed_calls": total - unreviewed,
    })


@hipaa_review_bp.route("/hipaa/review/calls", methods=["GET"])
@require_role("HIPAA_ADMIN")
def list_calls():
    start, end = _parse_date_range()
    role_filter = request.args.get("role")
    reviewed_filter = request.args.get("reviewed")  # "true" / "false" / absent = both
    limit = min(int(request.args.get("limit", 100)), 500)

    query = LlmHipaaReviewLog.query.filter(
        LlmHipaaReviewLog.created_at >= start, LlmHipaaReviewLog.created_at < end
    )
    if role_filter:
        query = query.filter_by(actor_role=role_filter)
    if reviewed_filter is not None:
        query = query.filter_by(reviewed=(reviewed_filter.lower() == "true"))

    rows = query.order_by(LlmHipaaReviewLog.created_at.desc()).limit(limit).all()
    return jsonify([r.to_dict(include_body=False) for r in rows])


@hipaa_review_bp.route("/hipaa/review/calls/<int:review_id>", methods=["GET"])
@require_role("HIPAA_ADMIN")
def get_call_detail(review_id):
    row = LlmHipaaReviewLog.query.get(review_id)
    if not row:
        return jsonify({"error": "not found"}), 404
    return jsonify(row.to_dict(include_body=True))


@hipaa_review_bp.route("/hipaa/review/calls/<int:review_id>/mark-reviewed", methods=["POST"])
@require_role("HIPAA_ADMIN")
def mark_reviewed(review_id):
    row = LlmHipaaReviewLog.query.get(review_id)
    if not row:
        return jsonify({"error": "not found"}), 404

    payload = request.get_json(force=True) or {}
    row.reviewed = True
    row.reviewed_by_staff_id = current_staff_id()
    row.reviewed_at = datetime.utcnow()
    row.review_notes = payload.get("notes")
    db.session.commit()
    return jsonify(row.to_dict(include_body=False))