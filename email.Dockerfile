FROM python:3.7-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install -r ./requirements.txt && \
    apt update -y 

COPY email_service ./email_service
COPY processing_service ./processing_service
COPY database ./database
COPY shared ./shared
COPY settings.docker.py ./settings.py

ENV MODE "service"
