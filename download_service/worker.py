import logging
import datetime
import json
import os
import zmq
import typing
from concurrent.futures import Future
from threading import Event, Thread
from queue import Queue, Empty as QueueIsEmpty
from sqlalchemy import create_engine
from flask import current_app
from .database.datamodel import download_videos
from common import IPCMessage, IPCType, TaskStatus
from executor import YoutubeDlExecutor


WORKER_IPC_POLL = 10000
EXTERNAL_IPC_POLL = 10000


class WorkerTask(object):
    __slots__ = ['link', 'deferred_task', 'progress', 'status']

    def __init__(self, link: str, deferred_task: Future) -> None:
        self.link = link  # type: str
        self.deferred_task = deferred_task
        self.progress = 0  # type: float
        self.status = TaskStatus.WAITING  # type: TaskStatus


class ProcessingTasks(Thread):

    def __init__(self, tasks_limit: int):
        super().__init__()
        self.limit = tasks_limit
        self.exit_event = Event()
        self.tasks_datastream = Queue()
        self.tasks = {}
        self.youtubedl_executor = YoutubeDlExecutor(self.tasks_datastream, max_workers=self.limit)

    def add_task(self, link: str):
        future = self.youtubedl_executor.submit(link)
        self.tasks[link] = WorkerTask(link, future)
        self.on_status_changed(link, TaskStatus.WORKING)

    def on_status_changed(self, link: str, status: TaskStatus):
        pass

    def get_info_task(self, link: str):
        if link in self.tasks:
            return self.tasks[link]
        return None

    def list_tasks(self):
        return [
            dict(link=task.link) for _, task in self.tasks
        ]

    def run(self) -> None:
        while not self.exit_event.is_set():
            try:
                message = self.tasks_datastream.get(False, WORKER_IPC_POLL) # type: IPCMessage
            except QueueIsEmpty:
                continue
            logging.debug(str(message))
            if message.message_type == IPCType.PROGRESS:
                if message.subject in self.tasks:
                    self.tasks[message.subject].progress = message.data
                else:
                    logging.warning('Missing subject: %s', message.subject)
            elif message.message_type == IPCType.STATUS:
                if message.subject in self.tasks:
                    self.tasks[message.subject].status = message.data
                    self.on_status_changed(message.subject, message.data)
                else:
                    logging.warning('Missing subject: %s', message.subject)
            elif message.message_type == IPCType.REMOVE_TASK:
                if message.subject in self.tasks:
                    del self.tasks[message.subject]
                else:
                    logging.warning('Missing subject: %s', message.subject)
        logging.info('Stopping worker')

    def shutdown(self) -> None:
        if not self.exit_event.is_set():
            self.exit_event.set()
            self.youtubedl_executor.shutdown()
            logging.info('Force stop worker')

    def stop(self, link: str):
        self.youtubedl_executor.task_stop(link)


class DatabaseChangingProcessing(ProcessingTasks):
    def __init__(self, database_url, tasks_limit):
        super().__init__(tasks_limit)
        self.dbe = create_engine(database_url)

    def on_status_changed(self, link: str, status: TaskStatus):
        extra_changes = {}
        if status == TaskStatus.WORKING:
            extra_changes['task_begin'] = datetime.datetime.now()
        elif status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
            extra_changes['task_end'] = datetime.datetime.now()
        self.dbe.execute(
            download_videos.update().where(download_videos.c.link == link).values(status=status.value, ** extra_changes)
        )


def start_server(address: str, tasks_limit: int):
    quit_event = Event()
    context = zmq.Context()
    server_socket = context.socket(zmq.REP)
    worker = ProcessingTasks(tasks_limit)
    worker.start()
    server_socket.bind(address)
    poller = zmq.Poller()
    poller.register(server_socket, zmq.POLLIN)
    while not quit_event.is_set():
        socks = poller.poll(10000)
        for sock, _ in socks:
            reply=None
            try:
                request = json.loads(sock.recv().decode('UTF-8'))
                if request['method'] == 'ping':
                    reply = 'pong'
                elif request['method'] == 'download':
                    if request['link'] is None:
                        raise ValueError("Not link")
                    print("Download starting")
                    worker.add_task(request['link'])
                elif request['method'] == 'cancel':
                    worker.stop(request['link'])
                elif request['method'] == 'list':
                    reply = worker.list_tasks()
                else:
                    logging.info('Not implemented')
                sock.send(json.dumps({'ok': True, 'data': reply}).encode('UTF-8'))
            except Exception as e:
                print(e)
                sock.send(json.dumps({"ok": False, "data": reply, "error": e}).encode('UTF-8'))
            finally:
                pass


if __name__ == "__main__":
    download_service_addr = 'tcp://127.0.0.1:6536'
    start_server(download_service_addr, 10)
