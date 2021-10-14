import zmq
import json
import logging
import signal
from threading import Event

class ZMQServer(object):
    POLLING_INTERVAL = 10000

    def __init__(self, address):
        self.address = address
        self.exit_event = Event()

    def prepare(self):
        """Method executed before starting server
        """
        pass

    def finalize(self):
        """Method executed after server stop
        """
        pass

    def handle(self, data):
        """Method handling incoming requests
        """
        pass

    def serve(self):
        self.prepare()
        ctx = zmq.Context()
        server_socket = ctx.socket(zmq.REP)
        server_socket.bind(self.address)
        poller = zmq.Poller()
        poller.register(server_socket, zmq.POLLIN)
        logging.info('Starting server at %s...', self.address)
        while not self.exit_event.is_set():
            socks = poller.poll(self.POLLING_INTERVAL)
            if socks:
                for sock, _ in socks:
                    try:
                        request = json.loads(sock.recv().decode('utf-8'))
                        reply = self.handle(request)
                        sock.send(json.dumps(reply).encode('utf-8'))
                    except Exception as e:
                        sock.send(json.dumps({'ok': False, 'error': str(e)}).encode('utf-8'))
        self.finalize()

    def shutdown(self):
        self.exit_event.set()