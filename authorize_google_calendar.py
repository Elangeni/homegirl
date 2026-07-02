"""One-time script to authorize Homegirl to read your Google Calendar.

Google Calendar's private data (your real schedule) cannot be read with a
plain API key — Google requires OAuth 2.0 user consent for anything that
isn't a calendar you've made public. Run this script once, from a machine
with a browser, after creating an OAuth client (type "Desktop app") in
Google Cloud Console and setting GOOGLE_OAUTH_CLIENT_ID and
GOOGLE_OAUTH_CLIENT_SECRET in your .env file.

It writes a refresh token to the path Homegirl reads on every run
(GOOGLE_CALENDAR_TOKEN_FILE, default google_calendar_token.json in the
project root). If you authorize from a different machine than the display
device, copy that file over to the device afterward.
"""

from __future__ import annotations

from dotenv import load_dotenv
from google_auth_oauthlib.flow import InstalledAppFlow

from homegirl.services.calendar import SCOPES
from homegirl.settings import Settings


def main() -> None:
    load_dotenv()
    settings = Settings.from_environment()

    if not settings.google_client_id or not settings.google_client_secret:
        raise SystemExit(
            "Set GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET in your .env "
            "before running this script."
        )

    client_config = {
        "installed": {
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"],
        }
    }

    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
    credentials = flow.run_local_server(port=0)

    token_path = settings.google_calendar_token_path
    token_path.write_text(credentials.to_json())
    print(f"Saved Google Calendar token to {token_path}")


if __name__ == "__main__":
    main()
