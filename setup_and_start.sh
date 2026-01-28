#!/usr/bin/env bash
set -euo pipefail

# setup_and_start.sh
# Usage:
#   ./setup_and_start.sh                # create venv, install deps, run tests (if available), start uvicorn
#   ./setup_and_start.sh --start-streamlit            # also start Streamlit UI (background)
#   ./setup_and_start.sh --start-streamlit --streamlit-port 8502

START_STREAMLIT=0
STREAMLIT_PORT=8501

usage() {
  cat <<EOF
Usage: $0 [--start-streamlit] [--streamlit-port PORT]

Options:
  --start-streamlit        Start the Streamlit UI after starting uvicorn (runs in background)
  --streamlit-port PORT    Port for Streamlit server (default: 8501)
  -h, --help               Show this help message
EOF
  exit 1
}

# parse args
while [[ $# -gt 0 ]]; do
  case $1 in
    --start-streamlit) START_STREAMLIT=1; shift ;;
    --streamlit-port) STREAMLIT_PORT="$2"; shift 2 ;;
    -h|--help) usage ;;
    *) echo "Unknown argument: $1"; usage ;;
  esac
done

echo "=== NotesVault setup and start script ==="

# 1) Create venv if missing
if [ ! -d ".venv" ]; then
  echo "Creating virtualenv .venv..."
  python3 -m venv .venv
else
  echo "Using existing .venv"
fi

# Activate venv
# shellcheck source=/dev/null
source .venv/bin/activate

# 2) Upgrade pip and install requirements
echo "Upgrading pip and installing dependencies..."
pip install --upgrade pip
if [ -f requirements.txt ]; then
  pip install -r requirements.txt
else
  echo "requirements.txt not found — installing minimal dependencies"
  pip install fastapi uvicorn[standard] SQLAlchemy python-jose[cryptography] passlib[bcrypt] pydantic streamlit requests pytest
fi

# 3) Run tests if pytest is available
if command -v pytest >/dev/null 2>&1; then
  echo "Running pytest..."
  if pytest -q; then
    echo "Tests passed."
  else
    echo "Some tests failed. See pytest output above. Continuing to start the app."
  fi
else
  echo "pytest not installed — skipping tests"
fi

# 4) Ensure DB tables exist (uses the app's Base metadata)
echo "Creating/verifying database tables..."
python - <<'PY'
from app.db.database import engine, Base
Base.metadata.create_all(bind=engine)
print('DB tables created/verified')
PY

# 5) Start uvicorn (background)
UVICORN_LOG=uvicorn.log
echo "Starting uvicorn in background (logs -> $UVICORN_LOG)..."
nohup .venv/bin/uvicorn main:app --reload --host 0.0.0.0 --port 8000 > "$UVICORN_LOG" 2>&1 &
UVICORN_PID=$!
echo "Uvicorn started (PID $UVICORN_PID)."

# 6) Optionally start Streamlit in background
if [ "$START_STREAMLIT" -eq 1 ]; then
  STREAMLIT_LOG=streamlit.log
  echo "Starting Streamlit in background on port $STREAMLIT_PORT (logs -> $STREAMLIT_LOG)..."
  # disable telemetry for Streamlit runs started by this script
  export STREAMLIT_DISABLE_TELEMETRY=1

  # create a project-level secrets.toml with API_BASE if missing (convenience for this script)
  if [ ! -d ".streamlit" ]; then
    mkdir -p .streamlit
  fi
  if [ ! -f ".streamlit/secrets.toml" ]; then
    cat > .streamlit/secrets.toml <<EOF
API_BASE = "http://127.0.0.1:8000"
EOF
    echo "Created .streamlit/secrets.toml with default API_BASE"
  fi

  nohup .venv/bin/streamlit run streamlit_app.py --server.port "$STREAMLIT_PORT" --server.address 0.0.0.0 > "$STREAMLIT_LOG" &
  STREAMLIT_PID=$!
  echo "Streamlit started (PID $STREAMLIT_PID)."
else
  echo "To start Streamlit UI, run: STREAMLIT_DISABLE_TELEMETRY=1 .venv/bin/streamlit run streamlit_app.py"
fi

echo "Setup and start complete."
echo "FastAPI: http://127.0.0.1:8000"
if [ "$START_STREAMLIT" -eq 1 ]; then
  echo "Streamlit: http://127.0.0.1:$STREAMLIT_PORT"
fi
