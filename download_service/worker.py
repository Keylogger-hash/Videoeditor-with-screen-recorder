import sys
import os
sys.path.append(os.getcwd())

import logging
import datetime
import json
import zmq
import signal
import typing
from concurrent.futures import Future
from threading import Event, Thread
from queue import Queue, Empty as QueueIsEmpty
from sqlalchemy import create_engine
from flask import current_app
from database.datamodel import download_videos
from download_service.common import IPCMessage, IPCType, TaskStatus
from download_service.executor import YoutubeDlExecutor


WORKER_IPC_POLL = 10000
EXTERNAL_IPC_POLL = 10000


class WorkerTask(object):
    __slots__ = ['link', 'deferred_task', 'progress', 'status']

    def __init__(self, link: str, deferred_task: Future) -> None:
        self.link = link  # type: str
        self.deferred_task = deferred_task
        self.status = TaskStatus.WAITING  # type: TaskStatus


class ProcessingTasks(Thread):

    def __init__(self, database_url: str, tasks_limit: int):
        super().__init__()
        self.limit = tasks_limit
        self.dbe = create_engine(database_url)
        self.exit_event = Event()
        self.tasks_datastream = Queue()
        self.tasks = {}
        self.youtubedl_executor = YoutubeDlExecutor(self.tasks_datastream, max_workers=self.limit)

    def add_task(self, link: str, format_id: int, format_ext: str,destination: str):
        if link in self.tasks:
            raise KeyError('Link is queued already')
        self.on_status_changed(link, TaskStatus.WORKING)
        future = self.youtubedl_executor.submit(link=link, format_id=format_id,format_ext=format_ext,destination=destination)
        self.tasks[link] = WorkerTask(link, future)

    def on_status_changed(self, link: str, status: TaskStatus):
        extra_changes = {}
        if status == TaskStatus.WORKING:
            extra_changes['task_begin'] = datetime.datetime.now()
        elif status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
            extra_changes['task_end'] = datetime.datetime.now()
        self.dbe.execute(
            download_videos.update().where(download_videos.c.link == link).values(status=status.value,
                                                                                  ** extra_changes)
        )

    def get_info_task(self, link: str):
        if link in self.tasks:
            return self.tasks[link]
        return None

    def list_tasks(self):
        return [
            dict(link=task.link, status=task.status.name) for _, task in self.tasks
        ]

    def run(self) -> None:
        while not self.exit_event.is_set():
            try:
                message = self.tasks_datastream.get(True, WORKER_IPC_POLL) # type: IPCMessage
            except QueueIsEmpty:
                continue
            logging.debug(str(message))
            # if message.message_type == IPCType.PROGRESS:
            #     if message.subject in self.tasks:
            #         self.tasks[message.subject].progress = message.data
            #     else:
            #         logging.warning('Missing subject: %s', message.subject)
            if message.message_type == IPCType.STATUS:
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


def start_server(address: str, worker: ProcessingTasks):
    quit_event = Event()

    def signal_handler(*args):
        print('Got SIGTERM')
        quit_event.is_set()

    signal.signal(signal.SIGTERM, signal_handler)
    context = zmq.Context()
    server_socket = context.socket(zmq.REP)
    worker.start()
    server_socket.bind(address)
    poller = zmq.Poller()
    poller.register(server_socket, zmq.POLLIN)
    while not quit_event.is_set():
        socks = poller.poll(EXTERNAL_IPC_POLL)
        for sock, _ in socks:
            reply = None
            try:
                request = json.loads(sock.recv().decode('UTF-8'))
                if request['method'] == 'ping':
                    reply = 'pong'
                elif request['method'] == 'download':
                    if request['link'] is None:
                        raise ValueError("Not link")
                    print("Download starting")
                    worker.add_task(request['link'], request['format_id'], request['format_ext'], request['destination'])
                elif request['method'] == 'cancel':
                    worker.stop(request['link'])
                elif request['method'] == 'list':
                    reply = worker.list_tasks()
                else:
                    logging.info('Not implemented')
                sock.send(json.dumps({'ok': True, 'data': reply}).encode('UTF-8'))
            except Exception as e:
                print(e)
                sock.send(json.dumps({"ok": False, "error": str(e)}).encode('UTF-8'))
    logging.info('Server stoped')
    worker.shutdown()
    logging.info('Worker shutdown')


#if __name__ == "__main__":
#    download_service_addr = 'tcp://127.0.0.1:6536'
#    start_server(download_service_addr, 10)
