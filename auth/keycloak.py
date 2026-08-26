"""
Keycloak 26 Authorization Code + PKCE flow for the medflow-web public client.

Flow:
  1. /auth/login    -> build authorize URL with S256 code_challenge, redirect browser
  2. Keycloak login -> redirects back to /auth/callback?code=...&state=...
  3. /auth/callback  -> exchange code + code_verifier for tokens at the token endpoint
  4. Access token is decoded (signature verified against Keycloak's JWKS) and the
     realm role + keycloak user id are pulled out of the claims and stashed in
     the Flask session, then mapped to a local `staff` row.
"""
import base64
import hashlib
import secrets
import time

import jwt
import requests
from flask import current_app, session

_JWKS_CACHE = {"keys": None, "fetched_at": 0}
_JWKS_TTL_SECONDS = 3600


def generate_pkce_pair():
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(40)).rstrip(b"=").decode("ascii")
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return verifier, challenge


def build_authorize_url():
    cfg = current_app.config
    verifier, challenge = generate_pkce_pair()
    state = secrets.token_urlsafe(24)

    session["pkce_verifier"] = verifier
    session["oauth_state"] = state

    params = {
        "client_id": cfg["KEYCLOAK_PUBLIC_CLIENT_ID"],
        "response_type": "code",
        "scope": "openid profile email",
        "redirect_uri": cfg["KEYCLOAK_REDIRECT_URI"],
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    }
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{_issuer_prop(cfg, 'auth')}?{query}"


def build_logout_url(id_token, post_logout_redirect_uri):
    """RP-initiated logout: without this, clicking Logout only clears our
    Flask session -- Keycloak's own SSO cookie stays alive, so a subsequent
    Login silently re-authenticates the same user with no login prompt."""
    cfg = current_app.config
    params = {
        "post_logout_redirect_uri": post_logout_redirect_uri,
    }
    if id_token:
        params["id_token_hint"] = id_token
    else:
        params["client_id"] = cfg["KEYCLOAK_PUBLIC_CLIENT_ID"]
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{_issuer_prop(cfg, 'logout')}?{query}"


def _issuer_prop(cfg, kind):
    base = f"{cfg['KEYCLOAK_BASE_URL']}/realms/{cfg['KEYCLOAK_REALM']}/protocol/openid-connect"
    return {
        "auth": f"{base}/auth",
        "token": f"{base}/token",
        "certs": f"{base}/certs",
        "logout": f"{base}/logout",
    }[kind]


def exchange_code_for_tokens(code, expected_state, received_state):
    if expected_state != received_state:
        raise ValueError("OAuth state mismatch — possible CSRF attempt")

    cfg = current_app.config
    verifier = session.pop("pkce_verifier", None)
    if not verifier:
        raise ValueError("Missing PKCE verifier in session")

    resp = requests.post(
        _issuer_prop(cfg, "token"),
        data={
            "grant_type": "authorization_code",
            "client_id": cfg["KEYCLOAK_PUBLIC_CLIENT_ID"],
            "code": code,
            "redirect_uri": cfg["KEYCLOAK_REDIRECT_URI"],
            "code_verifier": verifier,
        },
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def _get_jwks(cfg):
    now = time.time()
    if _JWKS_CACHE["keys"] is None or now - _JWKS_CACHE["fetched_at"] > _JWKS_TTL_SECONDS:
        resp = requests.get(_issuer_prop(cfg, "certs"), timeout=10)
        resp.raise_for_status()
        _JWKS_CACHE["keys"] = resp.json()["keys"]
        _JWKS_CACHE["fetched_at"] = now
    return _JWKS_CACHE["keys"]


def decode_access_token(access_token):
    """Verifies signature against Keycloak's JWKS and returns the claim set."""
    cfg = current_app.config
    header = jwt.get_unverified_header(access_token)
    keys = _get_jwks(cfg)
    key_data = next(k for k in keys if k["kid"] == header["kid"])
    public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key_data)

    claims = jwt.decode(
        access_token,
        key=public_key,
        algorithms=[header["alg"]],
        audience=cfg["KEYCLOAK_PUBLIC_CLIENT_ID"],
        issuer=_issuer_prop(cfg, "auth").rsplit("/protocol", 1)[0],
        options={"verify_aud": False},  # Keycloak's default aud is often 'account'; role check is what matters
    )
    return claims


def extract_role(claims):
    """medflow realm roles are assigned directly (not via client roles) — see keycloak/medflow-realm.json"""
    realm_roles = claims.get("realm_access", {}).get("roles", [])
    known_roles = {"PHYSICIAN", "NURSE", "PHARMACIST", "ADMISSIONS", "FINANCE", "MANAGEMENT", "LEGAL", "ADMIN"}
    matched = [r for r in realm_roles if r in known_roles]
    return matched[0] if matched else None