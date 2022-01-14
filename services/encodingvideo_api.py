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

@api.get("/record/<video_id>/")
def get_record_progress(video_id):
    db = create_engine(current_app.config.get('DATABASE'))
    result = db.execute(select([records]).where(records.c.video_id==video_id)).fetchone()
    if result is None:
        return {
            "success":False,
            "error": "Result is none"
        }
    return {
        "success":True,
        "resultId":video_id,
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
            "resultId":item["video_id"],
            "output_name":item['output_name'],
            "title": item["title"],
            "type": item["type"],
            "taskStartedAt":item["task_begin"],
            "taskFinishedAt": item["task_end"],
            "progress": item['progress']
        } for item in result]
    }

@api.delete("/record/<video_id>/")
def delete_record(video_id):
    db = create_engine(current_app.config.get('DATABASE'))
    result = db.execute(select([records]).where(records.c.video_id == video_id)).fetchone()
    if result is None:
        return {
            'success': False,
            'error': 'Not found'
        }
    if result['status'] in (TaskStatus.QUEUED, TaskStatus.WORKING, TaskStatus.INACTIVE):
        videoservice = EncodeVideoService(current_app.config.get('ENCODE_SERVICE_ADDR'))
        output_name = result["output_name"]
        try:
            resp = videoservice.stop(output_name)
        except:
            print('Got exception when requested service')
    db.execute(records.delete().where(records.c.video_id == video_id))
    # NOTE: remove in service instead?
    if os.path.isfile(os.path.join(DOWNLOADS_LOCATION, result["output_name"])):
        os.remove(os.path.join(DOWNLOADS_LOCATION, result["output_name"]))
    if os.path.isfile(os.path.join(DOWNLOADS_LOCATION, result["source_name"])):
        os.remove(os.path.join(DOWNLOADS_LOCATION, result["source_name"]))
    return {'success': True}

@api.post("/record/")
def upload_record():
    type_file = ""
    output_name = ""
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
        file_id = uuid.uuid4()
        now = datetime.datetime.now()
        dirname = b32encode(file_id.bytes).strip(b'=').lower().decode('ascii')
        title, file_ext = os.path.splitext(uploaded_file.filename)
        if type_file=='audio':
            output_name = os.path.join(dirname, dirname + '.mp3')
            source_name = os.path.join(dirname,'audio.webm')
        if type_file=='video':
            output_name = os.path.join(dirname, dirname+'.mp4')
            source_name = os.path.join(dirname,'video.webm')
            
        os.makedirs(os.path.join(DOWNLOADS_LOCATION, os.path.dirname(source_name)), exist_ok=True)
        db.execute(records.insert().values(
            video_id=video_id,
            output_name=output_name,
            title=title,
            type=type_file,
            source_name=source_name,
            task_begin=now,
            status=TaskStatus.INACTIVE.value,
        ))
        uploaded_file.save(os.path.join(DOWNLOADS_LOCATION, source_name))
        try:
            resp = videoservice.start(source_name, output_name,type_file)
        except:
            return { 'success': False, 'error': 'Failed to request service' }
        if resp['ok']:
            return { 'success': True, 'result': { "resultId":video_id,'source': source_name, 'output': output_name } }
        else:
            return { 'success': False, 'error': resp['error'] }

        
        

      
    
    

@api.after_request
def add_cors_headers(response):
    headers = response.headers
    headers['Access-Control-Allow-Origin'] = '*'
    headers['Access-Control-Allow-Methods'] = 'GET,POST,DELETE'
    headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response
