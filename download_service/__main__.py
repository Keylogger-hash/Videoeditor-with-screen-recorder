import logging
from worker import start_server
from settings import context, DOWNLOAD_SERVICE_ADDR
from worker import DatabaseChangingProcessing
import sys
import os

sys.path.append(os.getcwd())
worker = DatabaseChangingProcessing(context['DATABASE_URL'], 4)
logging.basicConfig(level=logging.DEBUG)
start_server(DOWNLOAD_SERVICE_ADDR, 10)
