import logging
import os
import typing
import traceback
from queue import Queue
from youtubedl_wrap import download_video
from concurrent.futures import ThreadPoolExecutor, Future
from settings import DOWNLOADS_LOCATION
from common import IPCType, IPCMessage, TaskStatus
from functools import partial
from threading import Event


class YoutubeDlExecutor:

    def __init__(self, dataStream: Queue, max_workers: int = 3):
        super().__init__()
        self.ex = ThreadPoolExecutor(max_workers=max_workers)
        self.datastream = dataStream
        self.task_stoppers = {}

    def shutdown(self) -> None:
        for task in self.task_stoppers:
            self.task_stoppers[task].set()
        self.ex.shutdown()

    def task_stop(self, link: str):
        print(self.task_stoppers)
        if link in self.task_stoppers:
            self.task_stoppers[link].set()

    def task_done(self, link: str, future: Future):
        retcode = future.result()
        logging.info('Done %s - %s', retcode, link)
        del self.task_stoppers[link]
        if retcode == 0:
            self.datastream.put(IPCMessage(IPCType.STATUS, link, TaskStatus.COMPLETED))
        else:
            self.datastream.put(IPCMessage(IPCType.STATUS, link, TaskStatus.FAILED))
        self.datastream.put(IPCMessage(IPCType.REMOVE_TASK, link))

    def task_started(self, link: str) -> None:
        logging.info('Started task: %s', link)
        self.datastream.put(IPCMessage(IPCType.STATUS, link, TaskStatus.WORKING))

    def submit(self, link: str, format_id: int,destination: str):
        exit_event = Event()
        self.task_stoppers[link] = exit_event
        print()
        try:
            task_future = self.ex.submit(
                download_video,
                link,
                format_id,
                destination,
                exit_event,
                partial(self.task_started, link)
            )
            task_future.add_done_callback(partial(self.task_done, link))
            return task_future
        except Exception as e:
            logging.warning('Error occured during processing: %s', link)
            traceback.print_exc()
            self.datastream.put(IPCMessage(IPCType.STATUS, link, TaskStatus.FAILED))
            return None
