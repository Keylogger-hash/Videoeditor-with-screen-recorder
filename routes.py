from flask import Flask
from flask import request
import json
from services import download_youtube_service, upload_service

app = Flask(__name__)


@app.route("/")
def index():
    return "Hello world"


@app.route("/download_video_from_youtube", methods=['POST'])
def download_video():
    data = request.get_json()
    if data == None:
        return "Wrong data format"
    if data['link'] == None:
        return "Link video not specified"
    link = data['link']
    if download_youtube_service.download(link) == True:
        return {
            "success": True,
            "error": None
        }
    return {
        'success': False,
        'error': "Video can't download"
    }


@app.route("/upload", methods=['POST', 'PUT'])
def upload_video():
    data = request.data
    if upload_service.upload(data) == True:
        return {
            "success": True,
            "error": None
        }
    return {
        "success": False,
        "error": "Video can't upload"
    }




if __name__ == "__main__":
    app.run()
