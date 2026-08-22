"""
Grades "react" question_type submissions in an ephemeral, sandboxed Docker
container (campus-react-grader:latest, built from react_grader/) - one
container per test case, mirroring how judge0_client treats one Judge0
submission per test case. Never call this from anywhere candidates can
reach directly - it stays behind app.py.

Sandboxing: --network none (no exfiltration/network abuse), --read-only +
--tmpfs /tmp (no filesystem tampering), --memory/--cpus caps + a hard
subprocess timeout (no runaway loops hanging the harness or the host).
--security-opt seccomp=unconfined is also required - Node can't create its
own background V8/libuv threads under this Docker Desktop/macOS 12 VM's
default seccomp profile (the same family of low-level fork/thread
restriction that needed `privileged: true` for Judge0's own postgres/redis
containers). This flag only relaxes the syscall filter - it does not grant
extra capabilities or device access the way `--privileged` would, so the
rest of the sandboxing above still fully applies.
"""

import json
import subprocess
import tempfile
import uuid
from pathlib import Path

IMAGE = "campus-react-grader:latest"
RUN_TIMEOUT_SECONDS = 20  # container startup (Node + jsdom + esbuild) alone takes ~3-9s on this machine


def is_react_grader_ready() -> tuple[bool, str]:
    """Checks the grading image has been built - call this before sending
    invites for a round that includes any 'react' question, same pattern as
    judge0_client.is_judge0_ready()."""
    result = subprocess.run(
        ["docker", "image", "inspect", IMAGE], capture_output=True, timeout=10
    )
    if result.returncode == 0:
        return True, "React grading image is built and ready."
    return False, (
        f"React grading image '{IMAGE}' not found - build it first "
        f"(docker build -t {IMAGE} react_grader/)."
    )


def _run_one(candidate_code: str, assertion_script: str) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        candidate_path = Path(tmp) / "candidate.jsx"
        assertion_path = Path(tmp) / "assertion.js"
        candidate_path.write_text(candidate_code)
        assertion_path.write_text(assertion_script)

        # Named explicitly so a timeout can force-kill the actual container,
        # not just the local `docker run` CLI process - subprocess.run's own
        # timeout only kills the CLI wrapper, leaving the container (and an
        # infinite-loop submission inside it) running server-side in the
        # Docker daemon indefinitely otherwise.
        container_name = f"campus-react-grader-{uuid.uuid4().hex[:12]}"

        try:
            proc = subprocess.run(
                [
                    "docker", "run", "--rm", "--name", container_name,
                    "--security-opt", "seccomp=unconfined",
                    "--network", "none",
                    "--memory", "512m",
                    "--cpus", "1.0",
                    "--read-only",
                    "--tmpfs", "/tmp",
                    "-v", f"{candidate_path}:/work/candidate.jsx:ro",
                    "-v", f"{assertion_path}:/work/assertion.js:ro",
                    IMAGE,
                ],
                capture_output=True,
                timeout=RUN_TIMEOUT_SECONDS,
                text=True,
            )
        except subprocess.TimeoutExpired:
            subprocess.run(["docker", "kill", container_name], capture_output=True, timeout=10)
            return {"passed": False, "message": "Timed out (possible infinite loop)."}

        last_line = (proc.stdout or "").strip().splitlines()[-1] if proc.stdout.strip() else None
        if last_line is None:
            return {"passed": False, "message": proc.stderr.strip() or "Grader produced no output."}
        try:
            return json.loads(last_line)
        except json.JSONDecodeError:
            return {"passed": False, "message": f"Grader output was not valid JSON: {last_line!r}"}


def run_react_submission(question, submitted_code: str, test_cases: list) -> list[dict]:
    """test_cases: CodingTestCase rows with assertion_script set. Returns
    the same result shape as judge0_client.run_against_test_cases: one
    dict per test case with {passed, weight, stdout, stderr, expected_output,
    status, time, memory}."""
    results = []
    for tc in test_cases:
        outcome = _run_one(submitted_code, tc.assertion_script)
        passed = bool(outcome.get("passed"))
        results.append({
            "passed": passed,
            "stdout": outcome.get("message", ""),
            "stderr": None if passed else outcome.get("message", ""),
            "expected_output": None,
            "status": "Accepted" if passed else "Wrong Answer",
            "time": None,
            "memory": None,
            "weight": tc.weight,
        })
    return results
