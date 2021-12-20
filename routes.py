import os
import uuid
import datetime
from base64 import b32encode
from functools import partial
from flask import Flask, request, current_app, send_from_directory
from sqlalchemy import create_engine
from services import cutvideo_api, downloadvideo_api
from frontend import demo_ui
from settings import DOWNLOADS_LOCATION, CUTS_LOCATION
from download_service.common import TaskStatus
from database.datamodel import download_videos


app = Flask(__name__, static_url_path='/_static')

@app.route("/api/upload", methods=['POST', 'PUT'])
def upload_video():
    if not 'upload' in request.files:
        return {
            'success': False,
            'error': 'No file uploaded'
        }
    uploaded_file = request.files['upload']
    if uploaded_file:
        db = create_engine(current_app.config.get('DATABASE'))
        video_id = uuid.uuid4()
        now = datetime.datetime.now()
        _, file_ext = os.path.splitext(uploaded_file.filename)
        output_filename = os.path.join(b32encode(video_id.bytes).strip(b'=').lower().decode('ascii'), 'video' + file_ext)
        os.makedirs(os.path.join(DOWNLOADS_LOCATION, os.path.dirname(output_filename)), exist_ok=True)
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
            "result": {
                "videoId": video_id
            }
        }
    return {
        "success": False,
        "error": "No file uploaded"
    }



app.register_blueprint(demo_ui.demo_ui, url_prefix='/')
app.register_blueprint(cutvideo_api.api, url_prefix='/api')
app.register_blueprint(downloadvideo_api.api, url_prefix='/api')
app.config.from_object('settings')

# NOTE: serve files, do not use in production
app.add_url_rule('/files/uploads/<path:path>', 'serve_uploads', view_func=partial(send_from_directory, DOWNLOADS_LOCATION))
app.add_url_rule('/files/cuts/<path:path>', 'serve_cuts', view_func=partial(send_from_directory, CUTS_LOCATION))

if __name__ == "__main__":
    app.run(debug=True)
