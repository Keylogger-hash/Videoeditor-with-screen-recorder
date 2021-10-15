import sys
import os

sys.path.append(os.getcwd())
import logging
from settings import context, DOWNLOAD_SERVICE_ADDR
from worker import ProcessingTasks, start_server

worker = ProcessingTasks(database_url=context['DATABASE_URL'], tasks_limit=5)
logging.basicConfig(level=logging.DEBUG)
start_server(DOWNLOAD_SERVICE_ADDR, worker)
