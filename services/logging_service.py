"""
Global logging service. Two independent write paths, each writing to TWO
sinks -- a MySQL table (queryable from the app) and a structured stdout JSON
line (for FluentD/ELK-style centralization, see structured_logger.py):

  log_http_call() -- called once per request from app.py's after_request
                      hook. Covers every inbound HTTP call regardless of
                      caller: browser (session auth), the LangGraph agent's
                      internal service-channel calls to its own REST API,
                      and bash/script Bearer-token calls. One hook, one
                      mechanism, all three paths -- see auth/middleware.py
                      for how each of those three is authenticated.

  log_llm_call()   -- called once per Anthropic API call from
                      agent/graph.py's agent_node, with the full message
                      list, token counts, and a cost estimate from
                      agent/pricing.py.

Both are best-effort: a logging failure must never break the actual request
or chat turn, so callers (app.py, agent/graph.py) wrap these in try/except.
The console emission is deliberately NOT truncated the way the DB copy is --
the whole point of the console stream is a full, ungapped record for
downstream tooling; the DB copy is capped to keep MySQL row sizes sane for
in-app querying.
"""
import json
from decimal import Decimal

from extensions import db
from models.system_log import HttpCallLog, LlmCallLog
from agent.pricing import get_pricing_for_model
from .structured_logger import http_logger, llm_logger
from models.llm_hipaa_review import LlmHipaaReviewLog

MAX_LOGGED_BODY_CHARS = 8000  # cap applied to the MySQL copy only, not the console/ELK stream


def _truncate(text):
    if text is None:
        return None
    if len(text) > MAX_LOGGED_BODY_CHARS:
        return text[:MAX_LOGGED_BODY_CHARS] + f"...[truncated, {len(text)} chars total]"
    return text


def log_http_call(*, staff_id, actor_role, method, path, query_string,
                   request_body, response_status, response_body,
                   duration_ms, ip_address):
    # --- Sink 1: MySQL (truncated, queryable from the app) ---
    entry = HttpCallLog(
        staff_id=staff_id,
        actor_role=actor_role,
        method=method,
        path=path,
        query_string=query_string,
        request_body=_truncate(request_body),
        response_status=response_status,
        response_body=_truncate(response_body),
        duration_ms=duration_ms,
        ip_address=ip_address,
    )
    db.session.add(entry)
    db.session.commit()

    # --- Sink 2: stdout JSON line (full, untruncated -- for FluentD/ELK) ---
    try:
        http_logger.info({
            "event": "http_call",
            "staff_id": staff_id,
            "actor_role": actor_role,
            "method": method,
            "path": path,
            "query_string": query_string,
            "request_body": request_body,
            "response_status": response_status,
            "response_body": response_body,
            "duration_ms": duration_ms,
            "ip_address": ip_address,
        })
    except Exception:
        pass  # console logging must never break the request

    return entry


def messages_to_loggable(messages):
    """Convert LangChain BaseMessage objects into plain JSON-able dicts."""
    out = []
    for m in messages:
        item = {"type": m.__class__.__name__, "content": m.content}
        tool_calls = getattr(m, "tool_calls", None)
        if tool_calls:
            item["tool_calls"] = tool_calls
        tool_call_id = getattr(m, "tool_call_id", None)
        if tool_call_id:
            item["tool_call_id"] = tool_call_id
        out.append(item)
    return out


def log_llm_call(*, staff_id, actor_role, chat_session_id, model,
                  request_messages, response_message,
                  input_tokens, output_tokens, latency_ms):
    pricing = get_pricing_for_model(model)
    cost_usd = None
    if pricing and input_tokens is not None and output_tokens is not None:
        cost_usd = (
            (input_tokens / 1_000_000) * pricing["input_per_mtok"]
            + (output_tokens / 1_000_000) * pricing["output_per_mtok"]
        )

    request_loggable = messages_to_loggable(request_messages)
    response_loggable = messages_to_loggable([response_message]) if response_message else []

    # --- Sink 1: MySQL (truncated JSON strings, queryable from the app) ---
    entry = LlmCallLog(
        staff_id=staff_id,
        actor_role=actor_role,
        chat_session_id=chat_session_id,
        model=model,
        request_json=_truncate(json.dumps(request_loggable)),
        response_json=_truncate(json.dumps(response_loggable)),
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost_usd=Decimal(str(round(cost_usd, 6))) if cost_usd is not None else None,
        latency_ms=latency_ms,
    )
    db.session.add(entry)
    db.session.commit()

    # --- Sink 2: stdout JSON line (full nested JSON, untruncated -- for FluentD/ELK) ---
    try:
        llm_logger.info({
            "event": "llm_call",
            "staff_id": staff_id,
            "actor_role": actor_role,
            "chat_session_id": chat_session_id,
            "model": model,
            "request_messages": request_loggable,
            "response_message": response_loggable,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": cost_usd,
            "latency_ms": latency_ms,
        })
    except Exception:
        pass  # console logging must never break the chat turn

    return entry

def log_llm_hipaa_review(*, staff_id, actor_role, chat_session_id, purpose,
                          http_method, url, request_headers, request_params,
                          request_body, response_status, response_body,
                          model, input_tokens, output_tokens, latency_ms):
    """Writes the detailed, unredacted (except API key) compliance record.
    Deliberately no truncation here -- unlike log_llm_call()'s copy, a
    reviewer needs the complete request/response."""
    pricing = get_pricing_for_model(model)
    cost_usd = None
    if pricing and input_tokens is not None and output_tokens is not None:
        cost_usd = (
            (input_tokens / 1_000_000) * pricing["input_per_mtok"]
            + (output_tokens / 1_000_000) * pricing["output_per_mtok"]
        )

    entry = LlmHipaaReviewLog(
        staff_id=staff_id,
        actor_role=actor_role,
        chat_session_id=chat_session_id,
        purpose=purpose[:500] if purpose else None,
        http_method=http_method,
        url=url,
        request_headers=json.dumps(request_headers) if request_headers is not None else None,
        request_params=json.dumps(request_params) if request_params is not None else None,
        request_body=request_body,
        response_status=response_status,
        response_body=response_body,
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost_usd=Decimal(str(round(cost_usd, 6))) if cost_usd is not None else None,
        latency_ms=latency_ms,
    )
    db.session.add(entry)
    db.session.commit()
    return entry