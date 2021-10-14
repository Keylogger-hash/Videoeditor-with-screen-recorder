import os
import sys
import logging
sys.path.append(os.getcwd())
import settings
from processing_service.worker import start_server, DatabaseProcessingWorker
logging.basicConfig(level=logging.DEBUG)
worker = DatabaseProcessingWorker(settings.DATABASE, settings.VIDEOCUT_SERVICE_WORKERS)
start_server(settings.VIDEOCUT_SERVICE_ADDR, worker)
