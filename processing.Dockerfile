FROM python:3.7-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install -r ./requirements.txt && \
    apt update -y && \
    apt install -y --no-install-recommends ffmpeg

COPY processing_service ./processing_service
COPY database ./database
COPY shared ./shared
COPY settings.docker.py ./settings.py

ENV MODE "service"

ENTRYPOINT ["python3", "-m", "processing_service"]
