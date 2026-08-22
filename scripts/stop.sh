#!/usr/bin/env bash
# Stops both local servers started by scripts/start.sh.
set -uo pipefail

PID_DIR="${TMPDIR:-/tmp}"
API_PID_FILE="$PID_DIR/asi-platform-api.pid"
DOCS_PID_FILE="$PID_DIR/asi-platform-docs.pid"

stop_one() {
  local name="$1" pid_file="$2"
  if [[ -f "$pid_file" ]]; then
    local pid
    pid="$(cat "$pid_file")"
    if kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null
      echo "Stopped $name (pid $pid)"
    else
      echo "$name was not running (removing stale pid file)"
    fi
    rm -f "$pid_file"
  else
    echo "$name is not running"
  fi
}

stop_one "API server" "$API_PID_FILE"
stop_one "Docs server" "$DOCS_PID_FILE"
