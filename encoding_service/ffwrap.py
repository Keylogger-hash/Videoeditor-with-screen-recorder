import os
import typing as t
from threading import Event
from processing_service.myff import FFprobe, FFmpeg, Error as FFmpegError

ERROR_INCORRECT_ARGUMENTS = 500
ERROR_PROBE_FAILED = 510
ERROR_TASK_CANCELLED = 520
ERROR_EXCEPTION = 600

TRANSCODING_SETTINGS = ['-avoid_negative_ts', '1']  # type: t.List[str]


def parsetime(text: str) -> float:
    s, ms = text.split('.')
    return int(s) * 1e6 + int(ms)


def convert_file(input_file: str, output_file: str,  type: str, external_stop: t.Optional[Event]=None, progress_callback=None, start_callback=None) -> t.Optional[int]:
    try:
        if start_callback is not None:
            start_callback()
        total_duration = float(FFprobe().input(input_file).options(select_streams='v:0', show_entries='format=duration').json()['format']['duration'])
    
        extra_options = []
        if type == 'audio':
            extra_options.append('-b:a')
            extra_options.append('320k')
            extra_options.append('-fflags')
            extra_options.append('+genpts')
            extra_options.append('-vn')
        elif type == 'video':
            extra_options.append('-c:v')
            extra_options.append('h264')
            extra_options.append('-fflags')
            extra_options.append('+genpts')
        proc = FFmpeg().\
            global_args('-y', '-v', 'error', '-progress', '-').\
            input(input_file).\
            output(output_file, *TRANSCODING_SETTINGS, *extra_options).\
            run(wait=False)
        while external_stop is None or not external_stop.is_set():
            output = proc.stdout.readline()
            if output == b'' and proc.poll() is not None:
                break
            if output != b'' and output.startswith(b'out_time_ms='):
                if progress_callback is not None:
                    progress_callback(100.0 * ((int(output[12:]) / 1e6) / total_duration))
        if external_stop is None or not external_stop.is_set():
            progress_callback(100)
            return proc.poll()
        else:
            proc.terminate()
            proc.wait()
            os.remove(output_file)
            return ERROR_TASK_CANCELLED
    except FFmpegError:
        return ERROR_PROBE_FAILED
    except:
        return ERROR_EXCEPTION
