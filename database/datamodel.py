import typing
from sqlalchemy import MetaData, Table, Text, Column, String, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
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


download_videos = Table('download_videos', metadata,
    Column('video_id', UUID(as_uuid=True), nullable=False, primary_key=True),
    Column('filename', String, nullable=False),
    Column('link', String, nullable=False),
    Column('title', String, nullable=True),
    Column('quality', String, nullable=True, default='default'),
    Column('task_begin', DateTime, nullable=True),
    Column('task_end', DateTime, nullable=True),
    Column('status', Integer, nullable=False, default=TaskStatus.INACTIVE),
)