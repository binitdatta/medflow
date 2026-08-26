"""
Tools never accept staff_id/role/hospital_id as LLM-supplied arguments --
that would let a cleverly-worded prompt impersonate a different user. Instead
these contextvars are set once by run_agent() from the *already-authenticated*
Flask session before the graph runs, and every tool reads from here when it
calls the REST API. chat_session_id is carried the same way purely for
logging (services/logging_service.py) -- it's never used for authorization.
"""
from contextvars import ContextVar

current_staff_id: ContextVar[int] = ContextVar("current_staff_id", default=None)
current_role: ContextVar[str] = ContextVar("current_role", default=None)
current_hospital_id: ContextVar[int] = ContextVar("current_hospital_id", default=None)
current_chat_session_id: ContextVar[int] = ContextVar("current_chat_session_id", default=None)


def set_identity(staff_id, role, hospital_id, chat_session_id=None):
    current_staff_id.set(staff_id)
    current_role.set(role)
    current_hospital_id.set(hospital_id)
    current_chat_session_id.set(chat_session_id)