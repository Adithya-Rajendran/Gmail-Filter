import re

from GmailApp import GmailApp, audit_log

def checkLists(email_address, lists):
    domain = email_address.split('@')[-1]
    return email_address in lists or domain in lists

def handler(app):
    with open('allowlist.txt', 'r') as allow_lists:
        allowed_emails = allow_lists.read().splitlines()
    emails = app.list_inbox()
    readmail_ids = []

    for messages in emails.get('messages'):
        m = app.get_message(messages.get('id'))
        headers = (m.get("payload")).get("headers")
        #sender = next((header.get("value") for header in headers if header["name"] == "From"), None)
        #subject = next((header.get("value") for header in headers if header["name"] == "Subject"), None)
        sender = None
        subject = None
        headers.reverse() # Reversing here because these elements tend to show up towards the end
        for header in headers: 
            if header["name"] == "From":
                sender = header["value"]
            if header["name"] == "Subject":
                subject = header["value"]
            if sender and subject:
                break

        sender_email = (re.search('<(.*)>', sender)).group(1)

        if not checkLists(sender_email, allowed_emails):
            readmail_ids.append(messages.get('id'))
            audit_log("Filter", f'{sender} : {subject}')

    if readmail_ids:
        app.mod_label(readmail_ids, ["ReadMail"], ["INBOX"])

if __name__ == "__main__":
    app = GmailApp()
    handler(app)
    print("Done")
