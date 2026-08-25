"""
Load test for app.py's coding-round candidate flow: staged concurrency
(15 -> 25 -> 35 -> 50), adaptive batch ramp-up within each level, and a
live monitoring dashboard - all isolated from the system under test (its
own process/port, never calling app.py/webui.py except as a simulated
candidate would).

Requires: a coding round already built with real questions, and a
loadtest_tokens.txt file (one attempt token per line) for candidates on
that round. See campus-tests/loadtest/README.md for setup.

Usage:
    python3 loadtest/harness.py --base-url http://127.0.0.1:8788 \
        --tokens loadtest_tokens.txt --session-minutes 5

Dashboard: http://127.0.0.1:8790 while the test runs.
"""

import argparse
import asyncio
import sys
import random
import time
from collections import defaultdict
from pathlib import Path

import httpx
import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # models.py/metrics_dashboard.py live in campus-tests/, not loadtest/
from models import Attempt, SessionLocal  # noqa: E402
from metrics_dashboard import (  # noqa: E402
    EndpointMetrics, Metrics, dashboard_html, docker_stats_sampler as _docker_stats_sampler,
)

DEFAULT_LEVELS = [15, 25, 35, 50]
BATCH_SIZES = [5, 10, 15]


def reset_tokens_to_invited(tokens: list[str]) -> None:
    """Sync (call via asyncio.to_thread) - puts this level's attempts back
    to a fresh state so a token already used by a smaller level can be
    reused here. Only touches Attempt.status/session_started_at; assigned
    CodingAttemptQuestion rows are left alone (assignment is idempotent
    and reusing the same questions is fine)."""
    session = SessionLocal()
    try:
        session.query(Attempt).filter(Attempt.token.in_(tokens)).update(
            {"status": "invited", "session_started_at": None}, synchronize_session=False
        )
        session.commit()
    finally:
        session.close()


# --------------------------------------------------------------------------
# Candidate simulation
# --------------------------------------------------------------------------

async def timed_request(metrics: Metrics, name: str, coro):
    t0 = time.monotonic()
    ok = False
    lock_error = False
    try:
        resp = await coro
        elapsed = time.monotonic() - t0
        ok = resp.status_code < 400
        if not ok and "database is locked" in resp.text.lower():
            lock_error = True
        metrics.endpoints[name].record(elapsed, ok, lock_error)
        return resp
    except Exception:
        elapsed = time.monotonic() - t0
        metrics.endpoints[name].record(elapsed, False)
        return None


async def simulate_candidate(client: httpx.AsyncClient, token: str, base_url: str, metrics: Metrics, session_minutes: float):
    metrics.candidates_started += 1

    r = await timed_request(metrics, "start", client.get(f"{base_url}/start/{token}", follow_redirects=True))
    if r is None or r.status_code >= 400:
        return

    r = await timed_request(metrics, "session", client.get(f"{base_url}/coding/{token}/api/session"))
    if r is None or r.status_code >= 400:
        return
    try:
        questions = r.json().get("questions", [])
    except Exception:
        questions = []
    if not questions:
        return

    end_at = time.monotonic() + session_minutes * 60
    stop_poll = asyncio.Event()

    async def poll_loop():
        while not stop_poll.is_set() and time.monotonic() < end_at:
            await asyncio.sleep(5)
            if stop_poll.is_set():
                break
            await timed_request(metrics, "session", client.get(f"{base_url}/coding/{token}/api/session"))

    poller = asyncio.create_task(poll_loop())

    for q in questions:
        if time.monotonic() >= end_at:
            break
        code = q.get("starter_code") or "pass"
        qid = q.get("question_id")
        await asyncio.sleep(random.uniform(1, 4))
        await timed_request(
            metrics, "run",
            client.post(f"{base_url}/coding/{token}/api/run", data={"question_id": qid, "code": code}),
        )
        await asyncio.sleep(random.uniform(0.5, 2))
        await timed_request(
            metrics, "submit",
            client.post(f"{base_url}/coding/{token}/api/submit", data={"question_id": qid, "code": code}),
        )

    stop_poll.set()
    poller.cancel()
    try:
        await client.post(f"{base_url}/coding/{token}/api/finish")
    except Exception:
        pass
    metrics.candidates_finished += 1


async def docker_stats_sampler(metrics: Metrics, interval: float = 4.0):
    await _docker_stats_sampler(metrics, interval)


# --------------------------------------------------------------------------
# Orchestration: staged levels, adaptive batch ramp
# --------------------------------------------------------------------------

async def run_level(level_size: int, tokens: list[str], base_url: str, metrics: Metrics, session_minutes: float):
    metrics.current_level = level_size
    level_tokens = tokens[:level_size]
    # Levels reuse a prefix of the same token pool (15, then 25, then 35,
    # then 50) - every token in this level may already be "submitted" from
    # a smaller level that ran before it. Without this reset, app.py's
    # /start correctly 403s an already-finished attempt, and every level
    # after the first would look broken from stale tokens, not real load.
    await asyncio.to_thread(reset_tokens_to_invited, level_tokens)

    remaining = list(level_tokens)
    batch_size = 10
    all_tasks: list[asyncio.Task] = []
    client = httpx.AsyncClient(timeout=30.0)
    level_broken = asyncio.Event()

    async def watchdog():
        # Batch-start checks alone only catch startup failures (e.g. a
        # burst of 403s) - degradation that shows up minutes into a
        # session (slow Judge0 queueing, SQLite contention) would never
        # trip a batch-start-only check, since by the time it appears
        # there may be no more batches left to trigger one. This runs for
        # the level's whole duration instead.
        while not level_broken.is_set():
            await asyncio.sleep(5)
            alerts = metrics.check_thresholds()
            metrics.alerts = alerts
            broken = [a for a in alerts if a.startswith("BROKEN")]
            if broken:
                metrics.stop_reason = f"Level {level_size}: " + "; ".join(broken)
                level_broken.set()
                return

    watchdog_task = asyncio.create_task(watchdog())

    try:
        while remaining and not level_broken.is_set():
            batch = remaining[:batch_size]
            remaining = remaining[batch_size:]
            metrics.current_batch_size = batch_size

            for tok in batch:
                all_tasks.append(asyncio.create_task(simulate_candidate(client, tok, base_url, metrics, session_minutes)))

            await asyncio.sleep(3)  # let this batch's start calls register before adapting the next batch size
            if level_broken.is_set():
                break
            degraded = [a for a in metrics.alerts if a.startswith("DEGRADED")]
            batch_size = max(5, batch_size - 5) if degraded else min(15, batch_size + 5)

        pending = set(all_tasks)
        while pending and not level_broken.is_set():
            done, pending = await asyncio.wait(pending, timeout=2)

        watchdog_task.cancel()
        if level_broken.is_set():
            metrics.stopped = True
            for t in all_tasks:
                t.cancel()
            return False
        return True
    finally:
        await client.aclose()


async def run_all_levels(base_url: str, tokens: list[str], metrics: Metrics, session_minutes: float, levels: list[int]):
    for level in levels:
        if level > len(tokens):
            print(f"Skipping level {level}: only {len(tokens)} tokens available")
            continue
        print(f"\n=== Level: {level} concurrent candidates ===")
        ok = await run_level(level, tokens, base_url, metrics, session_minutes)
        snap = metrics.snapshot()
        metrics.level_results.append({
            "level": level, "passed": ok,
            "endpoints": snap["endpoints"], "docker_stats": snap["docker_stats"],
        })
        if not ok:
            print(f"STOPPED at level {level}: {metrics.stop_reason}")
            break
        print(f"Level {level}: passed. Cooling down 10s before next level...")
        await asyncio.sleep(10)
        # reset per-level counters so the next level's numbers aren't diluted by the previous one
        metrics.endpoints = defaultdict(EndpointMetrics)
        metrics.alerts = []
    metrics.stopped = True
    print("\nLoad test complete.")


# --------------------------------------------------------------------------
# Dashboard - separate FastAPI app, separate port, read-only view of Metrics
# --------------------------------------------------------------------------

def build_dashboard_app(metrics: Metrics) -> FastAPI:
    app = FastAPI()

    @app.get("/", response_class=HTMLResponse)
    def dashboard():
        return dashboard_html("Load Test Dashboard", "Coding App Load Test")

    @app.get("/metrics.json")
    def metrics_json():
        return JSONResponse(metrics.snapshot())

    return app


async def run_dashboard(metrics: Metrics, port: int):
    config = uvicorn.Config(build_dashboard_app(metrics), host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)
    await server.serve()


# --------------------------------------------------------------------------

async def main_async(args):
    tokens = [line.strip() for line in Path(args.tokens).read_text().splitlines() if line.strip()]
    print(f"Loaded {len(tokens)} candidate tokens")
    levels = [int(x) for x in args.levels.split(",")] if args.levels else DEFAULT_LEVELS
    print(f"Levels: {levels}")

    metrics = Metrics()
    dashboard_task = asyncio.create_task(run_dashboard(metrics, args.dashboard_port))
    stats_task = asyncio.create_task(docker_stats_sampler(metrics))
    print(f"Dashboard: http://127.0.0.1:{args.dashboard_port}")

    await run_all_levels(args.base_url, tokens, metrics, args.session_minutes, levels)

    print("\nFinal summary:")
    for lr in metrics.level_results:
        status = "PASSED" if lr["passed"] else "BROKEN"
        print(f"  Level {lr['level']}: {status}")
        for name, e in lr["endpoints"].items():
            print(f"    {name}: n={e['count']} err={e['error_rate']:.1%} p50={e['p50']}s p95={e['p95']}s p99={e['p99']}s")

    stats_task.cancel()
    if args.exit_after:
        dashboard_task.cancel()
        try:
            await dashboard_task
        except asyncio.CancelledError:
            pass
        return
    print("\nDashboard still running for review - Ctrl+C to exit.")
    await dashboard_task


def main():
    sys.stdout.reconfigure(line_buffering=True)
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True, help="e.g. http://127.0.0.1:8788 (app.py)")
    parser.add_argument("--tokens", default="loadtest_tokens.txt")
    parser.add_argument("--session-minutes", type=float, default=5.0, help="simulated per-candidate session length")
    parser.add_argument("--dashboard-port", type=int, default=8790)
    parser.add_argument("--levels", default="", help="comma-separated override, e.g. '2' for a smoke test (default: 15,25,35,50)")
    parser.add_argument("--exit-after", action="store_true", help="exit once the run completes instead of keeping the dashboard alive")
    args = parser.parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
