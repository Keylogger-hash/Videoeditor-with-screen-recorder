import os
import uuid
from database.datamodel import add_video
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool
from settings import context

DATABASE_URL = context['DATABASE_URL']


def upload(data):
    filename = uuid.uuid4()
    dbe = create_engine(DATABASE_URL, poolclass=NullPool)
    with open(f"/home/pavel1/sven-videoeditor/{filename}.mp4", "wb") as f:
        f.write(data)
    add_video(dbe, f"{filename}.mp4")
    return True