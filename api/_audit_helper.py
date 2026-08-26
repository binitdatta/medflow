from flask import request

from extensions import db
from models.audit import AuditLog


def write_audit(actor_staff_id, actor_role, action, resource_type, resource_id=None,
                 intent_text=None, phi_accessed=False):
    entry = AuditLog(
        actor_staff_id=actor_staff_id,
        actor_role=actor_role,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        intent_text=intent_text,
        phi_accessed=phi_accessed,
        ip_address=request.remote_addr if request else None,
    )
    db.session.add(entry)
    db.session.commit()
    return entry
