"""Text preprocessing and model loading shared by the app and the notebooks.

The trained model is saved as a single joblib bundle containing a scikit-learn
Pipeline (TF-IDF vectorizer + classifier) and the decision threshold chosen
during training. The vectorizer references preprocess_text() below, so this
module must be importable wherever the model is loaded.
"""
import os
import re
import warnings

import joblib
import sklearn

MODEL_FILE = 'spam_pipeline.joblib'
# Only the start of an email is used; some are megabytes long and the extra
# text adds noise and processing time rather than accuracy.
MAX_CHARS = 10_000

URL_RE = re.compile(r'(https?://|www\.)\S+')
EMAIL_RE = re.compile(r'\S+@\S+')
NUMBER_RE = re.compile(r'\d+')
NON_ALPHA_RE = re.compile(r'[^a-z\s]')
WHITESPACE_RE = re.compile(r'\s+')

def preprocess_text(text):
    """Truncates text to MAX_CHARS, lowercases it and replaces URLs, email
    addresses and numbers with placeholder tokens (they are strong spam
    signals), then strips everything that is not a letter."""
    text = text[:MAX_CHARS].lower()
    text = URL_RE.sub(' urltoken ', text)
    text = EMAIL_RE.sub(' emailtoken ', text)
    text = NUMBER_RE.sub(' numtoken ', text)
    text = NON_ALPHA_RE.sub(' ', text)
    return WHITESPACE_RE.sub(' ', text).strip()

def combine_text(subject, body):
    """Builds the single text field the model is trained on."""
    return f"{subject} {body}"

def save_model(model_dir, pipeline, threshold, metrics=None):
    os.makedirs(model_dir, exist_ok=True)
    bundle = {
        'pipeline': pipeline,
        'threshold': threshold,
        'sklearn_version': sklearn.__version__,
        'metrics': metrics or {},
    }
    path = os.path.join(model_dir, MODEL_FILE)
    joblib.dump(bundle, path)
    return path

def load_model(model_dir):
    """Loads the model bundle. Raises FileNotFoundError if it is missing.

    Only load bundles you trained yourself: joblib files are pickles and can
    execute arbitrary code when loaded."""
    bundle = joblib.load(os.path.join(model_dir, MODEL_FILE))
    if bundle['sklearn_version'] != sklearn.__version__:
        warnings.warn(f"Model was trained with scikit-learn {bundle['sklearn_version']} but "
                      f"{sklearn.__version__} is installed; retrain the model if predictions look wrong.",
                      stacklevel=2)
    return bundle

def spam_probability(pipeline, subject, body):
    """Returns the model's probability that the email is spam."""
    return float(pipeline.predict_proba([combine_text(subject, body)])[0][1])
