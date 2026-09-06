from flask import Blueprint, render_template, session, redirect, url_for, flash

web_bp = Blueprint("web", __name__, template_folder="templates")

def _require_login():
    return session.get("staff_id") is not None


def _require_hipaa_admin():
    return session.get("role") == "HIPAA_ADMIN"

def _require_admin():
    return session.get("role") == "ADMIN"

@web_bp.route("/admin/usage")
def admin_usage():
    if not _require_login():
        return redirect(url_for("web.login_page"))
    if not _require_admin():
        flash("The Usage & Cost dashboard is restricted to ADMIN accounts.", "warning")
        return redirect(url_for("web.dashboard"))
    return render_template(
        "admin_usage.html",
        role=session.get("role"),
        display_name=session.get("display_name"),
    )

# @web_bp.route("/")
# def index():
#     if _require_login():
#         return redirect(url_for("web.dashboard"))
#     return redirect(url_for("web.login_page"))

@web_bp.route("/")
def index():
    if _require_login():
        return redirect(url_for("web.dashboard"))
    return render_template("home.html")

@web_bp.route("/training/graph-theory-langgraph")
def training_graph_theory_langgraph():
    return render_template("training/graph_theory_langgraph.html")

@web_bp.route("/login")
def login_page():
    return render_template("login.html")


@web_bp.route("/dashboard")
def dashboard():
    if not _require_login():
        return redirect(url_for("web.login_page"))
    return render_template(
        "dashboard.html",
        role=session.get("role"),
        display_name=session.get("display_name"),
    )


@web_bp.route("/chat")
def chat_page():
    if not _require_login():
        return redirect(url_for("web.login_page"))
    return render_template(
        "chat.html",
        role=session.get("role"),
        display_name=session.get("display_name"),
    )


@web_bp.route("/training")
def training_index():
    return render_template("training/index.html")


@web_bp.route("/training/architecture")
def training_architecture():
    return render_template("training/architecture.html")


@web_bp.route("/training/rbac")
def training_rbac():
    return render_template("training/rbac.html")


@web_bp.route("/training/audit")
def training_audit():
    return render_template("training/audit.html")


@web_bp.route("/training/hl7-fhir")
def training_hl7_fhir():
    return render_template("training/hl7_fhir.html")

@web_bp.route("/training/genai-agentic-langgraph")
def training_genai_agentic_langgraph():
    return render_template("training/genai_agentic_langgraph.html")

# MedFlow Agent Architecture Training Course
# These routes are part of the existing web_bp and existing Flask application.

@web_bp.route("/training/agent-course")
def training_agent_index():
    return render_template("training/agent_course/index.html")


@web_bp.route("/training/agent-course/app-bootstrap")
def training_agent_app_bootstrap():
    return render_template("training/agent_course/app_bootstrap.html")


@web_bp.route("/training/agent-course/project-structure")
def training_agent_project_structure():
    return render_template("training/agent_course/project_structure.html")


@web_bp.route("/training/agent-course/agent-folder")
def training_agent_agent_folder():
    return render_template("training/agent_course/agent_folder.html")


@web_bp.route("/training/agent-course/graph-wiring")
def training_agent_graph_wiring():
    return render_template("training/agent_course/graph_wiring.html")


@web_bp.route("/training/agent-course/react-loop")
def training_agent_react_loop():
    return render_template("training/agent_course/react_loop.html")


@web_bp.route("/training/agent-course/context-identity")
def training_agent_context_identity():
    return render_template("training/agent_course/context_identity.html")


@web_bp.route("/training/agent-course/api-client")
def training_agent_api_client():
    return render_template("training/agent_course/api_client.html")


@web_bp.route("/training/agent-course/chat-request")
def training_agent_chat_request():
    return render_template("training/agent_course/chat_request.html")


@web_bp.route("/training/agent-course/role-subgraphs")
def training_agent_role_subgraphs():
    return render_template("training/agent_course/role_subgraphs.html")


@web_bp.route("/training/agent-course/nurse")
def training_agent_nurse():
    return render_template("training/agent_course/nurse.html")


@web_bp.route("/training/agent-course/physician")
def training_agent_physician():
    return render_template("training/agent_course/physician.html")


@web_bp.route("/training/agent-course/admissions-pharmacy")
def training_agent_admissions_pharmacy():
    return render_template("training/agent_course/admissions_pharmacy.html")


@web_bp.route("/training/agent-course/business-legal")
def training_agent_business_legal():
    return render_template("training/agent_course/business_legal.html")


@web_bp.route("/training/agent-course/security-observability")
def training_agent_security_observability():
    return render_template("training/agent_course/security_observability.html")


@web_bp.route("/training/agent-course/end-to-end")
def training_agent_end_to_end():
    return render_template("training/agent_course/end_to_end.html")


@web_bp.route("/hipaa/review")
def hipaa_review():
    if not _require_login():
        return redirect(url_for("web.login_page"))
    if not _require_hipaa_admin():
        flash("The HIPAA Review dashboard is restricted to HIPAA_ADMIN accounts.", "warning")
        return redirect(url_for("web.dashboard"))
    return render_template(
        "hipaa_review.html",
        role=session.get("role"),
        display_name=session.get("display_name"),
    )