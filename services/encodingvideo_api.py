import zmq
import os
import json
import zmq
import typing
from sqlalchemy import create_engine
from sqlalchemy.sql import select
from flask import Blueprint, current_app, request
from database.datamodel import videos, download_videos
import uuid
import datetime
from base64 import b32encode
from settings import DOWNLOADS_LOCATION
from encoding_service.common import TaskStatus


api = Blueprint('encodingvideo_api',__name__)

class EncodeVideoService(object):

    def __init__(self, address: str):
        self.address = address # type: str

    def _send(self, data: typing.Any) -> typing.Any:
        try:
            context = zmq.Context()
            sock = context.socket(zmq.REQ)
            # check if service is available by sending ping
            # and waiting for 10s
            sock.RCVTIMEO = 10000
            sock.connect(self.address)
            sock.send(b'{"method":"ping"}')
            sock.recv()
            sock.send(json.dumps(data).encode('utf-8'))
            reply = sock.recv()
        except Exception:
            raise
        finally:
            sock.close()
            return json.loads(reply.decode('utf-8'))

    def start(self, source: str, destination: str, type: str) -> typing.Any:
        return self._send({
            'method': 'encode',
            'input': source,
            'output': destination,
            'type': type
        })

    def stop(self, destination: str) -> typing.Any:
        return self._send({
            'method': 'cancel',
            'output': destination
        })

    def list_tasks(self) -> typing.Any:
        return self._send({
            'method': 'list'
        })

    def get_progress(self, destination: str) -> typing.Any:
        return self._send({
            'method': 'progress',
            'output': destination
        })

@api.post("/record/")
def upload_record():
    type_file = ""
    output_filename = ""
    if not ('audio' or 'video' in request.FILES):
        return {
            'success':False,
            'error': 'No file uploaded'
        }
    if 'audio' in request.files:
        type_file='audio'
        uploaded_file = request.files['audio']
    if 'video' in request.files:
        type_file='video'
        uploaded_file = request.files['video']
    videoservice = EncodeVideoService(current_app.config.get('ENCODE_SERVICE_ADDR'))

    if uploaded_file:
        db = create_engine(current_app.config.get('DATABASE'))
        video_id = uuid.uuid4()
        now = datetime.datetime.now()
        source_filename, file_ext = os.path.splitext(uploaded_file.filename)
        if type_file=='audio':
            output_filename = os.path.join(b32encode(video_id.bytes).strip(b'=').lower().decode('ascii'), 'video' + '.mp3')
            source_filename = source_filename+'.mp3'
        if type_file=='video':
            output_filename = os.path.join(b32encode(video_id.bytes).strip(b'=').lower().decode('ascii'), 'video' + '.mp4')
            source_filename = source_filename+'.mp4'
            


        os.makedirs(os.path.join(DOWNLOADS_LOCATION, os.path.dirname(output_filename)), exist_ok=True)
        db.execute(download_videos.insert().values(
            video_id=video_id,
            filename=output_filename,
            link='',
            title=source_filename,
            quality=None,
            task_begin=now,
            task_end=now,
            status=TaskStatus.WORKING.value
        ))
        uploaded_file.save(os.path.join(DOWNLOADS_LOCATION, output_filename))
        try:
            resp = videoservice.start(source_filename, output_filename,type_file)
        except:
            return { 'success': False, 'error': 'Failed to request service' }
        if resp['ok']:
            return { 'success': True, 'result': { 'source': source_filename, 'output': output_filename } }
        else:
            return { 'success': False, 'error': resp['error'] }

      
    
    

@api.after_request
def add_cors_headers(response):
    headers = response.headers
    headers['Access-Control-Allow-Origin'] = '*'
    headers['Access-Control-Allow-Methods'] = 'GET,POST,DELETE'
    headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

