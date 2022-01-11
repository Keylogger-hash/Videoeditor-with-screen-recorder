import os
import sys
import signal
import logging
sys.path.append(os.getcwd())
import settings
from encoding_service.worker import DatabaseProcessingWorker, EncodeServiceListener
logging.basicConfig(level=logging.DEBUG)
worker = DatabaseProcessingWorker(settings.DATABASE, settings.VIDEOCUT_SERVICE_WORKERS)
server = EncodeServiceListener(settings.ENCODE_SERVICE_ADDR, worker)
def stop_server(*args):
    print('Stopping server in about {} sec...'.format(server.POLLING_INTERVAL / 1e3))
    server.shutdown()
signal.signal(signal.SIGTERM, stop_server)
signal.signal(signal.SIGINT, stop_server)
server.serve()
