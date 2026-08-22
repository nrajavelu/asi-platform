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
import plistlib
from pathlib import Path


def personalize_seb(template_path: Path, start_url: str, out_path: Path) -> None:
    with template_path.open("rb") as f:
        config = plistlib.load(f)
    config["startURL"] = start_url
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("wb") as f:
        plistlib.dump(config, f, fmt=plistlib.FMT_XML)


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
