# MedFlow — Phase 1

HIPAA/HL7-pattern Agentic AI POC for a multi-hospital group.
Stack: **Python 3.12 · Flask · SQLAlchemy · MySQL 8.x · LangChain · LangGraph · Bootstrap 5 (Light Blue) · Keycloak 26 (PKCE)**

Phase 1 scope: **Admissions, Nurse, Pharmacist** skills, fully wired end-to-end
(chat → LangGraph → Flask REST API → MySQL, with RBAC + audit logging).
Physician / Finance / Management / Legal are schema-complete but not yet
wired to a subgraph — see **Phase 2** below for exactly how to add them.

---

## 1. Prerequisites

- Python 3.12
- MySQL 8.x running locally (or reachable)
- Keycloak 26 running locally (default assumed at `http://localhost:8080`)
- An Anthropic API key (for the LangGraph agent's LLM calls)
- PyCharm (or any IDE) — this project has no PyCharm-specific config beyond a
  standard Flask run configuration, described below

## 2. Project layout

```
medflow/
├── app.py                   # Flask app factory / entrypoint
├── config.py                # Config from .env
├── extensions.py            # db = SQLAlchemy()
├── requirements.txt
├── .env.example              # copy to .env and fill in
├── models/                   # SQLAlchemy models (1:1 with db/ddl.sql)
├── auth/                     # Keycloak PKCE flow, RBAC decorator, identity middleware
├── api/                      # Flask REST blueprints (patients, encounters, beds, meds, inventory, audit, chat)
├── agent/                    # LangGraph state, tools, per-role subgraphs, graph builder
│   └── subgraphs/            # nurse.py, pharmacy.py, admissions.py
├── web/                      # UI routes + Jinja templates (Bootstrap 5 Light Blue)
│   └── templates/training/   # Training menu pages
├── static/                   # theme.css, chat.js
├── db/                       # ddl.sql, seed.sql  <- load these into MySQL manually
├── keycloak/                 # medflow-realm.json, test_confidential_client.sh
└── scripts/                  # init_db.py (connectivity sanity check only)
```

## 3. Set up MySQL

```bash
mysql -u root -p < db/ddl.sql
mysql -u root -p medflow < db/seed.sql
```

`db/ddl.sql` creates the `medflow` schema and all Phase 1 + Phase 2 tables
(billing/audit/chat tables are included now so foreign keys never need
retrofitting later). `db/seed.sql` loads two hospitals, a handful of units
and beds, five staff records, two patients, two encounters, three medication
requests, and starter inventory.

**Important:** `db/seed.sql`'s `staff.keycloak_user_id` values are hardcoded
UUIDs that must exactly match the user `id` fields in
`keycloak/medflow-realm.json`. If you regenerate either file independently,
keep those UUIDs in sync or logins will succeed at Keycloak but fail to
resolve to a local staff/role record.

## 4. Set up Keycloak

1. In the Keycloak admin console: **Realm settings → Create realm → Import** and select `keycloak/medflow-realm.json`. This creates:
   - Realm roles: `PHYSICIAN`, `NURSE`, `PHARMACIST`, `ADMISSIONS`, `FINANCE`, `MANAGEMENT`, `LEGAL`, `ADMIN`
   - **`medflow-web`** — public client, Authorization Code + PKCE (S256), redirect URI `http://localhost:5000/*`
   - **`medflow-service`** — confidential client, direct access grants + service accounts enabled, used for bash/script testing and by the agent's internal service channel
   - Five test users: `nurse1` / `Nurse123!`, `pharm1` / `Pharm123!`, `admissions1` / `Admissions123!`, `physician1` / `Physician123!`, `svc.tester` / `TesterPass123!`
2. Note the **client secret** for `medflow-service` (Clients → medflow-service → Credentials tab) and put it in `.env` as `KEYCLOAK_CONFIDENTIAL_CLIENT_SECRET`. The realm export sets it to `change-me-service-secret` — rotate it if you re-import into a shared Keycloak instance.

## 5. Configure the app

```bash
cp .env.example .env
# then edit .env: MySQL credentials, Keycloak base URL/secret, ANTHROPIC_API_KEY
```

## 6. Install & run

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python scripts/init_db.py          # sanity check: confirms MySQL connectivity + seed data is visible
python app.py                      # runs on http://localhost:5000
```

Open `http://localhost:5000`, click **Sign in with Keycloak**, log in as
`nurse1` / `Nurse123!` (or `pharm1` / `admissions1`), and open **Assistant**
to chat. Try:
- as `nurse1`: *"Which patients are on unit 1 and what's their bed number?"*
- as `pharm1`: *"Check for interactions between warfarin and aspirin"*
- as `admissions1`: *"Look up patient MRN-100234"*

## 7. PyCharm setup

1. **Open** the extracted `medflow/` folder as a PyCharm project.
2. **Settings → Project → Python Interpreter → Add Interpreter → Virtualenv**, point it at Python 3.12, let PyCharm create `.venv` and install `requirements.txt` (or run the pip install manually as above).
3. **Run/Debug Configurations → Add → Python**: script path `app.py`, working directory = project root. Add a `.env` file as described above; `python-dotenv` loads it automatically via `config.py`.

## 8. Testing the confidential client / bash script path

```bash
chmod +x keycloak/test_confidential_client.sh
./keycloak/test_confidential_client.sh
```

This exercises the API purely over HTTP with Bearer tokens obtained from
the `medflow-service` confidential client (Resource Owner Password
Credentials grant) — no browser session involved — including a deliberate
negative test (a Nurse token calling an Admissions-only endpoint, expecting
HTTP 403). Requires `curl` and `jq`.

## 9. Implementation notes worth knowing before you extend this

- **Audit logging happens inside each Flask endpoint**, not as a separate
  post-hoc LangGraph node (see `api/_audit_helper.py`). This was a deliberate
  simplification from the original design sketch: writing the audit row in
  the same request as the data access guarantees it can't be skipped by an
  agent run failing partway through. See Training → Audit Logging Pattern.
- **Three ways the API resolves caller identity** (`auth/middleware.py`):
  browser session (PKCE), Bearer JWT (confidential client, verified against
  Keycloak's JWKS), and an internal service channel the agent uses to call
  its own REST API — which cross-checks the claimed role against the `staff`
  table rather than trusting a header. See Training → RBAC in LangGraph.
- **Role is fixed by identity, never by prompt text.** `api/chat.py` passes
  the session's role into `run_agent()`; nothing in the chat message itself
  can change which LangGraph subgraph or toolset gets used.

---

## Phase 2 — how to add a new role skill (Physician, Finance, Management, Legal)

Everything below is additive. You should not need to touch Phase 1 files
except `agent/graph.py`'s `ROLE_CONFIG` dict and, if the role needs new
endpoints, `api/__init__.py`'s blueprint registration.

1. **Endpoints** (if new ones are needed): add a new file under `api/`
   (e.g. `api/diagnoses.py`, `api/billing.py`), following the pattern in
   `api/medications.py` — use `@require_role(...)`, call `write_audit(...)`
   on every PHI-touching read/write, return `.to_dict()`. The models already
   exist (`models/encounter.py::Diagnosis`, `models/billing.py::BillingClaim`).
   Register the blueprint in `api/__init__.py`.
2. **Tools**: add `agent/subgraphs/physician.py` (or finance/management/legal),
   following `agent/subgraphs/nurse.py`'s pattern — `@tool`-decorated
   functions that call `agent/api_client.py`'s `api_get`/`api_post` against
   your new endpoints, reading identity from `agent/context.py`'s
   contextvars (never as an LLM-supplied argument).
3. **Wire it in**: in `agent/graph.py`, uncomment/add a line in `ROLE_CONFIG`:
   ```python
   from .subgraphs.physician import PHYSICIAN_TOOLS, PHYSICIAN_SYSTEM_PROMPT
   ROLE_CONFIG["PHYSICIAN"] = (PHYSICIAN_TOOLS, PHYSICIAN_SYSTEM_PROMPT)
   ```
   That's it — `_build_graph()` and `run_agent()` are role-agnostic and will
   pick it up automatically.
4. **Keycloak**: the `PHYSICIAN`, `FINANCE`, `MANAGEMENT`, `LEGAL` realm
   roles and a `physician1` test user already exist in
   `keycloak/medflow-realm.json` — add Finance/Management/Legal test users
   the same way if needed.
5. **Training page**: the Training menu structure (`web/templates/training/`)
   is ready for a new page per phase if you want a dedicated
   YouTube-recording page walking through the new skill.

Suggested Phase 2 build order: **Physician** (shares the most schema with
Nurse/Admissions — diagnoses, lab orders, discharge summaries) → **Finance**
→ **Management** → **Legal** (reads the same `audit_log` table this phase
already writes to).
