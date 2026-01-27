# NoteVault

Version: 1.0

A small notes application built with FastAPI + SQLAlchemy and a simple Streamlit UI. This repository implements user signup/login (JWT token flow), per-user notes CRUD, tests, and helper scripts to run the app locally.

---

## Features

- FastAPI backend with routes for health, user signup/login, and notes CRUD
- SQLite (file-based) database for development (`notes_app.db`) using SQLAlchemy ORM
- User model with hashed passwords (server-side hashing) and JWT access tokens
- Note model tied to a user (owner) with create/read/update/delete operations
- Streamlit UI client (`streamlit_app.py`) for signing up, logging in, and managing notes
- Tests using pytest + FastAPI TestClient that run against an in-memory SQLite DB
- Convenience script `setup_and_start.sh` to bootstrap environment, create DB tables and start servers
- Telemetry disabled by default for privacy (project-level Streamlit config)

---

## Quickstart (local, macOS / zsh)

1. Clone or open the project in your working directory.
2. Make the helper script executable and run it (recommended):

```bash
chmod +x setup_and_start.sh
./setup_and_start.sh --start-streamlit
```

What the script does (default behavior):
- Creates a Python venv at `./.venv` if missing and installs dependencies from `requirements.txt`.
- Runs tests (if `pytest` is present) and prints results.
- Creates/validates database tables using SQLAlchemy's `Base.metadata.create_all`.
- Starts Uvicorn (FastAPI) in the background (logs → `uvicorn.log`).
- Optionally starts Streamlit in the background (logs → `streamlit.log`) and ensures telemetry is disabled for that run.

Manual alternative (step-by-step):

```bash
# create and activate venv
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# start the API (foreground)
.venv/bin/uvicorn main:app --reload --host 127.0.0.1 --port 8000

# start the UI (in a separate terminal)
# disable telemetry for this run
STREAMLIT_DISABLE_TELEMETRY=1 .venv/bin/streamlit run streamlit_app.py
```

Open the UI at: `http://localhost:8501` (Streamlit) and the API docs at: `http://127.0.0.1:8000/docs`.

---

## Configuration

- `app/config.py` contains simple configuration constants used by the app:
  - `SECRET_KEY` — change this in production to a secure random value.
  - `ALGORITHM` and `ACCESS_TOKEN_EXPIRE_MINUTES` for JWT tokens.
- Streamlit secrets (optional): `.streamlit/secrets.toml` may contain `API_BASE = "http://127.0.0.1:8000"` to override the API base URL used by the UI.
- Telemetry: a project-level `.streamlit/config.toml` with `gatherUsageStats = false` has been added to prevent analytics being sent.

Security note: do not commit production secrets to the repo. Prefer environment variables or a configured secrets manager for deployment.

---

## API Endpoints

Base URL: `http://127.0.0.1:8000`

Health & meta
- GET `/health` — Returns `{"status": "ok"}`
- GET `/` — Returns `{"message":"Hello World"}`

User (authentication)
- POST `/users/` — Signup. JSON body: `{ "username": "alice", "password": "secret" }`. Returns created user (id, username).
- POST `/users/token` — OAuth2 password flow to obtain JWT token. Form data: `username` & `password`. Returns `{ "access_token": "...", "token_type": "bearer" }`.
- GET `/users/me` — Returns the current user; requires `Authorization: Bearer <token>` header.

Notes (authenticated; require Bearer token)
- POST `/notes/` — Create a note. JSON: `{ "title": "Title", "content": "..." }`. Returns created note.
- GET `/notes/` — List notes owned by the authenticated user. Returns JSON list.
- GET `/notes/{note_id}` — Get a single note (owner-only).
- PUT `/notes/{note_id}` — Update a note (owner-only). JSON: `{ "title": ..., "content": ... }`.
- DELETE `/notes/{note_id}` — Delete a note (owner-only).

Use the interactive docs at `/docs` to try requests with the Swagger UI (you can paste a Bearer token there to authorize requests).

---

## Streamlit UI (`streamlit_app.py`)

Features:
- Signup and Login in the sidebar
- After login, lists all notes for the current user
- Create new notes with a form
- Edit and delete notes inline
- Shows the configured API base in the sidebar and a warning if the default is used

If you run the Streamlit UI and you do not see notes after login:
- Verify the backend is running (curl `http://127.0.0.1:8000/health`).
- Confirm the sidebar API base matches where your API runs.
- Open browser DevTools → Network and inspect the `/notes/` request (Authorization header and responses).

---

## Tests

- `tests/test_database.py` validates that the DB engine and session can execute a basic query.
- `app/tests/test_api.py` (or `tests/test_api.py`) contains pytest tests that exercise signup, token generation, and the full notes CRUD flow using an in-memory SQLite DB and FastAPI TestClient.

Run tests:

```bash
# run all tests
pytest -q

# or run just the API tests
pytest -q app/tests/test_api.py
```

---

## Troubleshooting & common issues

- bcrypt / passlib errors: the project uses `pbkdf2_sha256` via passlib to avoid native bcrypt wheel issues. If you prefer bcrypt, install the `bcrypt` package with appropriate system dependencies.
- "No such table" when running tests: ensure you run the provided pytest test file which uses an in-memory DB with a shared connection; run `pytest --cache-clear` if you hit stale caches.
- Telemetry: if you see POSTs to `webhooks.fivetran.com` they are Streamlit telemetry; telemetry is disabled by default in the project config, and the start script sets `STREAMLIT_DISABLE_TELEMETRY=1` when launching Streamlit.

---

## Development notes & next steps

Possible improvements and next tasks:
- Use Alembic for DB migrations instead of `create_all`.
- Add stronger password policy and rate-limiting on auth endpoints.
- Replace server-side truncation with a pre-hash approach (SHA-256 then KDF) to preserve passphrase entropy.
- Add pagination, search and sorting for notes in the API and UI.
- Add CI workflow (GitHub Actions) to run unit tests on each push.

---

If you want, I can also generate a small architecture diagram (endpoints, models, flow) or add a GitHub Actions workflow that runs `pytest` on every push. Just tell me which you prefer.
