import os
import json
import zmq
import glob
from sqlalchemy import create_engine
from sqlalchemy.sql import select
from flask import Blueprint, current_app, request
from database.datamodel import videos, download_videos
import uuid
import youtube_dl
from download_service.common import TaskStatus
# from download_service.paths import DOWNLOADS_LOCATION


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

    def start(self, link):
        return self._send({
            "method": "download",
            "link": link
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
    dbe = create_engine(current_app.config.get('database'))
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
    dbe = create_engine(current_app.config.get('database'))
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
    dbe = create_engine(current_app.config.get('database'))
    result = dbe.execute(select([download_videos]).where(download_videos.c.video_id == id)).fetchone()
    if result is None:
        return {'success': False, 'error': "Record doesn't exist"}

    if result['status'] in (TaskStatus.WAITING, TaskStatus.WORKING, TaskStatus.INACTIVE):
        download_service = DownloadVideoApi(current_app.config.get('download_service_addr'))
        resp = download_service.stop(result['link'])
        print(resp)

    return {'success': True}


@api.post('downloads/')
def start_downloading():
    data = request.json
    dbe = create_engine(current_app.config.get('database'))
    result = dbe.execute(select([download_videos.c.status]).where(download_videos.c.link == data['link'])).fetchone()
    print(result)
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
        uuid4 = uuid.uuid4()
        dbe.execute(
            download_videos.insert().values(
                video_id=uuid4,
                link=data["link"],
                quality=data['quality'],
                title=info_dict['title'],
                status=TaskStatus.INACTIVE
            )
        )

    download_service = DownloadVideoApi(current_app.config.get('download_service_addr'))
    resp = download_service.start(data["link"])
    print(resp)
    if resp["ok"]:
        return {"success": resp['ok']}
    else:
        return {"success": resp["ok"], "error": resp["error"]}


