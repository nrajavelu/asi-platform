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
from collections import defaultdict, deque
from pathlib import Path

import httpx
import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # models.py lives in campus-tests/, not loadtest/
from models import Attempt, SessionLocal  # noqa: E402

DEFAULT_LEVELS = [15, 25, 35, 50]
BATCH_SIZES = [5, 10, 15]
DOCKER_CONTAINERS = [
    "judge0-v1-server-1", "judge0-v1-workers-1", "judge0-v1-redis-1", "judge0-v1-db-1", "pgvector-db-1",
]

THRESHOLDS = {
    "start":   {"degraded": 2.0, "broken": 5.0},
    "session": {"degraded": 1.0, "broken": 3.0},
    "run":     {"degraded": 15.0, "broken": 25.0},
    "submit":  {"degraded": 15.0, "broken": 25.0},
}
ERROR_RATE_DEGRADED = 0.02
ERROR_RATE_BROKEN = 0.05


class EndpointMetrics:
    def __init__(self, maxlen: int = 300):
        self.latencies: deque = deque(maxlen=maxlen)
        self.count = 0
        self.errors = 0
        self.lock_errors = 0

    def record(self, elapsed: float, ok: bool, lock_error: bool = False) -> None:
        self.latencies.append(elapsed)
        self.count += 1
        if not ok:
            self.errors += 1
        if lock_error:
            self.lock_errors += 1

    def percentile(self, pct: float) -> float:
        if not self.latencies:
            return 0.0
        s = sorted(self.latencies)
        idx = min(len(s) - 1, int(len(s) * pct))
        return s[idx]

    def error_rate(self) -> float:
        return (self.errors / self.count) if self.count else 0.0


class Metrics:
    """Everything the dashboard reads lives here, in memory. Populated
    only by (a) the harness's own request observations - already
    happening, free to expose - and (b) a low-frequency docker stats
    sample. Nothing here ever calls app.py/webui.py beyond what a
    simulated candidate does."""

    def __init__(self):
        self.endpoints: dict[str, EndpointMetrics] = defaultdict(EndpointMetrics)
        self.candidates_started = 0
        self.candidates_finished = 0
        self.current_level = 0
        self.current_batch_size = 0
        self.docker_stats: dict[str, dict] = {}
        self.alerts: list[str] = []
        self.level_results: list[dict] = []
        self.start_time = time.monotonic()
        self.stopped = False
        self.stop_reason = ""

    def check_thresholds(self) -> list[str]:
        alerts = []
        for name, em in self.endpoints.items():
            if em.count == 0:
                continue
            p95 = em.percentile(0.95)
            th = THRESHOLDS.get(name, {"degraded": 999, "broken": 9999})
            if p95 > th["broken"]:
                alerts.append(f"BROKEN: {name} p95={p95:.2f}s (limit {th['broken']}s)")
            elif p95 > th["degraded"]:
                alerts.append(f"DEGRADED: {name} p95={p95:.2f}s (limit {th['degraded']}s)")
            err = em.error_rate()
            if err > ERROR_RATE_BROKEN:
                alerts.append(f"BROKEN: {name} error_rate={err:.1%}")
            elif err > ERROR_RATE_DEGRADED:
                alerts.append(f"DEGRADED: {name} error_rate={err:.1%}")
            if em.lock_errors:
                alerts.append(f"BROKEN: {name} sqlite_lock_errors={em.lock_errors}")
        return alerts

    def snapshot(self) -> dict:
        return {
            "elapsed_s": round(time.monotonic() - self.start_time, 1),
            "current_level": self.current_level,
            "current_batch_size": self.current_batch_size,
            "candidates_started": self.candidates_started,
            "candidates_finished": self.candidates_finished,
            "stopped": self.stopped,
            "stop_reason": self.stop_reason,
            "endpoints": {
                name: {
                    "count": em.count,
                    "errors": em.errors,
                    "error_rate": round(em.error_rate(), 4),
                    "p50": round(em.percentile(0.50), 3),
                    "p95": round(em.percentile(0.95), 3),
                    "p99": round(em.percentile(0.99), 3),
                    "lock_errors": em.lock_errors,
                }
                for name, em in self.endpoints.items()
            },
            "docker_stats": self.docker_stats,
            "alerts": self.alerts,
            "level_results": self.level_results,
        }


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


# --------------------------------------------------------------------------
# Docker stats sampler - external to the app entirely, low frequency
# --------------------------------------------------------------------------

async def docker_stats_sampler(metrics: Metrics, interval: float = 4.0):
    fmt = "{{.Name}}|{{.CPUPerc}}|{{.MemPerc}}"
    while not metrics.stopped:
        try:
            proc = await asyncio.create_subprocess_exec(
                "docker", "stats", "--no-stream", "--format", fmt, *DOCKER_CONTAINERS,
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL,
            )
            out, _ = await proc.communicate()
            for line in out.decode().splitlines():
                parts = line.split("|")
                if len(parts) == 3:
                    name, cpu, mem = parts
                    metrics.docker_stats[name] = {"cpu": cpu, "mem": mem}
        except Exception:
            pass
        await asyncio.sleep(interval)


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
        return """
<!doctype html><html><head><title>Load Test Dashboard</title>
<style>
body{font-family:-apple-system,sans-serif;background:#0f1114;color:#e6e8eb;margin:0;padding:24px;}
h1{font-size:18px;} .card{background:#181b20;border:1px solid #2a2e35;border-radius:10px;padding:16px;margin-bottom:16px;}
table{width:100%;border-collapse:collapse;font-size:13px;} td,th{padding:6px 10px;text-align:left;border-bottom:1px solid #2a2e35;}
.alert{padding:8px 12px;border-radius:6px;margin-bottom:6px;font-size:13px;}
.broken{background:#3a1418;color:#ff6b6b;} .degraded{background:#3a2e14;color:#ffb020;}
.ok{color:#3ddc97;} .muted{color:#8a8f98;}
</style></head><body>
<h1>Coding App Load Test</h1>
<div id="root"></div>
<script>
async function tick(){
  const r = await fetch('/metrics.json'); const d = await r.json();
  let html = `<div class="card">Elapsed: ${d.elapsed_s}s &middot; Level: ${d.current_level} &middot; Batch size: ${d.current_batch_size} &middot; Started: ${d.candidates_started} &middot; Finished: ${d.candidates_finished}${d.stopped ? ' &middot; <b style="color:#ff6b6b">STOPPED: '+d.stop_reason+'</b>' : ''}</div>`;
  html += '<div class="card"><b>Alerts</b><br>';
  html += d.alerts.length ? d.alerts.map(a => `<div class="alert ${a.startsWith('BROKEN')?'broken':'degraded'}">${a}</div>`).join('') : '<span class="muted">none</span>';
  html += '</div>';
  html += '<div class="card"><b>Endpoints</b><table><tr><th>Endpoint</th><th>Count</th><th>Errors</th><th>Error rate</th><th>p50</th><th>p95</th><th>p99</th><th>Lock errors</th></tr>';
  for (const [name, e] of Object.entries(d.endpoints)) {
    html += `<tr><td>${name}</td><td>${e.count}</td><td>${e.errors}</td><td>${(e.error_rate*100).toFixed(1)}%</td><td>${e.p50}s</td><td>${e.p95}s</td><td>${e.p99}s</td><td>${e.lock_errors}</td></tr>`;
  }
  html += '</table></div>';
  html += '<div class="card"><b>Infra (docker stats)</b><table><tr><th>Container</th><th>CPU</th><th>Mem</th></tr>';
  for (const [name, s] of Object.entries(d.docker_stats)) {
    html += `<tr><td>${name}</td><td>${s.cpu}</td><td>${s.mem}</td></tr>`;
  }
  html += '</table></div>';
  document.getElementById('root').innerHTML = html;
}
tick(); setInterval(tick, 2000);
</script></body></html>
"""

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
