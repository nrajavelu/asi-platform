#!/usr/bin/env bash
# Starts both local servers for the ASI Platform POC:
#   - the FastAPI backend (poc-backend/)      -> http://localhost:$ASI_API_PORT
#   - a static file server for docs/           -> http://localhost:$ASI_DOCS_PORT
#
# Safe to re-run: if a server is already up, it's left alone.
#
# Usage:
#   scripts/start.sh
#   ASI_API_PORT=8001 ASI_DOCS_PORT=8081 scripts/start.sh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_PORT="${ASI_API_PORT:-8000}"
DOCS_PORT="${ASI_DOCS_PORT:-8080}"

PID_DIR="${TMPDIR:-/tmp}"
API_PID_FILE="$PID_DIR/asi-platform-api.pid"
DOCS_PID_FILE="$PID_DIR/asi-platform-docs.pid"

LOG_DIR="$ROOT_DIR/scripts/.logs"
mkdir -p "$LOG_DIR"
API_LOG="$LOG_DIR/api.log"
DOCS_LOG="$LOG_DIR/docs.log"

is_running() {
  [[ -f "$1" ]] && kill -0 "$(cat "$1")" 2>/dev/null
}

# --- API server ---------------------------------------------------------
if is_running "$API_PID_FILE"; then
  echo "API server already running (pid $(cat "$API_PID_FILE"))"
else
  if [[ ! -d "$ROOT_DIR/poc-backend/.venv" ]]; then
    echo "poc-backend/.venv not found. Set it up first:"
    echo "  cd poc-backend && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    exit 1
  fi
  (
    cd "$ROOT_DIR/poc-backend"
    # shellcheck disable=SC1091
    source .venv/bin/activate
    nohup python3 cli.py serve --port "$API_PORT" > "$API_LOG" 2>&1 &
    echo $! > "$API_PID_FILE"
  )
  sleep 1
  if is_running "$API_PID_FILE"; then
    echo "API server started (pid $(cat "$API_PID_FILE")), logging to $API_LOG"
  else
    echo "API server failed to start -- check $API_LOG"
    rm -f "$API_PID_FILE"
  fi
fi

# --- Static docs server --------------------------------------------------
if is_running "$DOCS_PID_FILE"; then
  echo "Docs server already running (pid $(cat "$DOCS_PID_FILE"))"
else
  (
    cd "$ROOT_DIR/docs"
    nohup python3 -m http.server "$DOCS_PORT" > "$DOCS_LOG" 2>&1 &
    echo $! > "$DOCS_PID_FILE"
  )
  sleep 1
  if is_running "$DOCS_PID_FILE"; then
    echo "Docs server started (pid $(cat "$DOCS_PID_FILE")), logging to $DOCS_LOG"
  else
    echo "Docs server failed to start -- check $DOCS_LOG"
    rm -f "$DOCS_PID_FILE"
  fi
fi

cat <<URLS

Check these URLs:
  API -- interactive docs   http://localhost:$API_PORT/docs
  API -- cases list         http://localhost:$API_PORT/api/v1/cases
  API -- health check       http://localhost:$API_PORT/health

  ASI Console                http://localhost:$DOCS_PORT/asi-console.html
  ASI Platform (pitch page)  http://localhost:$DOCS_PORT/asi-platform.html
  ASI Platform Briefing deck http://localhost:$DOCS_PORT/asi-platform-deck.html

Run scripts/stop.sh to stop both servers.
URLS
