import sys
import os
sys.path.append(os.getcwd())
import logging

from settings import DOWNLOAD_SERVICE_ADDR, DATABASE
from download_service.worker import ProcessingTasks, start_server

worker = ProcessingTasks(database_url=DATABASE, tasks_limit=5)

logging.basicConfig(level=logging.DEBUG)
start_server(DOWNLOAD_SERVICE_ADDR, worker)
