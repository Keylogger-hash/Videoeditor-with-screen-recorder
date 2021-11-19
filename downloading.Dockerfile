FROM python:3.7-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install -r ./requirements.txt && \
    apt-get update -y && \
    apt-get install -y --no-install-recommends wget xz-utils && \
    cd /tmp && \
    wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz && \
    tar xvf ffmpeg-release-amd64-static.tar.xz && \
    mv ffmpeg-*-static/ffmpeg ffmpeg-*-static/ffprobe ffmpeg-*-static/qt-faststart /usr/bin/


COPY download_service ./download_service
COPY processing_service ./processing_service
COPY database ./database
COPY shared ./shared
COPY settings.docker.py ./settings.py

ENV MODE "service"

ENTRYPOINT ["python3", "-m", "download_service"]