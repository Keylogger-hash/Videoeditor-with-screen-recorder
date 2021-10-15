import os
import uuid
import datetime
from base64 import b32encode
from flask import Flask, request, current_app
from sqlalchemy import create_engine
from services import cutvideo_api, downloadvideo_api
from settings import DOWNLOADS_LOCATION
from download_service.common import TaskStatus
from database.datamodel import download_videos


app = Flask(__name__)


@app.route("/")
def index():
    return "Hello world"

@app.route("/upload", methods=['POST', 'PUT'])
def upload_video():
    if not 'upload' in request.files:
        return {
            'success': False,
            'error': 'No file sent for uploading'
        }
    uploaded_file = request.files['upload']
    if uploaded_file:
        db = create_engine(current_app.config.get('DATABASE'))
        video_id = uuid.uuid4()
        now = datetime.datetime.now()
        _, file_ext = os.path.splitext(uploaded_file.filename)
        output_filename = b32encode(video_id.bytes).strip(b'=').lower().decode('ascii') + file_ext
        db.execute(download_videos.insert().values(
            video_id=video_id,
            filename=output_filename,
            link='',
            title=uploaded_file.filename,
            quality=None,
            task_begin=now,
            task_end=now,
            status=TaskStatus.COMPLETED.value
        ))
        uploaded_file.save(os.path.join(DOWNLOADS_LOCATION, output_filename))
        return {
            "success": True,
            "error": None
        }
    return {
        "success": False,
        "error": "Video can't upload"
    }

app.register_blueprint(cutvideo_api.api, url_prefix='/api')
app.register_blueprint(downloadvideo_api.api, url_prefix='/api')
app.config.from_object('settings')

if __name__ == "__main__":
    app.run(debug=True)
