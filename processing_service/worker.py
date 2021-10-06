import logging
import json
import os
import zmq
import typing
from concurrent.futures import Future
from threading import Event, Thread
from queue import Queue
from sqlalchemy import create_engine
from executor import FFmpegThreadExecutor
from common import IPCMessage, IPCType, TaskStatus
from dbmodels import videos

class WorkerTask(object):
    __slots__ = ['output_filename', 'deferred_task', 'progress', 'status']
    def __init__(self, output_filename: str, deferred_task: Future) -> None:
        self.output_filename = output_filename # type: str
        self.deferred_task = deferred_task # type: Future
        self.progress = 0 # type: float
        self.status = TaskStatus.WAITING # type: TaskStatus

class ProcessingWorker(Thread):
    def __init__(self, task_limit: int) -> None:
        super().__init__()
        self.exit_event = Event() # type: Event
        self.tasks_datastream = Queue() # type: Queue
        self.tasks = {} # type: typing.Dict[str, WorkerTask]
        self.ffmpeg_executor = FFmpegThreadExecutor(self.tasks_datastream, task_limit) # type: FFmpegThreadExecutor

    def add_task(self, input_filename: str, output_filename: str, start_at: int, end_at: int) -> None:
        if output_filename in self.tasks:
            raise KeyError('Output file is queued already')
        future = self.ffmpeg_executor.submit(input_filename, output_filename, start_at, end_at)
        self.tasks[output_filename] = WorkerTask(output_filename, future)

    def stop_task(self, output_filename: str) -> None:
        self.ffmpeg_executor.stop_task(output_filename)
        # del self.tasks[output_filename]

    def get_task_info(self, output_filename: str) -> typing.Optional[WorkerTask]:
        if output_filename in self.tasks:
            return self.tasks[output_filename]
        return None

    def list_tasks(self):
        return [
            dict(outputFilename=task.output_filename, progress=task.progress, status=task.status.name)
            for _, task in self.tasks.items()
        ]

    def on_progress(self, subject: str, percent: float):
        pass

    def on_status_changed(self, subject: str, status: TaskStatus):
        pass

    def run(self) -> None:
        while not self.exit_event.is_set():
            message = self.tasks_datastream.get() # type: IPCMessage
            logging.debug(str(message))
            if message.message_type == IPCType.PROGRESS:
                if message.subject in self.tasks:
                    self.tasks[message.subject].progress = message.data
                    self.on_progress(message.subject, message.data)
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
        self.exit_event.set()
        self.ffmpeg_executor.shutdown()
        logging.info('Force stop worker')

class DatabaseProcessingWorker(ProcessingWorker):
    def __init__(self, database_url, tasks_limit):
        super().__init__(tasks_limit)
        self.dbe = create_engine(database_url)

    def on_status_changed(self, subject, status):
        self.dbe.execute(
            videos.update().where(videos.c.output_filename == subject).values(status=status.value)
        )

    def on_progress(self, subject, value):
        self.dbe.execute(
            videos.update().where(videos.c.output_filename == subject).values(progress=value)
        )

def start_server(address: str, tasks_limit: int) -> None:
    quit_event = Event()
    ctx = zmq.Context()
    worker = ProcessingWorker(tasks_limit)
    worker.start()
    server_socket = ctx.socket(zmq.REP)
    server_socket.bind(address)
    poller = zmq.Poller()
    poller.register(server_socket, zmq.POLLIN)
    while not quit_event.is_set():
        socks = poller.poll(10000)
        if socks:
            for sock, _ in socks:
                try:
                    request = json.loads(sock.recv().decode('utf-8'))
                    reply = None
                    if request['method'] == 'ping':
                        reply = 'pong'
                    elif request['method'] == 'cut':
                        if (request['startAt'] < 0) or (request['endAt'] < 0) or (request['startAt'] > request['endAt']):
                            raise ValueError('Incorrect range')
                        if not os.path.isfile(request['input']):
                            raise IOError('Source not found')
                        if not os.path.isdir(os.path.dirname(request['output'])):
                            raise IOError('Output location not found')
                        worker.add_task(
                            request['input'],
                            request['output'],
                            request['startAt'],
                            request['endAt']
                        )
                    elif request['method'] == 'cancel':
                        worker.stop_task(request['output'])
                    elif request['method'] == 'status':
                        task = worker.get_task_info(request['output'])
                        if task is None:
                            raise KeyError('No such task')
                        else:
                            reply = str(worker.tasks[request['output']].status.name)
                    elif request['method'] == 'progress':
                        task = worker.get_task_info(request['output'])
                        if task is None:
                            raise KeyError('No such task')
                        else:
                            reply = worker.tasks[request['output']].progress
                    elif request['method'] == 'list':
                        reply = worker.list_tasks()
                    elif request['method'] == 'stop':
                        worker.shutdown()
                        quit_event.set()
                    else:
                        logging.info('Not implemented')
                    sock.send(json.dumps({'ok': True, 'data': reply}).encode('utf-8'))
                except Exception as e:
                    sock.send(json.dumps({'ok': False, 'error': str(e)}).encode('utf-8'))


if __name__ == "__main__":
    start_server("tcp://127.0.0.1:5555", 10)
