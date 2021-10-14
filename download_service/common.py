from enum import IntEnum
import typing


class TaskStatus(IntEnum):
    INACTIVE = 0
    WAITING = 0
    WORKING = 1
    COMPLETED = 2
    FAILED = 3


class IPCType(IntEnum):
    ADD = 0
    PROGRESS = 1
    STATUS = 2
    REMOVE_TASK = 3


class IPCMessage(object):
    def __init__(self, message_type: IPCType, subject: str, data: typing.Any=None) -> None:
        self.message_type = message_type # type: IPCType
        self.subject = subject # type: str
        self.data = data # type: typing.Any

    def __str__(self) -> str:
        return '<IPCMessage: {} {} {}>'.format(self.message_type, self.subject, self.data)

