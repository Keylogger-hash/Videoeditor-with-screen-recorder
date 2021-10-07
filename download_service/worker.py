import logging
import json
import os
import zmq
import typing
from concurrent.futures import Future
from threading import Event, Thread
from queue import Queue
from sqlalchemy import create_engine
from common import IPCMessage, IPCType, TaskStatus
from executor import YoutubeDlExecutor


class WorkerTask:
    __slots__ = ['link', 'deffered_task', 'progress', 'status']

    def __init__(self, link: str, deferred_task: Future) -> None:
        self.link = link  # type: str
        self.deferred_task = deferred_task
        self.progress = 0  # type: float
        self.status = TaskStatus.WAITING  # type: TaskStatus


class ProcessingTasks(Thread):

    def __init__(self, tasks_limit: int):
        super().__init__()
        self.limit = tasks_limit
        self.tasks_datastream = Queue()
        self.tasks = {}
        self.youtubedl_executor = YoutubeDlExecutor(self.tasks_datastream, max_workers=self.limit)

    def add_task(self, link: str):
        future = self.youtubedl_executor.submit(link)
        self.tasks[link] = WorkerTask(link, future)

    def stop(self, link: str):
        self.youtubedl_executor.task_stop(link)


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
            try:
                request = json.loads(sock.recv().decode('UTF-8'))
                reply = None
                if request['method'] == 'ping':
                    reply = 'pong'
                elif request['method'] == 'download':
                    if request['link'] == "None":
                        raise ValueError("Not link")
                    print("Download starting")
                    worker.add_task(request['link'])
                elif request['method'] == 'cancel':
                    worker.stop(request['link'])
                elif request['method'] == 'pause':
                    pass
                elif request['method'] == 'resume':
                    pass
                elif request['method'] == 'progress':
                    pass
                elif request['method'] == 'list_info':
                    pass

                else:
                    logging.info('Not implemented')
                sock.send(json.dumps({'ok': True, 'data': reply}).encode('UTF-8'))
            except Exception as e:
                print(e)
                sock.send(json.dumps({'ok': False, 'data': reply}).encode('UTF-8'))
            finally:
                pass


if __name__ == "__main__":
    start_server("tcp://127.0.0.1:6555", 10)