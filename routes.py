from flask import Flask
from flask import request
from download_services import youtubedl_wrap
from services import upload_service, cutvideo_api, downloadvideo_api
import os
import uuid


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
    if youtubedl_wrap.download(link) == True:
        return "Finish uploading"

@app.route("/upload", methods=['POST', 'PUT'])
def upload_video():
    data = request.data
    upload_service.upload(data)

    return "Success upload"

app.config['database'] = 'sqlite:///main.db'
app.config['videocut_service_addr'] = 'tcp://127.0.0.1:15320'
app.register_blueprint(cutvideo_api.api, url_prefix='/api')
app.register_blueprint(downloadvideo_api, url_prefix='/api')


if __name__ == "__main__":
    app.run()
