import os
import json
import zmq
import glob
import functools
from sqlalchemy import create_engine
from sqlalchemy.sql import select
from flask import Blueprint, current_app, request
from jsonschema import validate, ValidationError
from database.datamodel import videos
from processing_service.common import TaskStatus
from processing_service.paths import UPLOADS_LOCATION, CUTS_LOCATION

api = Blueprint('cutvideo_api', __name__)

TASK_ADD_REQUEST_SCHEMA = {
    'type': 'object',
    'required': [
        'source',
        'destination',
        'startAt',
        'endAt',
        'keepStreams'
    ],
    'properties': {
        'source': {
            'type': 'string'
        },
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
        }
    }
}

def get_link_to_cut_video(video_name):
    return '/files/cuts/' + video_name

class CutVideoService(object):

    def __init__(self, address):
        self.address = address

    def _send(self, data):
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
        except Exception as e:
            raise
        finally:
            sock.close()
            return json.loads(reply.decode('utf-8'))

    def start(self, source, destination, range_start, range_end, keep_streams):
        return self._send({
            'method': 'cut',
            'input': source,
            'output': destination,
            'startAt': range_start,
            'endAt': range_end,
            'keepStreams': keep_streams
        })

    def stop(self, destination):
        return self._send({
            'method': 'cancel',
            'output': destination
        })

    def list_tasks(self):
        return self._send({
            'method': 'list'
        })

    def get_progress(self, destination):
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
    if result['status'] in (TaskStatus.WAITING, TaskStatus.WORKING, TaskStatus.INACTIVE):
        videoservice = CutVideoService(current_app.config.get('VIDEOCUT_SERVICE_ADDR'))
        try:
            resp = videoservice.stop(output_name)
        except:
            print('Got exception when requested service')
    db.execute(videos.delete().where(videos.c.output_filename == output_name))
    # NOTE: remove in service instead?
    if os.path.isfile(output_name):
        os.remove(os.path.join(CUTS_LOCATION, output_name))
    return {'success': True}


@api.post('/cuts/')
@requires_db
def start_videocut(db):
    data = request.json
    # TODO: validation
    try:
        validate(data, TASK_ADD_REQUEST_SCHEMA)
    except ValidationError as e:
        return {
            'success': False,
            'error': 'Invalid request: {}'.format(e.message)
        }
    videoservice = CutVideoService(current_app.config.get('VIDEOCUT_SERVICE_ADDR'))
    result = db.execute(select([videos.c.status]).where(videos.c.output_filename == data['destination'])).fetchone()
    # NOTE: allowing retrying complete task with same output name is meaningless a bit - should be reconsidered
    if result is not None and result['status'] in (TaskStatus.FAILED, TaskStatus.COMPLETED, TaskStatus.INACTIVE):  # restarting completed/failed task
        db.execute(
            videos.update().where(videos.c.output_filename == data['destination']).values(status=TaskStatus.INACTIVE, progress=0)
        )
    elif result is None:  # creating new task
        db.execute(
            videos.insert().values(
                output_filename=data['destination'],
                source=data['source'],
                status=TaskStatus.INACTIVE,
                progress=0
            )
        )
    else:  # task is queued/in progress
        return {
            'success': False,
            'error': 'Task is active'
        }
    try:
        resp = videoservice.start(data['source'], data['destination'], data['startAt'], data['endAt'], data['keepStreams'])
    except:
        return { 'success': False, 'error': 'Failed to request service' }
    if resp['ok']:
        return { 'success': True }
    else:
        return { 'success': False, 'error': resp['error'] }

# DEBUG METHOD SHOULD BE REMOVED
@api.get('/_uploads/')
def list_uploads():
    uploaded_videos = [os.path.basename(name) for name in glob.glob('{}/*.[Mm][Pp]4'.format(UPLOADS_LOCATION),)]
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
