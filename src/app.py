import re
import time

from GmailApp import GmailApp, audit_log

def checkLists(email_address, lists):
    domain = email_address.split('@')[-1]
    return email_address in lists or domain in lists

def filter_mail(messages):
    with open('allowlist.txt', 'r') as allow_lists:
        allowed_emails = allow_lists.read().splitlines()

    readmail_ids = []

    for message in messages:
        m = app.get_message(message.get('id'))
        headers = (m.get("payload")).get("headers")
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
        try:
            sender_email = (re.search(r'[\w\.-]+@[\w\.-]+', sender)).group()
        except:
            print(f"\033[1;31;40m{sender} {subject}\033[0m")
            continue
        readmail_ids.append(messages.get('id'))

        if not checkLists(sender_email, allowed_emails):
            readmail_ids.append(messages.get('id'))

    return readmail_ids


def handler(app):
    print("Getting the list of emails")
    emails = app.list_mail('INBOX','older_than:3y is:read -in:important -has:attachment')

    if emails.get('messages'):
        print(f"Filtering {len(emails.get('messages'))} emails")
        readmail_ids = filter_mail(emails.get('messages'))

        print("Trash the filtered emails")
        if readmail_ids:
            app.trash_mails(readmail_ids)

if __name__ == "__main__":
    app = GmailApp()
    start_time = time.time()
    handler(app)
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f'Elapsed time: {elapsed_time:.2f} seconds')
    print("\033[1;32;40mDone\033[0m")
