import os
from datetime import datetime
from zoneinfo import ZoneInfo

from googleapiclient.errors import HttpError  # type: ignore

from google_service import DATA_DIR, AuthorizeGoogle

# Read messages and modify labels / trash. Unlike https://mail.google.com/,
# this scope cannot permanently delete mail or change account settings.
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
LOG_FILE = os.path.join(DATA_DIR, 'logfile.txt')
LOG_TIMEZONE = ZoneInfo(os.environ.get('LOG_TIMEZONE', 'US/Pacific'))
# batchModify accepts at most 1000 message ids per request
BATCH_SIZE = 1000

def audit_log(type, string):
    date_format = '%m/%d/%Y %H:%M:%S %Z'
    date = datetime.now(tz=LOG_TIMEZONE)
    with open(LOG_FILE, 'a') as fd:
        fd.write(f'{date.strftime(date_format)} | {type} | {string}\n')

class GmailApp:
    def __init__(self):
        self.email = "me"
        self.service = AuthorizeGoogle(SCOPES)

    def list_mail(self, label: str, query: str, include_spam_trash: bool = False, limit: int | None = None):
        """Returns every message matching the query (up to limit), following pagination."""
        messages = []
        page_token = None
        try:
            while True:
                response = self.service.users().messages().list(userId=self.email, labelIds=label, maxResults=500,
                                                                q=query, pageToken=page_token,
                                                                includeSpamTrash=include_spam_trash).execute()
                messages.extend(response.get('messages', []))
                page_token = response.get('nextPageToken')
                if not page_token or (limit and len(messages) >= limit):
                    return messages[:limit]
        except HttpError as error:
            audit_log("Error ", f'An error occurred: {error}')
            return messages

    def get_message(self, message_id):
        try:
            return self.service.users().messages().get(userId=self.email, id=message_id, format="full").execute()
        except HttpError as error:
            audit_log("Error ", f'An error occurred: {error}')
            return False

    def mod_label(self, message_ids, addlabels: list, dellabels: list):
        # Check if the labels are present, if not, create them.
        labels_ids = [self.check_label(label) for label in addlabels]

        try:
            for i in range(0, len(message_ids), BATCH_SIZE):
                body = {
                    "addLabelIds": labels_ids,
                    "ids": message_ids[i:i + BATCH_SIZE],
                    "removeLabelIds": dellabels
                }
                self.service.users().messages().batchModify(userId=self.email, body=body).execute()
            return True
        except HttpError as error:
            audit_log("Error ", f'An error occurred: {error}')
            return False

    def trash_mails(self, message_ids: list):
        for messageid in message_ids:
            try:
                self.service.users().messages().trash(userId=self.email, id=messageid).execute()
            except HttpError as error:
                audit_log("Error ", f'An error occurred: {error}')

    def check_label(self, name):
        try:
            labels = self.service.users().labels().list(userId=self.email).execute()
            for label in labels.get("labels", []):
                if label.get("name") == name:
                    return label.get("id")
            body = {
                "labelListVisibility": "labelShow",
                "name": name
            }
            label = self.service.users().labels().create(userId=self.email, body=body).execute()
            return label.get("id")
        except HttpError as error:
            audit_log("Error ", f'An error occurred: {error}')
