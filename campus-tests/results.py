"""
Phase 3: KPI summary, score ingestion from Google Forms, shortlisting, and
best-effort invite-bounce detection.
"""

import base64

from models import Attempt, Candidate, CodingAttemptQuestion, CodingQuestion, Round


def kpi_summary(session, round_: Round) -> dict:
    attempts = session.query(Attempt).filter_by(round_id=round_.id).all()
    invited = len(attempts)
    started = sum(1 for a in attempts if a.status in ("started", "submitted"))
    completed = sum(1 for a in attempts if a.status == "submitted")
    return {
        "invited": invited,
        "started": started,
        "completed": completed,
        "not_completed": invited - completed,
    }


def filter_attempts(session, round_: Round, status: str | None = None) -> list[Attempt]:
    query = session.query(Attempt).filter_by(round_id=round_.id)
    if status:
        query = query.filter_by(status=status)
    return query.order_by(Attempt.id).all()


def ingest_results(session, round_: Round, service) -> dict:
    """Pulls responses from the Forms API, matches to candidates by email
    (requires 'Collect email addresses' Verified to be on for the form),
    and updates score/percent/status='submitted' for each match."""
    if not round_.form_id:
        raise SystemExit(f"Round #{round_.id} has no form yet")

    form = service.forms().get(formId=round_.form_id).execute()
    max_score = 0
    for item in form.get("items", []):
        grading = item.get("questionItem", {}).get("question", {}).get("grading")
        if grading:
            max_score += grading.get("pointValue", 0)

    all_responses = []
    page_token = None
    while True:
        resp = (
            service.forms()
            .responses()
            .list(formId=round_.form_id, pageToken=page_token)
            .execute()
        )
        all_responses.extend(resp.get("responses", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break

    by_email = {}
    for r in all_responses:
        email = r.get("respondentEmail")
        if email:
            by_email[email.strip().lower()] = r

    attempts = session.query(Attempt).filter_by(round_id=round_.id).all()
    matched = 0
    for attempt in attempts:
        candidate = session.get(Candidate, attempt.candidate_id)
        r = by_email.get(candidate.email.strip().lower())
        if r is None:
            continue
        score = r.get("totalScore", 0)
        percent = round(100 * score / max_score) if max_score else 0
        attempt.score = score
        attempt.max_score = max_score
        attempt.percent = percent
        attempt.status = "submitted"
        attempt.submitted_at = r.get("lastSubmittedTime") or r.get("createTime")
        matched += 1

    session.commit()
    return {
        "form_responses": len(all_responses),
        "matched_to_roster": matched,
        "total_attempts": len(attempts),
        "max_score": max_score,
    }


def shortlist(session, round_: Round, bench_pct: int, borderline_pct: int) -> dict:
    """Bands every submitted attempt into shortlisted / borderline /
    rejected using the given cutoffs, and persists the band on each Attempt."""
    attempts = (
        session.query(Attempt)
        .filter_by(round_id=round_.id, status="submitted")
        .order_by(Attempt.percent.desc())
        .all()
    )
    bands = {"shortlisted": [], "borderline": [], "rejected": []}
    for a in attempts:
        if a.percent >= bench_pct:
            band = "shortlisted"
        elif a.percent >= borderline_pct:
            band = "borderline"
        else:
            band = "rejected"
        a.band = band
        bands[band].append(a)
    session.commit()
    return bands


def coding_question_analytics(session, round_: Round) -> list[dict]:
    """Coding rounds only: per-question breakdown of how many candidates
    passed / partially passed / failed / only-tried / never-touched each
    assigned question, sorted hardest-first (lowest pass rate)."""
    rows = (
        session.query(CodingAttemptQuestion)
        .join(Attempt, CodingAttemptQuestion.attempt_id == Attempt.id)
        .filter(Attempt.round_id == round_.id)
        .all()
    )

    by_question: dict[int, list] = {}
    for row in rows:
        by_question.setdefault(row.question_id, []).append(row)

    analytics = []
    for question_id, question_rows in by_question.items():
        question = session.get(CodingQuestion, question_id)
        total = len(question_rows)
        counts = {status: 0 for status in ("passed", "partial", "failed", "attempted", "not_attempted")}
        for r in question_rows:
            counts[r.status] = counts.get(r.status, 0) + 1
        analytics.append({
            "question_id": question_id,
            "title": question.title,
            "assigned_count": total,
            "passed": counts["passed"],
            "partial": counts["partial"],
            "failed": counts["failed"],
            "attempted_only": counts["attempted"],
            "not_attempted": counts["not_attempted"],
            "pass_rate": round(100 * counts["passed"] / total) if total else 0,
        })

    analytics.sort(key=lambda a: a["pass_rate"])
    return analytics


def top_n_attempts(session, round_: Round, n: int) -> list[Attempt]:
    return (
        session.query(Attempt)
        .filter_by(round_id=round_.id, status="submitted")
        .order_by(Attempt.percent.desc())
        .limit(n)
        .all()
    )


BOUNCE_QUERY = (
    'from:(mailer-daemon OR "Mail Delivery Subsystem") '
    'subject:(failure OR "delivery status" OR undelivered OR "not delivered" OR bounce OR "delivery incomplete")'
)


def _extract_message_text(msg: dict) -> str:
    parts_text = [msg.get("snippet", "")]

    def walk(part):
        data = part.get("body", {}).get("data")
        if data:
            try:
                parts_text.append(base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="ignore"))
            except Exception:
                pass
        for sub in part.get("parts", []):
            walk(sub)

    payload = msg.get("payload")
    if payload:
        walk(payload)
    return " ".join(parts_text)


def detect_bounces(gmail_svc, candidate_emails: list[str], after_epoch: int | None = None) -> list[str]:
    """Best-effort scan of the admin's inbox for delivery-failure
    notifications mentioning one of the given candidate emails. Bounce
    message formats vary by receiving mail server, so this can miss some -
    it's a helper to surface likely-bad addresses quickly, not a guarantee."""
    query = BOUNCE_QUERY
    if after_epoch:
        query += f" after:{after_epoch}"

    bounced = set()
    lower_targets = {e.lower() for e in candidate_emails}
    page_token = None
    while True:
        resp = (
            gmail_svc.users()
            .messages()
            .list(userId="me", q=query, pageToken=page_token)
            .execute()
        )
        for m in resp.get("messages", []):
            msg = gmail_svc.users().messages().get(userId="me", id=m["id"], format="full").execute()
            text = _extract_message_text(msg).lower()
            for email in lower_targets:
                if email in text:
                    bounced.add(email)
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return sorted(bounced)
