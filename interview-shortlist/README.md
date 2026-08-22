# Interview Shortlist

Local web app for reviewing Aizentify application exports. Upload the Tally
form export (CSV or XLSX) and it becomes a dated report: each applicant's
Indian state is inferred from their free-text city, an AI/Claude-relevance
signal is scored from their certifications and employer, and they're split
into Intern / Experienced tracks — all computed once, at upload time, and
filtered to candidates willing to relocate to Chennai.

From a report page you can mark a 1–5 star rating and Round 1 / Round 2
shortlist checkboxes per candidate; both save immediately to that report's
`candidates.csv`.

## Setup

```bash
cd interview-shortlist
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python webapp.py
```

Open http://127.0.0.1:8790 — binds to localhost only.

## Data layout

Each upload creates `data/reports/<YYYYMMDD-HHMMSS>/`:

- `source.csv` / `source.xlsx` — the original upload, untouched.
- `candidates.csv` — the working file: every relocating candidate plus
  computed `state`, `ai_score`, `tier`, `final_score`, and the editable
  `rating` / `round1` / `round2` columns. This is what the report page reads
  and writes on every rating/checkbox change.
- `meta.json` — report identity (original filename, upload timestamp) and
  top-line counts shown on the home page and report header.

`data/` is gitignored — reports are local working data, not source.

## Upload template

Expects the same columns as the Tally "Inviting Applications" export:
`Submission ID`, `Submitted at`, `Role Applying For`, `Name`, `Email`,
`Mobile Number`, `Current Employer`, `Total Professional Experience`,
`Your Current Location`, `Relevant Certifications if any (Claude Certified
Preferred)`, `Willing to relocate to Chennai?`, `Upload Resume`.
