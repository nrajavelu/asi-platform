"""
Grades "css" question_type submissions in an ephemeral, sandboxed Docker
container (campus-css-grader:latest, built from css_grader/ on top of
Playwright's official image) - one container per test case, same pattern
as react_grader.py. Never call this from anywhere candidates can reach
directly - it stays behind app.py.

Scope: computed-style/DOM assertions via a real headless Chromium, not
pixel-based visual regression (no reference-screenshot management needed -
see the plan for the reasoning).

Sandboxing: identical to react_grader.py - --network none, --read-only +
--tmpfs /tmp, --memory/--cpus caps, a hard subprocess timeout with an
explicit `docker kill` on expiry (subprocess.run's own timeout only kills
the CLI wrapper, not the container), and --security-opt seccomp=unconfined
(required for Node/Chromium to start at all under this Docker Desktop/
macOS 12 VM's default seccomp profile - see react_grader.py for the full
explanation, same root cause).
"""

import json
import subprocess
import tempfile
import uuid
from pathlib import Path

IMAGE = "campus-css-grader:latest"
RUN_TIMEOUT_SECONDS = 30  # Chromium launch is slower than Node+jsdom


def is_css_grader_ready() -> tuple[bool, str]:
    """Checks the grading image has been built - call this before sending
    invites for a round that includes any 'css' question, same pattern as
    judge0_client.is_judge0_ready()."""
    result = subprocess.run(
        ["docker", "image", "inspect", IMAGE], capture_output=True, timeout=10
    )
    if result.returncode == 0:
        return True, "CSS grading image is built and ready."
    return False, (
        f"CSS grading image '{IMAGE}' not found - build it first "
        f"(docker build -t {IMAGE} css_grader/)."
    )


def _run_one(scaffold_html: str, candidate_css: str, assertion_script: str) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        scaffold_path = Path(tmp) / "scaffold.html"
        css_path = Path(tmp) / "candidate.css"
        assertion_path = Path(tmp) / "assertion.js"
        scaffold_path.write_text(scaffold_html)
        css_path.write_text(candidate_css)
        assertion_path.write_text(assertion_script)

        container_name = f"campus-css-grader-{uuid.uuid4().hex[:12]}"

        try:
            proc = subprocess.run(
                [
                    "docker", "run", "--rm", "--name", container_name,
                    "--security-opt", "seccomp=unconfined",
                    "--network", "none",
                    "--memory", "1g",
                    "--cpus", "1.0",
                    "--read-only",
                    "--tmpfs", "/tmp",
                    "--shm-size", "1g",  # Chromium needs real shared memory, not the tiny 64MB Docker default
                    "-v", f"{scaffold_path}:/work/scaffold.html:ro",
                    "-v", f"{css_path}:/work/candidate.css:ro",
                    "-v", f"{assertion_path}:/work/assertion.js:ro",
                    IMAGE,
                ],
                capture_output=True,
                timeout=RUN_TIMEOUT_SECONDS,
                text=True,
            )
        except subprocess.TimeoutExpired:
            subprocess.run(["docker", "kill", container_name], capture_output=True, timeout=10)
            return {"passed": False, "message": "Timed out (possible infinite loop or hang)."}

        last_line = (proc.stdout or "").strip().splitlines()[-1] if proc.stdout.strip() else None
        if last_line is None:
            return {"passed": False, "message": proc.stderr.strip() or "Grader produced no output."}
        try:
            return json.loads(last_line)
        except json.JSONDecodeError:
            return {"passed": False, "message": f"Grader output was not valid JSON: {last_line!r}"}


def run_css_submission(question, submitted_css: str, test_cases: list) -> list[dict]:
    """test_cases: CodingTestCase rows with assertion_script set.
    question.harness_fixture holds the HTML scaffold (with a {{CSS}}
    placeholder) the candidate's CSS gets rendered into. Returns the same
    result shape as judge0_client.run_against_test_cases."""
    results = []
    for tc in test_cases:
        outcome = _run_one(question.harness_fixture or "", submitted_css, tc.assertion_script)
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
