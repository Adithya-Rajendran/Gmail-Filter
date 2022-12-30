import re
from fnmatch import fnmatch

from GmailApp import GmailApp, audit_log

def handler(app):
        black_lists = open('blacklist.txt', 'r')
        blocked_emails = black_lists.read().splitlines()
        emails = app.list_inbox()
        blacklist_ids = []
        for messages in emails.get('messages'):
            m = app.get_message(messages.get('id'))
            headers = (m.get("payload")).get("headers")
            subject = next((header.get("value") for header in headers if header["name"] == "Subject"), None)
            sender = next((header.get("value") for header in headers if header["name"] == "From"), None)
            sender_email = (re.search('<(.*)>', sender)).group(1)
            for blocked_email in blocked_emails:
                if fnmatch(sender_email,blocked_email):
                    blacklist_ids.append(messages.get('id'))
                    audit_log("Filter", f'{sender} : {subject}')
                    break

        if blacklist_ids:
            app.add_quarantine(blacklist_ids)

if __name__ == "__main__":
    app = GmailApp("Test", "Account", "spamfilterbottester@gmail.com", "Quarantine")
    handler(app)
    print("Done")