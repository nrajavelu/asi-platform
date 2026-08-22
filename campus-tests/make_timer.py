"""
Generates a standalone, self-contained countdown-timer HTML page for a
round's admin-defined duration. No server, no network, no dependency on
anything else in this system once generated - open the file in any
browser (even offline) and click Start. Meant to be displayed on a
projector/shared screen at the front of the room, like a physical exam
clock, since Google Forms has no native time-limit feature at all.

Usage:
    python make_timer.py --round-id 1
"""

import argparse
from pathlib import Path

from models import Round, SessionLocal, init_db

OUT_DIR = Path(__file__).parent / "timers"

TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{title} - Timer</title>
<style>
  :root {{
    --bg: #0a0b0d; --bg-soft: #12141a;
    --ink: #f4f7fb; --ink-soft: #9ea3a9;
    --ok: #3dd1f2; --warn: #ffb020; --danger: #ff4d4d;
    --line: #22262e;
  }}
  * {{ box-sizing: border-box; }}
  html, body {{
    margin: 0; height: 100%;
    background: var(--bg); color: var(--ink);
    font-family: -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  }}
  body {{
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    text-align: center; gap: 18px; padding: 24px;
  }}
  .eyebrow {{
    text-transform: uppercase; letter-spacing: 0.14em; font-size: clamp(13px, 1.6vw, 18px);
    color: var(--ink-soft); font-weight: 600;
  }}
  h1 {{
    margin: 0; font-size: clamp(22px, 3.2vw, 40px); font-weight: 700;
  }}
  .meta {{ color: var(--ink-soft); font-size: clamp(13px, 1.4vw, 17px); margin-top: -8px; }}
  .clock {{
    font-variant-numeric: tabular-nums;
    font-size: clamp(80px, 22vw, 260px);
    font-weight: 700;
    line-height: 1;
    color: var(--ok);
    transition: color 0.4s ease;
  }}
  .clock.warn {{ color: var(--warn); }}
  .clock.danger {{ color: var(--danger); animation: pulse 1s infinite; }}
  @keyframes pulse {{ 0%,100% {{ opacity: 1; }} 50% {{ opacity: 0.55; }} }}
  .status {{ font-size: clamp(14px, 1.8vw, 22px); color: var(--ink-soft); }}
  button {{
    margin-top: 12px;
    background: linear-gradient(120deg, #3dd1f2, #1a7ee8 55%, #1450e8);
    color: white; border: none; padding: 16px 40px; border-radius: 12px;
    font-size: clamp(16px, 1.8vw, 22px); font-weight: 700; cursor: pointer;
    box-shadow: 0 12px 30px rgba(26, 126, 232, 0.35);
  }}
  button:disabled {{ opacity: 0.4; cursor: default; box-shadow: none; }}
  .timesup {{
    display: none;
    background: var(--danger); color: white; font-weight: 800;
    font-size: clamp(20px, 3vw, 44px);
    padding: 18px 36px; border-radius: 16px;
    letter-spacing: 0.02em;
  }}
  .timesup.show {{ display: block; }}
  footer {{ position: absolute; bottom: 18px; color: var(--ink-soft); font-size: 12px; letter-spacing: 0.05em; }}
</style>
</head>
<body>
  <div class="eyebrow">Aizentify Campus</div>
  <h1>{title}</h1>
  <div class="meta">{round_type} round &middot; {duration} minutes</div>

  <div id="timesup" class="timesup">TIME'S UP &mdash; PLEASE SUBMIT NOW</div>
  <div id="clock" class="clock">{duration:02d}:00</div>
  <div id="status" class="status">Click Start when the test session begins</div>
  <button id="startBtn">Start Timer</button>

  <footer>This page runs fully offline once loaded &mdash; no submission or scoring happens here</footer>

<script>
  const DURATION_SECONDS = {duration} * 60;
  const clockEl = document.getElementById('clock');
  const statusEl = document.getElementById('status');
  const startBtn = document.getElementById('startBtn');
  const timesupEl = document.getElementById('timesup');
  let remaining = DURATION_SECONDS;
  let intervalId = null;

  function format(secs) {{
    const m = Math.floor(secs / 60).toString().padStart(2, '0');
    const s = Math.floor(secs % 60).toString().padStart(2, '0');
    return m + ':' + s;
  }}

  function beep() {{
    try {{
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.connect(gain); gain.connect(ctx.destination);
      osc.frequency.value = 880;
      gain.gain.setValueAtTime(0.2, ctx.currentTime);
      osc.start();
      osc.stop(ctx.currentTime + 0.8);
    }} catch (e) {{}}
  }}

  function tick() {{
    remaining -= 1;
    clockEl.textContent = format(Math.max(remaining, 0));
    clockEl.classList.remove('warn', 'danger');
    if (remaining <= 60) {{
      clockEl.classList.add('danger');
    }} else if (remaining <= 300) {{
      clockEl.classList.add('warn');
    }}
    if (remaining <= 0) {{
      clearInterval(intervalId);
      statusEl.textContent = 'Time is up.';
      timesupEl.classList.add('show');
      beep();
    }}
  }}

  startBtn.addEventListener('click', () => {{
    if (intervalId !== null) return;
    startBtn.disabled = true;
    statusEl.textContent = 'Timer running';
    intervalId = setInterval(tick, 1000);
  }});
</script>
</body>
</html>
"""


def generate_timer_html(round_: Round, out_path: Path) -> None:
    html = TEMPLATE.format(
        title=f"{round_.drive.name} - {round_.round_type.title()}",
        round_type=round_.round_type.title(),
        duration=round_.duration_minutes,
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--round-id", type=int, required=True)
    args = parser.parse_args()

    init_db()
    session = SessionLocal()
    round_ = session.get(Round, args.round_id)
    if round_ is None:
        raise SystemExit(f"No round with id {args.round_id}")

    out_path = OUT_DIR / f"round_{round_.id}_timer.html"
    generate_timer_html(round_, out_path)
    print(f"Wrote {out_path}")
    print(f"Open this file in a browser and display it on a projector/shared screen.")


if __name__ == "__main__":
    main()
