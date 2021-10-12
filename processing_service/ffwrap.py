import os
import typing as t
from threading import Event
from myff import FFprobe, FFmpeg, Error as FFmpegError

ERROR_INCORRECT_ARGUMENTS = 500
ERROR_PROBE_FAILED = 510
ERROR_TASK_CANCELLED = 520

TRANSCODING_SETTINGS = ['-c', 'copy', '-avoid_negative_ts', '1'] # type: t.List[str]

def parsetime(text: str) -> float:
    s, ms = text.split('.')
    return int(s) * 1e6 + int(ms)

def convert_file(input_file: str, output_file: str, start_at: int, end_at: int, keep_streams: str, fire_exit: t.Optional[Event]=None, progress_callback=None, start_callback=None) -> t.Optional[int]:
    try:
        if start_callback is not None:
            start_callback()
        total_duration = float(FFprobe().input(input_file).options(select_streams='v:0', show_entries='format=duration').json()['format']['duration'])
        if end_at > total_duration:
            return ERROR_INCORRECT_ARGUMENTS
        duration = end_at - start_at
        extra_options = []
        if keep_streams == 'audio':
            extra_options.append('-vn')
        elif keep_streams == 'video':
            extra_options.append('-an')
        proc = FFmpeg().\
            global_args('-y', '-v', 'error', '-progress', '-').\
            input(input_file).\
            output(output_file, *TRANSCODING_SETTINGS, *extra_options, ss=str(start_at), t=str(duration)).\
            run(wait=False)
        while fire_exit is None or not fire_exit.is_set():
            output = proc.stdout.readline()
            if output == b'' and proc.poll() is not None:
                break
            if output != b'' and output.startswith(b'out_time_ms='):
                if progress_callback is not None:
                    progress_callback(100.0 * ((int(output[12:]) / 1e6) / duration))
        if fire_exit is None or not fire_exit.is_set():
            progress_callback(100)
            return proc.poll()
        else:
            proc.terminate()
            proc.wait()
            os.remove(output_file)
            return ERROR_TASK_CANCELLED
    except FFmpegError:
        return ERROR_PROBE_FAILED
