from threading import Event
from settings import YOUTUBE_DL_EXECUTABLE
from download_service.myyoutube_dl import YoutubeDl

dls_opt = {"ratelimit": 1000000000}

youtubedl = YoutubeDl(YOUTUBE_DL_EXECUTABLE)


def download_video(link: str, destination: str, fire_exit: Event = None):
    proc = youtubedl.input(link).global_args('--output', destination).run(wait=False)

    while fire_exit is None or not fire_exit.is_set():
        output = proc.stdout.readline()
        if output == b'' and proc.poll() is not None:
            break

    if fire_exit is None or not fire_exit.is_set():
        return proc.poll()

def stop_download_video(link: str, fire_exit: Event=None):
    proc = youtubedl.input(link).stop()
    print(proc.poll())
    if fire_exit is None or not fire_exit.is_set():
        return proc.poll()

