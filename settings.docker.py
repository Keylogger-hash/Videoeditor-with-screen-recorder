import os

DATABASE = os.environ['DATABASE']
if os.environ['MODE'] == 'api':
    VIDEOCUT_SERVICE_ADDR = "tcp://processing_svc:4000"
    DOWNLOAD_SERVICE_ADDR = "tcp://downloader_svc:4000"
else:
    VIDEOCUT_SERVICE_ADDR = "tcp://0.0.0.0:4000"
    DOWNLOAD_SERVICE_ADDR = "tcp://0.0.0.0:4000"
VIDEOCUT_SERVICE_WORKERS = 4
DOWNLOADS_LOCATION = '/data/sources'
CUTS_LOCATION = '/data/outputs'
YOUTUBE_DL_EXECUTABLE = '/usr/local/bin/youtube-dl'
