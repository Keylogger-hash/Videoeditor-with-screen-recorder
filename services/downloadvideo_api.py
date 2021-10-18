import os
import json
import zmq
import shutil
from sqlalchemy import create_engine
from sqlalchemy.sql import select
from flask import Blueprint, current_app, request
from database.datamodel import videos, download_videos
import uuid
import youtube_dl
from base64 import b32encode
from settings import DOWNLOADS_LOCATION
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

    def start(self, link: str, format_id: int, destination: str):
        return self._send({
            "method": "download",
            "destination": destination,
            "format_id": format_id,
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
def list_of_records():
    dbe = create_engine(current_app.config.get('database'))
    result = dbe.execute(select([download_videos])).fetchall()
    return {
        "success": True,
        "downloads": [
            {
                "video_id": item["video_id"],
                "link": item["link"],
                "quality": item["quality"],
                "filename": item["filename"],
                "status": item["status"]
            }
            for item in result
        ]
    }


@api.get("downloads/<id>/info")
def get_info_download_video(id):
    data = request.json
    dbe = create_engine(current_app.config.get('database'))
    result = dbe.execute(select([download_videos]).where(download_videos.c.video_id == id)).fetchone()
    print(result)
    if result is None:
        return {
            "success": False,
            "error": "Record doesn't exist"
        }
    else:
        return {
            "success": True,
            "record": {
                "video_id": result["video_id"],
                "output_filename": result["filename"],
                "link": result["link"],
                "title": result["title"],
                "status": result["status"],
                "quality": result["quality"]
            }
        }


@api.post("downloads/info")
def get_info_about_youtube_video():
    data = request.json
    if data["link"] is None:
        return {
            "success": False,
            "error": "Link is invalid"
        }
    link = data["link"]
    with youtube_dl.YoutubeDL() as ydl:
        info_dict = ydl.extract_info(link, download=False)
        formats = info_dict['formats']
    return {
        "success": True,
        "error": None,
        "title": info_dict["title"],
        "thumbnails": [{
            "height": thumbnail["height"],
            "url": thumbnail["url"],
            "width": thumbnail["width"],
            "resolution": thumbnail["resolution"]
        } for thumbnail in info_dict["thumbnails"]
        ],
        "info": [{
            "format_id": item["format_id"],
            "ext": item["ext"],
            "quality": item["format"].split('- ')[1],
            "fps": item["fps"]
        } for item in formats]
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
    dbe.execute(download_videos.delete().where(download_videos.c.video_id == id))
    path = os.path.join(DOWNLOADS_LOCATION, result['filename'])
    # path_to_mp4_file = os.listdir(path)
    # final_path = os.path.join(path, path_to_mp4_file[0])
    if os.path.isdir(path):
        shutil.rmtree(path)

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
        title = data['title']
        format_video = data['format']
        format_ext = data['ext']
        format_id = data['format_id']
        quality = f"{format_ext} - {format_id} - {format_video}"
        video_id = uuid.uuid4()
        output_filename = b32encode(video_id.bytes).strip(b'=').lower().decode('ascii')
        path = os.path.join(DOWNLOADS_LOCATION, output_filename)
        os.mkdir(path)
        dbe.execute(
            download_videos.insert().values(
                video_id=video_id,
                link=data["link"],
                quality=quality,
                title=title,
                status=TaskStatus.INACTIVE,
                filename=output_filename
            )
        )
    else:
        output_filename = result['filename']

    download_service = DownloadVideoApi(current_app.config.get('download_service_addr'))
    resp = download_service.start(link=data["link"],
                                  format_id=format_id,
                                  destination=os.path.join(path, output_filename+f'.{format_ext}'))
    print(resp)
    if resp["ok"]:
        return {"success": resp['ok'], "video_id": video_id}
    else:
        return {"success": resp["ok"], "error": resp["error"]}


