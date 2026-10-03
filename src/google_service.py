import os

from google.auth.exceptions import RefreshError  # type: ignore
from google.auth.transport.requests import Request  # type: ignore
from google.oauth2.credentials import Credentials  # type: ignore
from google_auth_oauthlib.flow import InstalledAppFlow  # type: ignore
from googleapiclient.discovery import build  # type: ignore

# Directory holding credentials.json, token.json and the log file
DATA_DIR = os.environ.get('DATA_DIR', '.')
CREDENTIALS_FILE = os.path.join(DATA_DIR, 'credentials.json')
TOKEN_FILE = os.path.join(DATA_DIR, 'token.json')

def AuthorizeGoogle(scopes: list):
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE)
        # A token granted for different scopes must be re-authorized
        if set(creds.scopes or []) != set(scopes):
            creds = None
    # If there are no (valid) credentials available, let the user log in.
    if creds and not creds.valid and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except RefreshError:
            # Refresh token was revoked or expired, fall back to a fresh login
            creds = None
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, scopes)
        creds = flow.run_local_server(port=8000, open_browser=False)
    # Save the credentials for the next run, readable only by the owner
    fd = os.open(TOKEN_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, 'w') as token:
        token.write(creds.to_json())
    os.chmod(TOKEN_FILE, 0o600)

    return build('gmail', 'v1', credentials=creds)
