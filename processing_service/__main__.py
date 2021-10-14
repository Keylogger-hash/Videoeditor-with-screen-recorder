import logging
from worker import start_server, DatabaseProcessingWorker
import os
import sys

sys.path.append(os.getcwd())
logging.basicConfig(level=logging.DEBUG)
worker = DatabaseProcessingWorker('sqlite:///main.db', 4)
start_server('tcp://127.0.0.1:15320', worker)
