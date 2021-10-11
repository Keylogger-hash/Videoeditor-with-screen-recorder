import os
import logging
import typing
import traceback
from queue import Queue
from concurrent.futures import ThreadPoolExecutor, Future
from functools import partial
from threading import Event
from processing_service.common import IPCType, IPCMessage, TaskStatus
from processing_service.ffwrap import convert_file
from processing_service.paths import UPLOADS_LOCATION, CUTS_LOCATION

class FFmpegThreadExecutor(object):
    def __init__(self, datastream: Queue, workers_queue: int=3) -> None:
        super().__init__()
        self.ex = ThreadPoolExecutor(max_workers=workers_queue) # type: ThreadPoolExecutor
        self.datastream = datastream # type: Queue
        self.task_stoppers = {} # type: typing.Dict[str, Event]

    def shutdown(self) -> None:
        for task in self.task_stoppers:
            self.task_stoppers[task].set()
        self.ex.shutdown()

    def stop_task(self, output_filename: str) -> None:
        if output_filename in self.task_stoppers:
            self.task_stoppers[output_filename].set()

    def task_progress(self, output_filename: str, percent: float) -> None:
        self.datastream.put(IPCMessage(IPCType.PROGRESS, output_filename, percent))

    def task_done(self, output_filename: str, future: Future) -> None:
        retcode = future.result()
        logging.info('Done %s - %s', output_filename, retcode)
        del self.task_stoppers[output_filename]
        if retcode == 0:
            self.datastream.put(IPCMessage(IPCType.STATUS, output_filename, TaskStatus.COMPLETED))
        else:
            self.datastream.put(IPCMessage(IPCType.STATUS, output_filename, TaskStatus.FAILED))
        self.datastream.put(IPCMessage(IPCType.REMOVE_TASK, output_filename))

    def task_started(self, output_filename: str) -> None:
        logging.info('Started conversion: %s', output_filename)
        self.datastream.put(IPCMessage(IPCType.STATUS, output_filename, TaskStatus.WORKING))

    def submit(self, input_filename: str, output_filename: str, start_at: int, end_at: int, keep_streams: str='both') -> typing.Optional[Future]:
        try:
            exit_event = Event()
            self.task_stoppers[output_filename] = exit_event
            task_future = self.ex.submit(
                convert_file,
                os.path.join(UPLOADS_LOCATION, input_filename),
                os.path.join(CUTS_LOCATION, output_filename),
                start_at,
                end_at,
                keep_streams,
                exit_event,
                partial(self.task_progress, output_filename),
                partial(self.task_started, output_filename)
            )
            task_future.add_done_callback(partial(self.task_done, output_filename))
            return task_future
        except:
            logging.warning('Error occured during processing: %s', input_filename)
            traceback.print_exc()
            self.datastream.put(IPCMessage(IPCType.STATUS, input_filename, TaskStatus.FAILED))
            return None