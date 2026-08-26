"""
Every LangGraph tool goes through this client rather than touching
SQLAlchemy directly -- that's the point of the architecture: the agent only
ever "sees" the same REST surface a human-built UI would, and the Flask
endpoint re-checks the role independently (see auth/middleware.py, Path 3).
"""
import os

import requests

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:5000")
SERVICE_SECRET = os.getenv("KEYCLOAK_CONFIDENTIAL_CLIENT_SECRET", "")


def _headers(staff_id, role):
    return {
        "X-Service-Secret": SERVICE_SECRET,
        "X-Acting-Staff-Id": str(staff_id),
        "X-Acting-Role": role,
        "Content-Type": "application/json",
    }


def api_get(path, staff_id, role, params=None):
    resp = requests.get(f"{API_BASE_URL}{path}", headers=_headers(staff_id, role), params=params, timeout=10)
    return resp.status_code, _safe_json(resp)


def api_post(path, staff_id, role, json_body=None):
    resp = requests.post(f"{API_BASE_URL}{path}", headers=_headers(staff_id, role), json=json_body or {}, timeout=10)
    return resp.status_code, _safe_json(resp)


def _safe_json(resp):
    try:
        return resp.json()
    except ValueError:
        return {"error": "non-json response", "status_code": resp.status_code}
