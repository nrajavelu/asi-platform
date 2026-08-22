"""
Grades "sql" question_type submissions against the self-hosted pgvector
Postgres instance (started via `docker compose up -d` in pgvector/). Never
call this from anywhere candidates can reach directly - it stays behind
app.py, same as judge0_client.

Isolation model (defense in depth, not just transaction rollback):
  - `campus_admin` (superuser-equivalent for this DB) provisions one schema
    per question, lazily, from the question's own harness_fixture DDL - this
    is admin-authored content, not candidate input.
  - `grader` is a genuinely SELECT-only role: granted USAGE + SELECT on a
    question's schema/tables right after provisioning, nothing else. It has
    no INSERT/UPDATE/DELETE/CREATE/TRUNCATE grants anywhere, so a malicious
    submission can't mutate data even if the rollback wrapper below had a
    bug - Postgres itself rejects the statement before running it.
  - Every submission still runs inside `BEGIN; SET LOCAL statement_timeout;
    ...; ROLLBACK;` on top of that, to bound runaway/expensive SELECTs.
"""

import json

import psycopg

HOST = "127.0.0.1"
PORT = 5433
DBNAME = "campus_sql_grading"
ADMIN_USER, ADMIN_PASSWORD = "campus_admin", "campus_admin_local_only"
GRADER_USER, GRADER_PASSWORD = "grader", "grader_local_only"
STATEMENT_TIMEOUT_MS = 5000


def _admin_conn():
    return psycopg.connect(host=HOST, port=PORT, dbname=DBNAME, user=ADMIN_USER, password=ADMIN_PASSWORD)


def _grader_conn():
    return psycopg.connect(host=HOST, port=PORT, dbname=DBNAME, user=GRADER_USER, password=GRADER_PASSWORD)


def is_pgvector_ready() -> tuple[bool, str]:
    """Lightweight reachability check - call this before sending invites for
    a round that includes any 'sql' question, same pattern as
    judge0_client.is_judge0_ready()."""
    try:
        with _admin_conn() as conn:
            conn.execute("SELECT 1")
    except psycopg.OperationalError:
        return False, (
            f"Cannot reach the SQL grading Postgres instance at {HOST}:{PORT} - is it running? "
            f"(docker compose up -d in pgvector/)"
        )
    except Exception as e:
        return False, f"SQL grading Postgres check failed: {e}"
    return True, "SQL grading Postgres is reachable and responding."


def _schema_name(question) -> str:
    return f"q_{question.external_id.lower().replace('-', '_')}"


def _ensure_question_schema(question) -> None:
    """Idempotent: creates and seeds this question's schema from its
    harness_fixture DDL on first use, then grants the read-only `grader`
    role access to it. Safe to call on every submission - no-ops if the
    schema already exists."""
    schema = _schema_name(question)
    with _admin_conn() as conn:
        exists = conn.execute(
            "SELECT 1 FROM information_schema.schemata WHERE schema_name = %s", (schema,)
        ).fetchone()
        if exists:
            return

        conn.execute(f'CREATE SCHEMA "{schema}"')
        conn.execute(f'SET search_path TO "{schema}", public')
        if question.harness_fixture:
            conn.execute(question.harness_fixture)
        conn.execute(f'GRANT USAGE ON SCHEMA "{schema}" TO {GRADER_USER}')
        conn.execute(f'GRANT SELECT ON ALL TABLES IN SCHEMA "{schema}" TO {GRADER_USER}')
        conn.commit()


def run_sql_submission(question, submitted_sql: str, test_cases: list) -> list[dict]:
    """test_cases: CodingTestCase rows, where expected_output holds a JSON
    string of expected rows (list of lists) and `ordered` controls whether
    row order matters for the diff. Returns the same result shape as
    judge0_client.run_against_test_cases: one dict per test case with
    {passed, stdout, stderr, expected_output, status, time, memory, weight}."""
    _ensure_question_schema(question)
    schema = _schema_name(question)

    results = []
    for tc in test_cases:
        expected_rows = json.loads(tc.expected_output)
        result = {"expected_output": tc.expected_output, "memory": None, "weight": tc.weight}

        try:
            with _grader_conn() as conn:
                conn.execute(f"SET statement_timeout = {STATEMENT_TIMEOUT_MS}")
                conn.execute(f'SET search_path TO "{schema}", public')
                import time as _time
                start = _time.monotonic()
                cur = conn.execute(submitted_sql)
                actual_rows = [list(row) for row in cur.fetchall()]
                elapsed = _time.monotonic() - start
                conn.rollback()  # grader has no write grants anyway; rollback is still correct hygiene

            compare_actual = actual_rows if tc.ordered else sorted(actual_rows, key=repr)
            compare_expected = expected_rows if tc.ordered else sorted(expected_rows, key=repr)
            passed = compare_actual == compare_expected

            result.update({
                "passed": passed,
                "stdout": json.dumps(actual_rows),
                "stderr": None,
                "status": "Accepted" if passed else "Wrong Answer",
                "time": round(elapsed, 3),
            })
        except psycopg.errors.QueryCanceled:
            result.update({"passed": False, "stdout": "", "stderr": "Query timed out", "status": "Time Limit Exceeded", "time": None})
        except psycopg.Error as e:
            result.update({"passed": False, "stdout": "", "stderr": str(e), "status": "Runtime Error", "time": None})

        results.append(result)
    return results
