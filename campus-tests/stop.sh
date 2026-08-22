#!/usr/bin/env bash
# Stops what start.sh started: the admin dashboard and the Judge0 stack
# (containers are stopped, not removed - quick to resume next time).
#
# Leaves Docker Desktop itself running (quit it manually if you want to),
# and does NOT touch app.py - if you started that separately for a live
# session, stop it in its own terminal.
#
# Usage:
#   ./stop.sh

set -uo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
JUDGE0_DIR="$ROOT_DIR/judge0/judge0-v1.13.1"
PGVECTOR_DIR="$ROOT_DIR/pgvector"
PID_DIR="${TMPDIR:-/tmp}"
WEBUI_PID_FILE="$PID_DIR/campus-tests-webui.pid"

echo "== Aizentify Campus Test Console - stop =="

if [ -f "$WEBUI_PID_FILE" ]; then
  pid="$(cat "$WEBUI_PID_FILE")"
  if kill -0 "$pid" 2>/dev/null; then
    kill "$pid"
    echo "Stopped admin dashboard (PID $pid)."
  else
    echo "Admin dashboard was not running."
  fi
  rm -f "$WEBUI_PID_FILE"
else
  echo "Admin dashboard was not running (no PID file)."
fi

if [ -d "$JUDGE0_DIR" ]; then
  echo "Stopping Judge0 (containers kept, quick to restart)..."
  (cd "$JUDGE0_DIR" && docker compose stop)
fi

if [ -d "$PGVECTOR_DIR" ] && docker compose -f "$PGVECTOR_DIR/docker-compose.yml" ps -q 2>/dev/null | grep -q .; then
  echo "Stopping SQL grading Postgres (container kept, quick to restart)..."
  (cd "$PGVECTOR_DIR" && docker compose stop)
fi

if lsof -i :8788 -sTCP:LISTEN > /dev/null 2>&1; then
  echo
  echo "NOTE: something is still listening on port 8788 (app.py) - this script"
  echo "      doesn't manage that. Stop it in its own terminal if it's still running."
fi

echo
echo "Done. Docker Desktop itself was left running."
