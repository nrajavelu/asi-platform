"""
Sends every invited candidate on a round their test access email. If
--base-url is given (the LAN URL app.py prints), each candidate gets a
unique /start/{token} link that marks their attempt "started" the moment
they open it, then redirects into the real Google Form - requires app.py
running and reachable for the whole test window. Without --base-url,
candidates get the direct Form link instead (no "started" tracking).

Three delivery modes (--delivery-mode), independent of --base-url above:
  direct       - candidates get the plain link (default)
  seb_attach   - a personalized .seb file (startURL patched to the
                 candidate's link) is attached to the email
  seb_download - the email links to /seb/{token} instead, which builds the
                 .seb on demand at click time rather than at send time -
                 avoids mail gateways that strip .seb attachments, and
                 narrows the window in which the LAN IP baked into the
                 file's startURL could go stale. Requires --base-url,
                 since app.py is what serves that download route.

Defaults to --dry-run (prints what would be sent, no email leaves the
account). Pass --send to actually email via Gmail.

Usage:
    python invite.py --round-id 1 --base-url http://192.168.1.42:8788 --dry-run
    python invite.py --round-id 1 --base-url http://192.168.1.42:8788 --send

    # without started-tracking (direct form link):
    python invite.py --round-id 1 --send

    # with SEB proctoring, attached:
    python invite.py --round-id 1 --base-url http://192.168.1.42:8788 \
        --delivery-mode seb_attach --seb-template seb_templates/forms.seb --send

    # with SEB proctoring, as a download link:
    python invite.py --round-id 1 --base-url http://192.168.1.42:8788 \
        --delivery-mode seb_download --send
"""

import argparse
import base64
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from google_auth import gmail_service
from judge0_client import is_judge0_ready
from css_grader import is_css_grader_ready
from models import Attempt, Candidate, CodingQuestion, Round, SessionLocal, init_db
from react_grader import is_react_grader_ready
from seb_config import personalize_seb, seb_template_for_round_type
from sql_grader import is_pgvector_ready

READINESS_CHECKS = {
    "code": is_judge0_ready,
    "sql": is_pgvector_ready,
    "react": is_react_grader_ready,
    "css": is_css_grader_ready,
}

SEB_OUT_DIR = Path(__file__).parent / "seb_templates" / "out"


def build_message(to_email: str, subject: str, body: str, seb_path: Path | None) -> dict:
    msg = MIMEMultipart()
    msg["to"] = to_email
    msg["subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    if seb_path is not None:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(seb_path.read_bytes())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f'attachment; filename="{seb_path.name}"')
        msg.attach(part)

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    return {"raw": raw}


def send_invites(
    session,
    round_: Round,
    base_url: str | None = None,
    delivery_mode: str = "direct",
    seb_template_path: str | None = None,
    dry_run: bool = True,
) -> list[dict]:
    if round_.round_type == "coding":
        if not base_url:
            raise ValueError(
                "Coding rounds require --base-url (from app.py) - there's no "
                "Google Form fallback link for this round type."
            )
        # coding_session.assign_coding_questions draws from the whole bank
        # (no per-round topic filter yet), so any question_type present
        # anywhere in the bank could be assigned to this round's candidates.
        types_in_use = {row[0] for row in session.query(CodingQuestion.question_type).distinct()}
        for qtype in types_in_use:
            check = READINESS_CHECKS.get(qtype)
            if check is None:
                continue
            ready, message = check()
            if not ready:
                raise ValueError(
                    f"Pre-flight check failed for '{qtype}' questions: {message} "
                    f"Refusing to send invites - candidates would hit a broken coding session."
                )
    elif not round_.responder_uri:
        raise ValueError(f"Round #{round_.id} has no form yet (build one first)")

    if delivery_mode not in ("direct", "seb_attach", "seb_download"):
        raise ValueError(f"Unknown delivery_mode {delivery_mode!r}")

    attempts = session.query(Attempt).filter_by(round_id=round_.id, status="invited").all()
    if not attempts:
        print("No attempts in 'invited' status for this round.")
        return []

    template_path = None
    if delivery_mode == "seb_attach":
        if not seb_template_path:
            raise ValueError("delivery_mode='seb_attach' requires seb_template_path.")
        template_path = Path(seb_template_path)
        if not template_path.exists():
            raise ValueError(f"Missing SEB template: {template_path}")
    elif delivery_mode == "seb_download":
        if not base_url:
            raise ValueError(
                "delivery_mode='seb_download' requires --base-url - the download link "
                "is served by app.py, same as the /start/{token} redirect."
            )
        template_path = seb_template_for_round_type(round_.round_type)
        if not template_path.exists():
            raise ValueError(
                f"No SEB template at {template_path} for round type {round_.round_type!r} - "
                f"regenerate and save it there before using delivery_mode='seb_download'."
            )

    service = None if dry_run else gmail_service()
    results = []

    for attempt in attempts:
        candidate = session.get(Candidate, attempt.candidate_id)
        subject = f"{round_.round_type.title()} Test Access - {round_.drive.name}"

        link = f"{base_url.rstrip('/')}/start/{attempt.token}" if base_url else round_.responder_uri

        seb_out = None
        if delivery_mode == "seb_attach":
            seb_out = SEB_OUT_DIR / f"{attempt.token}.seb"
            personalize_seb(template_path, link, seb_out)
            instructions = (
                f"Open the attached .seb file to launch it in the secure test "
                f"browser (SEB should already be installed on your lab machine).\n\n"
                f"If needed, your link is: {link}\n\n"
            )
        elif delivery_mode == "seb_download":
            download_link = f"{base_url.rstrip('/')}/seb/{attempt.token}"
            instructions = (
                f"Download your secure test file from this link, then open it to launch "
                f"the secure test browser (SEB should already be installed on your lab "
                f"machine): {download_link}\n\n"
            )
        else:
            instructions = f"Your test link: {link}\n\n"

        body = (
            f"Hi {candidate.name},\n\n"
            f"Your {round_.round_type} test is ready. {instructions}"
            f"This link is for you only and can only be used once. "
            f"This test also allows only one submission per Google account, so "
            f"make sure you're signed in to your registered Gmail account before starting.\n\n"
            f"Good luck!"
        )

        if dry_run:
            print(f"[dry-run] Would email {candidate.email}: {subject}")
            results.append({"email": candidate.email, "status": "dry-run"})
        else:
            message = build_message(candidate.email, subject, body, seb_out)
            service.users().messages().send(userId="me", body=message).execute()
            print(f"Sent to {candidate.email}")
            results.append({"email": candidate.email, "status": "sent"})

    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--round-id", type=int, required=True)
    parser.add_argument("--base-url", default=None, help="e.g. http://192.168.1.42:8788 (from app.py) - omit for no started-tracking")
    parser.add_argument(
        "--delivery-mode", default="direct", choices=["direct", "seb_attach", "seb_download"],
        help="direct (plain link, default), seb_attach (.seb attached), seb_download (link to /seb/<token>)",
    )
    parser.add_argument("--seb-template", default=None, help="required for --delivery-mode seb_attach")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dry-run", action="store_true")
    group.add_argument("--send", action="store_true")
    args = parser.parse_args()

    init_db()
    session = SessionLocal()
    round_ = session.get(Round, args.round_id)
    if round_ is None:
        raise SystemExit(f"No round with id {args.round_id}")

    try:
        send_invites(
            session, round_, base_url=args.base_url, delivery_mode=args.delivery_mode,
            seb_template_path=args.seb_template, dry_run=args.dry_run,
        )
    except ValueError as e:
        raise SystemExit(str(e))
    session.close()


if __name__ == "__main__":
    main()
