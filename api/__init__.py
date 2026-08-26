from .patients import patients_bp
from .encounters import encounters_bp
from .beds import beds_bp
from .medications import medications_bp
from .inventory import inventory_bp
from .audit import audit_bp
from .chat import chat_bp
from .diagnoses import diagnoses_bp
from .labs import labs_bp
from .billing import billing_bp
from .management import management_bp
from .admin_usage import admin_usage_bp

def register_api_blueprints(app):
    app.register_blueprint(patients_bp, url_prefix="/api")
    app.register_blueprint(encounters_bp, url_prefix="/api")
    app.register_blueprint(beds_bp, url_prefix="/api")
    app.register_blueprint(medications_bp, url_prefix="/api")
    app.register_blueprint(inventory_bp, url_prefix="/api")
    app.register_blueprint(audit_bp, url_prefix="/api")
    app.register_blueprint(chat_bp, url_prefix="/api")
    app.register_blueprint(diagnoses_bp, url_prefix="/api")
    app.register_blueprint(labs_bp, url_prefix="/api")
    app.register_blueprint(billing_bp, url_prefix="/api")
    app.register_blueprint(management_bp, url_prefix="/api")
    app.register_blueprint(admin_usage_bp, url_prefix="/api")