import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-only-not-secure")
    DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"

    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
    MYSQL_USER = os.getenv("MYSQL_USER", "medflow_app")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "medflow")

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}"
        f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True, "pool_recycle": 280}

    API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:5000")

    KEYCLOAK_BASE_URL = os.getenv("KEYCLOAK_BASE_URL", "http://localhost:8080")
    KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "medflow")
    KEYCLOAK_PUBLIC_CLIENT_ID = os.getenv("KEYCLOAK_PUBLIC_CLIENT_ID", "medflow-web")
    KEYCLOAK_CONFIDENTIAL_CLIENT_ID = os.getenv("KEYCLOAK_CONFIDENTIAL_CLIENT_ID", "medflow-service")
    KEYCLOAK_CONFIDENTIAL_CLIENT_SECRET = os.getenv("KEYCLOAK_CONFIDENTIAL_CLIENT_SECRET", "")
    KEYCLOAK_REDIRECT_URI = os.getenv("KEYCLOAK_REDIRECT_URI", "http://localhost:5000/auth/callback")

    @property
    def KEYCLOAK_ISSUER(self):
        return f"{self.KEYCLOAK_BASE_URL}/realms/{self.KEYCLOAK_REALM}"

    @property
    def KEYCLOAK_AUTH_URL(self):
        return f"{self.KEYCLOAK_ISSUER}/protocol/openid-connect/auth"

    @property
    def KEYCLOAK_TOKEN_URL(self):
        return f"{self.KEYCLOAK_ISSUER}/protocol/openid-connect/token"

    @property
    def KEYCLOAK_CERTS_URL(self):
        return f"{self.KEYCLOAK_ISSUER}/protocol/openid-connect/certs"

    @property
    def KEYCLOAK_LOGOUT_URL(self):
        return f"{self.KEYCLOAK_ISSUER}/protocol/openid-connect/logout"

    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
