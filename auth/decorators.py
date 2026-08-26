"""
require_role() is the server-side enforcement boundary.

Teaching point: this decorator checks the identity resolved by
auth/middleware.py's before_request hook -- which itself verified a Keycloak
token signature (browser session or Bearer JWT) or validated the internal
service secret + Staff-table role match (agent-to-API calls). It does NOT
trust anything the LangGraph agent or the LLM claims about the caller's role
beyond what middleware already verified. Even if a prompt convinces the
agent to call the wrong tool, the endpoint independently rejects it.
"""
from functools import wraps

from flask import g, jsonify


def require_role(*allowed_roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            role = getattr(g, "role", None)
            staff_id = getattr(g, "staff_id", None)
            if not role or not staff_id:
                return jsonify({"error": "unauthenticated"}), 401
            if role not in allowed_roles:
                return jsonify({
                    "error": "forbidden",
                    "detail": f"role '{role}' is not permitted to call this endpoint",
                }), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def current_staff_id():
    return getattr(g, "staff_id", None)


def current_role():
    return getattr(g, "role", None)


def current_hospital_id():
    return getattr(g, "hospital_id", None)
