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
import requests
from settings import DOWNLOADS_LOCATION
from download_service.common import TaskStatus


api = Blueprint('downloadvideo_api', __name__)
quality_video = ["mp4", "webm", "mov"]


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
    dbe = create_engine(current_app.config.get('DATABASE'))
    result = dbe.execute(select([download_videos])).fetchall()
    return {
        "success": True,
        "downloads": [
            {
                "id": item['video_id'],
                "title": item['title'],
                "filename": item['filename'],
                "link": item["link"],
                "quality": item["quality"],
                "status": TaskStatus(item["status"]).name
            }
            for item in result
        ]
    }


@api.get("downloads/<video_id>/info")
def get_downloading_info(video_id):
    dbe = create_engine(current_app.config.get('DATABASE'))
    result = dbe.execute(select([download_videos]).where(download_videos.c.video_id == video_id)).fetchone()
    if result is None:
        return {
            "success": False,
            "error": "Record doesn't exist"
        }
    else:
        path = os.path.join(DOWNLOADS_LOCATION, result['filename'].split('/')[0])
        if not os.path.exists(path):
            progress = 0.0
        else:
            video_filename = os.listdir(path)
            full_path = os.path.join(path, video_filename[0])
            progress = round(os.stat(full_path).st_size / result['filesize'] * 100, 2)
        return {
            "success": True,
            "result": {
                "id": result["video_id"],
                "title": result["title"],
                "filename": result["filename"],
                "link": result["link"],
                "quality": result["quality"],
                "filesize": result["filesize"],
                "status": TaskStatus(result['status']).name,
                "progress": progress
            }
        }


@api.post("downloads/info")
def get_info_about_youtube_video():
    data = request.json
    link = data.get("link", None)
    if data is None or data == {}:
        return {
            "success": False,
            "error": "Empty body"
        }
    if link is None:
        return {
            "success": False,
            "error": "Link is invalid"
        }

    with youtube_dl.YoutubeDL() as ydl:
        info_dict = ydl.extract_info(link, download=False)
        formats = info_dict['formats']
        info = []
        for item in formats:
            info.append({
                "format_id": item["format_id"],
                "ext": item["ext"],
                "quality": item["format"].split('- ')[1],
                "fps": item["fps"]
            })
        best_video = [item for item in info_dict['formats'] if item['asr'] is not None and item.get('quality', 0) != 0]
        best_video = best_video[0]
        print(best_video)
        best_quality = best_video['format'].split('- ')[1]
        best_ext = best_video['ext']
        best_format_id = best_video['format_id']

    return {
        "success": True,
        "error": None,
        "title": info_dict["title"],
        "best_format": best_quality,
        "best_ext": best_ext,
        "best_format_id": best_format_id,
        "thumbnails": [{
            "height": thumbnail["height"],
            "url": thumbnail["url"],
            "width": thumbnail["width"],
            "resolution": thumbnail["resolution"]
        } for thumbnail in info_dict["thumbnails"]
        ],
        "info": info
    }


@api.delete('downloads/<video_id>/cancel')
def stop_downloading_video(video_id):

    dbe = create_engine(current_app.config.get('DATABASE'))
    result = dbe.execute(select([download_videos]).where(download_videos.c.video_id == video_id)).fetchone()
    if result is None:
        return {'success': False, 'error': "Record doesn't exist"}

    if result['status'] in (TaskStatus.WAITING, TaskStatus.WORKING, TaskStatus.INACTIVE):
        download_service = DownloadVideoApi(current_app.config.get('DOWNLOAD_SERVICE_ADDR'))
        resp = download_service.stop(result['link'])
        print(resp)
    dbe.execute(download_videos.delete().where(download_videos.c.video_id == video_id))
    path = os.path.join(DOWNLOADS_LOCATION, os.path.dirname(result['filename']))

    if os.path.isdir(path):
        shutil.rmtree(path)

    return {'success': True}


@api.post('downloads/')
def start_downloading():
    data = request.json
    link = data.get("link", None)
    format_id = data.get("format_id", None)
    if data is None or data == {}:
        return {
            "success": False,
            "error": "Empty body"
        }

    if link is None:
        return {
            "success": False,
            "error": "Invalid link"
        }

    if format_id is None:
        return {
            "success": False,
            "error": "Format id video is invalid"
        }

    dbe = create_engine(current_app.config.get('DATABASE'))
    result = dbe.execute(select([download_videos.c.status, download_videos.c.filename, download_videos.c.video_id]).where(download_videos.c.link == link)).fetchone()
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

    format_ext = 'mp4'
    filesize = 0
    if result is None:
        video_info = youtube_dl.YoutubeDL().extract_info(data['link'], download=False)
        title = video_info['title']
        for variant in video_info['formats']:
            if variant['format_id'] == format_id:
                format_ext = variant['ext']
                r = requests.head(variant['url'])
                filesize = int(r.headers['Content-Length'])
                break
        quality = "{} - {}".format(format_ext, format_id)
        video_id = uuid.uuid4()
        output_filename = os.path.join(b32encode(video_id.bytes).strip(b'=').lower().decode('ascii'), 'video.' + format_ext)
        dbe.execute(
            download_videos.insert().values(
                video_id=video_id,
                filesize=filesize,
                link=link,
                quality=quality,
                title=title,
                status=TaskStatus.INACTIVE.value,
                filename=output_filename
            )
        )
    else:
        output_filename = result['filename']
        video_id = result['video_id']

    download_service = DownloadVideoApi(current_app.config.get('DOWNLOAD_SERVICE_ADDR'))
    resp = download_service.start(link=data["link"],
                                  format_id=format_id,
                                  destination=output_filename)
    print(resp)
    if resp["ok"]:
        return {"success": resp['ok'], "video_id": video_id}
    else:
        return {"success": resp["ok"], "error": resp["error"]}


@api.after_request
def add_cors_headers(response):
    headers = response.headers
    headers['Access-Control-Allow-Origin'] = '*'
    headers['Access-Control-Allow-Methods'] = 'GET,POST,DELETE'
    headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response
