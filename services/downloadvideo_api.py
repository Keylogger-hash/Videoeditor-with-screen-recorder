import os
import json
import zmq
import glob
from sqlalchemy import create_engine
from sqlalchemy.sql import select
from flask import Blueprint, current_app, request
from database.datamodel import videos
from download_service.common import TaskStatus
from download_service.paths import DOWNLOADS_LOCATION


api = Blueprint('downloadvideo_api', __name__)


class DownloadVideoApi(object):

    def __init__(self, address):
        self.address = address

    def _send(self, data):
        try:
            context = zmq.Context()
            socket = context.socket()
            socket.connect(f'tcp://127.0.0.1:{self.address}')
            socket.send(b"{'method':'ping'}")
            socket.recv()
            socket.send(json.dumps(data).encode('UTF-8'))
            message = socket.recv()
        except Exception as e:
            raise
        finally:
            socket.close()
            return json.loads(message).decode('UTF-8')


    def start(self):
        data = request.json
        self._send(data)

    def stop(self,):
        data = request.json
        self._send(data)

    def list_tasks(self):
        pass

    def get_proggress(self):
        pass


@api.get('downloads/')
def list_tasks_of_downloading():
    pass


@api.get('downloads/<id>/progress')
def get_downloading_video_info():
    pass


@api.get('downloads/<id>/cancel')
def stop_downloading_video():
    pass


@api.post('downloads/')
def start_downloading():
    pass
