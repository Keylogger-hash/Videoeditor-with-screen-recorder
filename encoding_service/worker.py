import logging
import signal
import json
import os
import zmq
import typing
import datetime
from concurrent.futures import Future
from threading import Event, Thread
from queue import Queue, Empty as QueueIsEmpty
from sqlalchemy import create_engine
from encoding_service.executor import FFmpegThreadExecutor
from encoding_service.common import IPCType, TaskStatus
from shared.zmqserver import ZMQServer
from database.datamodel import records
from settings import DOWNLOADS_LOCATION 

WORKER_IPC_POLL = 10


class WorkerTask(object):
    __slots__ = ['output_name', 'deferred_task', 'progress', 'status']

    def __init__(self, output_name: str, deferred_task: Future) -> None:
        self.output_name = output_name # type: str
        self.deferred_task = deferred_task # type: Future
        self.progress = 0 # type: float
        self.status = TaskStatus.QUEUED # type: TaskStatus


class ProcessingWorker(Thread):
    def __init__(self, task_limit: int) -> None:
        super().__init__()
        self.exit_event = Event() # type: Event
        self.tasks_datastream = Queue() # type: Queue
        self.tasks = {} # type: typing.Dict[str, WorkerTask]
        self.ffmpeg_executor = FFmpegThreadExecutor(self.tasks_datastream, task_limit) # type: FFmpegThreadExecutor

    def add_task(self, input_filename: str,output_name: str, type:str) -> None:
        if output_name in self.tasks:
            raise KeyError('Output file is queued already')
        self.tasks[output_name] = WorkerTask(output_name, None)
        future = self.ffmpeg_executor.submit(input_filename,output_name, type)
        self.tasks[output_name].deferred_task = future
        self.on_status_changed(output_name, TaskStatus.QUEUED)

    def stop_task(self, output_name: str) -> None:
        self.ffmpeg_executor.stop_task(output_name)
        # NOTE: task will be deleted when executor stops thread
        # del self.tasks[output_filename]

    def get_task_info(self, output_name: str) -> typing.Optional[WorkerTask]:
        if output_name in self.tasks:
            return self.tasks[output_name]
        return None

    def list_tasks(self):
        return [
            dict(outputFilename=task.output_name, progress=task.progress, status=task.status.name)
            for _, task in self.tasks.items()
        ]

    def on_progress(self, subject: str, percent: float):
        pass

    def on_status_changed(self, subject: str, status: TaskStatus):
        pass

    def run(self) -> None:
        while not self.exit_event.is_set():
            try:
                message = self.tasks_datastream.get(True, WORKER_IPC_POLL) # type: IPCMessage
            except QueueIsEmpty:
                continue
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
        if not self.exit_event.is_set():
            self.exit_event.set()
            self.ffmpeg_executor.shutdown()
            logging.info('Force stop worker')


class DatabaseProcessingWorker(ProcessingWorker):
    def __init__(self, database_url, tasks_limit):
        super().__init__(tasks_limit)
        self.dbe = create_engine(database_url)

    def on_status_changed(self, subject: str, status: TaskStatus):
        extra_changes = {}
        if status == TaskStatus.WORKING:
            extra_changes['task_begin'] = datetime.datetime.now()
        elif status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
            extra_changes['task_end'] = datetime.datetime.now()
        self.dbe.execute(
            records.update().where(records.c.output_name == subject).values(status=status.value, ** extra_changes)
        )

    def on_progress(self, subject: str, percent: float):
        self.dbe.execute(
            records.update().where(records.c.output_name == subject).values(progress=int(percent))
        )

class EncodeServiceListener(ZMQServer):
    def __init__(self, address: str, worker: ProcessingWorker):
        super().__init__(address)
        self.worker = worker

    def prepare(self):
        logging.info('Starting processing worker...')
        self.worker.start()
        logging.info('Starting server...')

    def finalize(self):
        logging.info('Shutting down worker...')
        self.worker.shutdown()
        logging.info('Server stopped')

    def handle(self, request):
        reply = None
        if request['method'] == 'ping':
            reply = 'pong'
        elif request['method'] == 'encode':
            if request['type'] is not None and request['type'] not in ('audio', 'video'):
                raise ValueError('Incorrect type option value')
            if not os.path.isfile(os.path.join(DOWNLOADS_LOCATION, request['input'])):
                raise IOError('Source not found')
            self.worker.add_task(
                request['input'],
                request['output'],
                request['type'],
            )
        elif request['method'] == 'cancel':
            self.worker.stop_task(request['output'])
        elif request['method'] == 'status':
            task = self.worker.get_task_info(request['output'])
            if task is None:
                raise KeyError('No such task')
            else:
                reply = str(self.worker.tasks[request['output']].status.name)
        elif request['method'] == 'progress':
            task = self.worker.get_task_info(request['output'])
            if task is None:
                raise KeyError('No such task')
            else:
                reply = self.worker.tasks[request['output']].progress
        elif request['method'] == 'list':
            reply = self.worker.list_tasks()
        elif request['method'] == 'stop':
            self.worker.shutdown()
            self.shutdown()
        else:
            logging.info('Not implemented')
        return {'ok': True, 'data': reply}

def start_server(address: str, worker: ProcessingWorker) -> None:
    quit_event = Event()

    def signal_handler(*args):
        print('Got SIGTERM')
        quit_event.set()
    signal.signal(signal.SIGTERM, signal_handler)
    ctx = zmq.Context()
    logging.info('Starting processing worker...')
    worker.start()
    server_socket = ctx.socket(zmq.REP)
    server_socket.bind(address)
    poller = zmq.Poller()
    poller.register(server_socket, zmq.POLLIN)
    logging.info('Starting server at %s...', address)
    while not quit_event.is_set():
        socks = poller.poll(EXTERNAL_IPC_POLL)
        if socks:
            for sock, _ in socks:
                try:
                    request = json.loads(sock.recv().decode('utf-8'))
                    reply = None
                    if request['method'] == 'ping':
                        reply = 'pong'
                    elif request['method'] == 'encode':
                        if request['type'] is not None and request['type'] not in ('audio', 'video'):
                            raise ValueError('Incorrect keepStreams option value')
                        if not os.path.isfile(os.path.join(DOWNLOADS_LOCATION, request['input'])):
                            raise IOError('Source not found')
                        worker.add_task(
                            request['input'],
                            request['output'],
                            request['type'],
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
    logging.info('Server stopped')
    worker.shutdown()
    logging.info('Worker stopped')
