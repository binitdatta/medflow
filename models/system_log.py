from datetime import datetime
from extensions import db


class HttpCallLog(db.Model):
    """Every inbound HTTP request the Flask app receives -- browser UI,
    the agent's own internal service-channel calls to its own REST API, and
    bash/script Bearer-token calls all land here via app.py's after_request
    hook, so this one table covers all three call paths."""
    __tablename__ = "http_call_log"

    log_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    staff_id = db.Column(db.BigInteger, db.ForeignKey("staff.staff_id"))
    actor_role = db.Column(db.String(30))
    method = db.Column(db.String(10), nullable=False)
    path = db.Column(db.String(255), nullable=False)
    query_string = db.Column(db.String(500))
    request_body = db.Column(db.Text)
    response_status = db.Column(db.Integer)
    response_body = db.Column(db.Text)
    duration_ms = db.Column(db.Integer)
    ip_address = db.Column(db.String(45))
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)

    def to_dict(self):
        return {
            "log_id": self.log_id,
            "staff_id": self.staff_id,
            "actor_role": self.actor_role,
            "method": self.method,
            "path": self.path,
            "query_string": self.query_string,
            "request_body": self.request_body,
            "response_status": self.response_status,
            "response_body": self.response_body,
            "duration_ms": self.duration_ms,
            "ip_address": self.ip_address,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class LlmCallLog(db.Model):
    """Every call the LangGraph agent makes to the Anthropic API, with the
    full request/response message list and a cost estimate. See
    agent/pricing.py for the (placeholder -- verify before trusting) rate
    table used to compute cost_usd."""
    __tablename__ = "llm_call_log"

    log_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    staff_id = db.Column(db.BigInteger, db.ForeignKey("staff.staff_id"))
    actor_role = db.Column(db.String(30))
    chat_session_id = db.Column(db.BigInteger, db.ForeignKey("chat_sessions.session_id"))
    model = db.Column(db.String(100), nullable=False)
    request_json = db.Column(db.Text)
    response_json = db.Column(db.Text)
    input_tokens = db.Column(db.Integer)
    output_tokens = db.Column(db.Integer)
    cost_usd = db.Column(db.Numeric(10, 6))
    latency_ms = db.Column(db.Integer)
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)

    def to_dict(self):
        return {
            "log_id": self.log_id,
            "staff_id": self.staff_id,
            "actor_role": self.actor_role,
            "chat_session_id": self.chat_session_id,
            "model": self.model,
            "request_json": self.request_json,
            "response_json": self.response_json,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cost_usd": float(self.cost_usd) if self.cost_usd is not None else None,
            "latency_ms": self.latency_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }