import youtube_dl
from database.datamodel import add_video
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool
from settings import context

dls_opt = {}
DATABASE_URL = context['DATABASE_URL']

def download(link: str):
    dbe = create_engine(DATABASE_URL, poolclass=NullPool)
    with youtube_dl.YoutubeDL(dls_opt) as ydl:
        info = ydl.extract_info(link, download=False)
        title = info['title']
        ydl.download([link])
        add_video(dbe, title)
    return True