from celery import Celery
from settings import CELERY_RESULT_BACKEND,CELERY_BROKER_URL,MAIL_SERVER,MAIL_PORT,MAIL_USERNAME,MAIL_PASSWORD,MAIL_USE_TLS,MAIL_USE_SSL
from flask_mail import Mail, Message, current_app
from flask import Flask
flask_app = Flask(__name__)

def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery

#app = Flask(__name__)
flask_app.config.update(  
    CELERY_BROKER_URL=CELERY_BROKER_URL,
    CELERY_RESULT_BACKEND=CELERY_RESULT_BACKEND,
    MAIL_SERVER=MAIL_SERVER,
    MAIL_PORT=MAIL_PORT,
    MAIL_USERNAME=MAIL_USERNAME,
    MAIL_PASSWORD=MAIL_PASSWORD,
    MAIL_USE_TLS=MAIL_USE_TLS,
    MAIL_USE_SSL=MAIL_USE_SSL,
)
celery_app = make_celery(flask_app)


@celery_app.task()
def send_async_email(email_data):
    with flask_app.app_context():
        mail = Mail(flask_app)
        sender=current_app.config.get('MAIL_USERNAME')
        msg = Message(subject=email_data["subject"],body=email_data["body"],sender=sender, recipients=[email_data["email"]])
        mail.send(message=msg)
    