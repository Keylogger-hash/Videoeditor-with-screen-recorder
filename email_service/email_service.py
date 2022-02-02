from sqlalchemy import create_engine
from sqlalchemy.sql import select
from flask import Blueprint, abort, current_app, render_template, url_for, send_from_directory, request
from email_service.celery_queue import send_async_email
from database.datamodel import records
import uuid
email_service = Blueprint('email', __name__, template_folder='html', static_url_path='/_static')

#     email_data={
    #     'subject':'Link to player',
    #     'to':email,
    #     'body':body
    # }
    # send_async_email.delay(email_data)
def is_valid_uuid(val: str):
    try:
        uuid.UUID(str(val))
        return True
    except ValueError:
        return False

@email_service.post('/email')
def send_email_task():
    data=request.json
    email=data.get('email',None)
    record_id=data.get('record_id',None)

    if email is None:
        return {
            'success': False,
            'error':'email is None'
        }
    if record_id is None:
        return {
            'success': False,
            'error': 'Record id is None'
        } 
    if is_valid_uuid(record_id) != True:
        return {
            'success': False,
            'error': 'Record id has invalid uuid type'
        }
    dbe = create_engine(current_app.config.get('DATABASE'))
    result = dbe.execute(select([records]).where(records.c.video_id==record_id)).fetchone()
    if result is None:
        return {
            'success': False,
            'error': 'Record is not found'
        }
    else:
        output_name_view="_".join(result['output_name'].split("/"))
        link_player = f"http://localhost:4040/play/record/{output_name_view}"
        body=f"Hello! Link to player is:{link_player}"
        subject = "Link to player"
        email_data={"subject": subject, "body":body,"email":email}
        send_async_email.delay(email_data)
        return {'success':True}

