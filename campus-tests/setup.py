"""
One-time provisioning for the Aizentify Campus Test Console on a fresh
machine (macOS, Windows, or Linux) - run this once after `git clone`,
before ever using start.py.

What it does, in order:
  1. Checks Python and git are new enough / present.
  2. Checks Docker is installed and running - guides you through
     installing it if not (can't be silently automated: Docker Desktop's
     installer is a GUI flow on macOS/Windows, and it needs to be launched
     and accepted once by a human).
  3. Creates ./.venv and pip installs requirements.txt into it.
  4. Generates judge0/judge0-v1.13.1/judge0.conf from the checked-in
     .example template, with freshly random secrets - never reuses secrets
     across machines, and keeps credentials/judge0_token.txt in sync with
     whatever AUTHN_TOKEN it generates.
  5. Checks for credentials/client_secret.json (Google OAuth client) - this
     one genuinely can't be automated (it's created by hand in Google Cloud
     Console), so this step only guides you, it doesn't do it for you.
  6. If client_secret.json is present but credentials/token.json isn't,
     offers to run generate_refresh_token.py now (opens a browser for a
     one-time Google sign-in).

Safe to re-run: every step is skip-if-already-done, same idempotent
philosophy as the rest of this project's scripts.

Usage:
    python3 setup.py        (macOS/Linux)
    python setup.py         (Windows)
"""

import platform
import secrets
import shutil
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(line_buffering=True)  # keep our prints interleaved correctly with subprocess output

ROOT_DIR = Path(__file__).parent
VENV_DIR = ROOT_DIR / ".venv"
JUDGE0_DIR = ROOT_DIR / "judge0" / "judge0-v1.13.1"
CREDENTIALS_DIR = ROOT_DIR / "credentials"
MIN_PYTHON = (3, 10)

IS_WINDOWS = platform.system() == "Windows"


def step(msg: str) -> None:
    print(f"\n== {msg} ==")


def ok(msg: str) -> None:
    print(f"    OK: {msg}")


def warn(msg: str) -> None:
    print(f"    WARNING: {msg}")


def fail(msg: str) -> None:
    print(f"    ERROR: {msg}")


def venv_python() -> Path:
    return VENV_DIR / ("Scripts/python.exe" if IS_WINDOWS else "bin/python3")


def check_python() -> None:
    step("Checking Python version")
    if sys.version_info < MIN_PYTHON:
        fail(f"Python {'.'.join(map(str, MIN_PYTHON))}+ required, found {sys.version.split()[0]}.")
        raise SystemExit(1)
    ok(f"Python {sys.version.split()[0]}")


def check_git() -> None:
    step("Checking git")
    if shutil.which("git") is None:
        fail("git not found on PATH. Install it from https://git-scm.com/downloads and re-run this script.")
        raise SystemExit(1)
    ok("git found")


def check_docker() -> None:
    step("Checking Docker")
    if shutil.which("docker") is not None:
        try:
            subprocess.run(["docker", "info"], capture_output=True, timeout=10, check=True)
            ok("Docker is installed and running")
            return
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            warn("Docker is installed but doesn't seem to be running - start Docker Desktop, then re-run this script.")
            raise SystemExit(1)

    fail("Docker not found.")
    if platform.system() == "Darwin":
        print("    Install: https://www.docker.com/products/docker-desktop/")
        if shutil.which("brew"):
            print('    Or run: brew install --cask docker   (then launch it once from Applications)')
    elif IS_WINDOWS:
        print("    Install: https://www.docker.com/products/docker-desktop/")
        print("    Requires WSL2 - Docker Desktop's installer will guide you through enabling it if needed.")
        if shutil.which("winget"):
            print("    Or run: winget install Docker.DockerDesktop   (then launch it once and finish its setup)")
    else:
        print("    Install: https://docs.docker.com/engine/install/  (pick your distro)")
        print("    Then add your user to the docker group and re-login, or use sudo.")
    print("    Re-run this script once Docker is installed and running.")
    raise SystemExit(1)


def setup_venv_and_deps() -> None:
    step("Setting up Python virtual environment")
    if not VENV_DIR.exists():
        subprocess.run([sys.executable, "-m", "venv", str(VENV_DIR)], check=True)
        ok(f"Created {VENV_DIR}")
    else:
        ok(f"{VENV_DIR} already exists")

    step("Installing Python dependencies")
    subprocess.run(
        [str(venv_python()), "-m", "pip", "install", "--quiet", "--upgrade", "pip"], check=True
    )
    subprocess.run(
        [str(venv_python()), "-m", "pip", "install", "--quiet", "-r", str(ROOT_DIR / "requirements.txt")],
        check=True,
    )
    ok("requirements.txt installed")


def setup_judge0_conf() -> None:
    step("Setting up Judge0 configuration")
    conf_path = JUDGE0_DIR / "judge0.conf"
    template_path = JUDGE0_DIR / "judge0.conf.example"

    if conf_path.exists():
        ok(f"{conf_path} already exists, leaving it alone")
        return
    if not template_path.exists():
        fail(f"Missing template: {template_path}")
        raise SystemExit(1)

    auth_token = secrets.token_urlsafe(32)
    redis_password = secrets.token_urlsafe(24)
    postgres_password = secrets.token_urlsafe(24)

    content = template_path.read_text()
    content = content.replace("{{AUTHN_TOKEN}}", auth_token)
    content = content.replace("{{REDIS_PASSWORD}}", redis_password)
    content = content.replace("{{POSTGRES_PASSWORD}}", postgres_password)
    conf_path.write_text(content)
    ok(f"Generated {conf_path} with fresh secrets")

    CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
    token_file = CREDENTIALS_DIR / "judge0_token.txt"
    token_file.write_text(auth_token)
    ok(f"Wrote matching AUTHN_TOKEN to {token_file}")


def setup_google_credentials() -> None:
    step("Checking Google API credentials")
    CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
    client_secret = CREDENTIALS_DIR / "client_secret.json"
    token_file = CREDENTIALS_DIR / "token.json"

    if not client_secret.exists():
        warn(f"{client_secret} not found - this can't be automated.")
        print("    1. Go to https://console.cloud.google.com/apis/credentials")
        print("    2. Create an OAuth 2.0 Client ID (Desktop app), for the Google account")
        print("       that should own the Forms/Gmail this console creates and sends from.")
        print("    3. Download the JSON and save it exactly as:")
        print(f"       {client_secret}")
        print("    4. Re-run this script once that's done, to complete the sign-in step.")
        return

    ok(f"{client_secret} found")
    if token_file.exists():
        ok(f"{token_file} already exists")
        return

    warn(f"{token_file} not found - one-time Google sign-in needed.")
    answer = input("    Run the sign-in flow now? It opens a browser window. [y/N] ").strip().lower()
    if answer != "y":
        print(f"    Skipped. Run later with: {venv_python()} generate_refresh_token.py")
        return
    subprocess.run([str(venv_python()), str(ROOT_DIR / "generate_refresh_token.py")], check=True)
    ok("Signed in, token.json written")


def main() -> None:
    print(f"Aizentify Campus Test Console setup - {platform.system()} {platform.release()}")
    check_python()
    check_git()
    check_docker()
    setup_venv_and_deps()
    setup_judge0_conf()
    setup_google_credentials()

    print("\n== Done ==")
    print("Next: python3 start.py   (macOS/Linux)   or   python start.py   (Windows)")


if __name__ == "__main__":
    main()
