import logging
import typing
import traceback
from queue import Queue
from youtubedl_wrap import download_video
from concurrent.futures import ThreadPoolExecutor, Future
from common import IPCType, IPCMessage, TaskStatus
from functools import partial
from threading import Event

class YoutubeDlExecutor:

    def __init__(self,dataStream: Queue, max_workers=3):
        super().__init__()
        self.ex = ThreadPoolExecutor(max_workers=max_workers)
        self.datastream = dataStream
        self.task_stoppers = {}

    def task_done(self, link: str, future: Future):
        result = future.result()
        logging.info('Done %s - %s', result, link)
        del self.task_stoppers[link]

    def task_stop(self, link: str):
        if link in self.task_stoppers:
            self.task_stoppers[link].set()

    def submit(self, link: str):
        exit_event = Event()
        self.task_stoppers[link] = exit_event
        try:
            task_future = self.ex.submit(
                download_video,
                link,
                exit_event
            )
            task_future.add_done_callback(partial(self.task_done, link))
            return task_future
        except Exception as e:
            logging.warning('Error occured during processing: %s', link)
            traceback.print_exc()
            self.datastream.put(IPCMessage(IPCType.STATUS, link, TaskStatus.FAILED))
            return None
