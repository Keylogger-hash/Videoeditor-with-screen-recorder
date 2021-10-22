from flask import Blueprint, send_from_directory

demo_ui = Blueprint('demo_frontend', __name__)

@demo_ui.get('/')
def upload_page():
    return send_from_directory('frontend/html', 'upload.html')

@demo_ui.get('/edit')
def editor_page():
    return send_from_directory('frontend/html', 'editor.html')

@demo_ui.get('/results')
def results_page():
    return send_from_directory('frontend/html', 'results.html')

@demo_ui.get('/static/<path>')
def serve_static_assets(path):
    return send_from_directory('frontend/static', path)