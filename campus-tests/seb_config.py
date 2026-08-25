"""
Patches a Safe Exam Browser (.seb) template with a per-candidate startURL.

The template must be built once per round type using the official SEB
Config Tool (https://safeexambrowser.org/download.html) — set the URL
whitelist, quit password, kiosk/lockdown settings, and Config Key options
there, then export as an UNENCRYPTED .seb file. This script does not
construct or guess at the SEB schema; it only rewrites the startURL key
inside whatever template you give it, using plistlib since unencrypted
.seb files are plain Apple property lists.

Usage:
    python seb_config.py --template seb_templates/aptitude.seb \
        --start-url "https://yourdomain/start/<token>" \
        --out seb_templates/out/<token>.seb
"""

import argparse
import io
import plistlib
from pathlib import Path

SEB_TEMPLATE_DIR = Path(__file__).parent / "seb_templates"

# Which template a round type gets when SEB is delivered as a download link
# (invite.py's "seb_download" mode) - resolved at download time, not
# invite-send time, since the round type is all that's known until then.
# Aptitude/Programming go through a live Google Form (needs the UA
# spoofing + relaxed URL filtering prog.seb has, to survive Google's
# sign-in-in-embedded-webview blocking); Coding is served entirely by
# this same app, so it can use a much stricter, Google-free template.
SEB_TEMPLATES_BY_ROUND_TYPE = {
    "aptitude": SEB_TEMPLATE_DIR / "forms.seb",
    "programming": SEB_TEMPLATE_DIR / "forms.seb",
    "coding": SEB_TEMPLATE_DIR / "coding.seb",
}


def seb_template_for_round_type(round_type: str) -> Path:
    path = SEB_TEMPLATES_BY_ROUND_TYPE.get(round_type)
    if path is None:
        raise ValueError(f"No SEB template mapping for round type {round_type!r}")
    return path


def personalized_seb_bytes(template_path: Path, start_url: str) -> bytes:
    with template_path.open("rb") as f:
        config = plistlib.load(f)
    config["startURL"] = start_url
    buf = io.BytesIO()
    plistlib.dump(config, buf, fmt=plistlib.FMT_XML)
    return buf.getvalue()


def personalize_seb(template_path: Path, start_url: str, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(personalized_seb_bytes(template_path, start_url))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--template", required=True)
    parser.add_argument("--start-url", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    personalize_seb(Path(args.template), args.start_url, Path(args.out))
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
