from datetime import datetime
import pytz
from googleapiclient.errors import HttpError

from google_service import AuthorizeGoogle

def audit_log(type, string):
        date_format='%m/%d/%Y %H:%M:%S %Z'
        date = datetime.now(tz=pytz.utc)
        date = date.astimezone(pytz.timezone('US/Pacific'))
        fd = open("logfile.txt", 'a')
        fd.writelines(f'{date.strftime(date_format)} | {type} | {string}\n')
        fd.close()

class GmailApp:
    def __init__(self, first, last, email, label_name):
        self.first = first
        self.last = last
        self.email = email
        self.service = AuthorizeGoogle(['https://mail.google.com/'])
        self.label_id = self.check_label(label_name)
    
    def list_inbox(self):
        try:
            return self.service.users().messages().list(userId=self.email, labelIds='INBOX').execute()
        except HttpError as error:
            audit_log("Error", f'An error occurred: {error}')
            return False
    
    def get_message(self, message_id):
        try:
            return self.service.users().messages().get(userId=self.email, id=message_id, format='metadata').execute()
        except HttpError as error:
            audit_log("Error", f'An error occurred: {error}')
            return False

    def add_quarantine(self, message_ids):
        try:
            body={
                "addLabelIds": [self.label_id],
                "ids": message_ids,
                "removeLabelIds": ['INBOX']
            }
            self.service.users().messages().batchModify(userId=self.email, body=body).execute()
        except HttpError as error:
            audit_log("Error", f'An error occurred: {error}')


    def check_label(self, name):
        try:
            labels= self.service.users().labels().list(userId=self.email).execute()
            for label in labels.get("labels"):
                if label.get("name") == name:
                    return label.get("id")
            else: 
                label = self.service.users().labels().create(userId=self.email,body={"name":name}).execute()
                return label.get("id")
        except HttpError as error:
            audit_log("Error", f'An error occurred: {error}')