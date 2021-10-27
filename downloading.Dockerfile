FROM python:3.7-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install -r ./requirements.txt

COPY download_service ./download_service
COPY processing_service ./processing_service
COPY database ./database
COPY shared ./shared
COPY settings.docker.py ./settings.py

ENV MODE "service"

ENTRYPOINT ["python3", "-m", "download_service"]