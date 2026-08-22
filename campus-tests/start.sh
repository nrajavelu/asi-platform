#!/usr/bin/env bash
# Starts the Aizentify Campus Test Console's local stack in the background:
#   1. Docker Desktop (if not already running)
#   2. Judge0 (self-hosted code execution engine, for coding rounds)
#   3. The admin dashboard (webui.py) on http://127.0.0.1:8787
#
# Does NOT start app.py (the candidate-facing LAN gate) - that binds to
# your whole network and is meant to run only during an actual live test
# window, not as routine background infra. Start it separately when you're
# about to run a session:
#   source .venv/bin/activate && python app.py
#
# Safe to re-run: anything already running is left alone.
#
# Usage:
#   ./start.sh

set -uo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
JUDGE0_DIR="$ROOT_DIR/judge0/judge0-v1.13.1"
PGVECTOR_DIR="$ROOT_DIR/pgvector"
REACT_GRADER_DIR="$ROOT_DIR/react_grader"
CSS_GRADER_DIR="$ROOT_DIR/css_grader"
PID_DIR="${TMPDIR:-/tmp}"
WEBUI_PID_FILE="$PID_DIR/campus-tests-webui.pid"
WEBUI_LOG="$ROOT_DIR/data/webui.log"

mkdir -p "$ROOT_DIR/data"
cd "$ROOT_DIR"

echo "== Aizentify Campus Test Console - start =="

# 1. Docker Desktop
if docker info > /dev/null 2>&1; then
  echo "[1/3] Docker Desktop already running."
else
  echo "[1/3] Starting Docker Desktop..."
  open -a Docker
  ready=0
  for i in $(seq 1 40); do
    if docker info > /dev/null 2>&1; then
      ready=1
      break
    fi
    sleep 5
  done
  if [ "$ready" -ne 1 ]; then
    echo "ERROR: Docker Desktop did not become ready after ~200s. Start it manually and re-run this script."
    exit 1
  fi
  echo "      Docker Desktop is ready."
fi

# 2. Judge0
echo "[2/3] Starting Judge0..."
if [ ! -d "$JUDGE0_DIR" ]; then
  echo "ERROR: $JUDGE0_DIR not found."
  exit 1
fi
(cd "$JUDGE0_DIR" && docker compose up -d) || { echo "ERROR: docker compose up failed for Judge0."; exit 1; }

echo "      Waiting for Judge0 to accept requests..."
source "$ROOT_DIR/.venv/bin/activate"
judge0_ready=0
for i in $(seq 1 30); do
  if python3 -c "from judge0_client import is_judge0_ready; import sys; sys.exit(0 if is_judge0_ready()[0] else 1)" 2>/dev/null; then
    judge0_ready=1
    break
  fi
  sleep 3
done
if [ "$judge0_ready" -eq 1 ]; then
  echo "      Judge0 is ready."
else
  echo "      WARNING: Judge0 did not respond in time. Coding rounds may not work yet -"
  echo "               check with: docker compose logs -f   (run from $JUDGE0_DIR)"
fi

# 2b. SQL/pgvector grading (only if the coding question bank actually has
# any 'sql' questions - most admins never pay this cost)
needs_sql=$(python3 -c "
from models import SessionLocal, CodingQuestion, init_db
init_db()
session = SessionLocal()
print(1 if session.query(CodingQuestion).filter_by(question_type='sql').first() else 0)
" 2>/dev/null)
if [ "$needs_sql" = "1" ]; then
  echo "      Coding bank has SQL questions - starting SQL grading Postgres..."
  (cd "$PGVECTOR_DIR" && docker compose up -d) || { echo "ERROR: docker compose up failed for pgvector."; exit 1; }
  sql_ready=0
  for i in $(seq 1 20); do
    if python3 -c "from sql_grader import is_pgvector_ready; import sys; sys.exit(0 if is_pgvector_ready()[0] else 1)" 2>/dev/null; then
      sql_ready=1
      break
    fi
    sleep 3
  done
  if [ "$sql_ready" -eq 1 ]; then
    echo "      SQL grading Postgres is ready."
  else
    echo "      WARNING: SQL grading Postgres did not respond in time - SQL questions may not work yet."
  fi
fi

# 2c. React grading image (only if the coding question bank actually has
# any 'react' questions)
needs_react=$(python3 -c "
from models import SessionLocal, CodingQuestion, init_db
init_db()
session = SessionLocal()
print(1 if session.query(CodingQuestion).filter_by(question_type='react').first() else 0)
" 2>/dev/null)
if [ "$needs_react" = "1" ]; then
  if docker image inspect campus-react-grader:latest > /dev/null 2>&1; then
    echo "      Coding bank has React questions - grading image already built."
  else
    echo "      Coding bank has React questions - building grading image (one-time)..."
    if [ ! -d "$REACT_GRADER_DIR/node_modules" ]; then
      echo "      ERROR: $REACT_GRADER_DIR/node_modules is missing - regenerate it first:"
      echo "        cd react_grader && rm -rf node_modules package-lock.json && \\"
      echo "        npm install --no-audit --no-fund --os=linux --cpu=x64 --libc=glibc"
    else
      (cd "$REACT_GRADER_DIR" && docker build -t campus-react-grader:latest .) || { echo "ERROR: docker build failed for react_grader."; exit 1; }
      echo "      React grading image built."
    fi
  fi
fi

# 2d. CSS grading image (only if the coding question bank actually has
# any 'css' questions)
needs_css=$(python3 -c "
from models import SessionLocal, CodingQuestion, init_db
init_db()
session = SessionLocal()
print(1 if session.query(CodingQuestion).filter_by(question_type='css').first() else 0)
" 2>/dev/null)
if [ "$needs_css" = "1" ]; then
  if docker image inspect campus-css-grader:latest > /dev/null 2>&1; then
    echo "      Coding bank has CSS questions - grading image already built."
  else
    echo "      Coding bank has CSS questions - building grading image (one-time, ~2GB base image)..."
    if [ ! -d "$CSS_GRADER_DIR/node_modules" ]; then
      echo "      ERROR: $CSS_GRADER_DIR/node_modules is missing - regenerate it first:"
      echo "        cd css_grader && rm -rf node_modules package-lock.json && \\"
      echo "        PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 npm install --no-audit --no-fund --os=linux --cpu=x64 --libc=glibc"
    else
      (cd "$CSS_GRADER_DIR" && docker build -t campus-css-grader:latest .) || { echo "ERROR: docker build failed for css_grader."; exit 1; }
      echo "      CSS grading image built."
    fi
  fi
fi

# 3. Admin dashboard
echo "[3/3] Starting admin dashboard..."
if [ -f "$WEBUI_PID_FILE" ] && kill -0 "$(cat "$WEBUI_PID_FILE")" 2>/dev/null; then
  echo "      Already running (PID $(cat "$WEBUI_PID_FILE"))."
elif lsof -i :8787 -sTCP:LISTEN > /dev/null 2>&1; then
  echo "      Port 8787 is already in use by another process (not one this script started -"
  echo "      probably a manually-run instance). Assuming it's already serving the dashboard."
else
  nohup python3 webui.py > "$WEBUI_LOG" 2>&1 &
  echo $! > "$WEBUI_PID_FILE"
  sleep 2
  if kill -0 "$(cat "$WEBUI_PID_FILE")" 2>/dev/null; then
    echo "      Running (PID $(cat "$WEBUI_PID_FILE")), log: $WEBUI_LOG"
  else
    echo "ERROR: Admin dashboard failed to start - check $WEBUI_LOG"
    exit 1
  fi
fi

echo
echo "== Ready =="
echo "Admin dashboard: http://127.0.0.1:8787"
echo "Judge0:          http://127.0.0.1:2358 (internal only - not for direct use)"
echo
echo "To run a live coding-round test session, start app.py separately"
echo "(it needs to stay attached to your LAN for the whole test window):"
echo "  source .venv/bin/activate && python app.py"
echo
echo "Run ./stop.sh when you're done for the day."
