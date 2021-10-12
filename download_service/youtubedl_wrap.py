from threading import Event
from myyoutube_dl import YoutubeDl
import subprocess

dls_opt = {"ratelimit": 1000000000}

youtubedl = YoutubeDl()


def download_video(link: str, fire_exit: Event=None, progress_callback=None):
    proc = youtubedl.input(link).global_args().run(wait=True)
    print(proc)

    while fire_exit is None or not fire_exit.is_set():
        output = proc.stdout.readline()
        print(output)
        if output == b'' and proc.poll() is not None:
            break

    if fire_exit is None or not fire_exit.is_set():
        return proc.poll()

def stop_download_video(link: str, fire_exit: Event=None):
    proc = youtubedl.input(link).stop()
    print(proc.poll())
    if fire_exit is None or not fire_exit.is_set():
        return proc.poll()

