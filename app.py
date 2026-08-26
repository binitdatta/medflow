import os
import time

from flask import Flask, g, request

from config import Config
from extensions import db

# Paths we don't bother logging -- static assets are noise, not integration events.
_HTTP_LOG_EXCLUDED_PREFIXES = ("/static",)


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    # Import models so SQLAlchemy metadata is registered (used by scripts/init_db.py,
    # not for auto-migration -- DDL is DBA-owned, see db/ddl.sql).
    import models  # noqa: F401

    # Auth middleware resolves the caller identity (browser session / Bearer JWT /
    # internal agent service channel) before every request.
    from auth.middleware import resolve_identity
    app.before_request(resolve_identity)

    @app.before_request
    def _start_http_log_timer():
        g._http_log_start = time.time()
        try:
            g._http_log_request_body = request.get_data(as_text=True)
        except Exception:
            g._http_log_request_body = None

    @app.after_request
    def _write_http_log(response):
        # Logging must never break the actual response -- wrap the whole
        # thing and always return `response` regardless of outcome.
        try:
            if not request.path.startswith(_HTTP_LOG_EXCLUDED_PREFIXES) and not getattr(
                response, "direct_passthrough", False
            ):
                from services.logging_service import log_http_call

                duration_ms = int((time.time() - getattr(g, "_http_log_start", time.time())) * 1000)
                log_http_call(
                    staff_id=getattr(g, "staff_id", None),
                    actor_role=getattr(g, "role", None),
                    method=request.method,
                    path=request.path,
                    query_string=request.query_string.decode("utf-8", errors="ignore"),
                    request_body=getattr(g, "_http_log_request_body", None),
                    response_status=response.status_code,
                    response_body=response.get_data(as_text=True),
                    duration_ms=duration_ms,
                    ip_address=request.remote_addr,
                )
        except Exception as exc:
            app.logger.warning(f"HTTP call logging failed: {exc}")
        return response

    from auth.routes import auth_bp
    app.register_blueprint(auth_bp)

    from web.routes import web_bp
    app.register_blueprint(web_bp)

    from api import register_api_blueprints
    register_api_blueprints(app)

    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=app.config["DEBUG"])