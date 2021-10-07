import logging
from .worker import start_server, DatabaseProcessingWorker
logging.basicConfig(level=logging.DEBUG)
worker = DatabaseProcessingWorker('sqlite:///main.db', 4)
start_server('tcp://127.0.0.1:15320', worker)