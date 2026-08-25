"""
Small cross-platform helpers shared by start.py/stop.py: PID file
management and port-listening checks. Uses a local .run/ directory rather
than the system temp dir (avoids $TMPDIR vs %TEMP% differences across
macOS/Windows/Linux entirely) and Python's socket module rather than
lsof/netstat (neither exists on all three platforms; a raw TCP connect
attempt does the same job everywhere with no external tool at all).
"""

import os
import platform
import socket
import subprocess
from pathlib import Path

IS_WINDOWS = platform.system() == "Windows"

ROOT_DIR = Path(__file__).parent
RUN_DIR = ROOT_DIR / ".run"
WEBUI_PID_FILE = RUN_DIR / "webui.pid"
WEBUI_LOG = ROOT_DIR / "data" / "webui.log"
# app.py writes its per-run monitor secret here on startup so webui.py's
# Live Monitor page can proxy /monitor-data itself - the admin never has to
# copy a token URL, only app.py's own printed link needs it (candidates on
# the LAN reaching that link directly).
MONITOR_TOKEN_FILE = RUN_DIR / "monitor_token.txt"


def venv_python() -> Path:
    return ROOT_DIR / ".venv" / ("Scripts/python.exe" if IS_WINDOWS else "bin/python3")


def get_lan_ip() -> str | None:
    """Best-effort local LAN IP, freshly detected per call so it's always
    correct for whatever network this machine is currently on - no network
    traffic actually sent, this just asks the OS which interface/address
    would be used to reach an external host."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return None


def port_is_listening(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0


def pid_is_running(pid: int) -> bool:
    if IS_WINDOWS:
        out = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}"], capture_output=True, text=True
        )
        return str(pid) in out.stdout
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def kill_pid(pid: int) -> None:
    if IS_WINDOWS:
        subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)
        return
    import signal
    os.kill(pid, signal.SIGTERM)


def read_pid_file(path: Path) -> int | None:
    if not path.exists():
        return None
    try:
        return int(path.read_text().strip())
    except ValueError:
        return None
