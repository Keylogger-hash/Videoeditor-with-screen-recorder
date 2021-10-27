FROM tiangolo/uwsgi-nginx-flask:python3.8

WORKDIR /app

ENV MODE "api"
ENV STATIC_PATH /app/frontend/static

COPY requirements.txt ./
RUN pip install -r ./requirements.txt

COPY frontend ./frontend
COPY database ./database
COPY services ./services
COPY processing_service ./processing_service
COPY download_service ./download_service
COPY settings.docker.py ./settings.py
COPY routes.py ./extra/uwsgi.ini ./