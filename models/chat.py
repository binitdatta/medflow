from datetime import datetime
from extensions import db


class ChatSession(db.Model):
    __tablename__ = "chat_sessions"

    session_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    staff_id = db.Column(db.BigInteger, db.ForeignKey("staff.staff_id"), nullable=False)
    role_context = db.Column(db.String(30), nullable=False)
    started_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)

    messages = db.relationship("ChatMessage", backref="session", lazy=True)

    def to_dict(self):
        return {
            "session_id": self.session_id,
            "staff_id": self.staff_id,
            "role_context": self.role_context,
            "started_at": self.started_at.isoformat() if self.started_at else None,
        }


class ChatMessage(db.Model):
    __tablename__ = "chat_messages"

    message_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    session_id = db.Column(db.BigInteger, db.ForeignKey("chat_sessions.session_id"), nullable=False)
    sender = db.Column(db.Enum("USER", "ASSISTANT", "TOOL"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    tool_name = db.Column(db.String(100))
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)

    def to_dict(self):
        return {
            "message_id": self.message_id,
            "session_id": self.session_id,
            "sender": self.sender,
            "content": self.content,
            "tool_name": self.tool_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
