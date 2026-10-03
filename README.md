# Gmail-Spam-Filter

Python app that uses the Gmail API and a machine-learning classifier to find
spam and phishing emails in your inbox. By default it only **reports** what it
finds; set `SPAM_LABEL` to have it tag those emails with a Gmail label.

```
Gmail API ──► app.py ──► subject + body text ──► spam_pipeline.joblib ──► report / label
                              (TF-IDF + classifier, trained in train-model.ipynb)
```

## Project layout

| Path | Purpose |
|---|---|
| `src/app.py` | Entry point: lists recent emails, extracts their text and classifies them |
| `src/spam_model.py` | Text preprocessing and model save/load, shared by the app and notebooks |
| `src/GmailApp.py` | Thin wrapper around the Gmail API (list, get, label, trash) |
| `src/google_service.py` | OAuth login and token storage |
| `src/export_training_data.py` | Exports your Spam folder and Inbox as local training data |
| `train-model.ipynb` | Downloads the dataset, compares models, picks a threshold, saves the model |
| `load-model.ipynb` | Loads the saved model and tries it on example emails |
| `tests/` | Unit tests (no Gmail account or trained model needed) |
| `data/` | *Not committed.* `credentials.json`, `token.json`, `logfile.txt`, `gmail_dataset.csv` |
| `model/` | *Not committed.* The trained `spam_pipeline.joblib` |

## 1. Set up Gmail API credentials

1. In the [Google Cloud Console](https://console.cloud.google.com/), create a
   project and enable the **Gmail API**.
2. Configure the OAuth consent screen and add your account as a test user.
3. Create an **OAuth client ID** of type *Desktop app*, download it and save it
   as `data/credentials.json`.

The first run prints a login URL. After you approve access, the token is stored
in `data/token.json` (owner-readable only). The app requests the
`gmail.modify` scope, which lets it read mail and change labels but not
permanently delete mail.

> If you used an older version of this project, move `credentials.json` from
> `src/` to `data/`. You'll be asked to log in once more because the requested
> scope got narrower.

## 2. Train the model

```bash
python3 -m venv .venv
```
```bash
.venv/bin/pip install -r requirements-dev.txt
```
```bash
.venv/bin/nbstripout --install
```

Open `train-model.ipynb` with the `.venv` kernel and run all cells (about a minute and
under 1 GB of RAM). It saves `model/spam_pipeline.joblib`. Retrain whenever you upgrade
`scikit-learn`.

### How good is it?

Trained on six public corpora (CEAS 2008, Enron, Ling-Spam, Nazario, Nigerian Fraud,
SpamAssassin; 82k emails) with TF-IDF + logistic regression:

| Evaluation | Precision | Recall | F1 |
|---|---|---|---|
| Random 20% test split | 0.989 | 0.985 | 0.987 |
| Tested on a corpus left out of training (range over 4 corpora) | 0.80–0.92 | 0.79–0.96 | 0.83–0.91 |

The second row is the realistic one. These corpora are from 2000–2008 and contain almost
no modern legitimate email, so the model tends to flag things like shipping notifications.

### Train on your own mail (recommended)

No public dataset contains modern *legitimate* email, so your own mail is the best data
you can add. This exports your Spam folder (label 1) and recent Inbox (label 0):

```bash
cd src && DATA_DIR=../data ../.venv/bin/python export_training_data.py --max 2000
```

Re-running merges new messages into `data/gmail_dataset.csv`; Gmail deletes spam after 30
days, so running it regularly builds up more spam examples. `train-model.ipynb` picks the
file up automatically and reports how the public-data model does on your mail.

Your Spam folder is Gmail's own verdict, so spot-check it; an Inbox may also hold missed
spam. **The CSV and any model trained on it contain your private email: never commit,
upload or share them.** Both live in git-ignored folders.

## 3. Run with Docker

```bash
docker build -t gmailfilter .
```
```bash
docker run -it --rm --name gmailbot --net=host -v "$(pwd)/data:/data" -v "$(pwd)/model:/usr/src/model:ro" gmailfilter
```

`--net=host` is needed for the one-time OAuth login callback on port 8000. The
container runs as UID 1000; if your user has a different UID, build with
`--build-arg UID=$(id -u)`.

To run without Docker: `cd src && DATA_DIR=../data MODEL_DIR=../model ../.venv/bin/python app.py`.

### Configuration

| Variable | Default | Meaning |
|---|---|---|
| `GMAIL_QUERY` | `newer_than:1d` | [Gmail search query](https://support.google.com/mail/answer/7190) for the emails to check |
| `SPAM_LABEL` | *(unset)* | If set, spam is tagged with this label (created if missing) |
| `SPAM_THRESHOLD` | *(from model)* | Spam probability needed to flag an email |
| `DATA_DIR` | `/data` in Docker, `.` otherwise | Where credentials, token and log live |
| `MODEL_DIR` | `/usr/src/model` | Where `spam_pipeline.joblib` lives |
| `LOG_TIMEZONE` | `US/Pacific` | Timezone used in `logfile.txt` |

## Development

```bash
.venv/bin/pytest
```
```bash
.venv/bin/ruff check .
```

CI runs both on every push and pull request. Notebook outputs are stripped on
commit by `nbstripout` so diffs stay readable and no local paths leak.
