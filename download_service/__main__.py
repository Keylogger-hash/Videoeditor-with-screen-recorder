import sys
import os
sys.path.append(os.getcwd())
import logging
from settings import DOWNLOAD_SERVICE_ADDR, DATABASE
from download_service.worker import start_server
from download_service.worker import DatabaseChangingProcessing

worker = DatabaseChangingProcessing(DATABASE, 4)
logging.basicConfig(level=logging.DEBUG)
start_server(DOWNLOAD_SERVICE_ADDR, 10)
