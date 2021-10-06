import youtube_dl
from threading import Event

dls_opt = {"ratelimit": 1000000000}



def download_video(link: str, fire_exit: Event=None):
    with youtube_dl.YoutubeDL(dls_opt) as ydl:
        ydl.download([link])
    if fire_exit is None or not fire_exit.is_set():
        return True