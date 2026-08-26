"""
Usage & Cost dashboard API. Restricted to ADMIN accounts (see the
require_role decorator on every route below) -- this surfaces cost/latency
data across ALL roles, which is a different sensitivity level than any
single role's own tools, so it gets its own tighter gate rather than being
folded into an existing role's toolset.
"""
import csv
import io
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request, Response

from auth.decorators import require_role
from models.system_log import HttpCallLog, LlmCallLog

admin_usage_bp = Blueprint("admin_usage", __name__)


def _parse_date_range():
    """?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD, defaulting to the last 7
    days (inclusive of today) if not provided. end is exclusive internally
    (end_date + 1 day) so a same-day range still captures that whole day."""
    end_str = request.args.get("end_date")
    start_str = request.args.get("start_date")
    end = (datetime.strptime(end_str, "%Y-%m-%d") + timedelta(days=1)) if end_str else (
        datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    )
    start = datetime.strptime(start_str, "%Y-%m-%d") if start_str else (end - timedelta(days=8))
    return start, end


@admin_usage_bp.route("/admin/usage/cost-summary", methods=["GET"])
@require_role("ADMIN")
def cost_summary():
    start, end = _parse_date_range()
    rows = LlmCallLog.query.filter(LlmCallLog.created_at >= start, LlmCallLog.created_at < end).all()

    by_role = {}
    by_day = {}
    for r in rows:
        role_key = r.actor_role or "UNKNOWN"
        day_key = r.created_at.strftime("%Y-%m-%d") if r.created_at else "UNKNOWN"
        cost = float(r.cost_usd) if r.cost_usd is not None else 0.0

        rb = by_role.setdefault(role_key, {"total_cost_usd": 0.0, "call_count": 0, "input_tokens": 0, "output_tokens": 0})
        rb["total_cost_usd"] += cost
        rb["call_count"] += 1
        rb["input_tokens"] += r.input_tokens or 0
        rb["output_tokens"] += r.output_tokens or 0

        db_bucket = by_day.setdefault(day_key, {"total_cost_usd": 0.0, "call_count": 0})
        db_bucket["total_cost_usd"] += cost
        db_bucket["call_count"] += 1

    by_role_list = [{"actor_role": k, **v, "total_cost_usd": round(v["total_cost_usd"], 6)} for k, v in sorted(by_role.items())]
    by_day_list = [{"date": k, **v, "total_cost_usd": round(v["total_cost_usd"], 6)} for k, v in sorted(by_day.items())]

    return jsonify({
        "start_date": start.strftime("%Y-%m-%d"),
        "end_date": (end - timedelta(days=1)).strftime("%Y-%m-%d"),
        "total_cost_usd": round(sum(x["total_cost_usd"] for x in by_role_list), 6),
        "total_calls": sum(x["call_count"] for x in by_role_list),
        "by_role": by_role_list,
        "by_day": by_day_list,
    })


@admin_usage_bp.route("/admin/usage/llm-calls", methods=["GET"])
@require_role("ADMIN")
def list_llm_calls():
    start, end = _parse_date_range()
    role_filter = request.args.get("role")
    limit = min(int(request.args.get("limit", 100)), 1000)

    query = LlmCallLog.query.filter(LlmCallLog.created_at >= start, LlmCallLog.created_at < end)
    if role_filter:
        query = query.filter_by(actor_role=role_filter)
    rows = query.order_by(LlmCallLog.created_at.desc()).limit(limit).all()
    return jsonify([r.to_dict() for r in rows])


@admin_usage_bp.route("/admin/usage/http-calls", methods=["GET"])
@require_role("ADMIN")
def list_http_calls():
    start, end = _parse_date_range()
    role_filter = request.args.get("role")
    method_filter = request.args.get("method")
    limit = min(int(request.args.get("limit", 100)), 1000)

    query = HttpCallLog.query.filter(HttpCallLog.created_at >= start, HttpCallLog.created_at < end)
    if role_filter:
        query = query.filter_by(actor_role=role_filter)
    if method_filter:
        query = query.filter_by(method=method_filter)
    rows = query.order_by(HttpCallLog.created_at.desc()).limit(limit).all()
    return jsonify([r.to_dict() for r in rows])


def _csv_response(fieldnames, rows_as_dicts, filename):
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for row in rows_as_dicts:
        writer.writerow(row)
    return Response(
        buffer.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@admin_usage_bp.route("/admin/usage/llm-calls.csv", methods=["GET"])
@require_role("ADMIN")
def export_llm_calls_csv():
    start, end = _parse_date_range()
    role_filter = request.args.get("role")

    query = LlmCallLog.query.filter(LlmCallLog.created_at >= start, LlmCallLog.created_at < end)
    if role_filter:
        query = query.filter_by(actor_role=role_filter)
    rows = query.order_by(LlmCallLog.created_at.desc()).limit(5000).all()

    # Deliberately excludes request_json/response_json -- those are large
    # text blobs, not a fit for a summary CSV export. Use the JSON endpoint
    # (or query MySQL directly) if you need the full payloads.
    fieldnames = ["log_id", "created_at", "staff_id", "actor_role", "chat_session_id",
                  "model", "input_tokens", "output_tokens", "cost_usd", "latency_ms"]
    return _csv_response(fieldnames, [r.to_dict() for r in rows], "llm_call_log.csv")


@admin_usage_bp.route("/admin/usage/http-calls.csv", methods=["GET"])
@require_role("ADMIN")
def export_http_calls_csv():
    start, end = _parse_date_range()
    role_filter = request.args.get("role")
    method_filter = request.args.get("method")

    query = HttpCallLog.query.filter(HttpCallLog.created_at >= start, HttpCallLog.created_at < end)
    if role_filter:
        query = query.filter_by(actor_role=role_filter)
    if method_filter:
        query = query.filter_by(method=method_filter)
    rows = query.order_by(HttpCallLog.created_at.desc()).limit(5000).all()

    fieldnames = ["log_id", "created_at", "staff_id", "actor_role", "method", "path",
                  "response_status", "duration_ms", "ip_address"]
    return _csv_response(fieldnames, [r.to_dict() for r in rows], "http_call_log.csv")