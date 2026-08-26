from flask import Blueprint, redirect, request, session, url_for, flash

from models.staff import Staff
from .keycloak import (
    build_authorize_url,
    build_logout_url,
    exchange_code_for_tokens,
    decode_access_token,
    extract_role,
)

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login")
def login():
    return redirect(build_authorize_url())


@auth_bp.route("/callback")
def callback():
    code = request.args.get("code")
    state = request.args.get("state")
    if not code:
        flash("Login failed: no authorization code returned.", "danger")
        return redirect(url_for("web.login_page"))

    try:
        tokens = exchange_code_for_tokens(code, session.get("oauth_state"), state)
        claims = decode_access_token(tokens["access_token"])
    except Exception as exc:
        flash(f"Login failed: {exc}", "danger")
        return redirect(url_for("web.login_page"))

    role = extract_role(claims)
    keycloak_user_id = claims.get("sub")
    staff = Staff.query.filter_by(keycloak_user_id=keycloak_user_id).first()

    if not staff or not staff.active:
        flash("No active MedFlow staff record is linked to this Keycloak account.", "danger")
        return redirect(url_for("web.login_page"))

    if staff.role != role:
        flash("Keycloak role does not match the staff record on file. Contact an administrator.", "danger")
        return redirect(url_for("web.login_page"))

    session["staff_id"] = staff.staff_id
    session["role"] = staff.role
    session["hospital_id"] = staff.hospital_id
    session["display_name"] = f"{staff.first_name} {staff.last_name}"
    session["id_token"] = tokens.get("id_token")
    return redirect(url_for("web.dashboard"))


@auth_bp.route("/logout")
def logout():
    id_token = session.get("id_token")
    session.clear()
    # Must match a "Valid post logout redirect URI" registered on the
    # medflow-web client exactly -- that's currently http://localhost:5000/
    # with no wildcard, so we use web.index (which redirects to /login once
    # session.clear() above has already run) rather than /login directly.
    post_logout_redirect_uri = url_for("web.index", _external=True)
    return redirect(build_logout_url(id_token, post_logout_redirect_uri))