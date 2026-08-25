"""
Starts the Aizentify Campus Test Console's local stack in the background:
  1. Docker (if not already running)
  2. Judge0 (self-hosted code execution engine, for coding rounds) +
     SQL grading Postgres (always started, same reasoning as Judge0 - see
     inline comment below)
  2b/2c. React/CSS grading images (built once, only if the coding bank
     actually has that question type)
  3. The admin dashboard (webui.py) on http://127.0.0.1:8787

Does NOT start app.py (the candidate-facing LAN gate) - that binds to
your whole network and is meant to run only during an actual live test
window, not as routine background infra. Start it separately when you're
about to run a session:
    <venv python> app.py

Cross-platform (macOS/Windows/Linux) - see proc_utils.py for how the
OS-specific bits (process liveness, port checks) are unified rather than
duplicated per platform.

Safe to re-run: anything already running is left alone.

Usage:
    python3 start.py    (macOS/Linux)
    python start.py      (Windows)
"""

import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path

from proc_utils import (
    IS_WINDOWS, RUN_DIR, WEBUI_LOG, WEBUI_PID_FILE, ROOT_DIR,
    pid_is_running, port_is_listening, read_pid_file, venv_python,
)

sys.stdout.reconfigure(line_buffering=True)  # keep our prints interleaved correctly with subprocess output

JUDGE0_DIR = ROOT_DIR / "judge0" / "judge0-v1.13.1"
PGVECTOR_DIR = ROOT_DIR / "pgvector"
REACT_GRADER_DIR = ROOT_DIR / "react_grader"
CSS_GRADER_DIR = ROOT_DIR / "css_grader"


def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, **kw)


def docker_info_ok() -> bool:
    try:
        run(["docker", "info"], capture_output=True, timeout=10, check=True)
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return False


def start_docker_desktop() -> None:
    system = platform.system()
    if system == "Darwin":
        subprocess.run(["open", "-a", "Docker"])
    elif system == "Windows":
        candidates = [
            r"C:\Program Files\Docker\Docker\Docker Desktop.exe",
            r"C:\Program Files\Docker\Docker\resources\bin\docker.exe",
        ]
        launched = False
        for c in candidates:
            if Path(c).exists():
                subprocess.Popen([c])
                launched = True
                break
        if not launched:
            print("      Could not find Docker Desktop automatically - launch it manually, then re-run.")
            raise SystemExit(1)
    else:
        print("      Docker isn't running. On Linux this is usually a service: try `sudo systemctl start docker`.")
        raise SystemExit(1)


def ensure_docker() -> None:
    print("[1/3] Checking Docker...")
    if docker_info_ok():
        print("      Docker already running.")
        return
    print("      Starting Docker...")
    start_docker_desktop()
    for _ in range(40):
        if docker_info_ok():
            print("      Docker is ready.")
            return
        time.sleep(5)
    print("ERROR: Docker did not become ready after ~200s. Start it manually and re-run this script.")
    raise SystemExit(1)


def wait_ready(check_module: str, check_call: str, tries: int, delay: float, label: str) -> bool:
    for _ in range(tries):
        result = run(
            [str(venv_python()), "-c", f"from {check_module} import {check_call}; import sys; sys.exit(0 if {check_call}()[0] else 1)"],
            capture_output=True,
        )
        if result.returncode == 0:
            return True
        time.sleep(delay)
    return False


def start_judge0() -> None:
    print("[2/3] Starting Judge0...")
    if not JUDGE0_DIR.exists():
        print(f"ERROR: {JUDGE0_DIR} not found.")
        raise SystemExit(1)
    if run(["docker", "compose", "up", "-d"], cwd=JUDGE0_DIR).returncode != 0:
        print("ERROR: docker compose up failed for Judge0.")
        raise SystemExit(1)

    print("      Waiting for Judge0 to accept requests...")
    if wait_ready("judge0_client", "is_judge0_ready", tries=30, delay=3, label="Judge0"):
        print("      Judge0 is ready.")
    else:
        print("      WARNING: Judge0 did not respond in time. Coding rounds may not work yet -")
        print(f"               check with: docker compose logs -f   (run from {JUDGE0_DIR})")


def start_pgvector() -> None:
    # Started unconditionally, same reasoning as Judge0 - a bank-content
    # check here only ever runs at start.py time, so adding a SQL question
    # after the last restart would leave this silently stopped until the
    # next one, failing the invite pre-flight check for a reason unrelated
    # to that specific run. A single lightweight Postgres container is
    # cheap enough to just always have up.
    print("      Starting SQL grading Postgres...")
    if run(["docker", "compose", "up", "-d"], cwd=PGVECTOR_DIR).returncode != 0:
        print("ERROR: docker compose up failed for pgvector.")
        raise SystemExit(1)
    if wait_ready("sql_grader", "is_pgvector_ready", tries=20, delay=3, label="SQL grading Postgres"):
        print("      SQL grading Postgres is ready.")
    else:
        print("      WARNING: SQL grading Postgres did not respond in time - SQL questions may not work yet.")


def bank_has_question_type(qtype: str) -> bool:
    code = (
        "from models import SessionLocal, CodingQuestion, init_db; init_db(); "
        f"session = SessionLocal(); "
        f"import sys; sys.exit(0 if session.query(CodingQuestion).filter_by(question_type={qtype!r}).first() else 1)"
    )
    return run([str(venv_python()), "-c", code], capture_output=True).returncode == 0


def docker_image_exists(tag: str) -> bool:
    return run(["docker", "image", "inspect", tag], capture_output=True).returncode == 0


def build_grader_image(qtype: str, grader_dir: Path, tag: str, npm_extra: str = "") -> None:
    if not bank_has_question_type(qtype):
        return
    if docker_image_exists(tag):
        print(f"      Coding bank has {qtype} questions - grading image already built.")
        return
    print(f"      Coding bank has {qtype} questions - building grading image (one-time)...")
    if not (grader_dir / "node_modules").exists():
        print(f"      ERROR: {grader_dir / 'node_modules'} is missing - regenerate it first:")
        print(f"        cd {grader_dir.name} && rm -rf node_modules package-lock.json && \\")
        print(f"        {npm_extra}npm install --no-audit --no-fund --os=linux --cpu=x64 --libc=glibc")
        return
    if run(["docker", "build", "-t", tag, "."], cwd=grader_dir).returncode != 0:
        print(f"ERROR: docker build failed for {grader_dir.name}.")
        raise SystemExit(1)
    print(f"      {qtype.upper()} grading image built.")


def start_webui() -> None:
    print("[3/3] Starting admin dashboard...")
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    (ROOT_DIR / "data").mkdir(parents=True, exist_ok=True)

    existing_pid = read_pid_file(WEBUI_PID_FILE)
    if existing_pid is not None and pid_is_running(existing_pid):
        print(f"      Already running (PID {existing_pid}).")
        return
    if port_is_listening(8787):
        print("      Port 8787 is already in use by another process (not one this script started -")
        print("      probably a manually-run instance). Assuming it's already serving the dashboard.")
        return

    log_file = open(WEBUI_LOG, "wb")
    creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if IS_WINDOWS else 0
    proc = subprocess.Popen(
        [str(venv_python()), "webui.py"],
        cwd=ROOT_DIR, stdout=log_file, stderr=subprocess.STDOUT,
        creationflags=creationflags,
    )
    WEBUI_PID_FILE.write_text(str(proc.pid))
    time.sleep(2)
    if pid_is_running(proc.pid):
        print(f"      Running (PID {proc.pid}), log: {WEBUI_LOG}")
    else:
        print(f"ERROR: Admin dashboard failed to start - check {WEBUI_LOG}")
        raise SystemExit(1)


def main() -> None:
    if not venv_python().exists():
        print("ERROR: .venv not found - run setup.py first.")
        raise SystemExit(1)

    print("== Aizentify Campus Test Console - start ==")
    ensure_docker()
    start_judge0()
    start_pgvector()
    build_grader_image("react", REACT_GRADER_DIR, "campus-react-grader:latest")
    build_grader_image(
        "css", CSS_GRADER_DIR, "campus-css-grader:latest", npm_extra="PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 "
    )
    start_webui()

    print("\n== Ready ==")
    print("Admin dashboard: http://127.0.0.1:8787")
    print("Judge0:          http://127.0.0.1:2358 (internal only - not for direct use)")
    print("\nTo run a live coding-round test session, start app.py separately")
    print("(it needs to stay attached to your LAN for the whole test window):")
    print(f"  {venv_python()} app.py")
    print("\nRun stop.py when you're done for the day.")


if __name__ == "__main__":
    main()
