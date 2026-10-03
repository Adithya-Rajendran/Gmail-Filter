"""Exports your own Gmail as labelled training data for train-model.ipynb.

Messages in the Spam folder are labelled 1 and messages in the Inbox are
labelled 0. Rows are merged into DATA_DIR/gmail_dataset.csv by message id, so
running this regularly accumulates spam even though Gmail deletes it after 30
days.

The CSV contains the text of your private email: it is written owner-readable
only, lives in the git-ignored data/ directory, and must never be committed or
uploaded. A model trained on it can also leak words from your mail, so don't
publish that model either.

Usage (from src/): DATA_DIR=../data python export_training_data.py --max 2000
"""
import argparse
import csv
import os
from datetime import UTC, datetime

from app import get_email_content
from GmailApp import GmailApp
from google_service import DATA_DIR

OUTPUT_FILE = os.path.join(DATA_DIR, 'gmail_dataset.csv')
FIELDS = ['id', 'date', 'subject', 'body', 'label']

def read_existing(path):
    if not os.path.exists(path):
        return {}
    with open(path, newline='') as fd:
        return {row['id']: row for row in csv.DictReader(fd)}

def export(app, label_id, label, query, limit, rows):
    messages = app.list_mail(label_id, query, include_spam_trash=(label_id == 'SPAM'), limit=limit)
    new = [m for m in messages if m['id'] not in rows]
    print(f"{label_id}: {len(messages)} messages, {len(new)} new")
    for count, message in enumerate(new, 1):
        m = app.get_message(message['id'])
        if not m:
            continue
        subject, body = get_email_content(m)
        date = datetime.fromtimestamp(int(m['internalDate']) / 1000, tz=UTC).isoformat()
        rows[m['id']] = {'id': m['id'], 'date': date, 'subject': subject, 'body': body, 'label': label}
        if count % 100 == 0:
            print(f"  {count}/{len(new)}")

def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    parser.add_argument('--max', type=int, default=2000, help='maximum messages per folder (default 2000)')
    parser.add_argument('--ham-query', default='newer_than:1y',
                        help='Gmail query selecting legitimate Inbox mail (default: newer_than:1y)')
    args = parser.parse_args()

    rows = read_existing(OUTPUT_FILE)
    app = GmailApp()
    export(app, 'SPAM', 1, '', args.max, rows)
    export(app, 'INBOX', 0, args.ham_query, args.max, rows)

    os.makedirs(DATA_DIR, exist_ok=True)
    fd = os.open(OUTPUT_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, 'w', newline='') as out:
        writer = csv.DictWriter(out, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(sorted(rows.values(), key=lambda row: row['date']))
    os.chmod(OUTPUT_FILE, 0o600)
    spam = sum(int(row['label']) for row in rows.values())
    print(f"Wrote {len(rows)} messages ({spam} spam, {len(rows) - spam} legitimate) to {OUTPUT_FILE}")

if __name__ == '__main__':
    main()
