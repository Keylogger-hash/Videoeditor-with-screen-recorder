from ast import Interactive
import zmq
import os
import json
import zmq
import typing
from sqlalchemy import create_engine
from sqlalchemy.sql import select
from flask import Blueprint, current_app, request
from database.datamodel import records
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

@api.get("/record/<output_name>/")
def get_record_progress(output_name):
    db = create_engine(current_app.config.get('DATABASE'))
    result = db.execute(select([records]).where(records.c.output_filename==output_name)).fetchone()
    if result is None:
        return {
            "success":False,
            "error": "Result is none"
        }
    return {
        "success":True,
        "output_name":result['output_name'],
        "title": result["title"],
        "type": result["type"],
        "taskStartedAt":result["task_begin"],
        "taskFinishedAt": result["task_end"],
        "progress": result['progress']
    }

@api.get("/records/")
def get_all_records():
    db = create_engine(current_app.config.get('DATABASE'))
    result = db.execute(select[records]).fetchall()
    return {
        "success": True,
        "data":[{
            "output_name":item['output_name'],
            "title": item["title"],
            "type": item["type"],
            "taskStartedAt":item["task_begin"],
            "taskFinishedAt": item["task_end"],
            "progress": item['progress']
        } for item in result]
    }

@api.delete("/record/<output_name>/")
def delete_record(output_name):
    db = create_engine(current_app.config.get('DATABASE'))
    result = db.execute(select([records]).where(records.c.output_filename == output_name)).fetchone()
    if result is None:
        return {
            'success': False,
            'error': 'Not found'
        }
    if result['status'] in (TaskStatus.QUEUED, TaskStatus.WORKING, TaskStatus.INACTIVE):
        videoservice = EncodeVideoService(current_app.config.get('ENCODE_SERVICE_ADDR'))
        try:
            resp = videoservice.stop(output_name)
        except:
            print('Got exception when requested service')
    db.execute(records.delete().where(records.c.output_filename == output_name))
    # NOTE: remove in service instead?
    if os.path.isfile(os.path.join(DOWNLOADS_LOCATION, output_name)):
        os.remove(os.path.join(DOWNLOADS_LOCATION, output_name))
    return {'success': True}

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
        dirname = b32encode(video_id.bytes).strip(b'=').lower().decode('ascii')
        title, file_ext = os.path.splitext(uploaded_file.filename)
        if type_file=='audio':
            output_filename = os.path.join(dirname, dirname + '.mp3')
            source_filename = os.path.join(dirname,'audio.webm')
        if type_file=='video':
            output_filename = os.path.join(dirname, dirname+'.mp4')
            source_filename = os.path.join(dirname,'video.webm')
            


        os.makedirs(os.path.join(DOWNLOADS_LOCATION, os.path.dirname(source_filename)), exist_ok=True)
        db.execute(records.insert().values(
            output_filename=output_filename,
            title=title,
            type=type_file,
            source=source_filename,
            task_begin=now,
            status=TaskStatus.INACTIVE.value,
        ))
        uploaded_file.save(os.path.join(DOWNLOADS_LOCATION, source_filename))
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
