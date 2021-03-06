from threading import Event
from download_service.myyoutube_dl import YoutubeDl
import subprocess
from settings import YOUTUBE_DL_EXECUTABLE

dls_opt = {"ratelimit": 1000000000}


def download_video(link: str, format_id: int, format_ext: str, destination: str, fire_exit: Event = None, start_callback=None):
    if start_callback is not None:
        start_callback()
    youtubedl = YoutubeDl(YOUTUBE_DL_EXECUTABLE)
    proc = youtubedl.input(link).global_args("-q", "--output",
                                             destination,
                                             "-f", str(format_id)+"+bestaudio",
                                             "--merge-output-format",
                                             format_ext,
                                             ).run(wait=False)
    print(proc)

    while fire_exit is None or not fire_exit.is_set():
        # wait for 10s and break if process is terminated
        try:
            proc.wait(10)
            print('Process stopped')
            break
        except subprocess.TimeoutExpired:
            pass

    if fire_exit is None or not fire_exit.is_set():
        return proc.poll()
    else:
        proc.terminate()
        proc.wait() # wait until process terminates completely
