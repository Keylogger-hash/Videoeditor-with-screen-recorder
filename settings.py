import sys
import os

sys.path.append(os.path.abspath(os.path.join('..', 'settings')))

DATABASE = "sqlite:///main.db"
VIDEOCUT_SERVICE_ADDR = "tcp://127.0.0.1:15320"
DOWNLOAD_SERVICE_ADDR = "tcp://127.0.0.1:6536"
VIDEOCUT_SERVICE_WORKERS = 4
DOWNLOADS_LOCATION = 'downloads'

context = {"DATABASE_URL": 'postgresql://postgres:123@192.168.100.147/sven_videoeditor'}
