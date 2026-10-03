FROM python:3.14-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MODEL_DIR=/usr/src/model \
    DATA_DIR=/data

WORKDIR /usr/src/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ .

# Run as an unprivileged user; match the UID of the host user owning ./data
ARG UID=1000
RUN useradd --create-home --uid ${UID} app
USER app

CMD [ "python3", "app.py" ]
