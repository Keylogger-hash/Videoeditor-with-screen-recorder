import logging
from worker import start_server
import sys
import os

sys.path.append(os.getcwd())

logging.basicConfig(level=logging.DEBUG)
start_server('tcp://127.0.0.1:16535', 10)