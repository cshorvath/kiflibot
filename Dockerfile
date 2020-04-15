FROM python:3.8-slim

WORKDIR /opt/kiflibot

COPY ./requirements.txt .
COPY ./src .

RUN pip install -r requirements.txt

ENTRYPOINT  ["python3", "kifli.py"]