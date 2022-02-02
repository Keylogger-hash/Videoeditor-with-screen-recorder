from sqlalchemy import true


DATABASE = "postgresql://postgres:123@192.168.100.147/sven_videoeditor"
VIDEOCUT_SERVICE_ADDR = "tcp://127.0.0.1:15320"
DOWNLOAD_SERVICE_ADDR = "tcp://127.0.0.1:6536"
ENCODE_SERVICE_ADDR="tcp://127.0.0.1:34034"
VIDEOCUT_SERVICE_WORKERS = 4
DOWNLOADS_LOCATION = 'downloads'
CUTS_LOCATION = 'cuts'
YOUTUBE_DL_EXECUTABLE = '/usr/local/bin/yt-dlp'


# email
MAIL_SERVER=''
MAIL_PORT=587
MAIL_USERNAME=''
MAIL_PASSWORD=''
MAIL_USE_TLS=True
MAIL_USE_SSL=False

# celery
CELERY_BROKER_URL='redis://redis:6379/0',
CELERY_RESULT_BACKEND='redis://redis:6379/0'


# EMAIL_HOST = 'smtp.yandex.ru'
# EMAIL_PORT = 587
# EMAIL_HOST_USER = 'login@example.com'
# EMAIL_HOST_PASSWORD = 'password'
# DEFAULT_FROM_EMAIL = 'login@example.com'
# EMAIL_USE_TLS = True
