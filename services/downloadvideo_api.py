import json
import zmq
import uuid
import youtube_dl
from base64 import b32encode
from sqlalchemy import create_engine
from sqlalchemy.sql import select
from flask import Blueprint, current_app, request
from database.datamodel import videos, download_videos
from download_service.common import TaskStatus


api = Blueprint('downloadvideo_api', __name__)


class DownloadVideoApi(object):

    def __init__(self, address):
        self.address = address

    def _send(self, data):
        try:
            context = zmq.Context()
            socket = context.socket(zmq.REQ)
            socket.connect(self.address)
            # socket.send(b'{"method":"ping"}')
            # socket.recv()
            socket.send(json.dumps(data).encode('UTF-8'))
            message = socket.recv()
        except Exception as e:
            raise
        socket.close()
        return json.loads(message.decode('UTF-8'))

    def start(self, link, destination):
        return self._send({
            "method": "download",
            "link": link,
            "destination": destination
        })

    def stop(self, link):
        return self._send({
            "method": "cancel",
            "link": link
        })

    def list_tasks(self):
        return self._send({
            "method": "list"
        })


@api.get('downloads/')
def list_tasks_of_downloading():
    dbe = create_engine(current_app.config.get('DATABASE'))
    result = dbe.execute(select([download_videos])).fetchall()
    return {
        "success": True,
        "downloads": [
            {
                "link": item["link"],
                "quality": item["quality"],
                "status": item["status"],
                "progress": item["progress"]
            }
            for item in result
        ]
    }


@api.get("downloads/<id>/info")
def get_downloading_info():
    data = request.json
    dbe = create_engine(current_app.config.get('DATABASE'))
    result = dbe.execute(select([download_videos]).where(download_videos.c.link == data["link"]))
    if result is None:
        return {
            "success": False,
            "error": "Record doesn't exist"
        }
    else:
        return {
            "success": True,
            "link": data["link"],
            "title": result["title"],
            "quality": result["quality"]
        }


@api.delete('downloads/<id>/cancel')
def stop_downloading_video(id):
    dbe = create_engine(current_app.config.get('DATABASE'))
    result = dbe.execute(select([download_videos]).where(download_videos.c.video_id == id)).fetchone()
    if result is None:
        return {'success': False, 'error': "Record doesn't exist"}

    if result['status'] in (TaskStatus.WAITING, TaskStatus.WORKING, TaskStatus.INACTIVE):
        download_service = DownloadVideoApi(current_app.config.get('DOWNLOAD_SERVICE_ADDR'))
        resp = download_service.stop(result['link'])
        print(resp)

    return {'success': True}


@api.post('downloads/')
def start_downloading():
    data = request.json
    dbe = create_engine(current_app.config.get('DATABASE'))
    result = dbe.execute(select([download_videos.c.status]).where(download_videos.c.link == data['link'])).fetchone()
    if result is not None and result == TaskStatus.COMPLETED:
        return {
            "success": False,
            "error": "Video already downloading"
        }

    elif result is not None and result == TaskStatus.WORKING:
        return {
            "success": False,
            "error": "Task is active"
        }

    elif result is None:
        info_dict = youtube_dl.YoutubeDL().extract_info(url=data["link"], download=False)
        video_id = uuid.uuid4()
        # TODO: check extension somehow
        output_filename = b32encode(video_id.bytes).strip(b'=').lower().decode('ascii') + '.mp4'
        dbe.execute(
            download_videos.insert().values(
                video_id=video_id,
                filename=output_filename,
                link=data["link"],
                quality=data['quality'],
                title=info_dict['title'],
                status=TaskStatus.INACTIVE.value
            )
        )

    else:
        output_filename = result['filename']

    download_service = DownloadVideoApi(current_app.config.get('DOWNLOAD_SERVICE_ADDR'))
    resp = download_service.start(data["link"], output_filename)
    if resp["ok"]:
        return {"success": resp['ok']}
    else:
        return {"success": resp["ok"], "error": resp["error"]}


