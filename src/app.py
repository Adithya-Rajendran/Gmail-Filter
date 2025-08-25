import re
import time
import base64
import joblib
from bs4 import BeautifulSoup

from GmailApp import GmailApp, audit_log

try:
    model = joblib.load('/usr/src/model/spam_classifier_model.pkl')
    vectorizer = joblib.load('/usr/src/model/tfidf_vectorizer.pkl')
    print("Model and vectorizer loaded successfully.")
except FileNotFoundError:
    print("Error: Model or vectorizer files not found.")
    print("Please run the training script first to create these files.")
    exit()

def preprocess_text(text):
    """Applies the exact same cleaning steps used during training."""
    text = text.lower()
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def classify_email(subject, body):
    """
    Takes an email's subject and body, preprocesses them, and predicts
    if it is spam (1) or not spam (0).
    """
    full_text = subject + " " + body
    cleaned_text = preprocess_text(full_text)
    
    text_vector = vectorizer.transform([cleaned_text])
    
    prediction = model.predict(text_vector)
    probability = model.predict_proba(text_vector)
    
    # Get the probability of the email being spam (class 1)
    if prediction == 1:
        return prediction, f"{probability[0][1]:.2%}"
    else:
        return prediction, f"{probability[0][0]:.2%}"
    
def checkLists(email_address, lists):
    domain = email_address.split('@')[-1]
    return email_address in lists or domain in lists

def get_email_content(message):
    # Get value of 'payload' from dictionary 'txt'
    payload = message['payload']
    headers = payload['headers']
    # Look for Subject and Sender Email in the headers
    for d in headers:
        if d['name'] == 'Subject':
            subject = d['value']

    if 'parts' in payload:
        parts = payload['parts']
        for part in parts:
            if part['mimeType'] == 'text/plain':
                data = part['body']['data']
                decoded_data = base64.urlsafe_b64decode(data).decode('utf-8')
                body = decoded_data
            elif part['mimeType'] == 'text/html':
                data = part['body']['data']
                decoded_data = base64.urlsafe_b64decode(data).decode('utf-8')
                soup = BeautifulSoup(decoded_data, 'html.parser')
                body = soup.get_text()
    else:
        data = payload['body']['data']
        decoded_data = base64.urlsafe_b64decode(data).decode('utf-8')
        body = decoded_data

    return subject, body

def filter_mail(messages):
    readmail_ids = []

    for message in messages:
        m = app.get_message(message.get('id'))
        subject, body = get_email_content(m)
        
        prediction, probability = classify_email(subject, body)
        if prediction == 1:
            print(f"SPAM (Confidence: {probability})", subject)
            readmail_ids.append(m.get("id"))

    return readmail_ids


def handler(app):
    print("Getting the list of emails")
    emails = app.list_mail('INBOX','(in:spam OR in:all) after:{}')

    if emails.get('messages'):
        print(f"Filtering {len(emails.get('messages'))} emails")
        filter_mail(emails.get('messages'))

    print("Number of SPAM:", len(filter_mail(emails.get('messages'))))


if __name__ == "__main__":
    app = GmailApp()
    start_time = time.time()
    handler(app)
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f'Elapsed time: {elapsed_time:.2f} seconds')
    print("\033[1;32;40mDone\033[0m")
