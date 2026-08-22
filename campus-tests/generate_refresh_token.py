"""
One-time OAuth consent flow for aizentifycampus@gmail.com.

Run this locally, logged in as aizentifycampus@gmail.com in the browser
that opens. It writes credentials/token.json, which the FastAPI service
loads later to call the Forms/Sheets/Drive/Gmail APIs without logging in
again (google-auth auto-refreshes the access token from the refresh token
stored inside it).
"""

from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

CREDENTIALS_DIR = Path(__file__).parent / "credentials"
CLIENT_SECRET_FILE = CREDENTIALS_DIR / "client_secret.json"
TOKEN_FILE = CREDENTIALS_DIR / "token.json"

SCOPES = [
    "https://www.googleapis.com/auth/forms.body",
    "https://www.googleapis.com/auth/forms.responses.readonly",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
]


def main() -> None:
    if not CLIENT_SECRET_FILE.exists():
        raise SystemExit(
            f"Missing {CLIENT_SECRET_FILE}. Download the OAuth Client ID JSON "
            "from Cloud Console (Credentials > your Desktop app client) and "
            "save it there first."
        )

    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET_FILE), SCOPES)
    creds = flow.run_local_server(port=0, access_type="offline", prompt="consent")

    TOKEN_FILE.write_text(creds.to_json())
    print(f"Saved refresh token to {TOKEN_FILE}")


if __name__ == "__main__":
    main()
