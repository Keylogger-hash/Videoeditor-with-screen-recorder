from sqlalchemy import create_engine
from sqlalchemy.sql import select
from flask import Blueprint, abort, current_app, render_template, url_for, send_from_directory

from database.datamodel import videos


demo_ui = Blueprint('demo_frontend', __name__, template_folder='html', static_url_path='/_static')

@demo_ui.get('/')
def upload_page():
    return send_from_directory('frontend/html', 'upload.html')

@demo_ui.get('/edit')
def editor_page():
    return send_from_directory('frontend/html', 'editor.html')

@demo_ui.get('/play/<output_name>')
def player_page(output_name):
    database_url = current_app.config.get('DATABASE')
    db = create_engine(database_url)
    result = db.execute(select([videos]).where(videos.c.output_filename == output_name)).fetchone()
    if result is None:
        return abort(404)
    return render_template('player.html', output_name=output_name, title=result['description'])

@demo_ui.get('/static/<path:filepath>')
def serve_static_assets(filepath):
    return send_from_directory('frontend/static', filepath)
