FROM python:3.7-slim

WORKDIR /app

ENV MODE "api"

COPY requirements.txt ./
RUN pip install -r ./requirements.txt && \
    pip install gunicorn

COPY frontend ./frontend
COPY database ./database
COPY services ./services
COPY processing_service ./processing_service
COPY download_service ./download_service
COPY encoding_service ./encoding_service
COPY email_service ./email_service
COPY settings.docker.py ./settings.py
COPY routes.py ./

ENTRYPOINT ["/usr/local/bin/gunicorn", "-b", "0.0.0.0:4440", "-w", "4", "--access-logfile", "-", "routes:app"]
