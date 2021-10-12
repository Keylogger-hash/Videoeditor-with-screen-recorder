import typing
import uuid
from sqlalchemy import MetaData, Table, Column, String, Integer, Text, DateTime
from processing_service.common import TaskStatus
from sqlalchemy.dialects.postgresql import UUID
metadata = MetaData()

videos = Table('videos', metadata,
    Column('output_filename', String, nullable=False, primary_key=True),
    Column('source', String, nullable=False),
    Column('task_begin', DateTime, nullable=True),
    Column('task_end', DateTime, nullable=True),
    Column('status', Integer, nullable=False, default=TaskStatus.INACTIVE),
    Column('progress', Integer, default=0)
)

records = Table('records', metadata,
    Column('video_id', UUID(as_uuid=True), nullable=False, primary_key=True),
    Column('output_name', Text, nullable=True)
)


def add_video(dbe: typing.Any, filename: str) -> None:
    video_id = uuid.uuid4()
    dbe.execute(records.insert().values(
        video_id=video_id,
        output_name=filename
    ))

