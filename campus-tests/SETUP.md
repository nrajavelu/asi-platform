# Setting up on a new machine

Works on macOS, Windows, and Linux — `setup.py`/`start.py`/`stop.py` are
plain Python, not OS-specific shell scripts, so the same commands apply
everywhere (only the exact Python launch command differs, noted below).

## 1. Get the code

```
git clone https://github.com/nrajavelu/asi-platform.git
cd asi-platform/campus-tests
```

## 2. macOS/Linux quick path: `./install.sh`

```
./install.sh
```

Checks Python is present, runs `setup.py`, generates `start.sh`/`stop.sh`
launcher scripts (thin passthroughs to `start.py`/`stop.py` — regenerated
each time you run `install.sh`, safe to delete), starts the stack, and
prints a summary: the admin dashboard URL, this machine's LAN IP, and
whether Google credentials still need finishing. Covers everything in
steps 4-5 below in one go — skip ahead to step 6 once it's done.

On Windows, or if you'd rather run each step yourself, continue below.

## 3. Prerequisites (install these yourself first)

- **Python 3.10+** — https://www.python.org/downloads/
- **git** — https://git-scm.com/downloads
- **Docker** — Docker Desktop on macOS/Windows (https://www.docker.com/products/docker-desktop/), Docker Engine on Linux (https://docs.docker.com/engine/install/)

`setup.py` checks for all three and tells you exactly what's missing if
any aren't found — it won't silently proceed without them.

## 4. Run setup (once)

```
python3 setup.py        # macOS/Linux
python setup.py         # Windows
```

This creates `.venv`, installs Python dependencies, generates
`judge0/judge0-v1.13.1/judge0.conf` with fresh random secrets (never
reused across machines), and checks for Google API credentials.

**One step it can't automate**: Google OAuth credentials
(`credentials/client_secret.json`) have to be created by hand in
[Google Cloud Console](https://console.cloud.google.com/apis/credentials)
(OAuth 2.0 Client ID, Desktop app type) for whichever Google account
should own the Forms/Gmail this app creates and sends from. `setup.py`
tells you exactly where to save the downloaded file and re-run once
that's done — there's no way to script around a step that requires a
human clicking through Google's own console.

Safe to re-run `setup.py` any time — every step skips if already done.

## 5. Start / stop the local stack

```
python3 start.py    # macOS/Linux
python start.py     # Windows
```

Brings up Docker (Judge0 + SQL grading Postgres) and the admin
dashboard at **http://127.0.0.1:8787**.

```
python3 stop.py     # macOS/Linux
python stop.py      # Windows
```

Stops the admin dashboard and the Docker containers (containers are
stopped, not removed — `start.py` next time is fast). Leaves Docker
itself running.

## 6. Running a live test session

`start.py`/`stop.py` never touch `app.py` — that's the candidate-facing
process, deliberately bound to your whole LAN, meant to run only during
an actual test window rather than as routine background infra:

```
.venv/bin/python3 app.py     # macOS/Linux
.venv\Scripts\python app.py  # Windows
```

It prints the LAN URL to give `invite.py`/the Invites page as the
"Start-gate URL" when sending candidate invites.
