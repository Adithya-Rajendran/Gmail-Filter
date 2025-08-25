FROM python:3.11.1

WORKDIR /usr/src/app

COPY requirements.txt .
RUN pip install --upgrade -r requirements.txt

CMD [ "python3", "./app.py" ]