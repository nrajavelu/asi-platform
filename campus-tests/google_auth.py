from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

TOKEN_FILE = Path(__file__).parent / "credentials" / "token.json"


def get_credentials() -> Credentials:
    if not TOKEN_FILE.exists():
        raise ValueError(
            f"Missing {TOKEN_FILE}. Run generate_refresh_token.py first."
        )
    creds = Credentials.from_authorized_user_file(str(TOKEN_FILE))
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        TOKEN_FILE.write_text(creds.to_json())
    return creds


def forms_service():
    return build("forms", "v1", credentials=get_credentials())


def gmail_service():
    return build("gmail", "v1", credentials=get_credentials())
