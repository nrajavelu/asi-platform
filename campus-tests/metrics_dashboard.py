"""Shared live-metrics core used by both loadtest/harness.py (simulated
candidates) and app.py's real-test monitor (actual candidates): rolling
per-endpoint latency/error tracking, a degraded/broken threshold table,
a low-frequency docker stats sampler, and one reusable dashboard HTML+JS
template. Kept free of any DB/grading imports so pulling this into app.py
adds no import-time cost beyond stdlib + FastAPI.
"""

import time
from collections import defaultdict, deque

THRESHOLDS = {
    "start":   {"degraded": 2.0, "broken": 5.0},
    "session": {"degraded": 1.0, "broken": 3.0},
    "run":     {"degraded": 15.0, "broken": 25.0},
    "submit":  {"degraded": 15.0, "broken": 25.0},
}
ERROR_RATE_DEGRADED = 0.02
ERROR_RATE_BROKEN = 0.05

DOCKER_CONTAINERS = [
    "judge0-v1-server-1", "judge0-v1-workers-1", "judge0-v1-redis-1", "judge0-v1-db-1", "pgvector-db-1",
]


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
    """Everything a dashboard reads lives here, in memory. The load-test
    harness additionally uses current_level/current_batch_size/
    level_results/stopped/stop_reason for its own run-state; the live
    candidate monitor leaves those at their defaults and only ever
    populates endpoints/docker_stats/alerts/candidates_started/finished."""

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

    def record(self, name: str, elapsed: float, ok: bool, lock_error: bool = False) -> None:
        self.endpoints[name].record(elapsed, ok, lock_error)

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


async def docker_stats_sampler(metrics: Metrics, interval: float = 4.0, containers: list[str] = None):
    """External to whatever app is running - one `docker stats` call per
    interval, never per-request, so it can't add per-candidate overhead."""
    import asyncio

    fmt = "{{.Name}}|{{.CPUPerc}}|{{.MemPerc}}"
    names = containers if containers is not None else DOCKER_CONTAINERS
    while not metrics.stopped:
        try:
            proc = await asyncio.create_subprocess_exec(
                "docker", "stats", "--no-stream", "--format", fmt, *names,
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


def dashboard_html(page_title: str, heading: str, data_url: str = "/metrics.json") -> str:
    return f"""
<!doctype html><html><head><title>{page_title}</title>
<style>
body{{font-family:-apple-system,sans-serif;background:#0f1114;color:#e6e8eb;margin:0;padding:24px;}}
h1{{font-size:18px;}} .card{{background:#181b20;border:1px solid #2a2e35;border-radius:10px;padding:16px;margin-bottom:16px;}}
table{{width:100%;border-collapse:collapse;font-size:13px;}} td,th{{padding:6px 10px;text-align:left;border-bottom:1px solid #2a2e35;}}
.alert{{padding:8px 12px;border-radius:6px;margin-bottom:6px;font-size:13px;}}
.broken{{background:#3a1418;color:#ff6b6b;}} .degraded{{background:#3a2e14;color:#ffb020;}}
.ok{{color:#3ddc97;}} .muted{{color:#8a8f98;}}
</style></head><body>
<h1>{heading}</h1>
<div id="root"></div>
<script>
async function tick(){{
  const r = await fetch('{data_url}'); const d = await r.json();
  let html = `<div class="card">Elapsed: ${{d.elapsed_s}}s`;
  if (d.current_level) html += ` &middot; Level: ${{d.current_level}} &middot; Batch size: ${{d.current_batch_size}}`;
  html += ` &middot; Started: ${{d.candidates_started}} &middot; Finished: ${{d.candidates_finished}}`;
  if (d.stopped && d.stop_reason) html += ' &middot; <b style="color:#ff6b6b">STOPPED: '+d.stop_reason+'</b>';
  html += '</div>';
  html += '<div class="card"><b>Alerts</b><br>';
  html += d.alerts.length ? d.alerts.map(a => `<div class="alert ${{a.startsWith('BROKEN')?'broken':'degraded'}}">${{a}}</div>`).join('') : '<span class="muted">none</span>';
  html += '</div>';
  html += '<div class="card"><b>Endpoints</b><table><tr><th>Endpoint</th><th>Count</th><th>Errors</th><th>Error rate</th><th>p50</th><th>p95</th><th>p99</th><th>Lock errors</th></tr>';
  for (const [name, e] of Object.entries(d.endpoints)) {{
    html += `<tr><td>${{name}}</td><td>${{e.count}}</td><td>${{e.errors}}</td><td>${{(e.error_rate*100).toFixed(1)}}%</td><td>${{e.p50}}s</td><td>${{e.p95}}s</td><td>${{e.p99}}s</td><td>${{e.lock_errors}}</td></tr>`;
  }}
  html += '</table></div>';
  html += '<div class="card"><b>Infra (docker stats)</b><table><tr><th>Container</th><th>CPU</th><th>Mem</th></tr>';
  for (const [name, s] of Object.entries(d.docker_stats)) {{
    html += `<tr><td>${{name}}</td><td>${{s.cpu}}</td><td>${{s.mem}}</td></tr>`;
  }}
  html += '</table></div>';
  document.getElementById('root').innerHTML = html;
}}
tick(); setInterval(tick, 2000);
</script></body></html>
"""
