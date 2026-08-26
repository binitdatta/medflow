"""
Three ways a request arrives at the Flask API, and how identity is resolved
for each — this is registered as app.before_request in app.py.

1. Browser (medflow-web public client, PKCE)
   -> Authorization Code flow already ran; role/staff_id/hospital_id live in
      the Flask session (see auth/keycloak.py + web routes).

2. Bash / Postman / any external script (medflow-service confidential client)
   -> Caller sends `Authorization: Bearer <access_token>` obtained via the
      confidential client. Token signature is verified against Keycloak's
      JWKS and the realm role claim is read directly off the token — this is
      what keycloak/test_confidential_client.sh exercises.

3. LangGraph agent calling its own Flask REST API in-process
   -> The agent already knows the caller's staff_id/role (passed into
      run_agent by api/chat.py from the *already-authenticated* browser
      session). To avoid a second full OAuth round trip for a same-process
      call, the agent sends the shared confidential-client secret plus the
      claimed identity in headers. The middleware treats the secret as proof
      the caller is our own backend (not an arbitrary client) and then — the
      important part — verifies the claimed role against the Staff table
      rather than trusting the header value outright. A compromised or
      misprompted agent cannot claim a role the staff record doesn't have.
"""
from flask import current_app, g, request, session

from models.staff import Staff
from .keycloak import decode_access_token, extract_role


def resolve_identity():
    g.role = None
    g.staff_id = None
    g.hospital_id = None

    # --- Path 1: browser session ---
    if session.get("staff_id"):
        g.staff_id = session.get("staff_id")
        g.role = session.get("role")
        g.hospital_id = session.get("hospital_id")
        return

    # --- Path 3: internal agent -> API service channel ---
    service_secret = request.headers.get("X-Service-Secret")
    if service_secret and service_secret == current_app.config["KEYCLOAK_CONFIDENTIAL_CLIENT_SECRET"]:
        claimed_staff_id = request.headers.get("X-Acting-Staff-Id")
        claimed_role = request.headers.get("X-Acting-Role")
        if claimed_staff_id:
            staff = Staff.query.get(int(claimed_staff_id))
            # Verify against the DB record — never trust the header's role claim alone
            if staff and staff.active and staff.role == claimed_role:
                g.staff_id = staff.staff_id
                g.role = staff.role
                g.hospital_id = staff.hospital_id
        return

    # --- Path 2: Bearer JWT from the confidential client (bash/script testing) ---
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]
        try:
            claims = decode_access_token(token)
        except Exception:
            return
        role = extract_role(claims)
        keycloak_user_id = claims.get("sub")
        staff = Staff.query.filter_by(keycloak_user_id=keycloak_user_id).first()
        if staff and staff.active and staff.role == role:
            g.staff_id = staff.staff_id
            g.role = staff.role
            g.hospital_id = staff.hospital_id
