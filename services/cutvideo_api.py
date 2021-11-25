import os
import json
import zmq
import glob
import typing
import functools
from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.sql import select
from flask import Blueprint, current_app, request
from jsonschema import validate, ValidationError
from database.datamodel import videos, download_videos as source_videos
from processing_service.common import TaskStatus
from settings import DOWNLOADS_LOCATION, CUTS_LOCATION

api = Blueprint('cutvideo_api', __name__)

TASK_ADD_REQUEST_SCHEMA = {
    'type': 'object',
    'oneOf': [
        {
            'type': 'object',
            'required': ['source', 'startAt', 'endAt', 'keepStreams' ],
            'properties': {
                'source': {
                    'type': 'string'
                },
                'startAt': {
                    'type': 'number',
                    'minimum': 0
                },
                'endAt': {
                    'type': 'number',
                    'minimum': 0
                },
                'keepStreams': {
                    'type': 'string',
                    'enum': [
                        'both', 'video', 'audio'
                    ]
                },
                'description': {
                    'type': 'string'
                }
            }
        },
        {
            'type': 'object',
            'required': [ 'destination', 'startAt', 'endAt', 'keepStreams' ],
            'properties': {
                'destination': {
                    'type': 'string'
                },
                'startAt': {
                    'type': 'number',
                    'minimum': 0
                },
                'endAt': {
                    'type': 'number',
                    'minimum': 0
                },
                'keepStreams': {
                    'type': 'string',
                    'enum': [
                        'both', 'video', 'audio'
                    ]
                },
                'description': {
                    'type': 'string'
                }
            }
        }
    ]
}

def get_link_to_cut_video(video_name: str) -> str:
    return '/files/cuts/' + video_name

class CutVideoService(object):

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

    def start(self, source: str, destination: str, range_start: int, range_end: int, keep_streams: str) -> typing.Any:
        return self._send({
            'method': 'cut',
            'input': source,
            'output': destination,
            'startAt': range_start,
            'endAt': range_end,
            'keepStreams': keep_streams
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

def requires_db(callback):
    @functools.wraps(callback)
    def fn(*args, **kwargs):
        kwargs['db'] = create_engine(current_app.config.get('DATABASE'))
        return callback(*args, **kwargs)
    return fn

@api.get('/cuts/')
@requires_db
def get_cut_list(db):
    result = db.execute(select([videos]).order_by(videos.c.output_filename.asc())).fetchall()
    return {
        'success': True,
        'cuts': [
            {
                'filename': item['output_filename'],
                'description': item['description'],
                'link': get_link_to_cut_video(item['output_filename']),
                'source': item['source'],
                'taskStartedAt': item['task_begin'],
                'taskFinishedAt': item['task_end'],
                'status': TaskStatus(item['status']).name,
                'progress': item['progress']
            } for item in result
        ]
    }


@api.get('/cuts/<output_name>')
@requires_db
def get_cut_info(output_name, db):
    result = db.execute(select([videos]).where(videos.c.output_filename == output_name)).fetchone()
    if result is None:
        return {
            'success': False,
            'error': 'Not found'
        }
    return {
        'success': True,
        'result': {
            'filename': result['output_filename'],
            'description': result['description'],
            'link': get_link_to_cut_video(result['output_filename']),
            'source': result['source'],
            'taskStartedAt': result['task_begin'],
            'taskFinishedAt': result['task_end'],
            'status': TaskStatus(result['status']).name,
            'progress': result['progress']
        }
    }

@api.delete('/cuts/<output_name>')
@requires_db
def delete_cut(output_name, db):
    result = db.execute(select([videos]).where(videos.c.output_filename == output_name)).fetchone()
    if result is None:
        return {
            'success': False,
            'error': 'Not found'
        }
    if result['status'] in (TaskStatus.QUEUED, TaskStatus.WORKING, TaskStatus.INACTIVE):
        videoservice = CutVideoService(current_app.config.get('VIDEOCUT_SERVICE_ADDR'))
        try:
            resp = videoservice.stop(output_name)
        except:
            print('Got exception when requested service')
    db.execute(videos.delete().where(videos.c.output_filename == output_name))
    # NOTE: remove in service instead?
    if os.path.isfile(os.path.join(CUTS_LOCATION, output_name)):
        os.remove(os.path.join(CUTS_LOCATION, output_name))
    return {'success': True}


@api.post('/cuts/')
@requires_db
def start_videocut(db):
    data = request.json
    source_name = None
    output_name = None
    try:
        validate(data, TASK_ADD_REQUEST_SCHEMA)
    except ValidationError as e:
        return {
            'success': False,
            'error': 'Invalid request: {}'.format(e.message)
        }
    videoservice = CutVideoService(current_app.config.get('VIDEOCUT_SERVICE_ADDR'))

    if 'source' in data:
        source_name = data['source']
        file_ext = '.mp4' if data['keepStreams'] in ('both', 'video') else '.mp3'
        output_name = '{}{}'.format(uuid4(), file_ext)
        source_video = db.execute(select([source_videos.c.filename]).where(source_videos.c.video_id == data['source'])).fetchone()
        if source_video is None:
            return {'success': False, 'error': 'Missing source video'}
        db.execute(
            videos.insert().values(
                output_filename=output_name,
                source=data['source'],
                status=TaskStatus.INACTIVE.value,
                progress=0,
                description=data['description']
            )
        )
    else:
        video_cut = db.execute(select([videos.c.status, videos.c.source]).where(videos.c.output_filename == data['destination'])).fetchone()
        # NOTE: allowing retrying complete task with same output name is meaningless a bit - should be reconsidered
        if video_cut is not None and video_cut['status'] in (TaskStatus.FAILED, TaskStatus.COMPLETED, TaskStatus.INACTIVE):  # restarting completed/failed task
            db.execute(
                videos.update().where(videos.c.output_filename == data['destination']).values(status=TaskStatus.INACTIVE.value, progress=0)
            )
            source_name = video_cut['source']
            output_name = data['destination']
            source_video = db.execute(select([source_videos.c.filename]).where(source_videos.c.video_id == video_cut['source'])).fetchone()
            if source_video is None:
                return {'success': False, 'error': 'Missing source video'}
        else:  # task is queued/in progress
            return {
                'success': False,
                'error': 'Task is active'
            }
    try:
        resp = videoservice.start(source_video['filename'], output_name, data['startAt'], data['endAt'], data['keepStreams'])
    except:
        return { 'success': False, 'error': 'Failed to request service' }
    if resp['ok']:
        return { 'success': True, 'result': { 'source': source_name, 'output': output_name } }
    else:
        return { 'success': False, 'error': resp['error'] }

# DEBUG METHOD SHOULD BE REMOVED
@api.get('/_uploads/')
def list_uploads():
    uploaded_videos = [os.path.basename(name) for name in glob.glob('{}/*.[Mm][Pp]4'.format(DOWNLOADS_LOCATION),)]
    return {
        'success': True,
        'uploads': sorted(uploaded_videos)
    }


@api.after_request
def add_cors_headers(response):
    headers = response.headers
    headers['Access-Control-Allow-Origin'] = '*'
    headers['Access-Control-Allow-Methods'] = 'GET,POST,DELETE'
    headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

