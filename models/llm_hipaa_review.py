from datetime import datetime
from extensions import db


class LlmHipaaReviewLog(db.Model):
    """Detailed record of every actual HTTP call made to Anthropic on a
    user's behalf -- built for HIPAA compliance review, not for the Usage &
    Cost dashboard (see LlmCallLog for that, which stays truncated and
    unchanged). This table is deliberately NOT truncated, since a reviewer
    needs the complete picture -- expect it to grow quickly. See
    scripts/purge_hipaa_review_log.py for a starting point on a
    retention/purge routine before archiving to cold storage (e.g. S3)."""
    __tablename__ = "llm_hipaa_review_log"

    review_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    staff_id = db.Column(db.BigInteger, db.ForeignKey("staff.staff_id"))
    actor_role = db.Column(db.String(30))
    chat_session_id = db.Column(db.BigInteger, db.ForeignKey("chat_sessions.session_id"))
    purpose = db.Column(db.String(500))
    http_method = db.Column(db.String(10))
    url = db.Column(db.String(500))
    request_headers = db.Column(db.Text)
    request_params = db.Column(db.Text)
    request_body = db.Column(db.Text)
    response_status = db.Column(db.Integer)
    response_body = db.Column(db.Text)
    model = db.Column(db.String(100))
    input_tokens = db.Column(db.Integer)
    output_tokens = db.Column(db.Integer)
    cost_usd = db.Column(db.Numeric(10, 6))
    latency_ms = db.Column(db.Integer)
    reviewed = db.Column(db.Boolean, nullable=False, default=False)
    reviewed_by_staff_id = db.Column(db.BigInteger, db.ForeignKey("staff.staff_id"))
    reviewed_at = db.Column(db.DateTime)
    review_notes = db.Column(db.Text)
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)

    def to_dict(self, include_body=True):
        base = {
            "review_id": self.review_id,
            "staff_id": self.staff_id,
            "actor_role": self.actor_role,
            "chat_session_id": self.chat_session_id,
            "purpose": self.purpose,
            "http_method": self.http_method,
            "url": self.url,
            "response_status": self.response_status,
            "model": self.model,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cost_usd": float(self.cost_usd) if self.cost_usd is not None else None,
            "latency_ms": self.latency_ms,
            "reviewed": self.reviewed,
            "reviewed_by_staff_id": self.reviewed_by_staff_id,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "review_notes": self.review_notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_body:
            base.update({
                "request_headers": self.request_headers,
                "request_params": self.request_params,
                "request_body": self.request_body,
                "response_body": self.response_body,
            })
        return base