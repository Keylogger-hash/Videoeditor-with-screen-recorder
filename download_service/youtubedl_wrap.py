from threading import Event
from myyoutube_dl import YoutubeDl
import subprocess

dls_opt = {"ratelimit": 1000000000}

youtubedl = YoutubeDl()


def download_video(link: str, destination: str, fire_exit: Event = None, start_callback=None):
    if start_callback is not None:
        start_callback()

    proc = youtubedl.input(link).global_args("--output", destination, "-f", 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best').run(wait=False)
    print(proc)

    while fire_exit is None or not fire_exit.is_set():
        output = proc.stdout.readline()
        print(output)
        if output == b'' and proc.poll() is not None:
            break

    if fire_exit is None or not fire_exit.is_set():
        return proc.poll()
    else:
        proc.terminate()


def stop_download_video(link: str, fire_exit: Event=None):
    proc = youtubedl.input(link).stop()
    print(proc.poll())
    if fire_exit is None or not fire_exit.is_set():
        return proc.poll()

