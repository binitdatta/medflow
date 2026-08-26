from datetime import datetime
from extensions import db


class AuditLog(db.Model):
    __tablename__ = "audit_log"

    audit_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    actor_staff_id = db.Column(db.BigInteger, db.ForeignKey("staff.staff_id"), nullable=False)
    actor_role = db.Column(db.String(30), nullable=False)
    action = db.Column(db.Enum("READ", "CREATE", "UPDATE", "DELETE"), nullable=False)
    resource_type = db.Column(db.String(50), nullable=False)
    resource_id = db.Column(db.BigInteger)
    intent_text = db.Column(db.String(255))
    phi_accessed = db.Column(db.Boolean, nullable=False, default=False)
    occurred_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))

    def to_dict(self):
        return {
            "audit_id": self.audit_id,
            "actor_staff_id": self.actor_staff_id,
            "actor_role": self.actor_role,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "intent_text": self.intent_text,
            "phi_accessed": self.phi_accessed,
            "occurred_at": self.occurred_at.isoformat() if self.occurred_at else None,
            "ip_address": self.ip_address,
        }
