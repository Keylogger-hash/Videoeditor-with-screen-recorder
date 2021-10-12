import logging
from worker import start_server

logging.basicConfig(level=logging.DEBUG)
start_server('tcp://127.0.0.1:16535', 10)