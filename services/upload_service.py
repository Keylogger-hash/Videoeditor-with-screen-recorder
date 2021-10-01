import os
import uuid

def upload(data):
    filename = uuid.uuid4()
    with open(f"/home/pavel1/sven-videoeditor/{filename}.mp4", "wb") as f:
        f.write(data)
