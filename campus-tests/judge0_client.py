"""
Thin client for the locally self-hosted Judge0 instance (started via
`docker compose up -d` in judge0/judge0-v1.13.1/). Never call this from
anywhere candidates can reach directly - it stays behind app.py.
"""

from pathlib import Path

import requests

BASE_URL = "http://127.0.0.1:2358"
TOKEN_FILE = Path(__file__).parent / "credentials" / "judge0_token.txt"

STATUS_ACCEPTED = 3


def _auth_headers() -> dict:
    token = TOKEN_FILE.read_text().strip()
    return {"X-Auth-Token": token, "Content-Type": "application/json"}


def is_judge0_ready() -> tuple[bool, str]:
    """Lightweight reachability + auth check - call this before sending
    coding-round invites so candidates never hit a session with a dead
    execution backend."""
    try:
        resp = requests.get(f"{BASE_URL}/languages", headers=_auth_headers(), timeout=5)
    except requests.exceptions.ConnectionError:
        return False, (
            f"Cannot reach Judge0 at {BASE_URL} - is it running? "
            f"(docker compose up -d in judge0/judge0-v1.13.1/)"
        )
    except Exception as e:
        return False, f"Judge0 check failed: {e}"

    if resp.status_code == 200:
        return True, "Judge0 is reachable and responding."
    return False, f"Judge0 responded with HTTP {resp.status_code} - check it's running correctly."


def run_submission(source_code: str, language_id: int, stdin: str, expected_output: str) -> dict:
    """Submits one program against one test case and waits for the result.
    Returns Judge0's raw response dict (stdout, status, time, memory, ...)."""
    resp = requests.post(
        f"{BASE_URL}/submissions",
        params={"base64_encoded": "false", "wait": "true"},
        json={
            "source_code": source_code,
            "language_id": language_id,
            "stdin": stdin,
            "expected_output": expected_output,
        },
        headers=_auth_headers(),
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def run_against_test_cases(source_code: str, language_id: int, test_cases: list) -> list[dict]:
    """test_cases: list of objects with .stdin, .expected_output, .weight
    (CodingTestCase rows work directly). Returns one result dict per test
    case: {passed, stdout, expected_output, status, time, memory, weight}."""
    results = []
    for tc in test_cases:
        raw = run_submission(source_code, language_id, tc.stdin, tc.expected_output)
        passed = raw["status"]["id"] == STATUS_ACCEPTED
        results.append({
            "passed": passed,
            "stdout": (raw.get("stdout") or "").rstrip("\n"),
            "stderr": raw.get("stderr"),
            "compile_output": raw.get("compile_output"),
            "expected_output": tc.expected_output,
            "status": raw["status"]["description"],
            "time": raw.get("time"),
            "memory": raw.get("memory"),
            "weight": tc.weight,
        })
    return results
