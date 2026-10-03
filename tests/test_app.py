import base64

import pytest
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline

import app
from spam_model import combine_text, load_model, preprocess_text, save_model, spam_probability


def b64(text):
    return base64.urlsafe_b64encode(text.encode()).decode()


@pytest.fixture(scope="module")
def pipeline():
    texts = ["win a free prize now", "claim your cash reward", "meeting agenda for monday", "notes from the call"]
    return make_pipeline(TfidfVectorizer(preprocessor=preprocess_text), LogisticRegression()).fit(texts, [1, 1, 0, 0])


class FakeGmail:
    def __init__(self, messages):
        self.messages = messages
        self.labelled = []

    def list_mail(self, label, query):
        return [{"id": message_id} for message_id in self.messages]

    def get_message(self, message_id):
        # Simulates an API error for unknown ids
        return self.messages.get(message_id, False)

    def mod_label(self, message_ids, addlabels, dellabels):
        self.labelled.append((message_ids, addlabels))
        return True


def simple_message(message_id, subject, body):
    return {"id": message_id, "payload": {"mimeType": "text/plain", "headers": [{"name": "Subject", "value": subject}],
                                          "body": {"data": b64(body)}}}


def test_preprocess_text_replaces_urls_emails_and_numbers():
    text = "WIN $1000 at https://evil.example/x?a=1 or mail bob@evil.example!"
    assert preprocess_text(text) == "win numtoken at urltoken or mail emailtoken"


def test_nested_multipart_prefers_plain_text_and_skips_attachments():
    message = {"payload": {"mimeType": "multipart/mixed", "headers": [{"name": "From", "value": "x"}], "parts": [
        {"mimeType": "multipart/alternative", "body": {}, "parts": [
            {"mimeType": "text/plain", "body": {"data": b64("hello plain \xe9")}},
            {"mimeType": "text/html", "body": {"data": b64("<p>hello html</p>")}}]},
        {"mimeType": "text/plain", "filename": "a.txt", "body": {"attachmentId": "z"}}]}}
    assert app.get_email_content(message) == ("", "hello plain \xe9")


def test_html_only_message_is_converted_to_text():
    message = {"payload": {"mimeType": "text/html", "headers": [{"name": "subject", "value": "S"}],
                           "body": {"data": b64("<b>hi</b>")}}}
    assert app.get_email_content(message) == ("S", "hi")


def test_invalid_utf8_does_not_raise():
    data = base64.urlsafe_b64encode(b"\xff\xfe").decode()
    message = {"payload": {"mimeType": "text/plain", "headers": [], "body": {"data": data}}}
    assert app.get_email_content(message)[0] == ""


def test_filter_mail_flags_spam_and_skips_failed_fetches(pipeline):
    gmail = FakeGmail({"1": simple_message("1", "win a prize", "claim your free cash reward now"),
                       "2": simple_message("2", "agenda", "meeting notes for monday")})
    messages = gmail.list_mail("INBOX", "") + [{"id": "missing"}]
    assert app.filter_mail(gmail, pipeline, 0.5, messages) == ["1"]


def test_handler_labels_spam_only_when_configured(pipeline, monkeypatch):
    gmail = FakeGmail({"1": simple_message("1", "win a prize", "claim your free cash reward now")})
    app.handler(gmail, pipeline, 0.5)
    assert gmail.labelled == []

    monkeypatch.setattr(app, "SPAM_LABEL", "ML-Spam")
    logged = []
    monkeypatch.setattr(app, "audit_log", lambda *args: logged.append(args))
    app.handler(gmail, pipeline, 0.5)
    assert gmail.labelled == [(["1"], ["ML-Spam"])]
    assert len(logged) == 1


def test_model_bundle_round_trip(pipeline, tmp_path):
    save_model(tmp_path, pipeline, threshold=0.9, metrics={"f1": 1.0})
    bundle = load_model(tmp_path)
    assert bundle["threshold"] == 0.9
    assert spam_probability(bundle["pipeline"], "win", "free cash prize") > 0.5
    assert combine_text("a", "b") == "a b"
