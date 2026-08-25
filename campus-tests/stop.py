"""
Stops what start.py started: the admin dashboard and the Judge0/pgvector
stacks (containers are stopped, not removed - quick to resume next time).

Leaves Docker itself running (quit it manually if you want to), and does
NOT touch app.py - if you started that separately for a live session,
stop it in its own terminal.

Usage:
    python3 stop.py    (macOS/Linux)
    python stop.py      (Windows)
"""

import subprocess
import sys

from proc_utils import ROOT_DIR, WEBUI_PID_FILE, kill_pid, pid_is_running, port_is_listening, read_pid_file

sys.stdout.reconfigure(line_buffering=True)  # keep our prints interleaved correctly with subprocess output

JUDGE0_DIR = ROOT_DIR / "judge0" / "judge0-v1.13.1"
PGVECTOR_DIR = ROOT_DIR / "pgvector"


def stop_webui() -> None:
    pid = read_pid_file(WEBUI_PID_FILE)
    if pid is None:
        if port_is_listening(8787):
            print("Something is listening on port 8787 but there's no PID file for it - probably")
            print("started outside start.py (e.g. the old start.sh, or run manually). Stop it yourself:")
            print("  lsof -i :8787 -sTCP:LISTEN   (find the PID)   then   kill <pid>")
        else:
            print("Admin dashboard was not running (no PID file).")
        return
    if pid_is_running(pid):
        kill_pid(pid)
        print(f"Stopped admin dashboard (PID {pid}).")
    else:
        print("Admin dashboard was not running.")
    WEBUI_PID_FILE.unlink(missing_ok=True)


def compose_project_exists(compose_dir) -> bool:
    result = subprocess.run(
        ["docker", "compose", "-f", str(compose_dir / "docker-compose.yml"), "ps", "-q"],
        capture_output=True, text=True,
    )
    return bool(result.stdout.strip())


def main() -> None:
    print("== Aizentify Campus Test Console - stop ==")
    stop_webui()

    if JUDGE0_DIR.exists():
        print("Stopping Judge0 (containers kept, quick to restart)...")
        subprocess.run(["docker", "compose", "stop"], cwd=JUDGE0_DIR)

    if PGVECTOR_DIR.exists() and compose_project_exists(PGVECTOR_DIR):
        print("Stopping SQL grading Postgres (container kept, quick to restart)...")
        subprocess.run(["docker", "compose", "stop"], cwd=PGVECTOR_DIR)

    if port_is_listening(8788):
        print()
        print("NOTE: something is still listening on port 8788 (app.py) - this script")
        print("      doesn't manage that. Stop it in its own terminal if it's still running.")

    print("\nDone. Docker itself was left running.")


if __name__ == "__main__":
    main()
