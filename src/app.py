import base64
import os
import sys
import time

from bs4 import BeautifulSoup

from GmailApp import GmailApp, audit_log
from spam_model import load_model, spam_probability

MODEL_DIR = os.environ.get('MODEL_DIR', '/usr/src/model')
# Gmail search query for the messages to classify
QUERY = os.environ.get('GMAIL_QUERY', 'newer_than:1d')
# If set, spam is tagged with this Gmail label; otherwise it is only reported
SPAM_LABEL = os.environ.get('SPAM_LABEL')
# Overrides the decision threshold chosen when the model was trained
SPAM_THRESHOLD = os.environ.get('SPAM_THRESHOLD')

def decode_body(data):
    return base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')

def walk_parts(part):
    """Yields a MIME part and all of its nested sub-parts."""
    yield part
    for sub_part in part.get('parts', []):
        yield from walk_parts(sub_part)

def get_email_content(message):
    payload = message['payload']
    subject = next((h['value'] for h in payload.get('headers', [])
                    if h['name'].lower() == 'subject'), '')

    # Collect text from every (possibly nested) part, skipping attachments
    plain, html = [], []
    for part in walk_parts(payload):
        data = part.get('body', {}).get('data')
        if not data or part.get('filename'):
            continue
        if part.get('mimeType') == 'text/plain':
            plain.append(decode_body(data))
        elif part.get('mimeType') == 'text/html':
            html.append(BeautifulSoup(decode_body(data), 'html.parser').get_text())

    # Prefer the plain text version when both are present
    body = '\n'.join(plain or html)
    return subject, body

def filter_mail(app, pipeline, threshold, messages):
    spam_ids = []

    for message in messages:
        m = app.get_message(message.get('id'))
        if not m:
            continue
        subject, body = get_email_content(m)

        probability = spam_probability(pipeline, subject, body)
        if probability >= threshold:
            print(f"SPAM (Confidence: {probability:.2%})", subject)
            spam_ids.append(m.get("id"))

    return spam_ids


def handler(app, pipeline, threshold):
    print("Getting the list of emails")
    messages = app.list_mail('INBOX', QUERY)

    print(f"Filtering {len(messages)} emails")
    spam_ids = filter_mail(app, pipeline, threshold, messages)
    print("Number of SPAM:", len(spam_ids))

    if spam_ids and SPAM_LABEL:
        print(f"Labelling spam as '{SPAM_LABEL}'")
        if app.mod_label(spam_ids, [SPAM_LABEL], []):
            audit_log("Label ", f"Labelled {len(spam_ids)} messages as '{SPAM_LABEL}'")


if __name__ == "__main__":
    try:
        bundle = load_model(MODEL_DIR)
    except FileNotFoundError:
        print(f"Error: Model not found in {MODEL_DIR}.")
        print("Please run train-model.ipynb first to create it.")
        sys.exit(1)
    threshold = float(SPAM_THRESHOLD) if SPAM_THRESHOLD else bundle['threshold']
    print(f"Model loaded (spam threshold {threshold:.2f}).")

    app = GmailApp()
    start_time = time.time()
    handler(app, bundle['pipeline'], threshold)
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f'Elapsed time: {elapsed_time:.2f} seconds')
    print("\033[1;32;40mDone\033[0m")
