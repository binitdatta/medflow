from flask import Blueprint, jsonify, request

from auth.decorators import current_staff_id, current_role, current_hospital_id
from extensions import db
from models.chat import ChatSession, ChatMessage
from agent.graph import run_agent

chat_bp = Blueprint("chat", __name__)


@chat_bp.route("/chat/sessions", methods=["POST"])
def create_chat_session():
    staff_id = current_staff_id()
    role = current_role()
    if not staff_id:
        return jsonify({"error": "unauthenticated"}), 401

    session_row = ChatSession(staff_id=staff_id, role_context=role)
    db.session.add(session_row)
    db.session.commit()
    return jsonify(session_row.to_dict()), 201


@chat_bp.route("/chat/sessions/<int:session_id>/messages", methods=["POST"])
def post_chat_message(session_id):
    staff_id = current_staff_id()
    role = current_role()
    hospital_id = current_hospital_id()
    if not staff_id:
        return jsonify({"error": "unauthenticated"}), 401

    payload = request.get_json(force=True)
    user_text = payload.get("message", "").strip()
    if not user_text:
        return jsonify({"error": "message is required"}), 400

    # Fetch prior turns BEFORE saving this new user message, so chat_history
    # is exactly "everything before this turn" -- this is what was missing
    # before: each call to run_agent started with zero memory of earlier
    # turns, so a follow-up like "yes please" had nothing to resolve against.
    prior_rows = (
        ChatMessage.query
        .filter(ChatMessage.session_id == session_id, ChatMessage.sender.in_(["USER", "ASSISTANT"]))
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
    chat_history = [{"sender": r.sender, "content": r.content} for r in prior_rows]

    user_msg = ChatMessage(session_id=session_id, sender="USER", content=user_text)
    db.session.add(user_msg)
    db.session.commit()

    # role is taken from the authenticated session — never from the request body
    result_state = run_agent(
        user_query=user_text,
        staff_id=staff_id,
        role=role,
        hospital_scope=hospital_id,
        chat_history=chat_history,
        chat_session_id=session_id,
    )

    assistant_msg = ChatMessage(
        session_id=session_id,
        sender="ASSISTANT",
        content=result_state["response"],
    )
    db.session.add(assistant_msg)
    db.session.commit()

    return jsonify({
        "session_id": session_id,
        "response": result_state["response"],
        "tools_used": [t.get("tool_name") for t in result_state.get("tool_results", [])],
    })


@chat_bp.route("/chat/sessions/<int:session_id>/messages", methods=["GET"])
def get_chat_messages(session_id):
    rows = ChatMessage.query.filter_by(session_id=session_id).order_by(ChatMessage.created_at.asc()).all()
    return jsonify([r.to_dict() for r in rows])