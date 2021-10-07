from sqlalchemy import MetaData, Table, Column, String, Integer
from processing_service.common import TaskStatus
metadata = MetaData()

videos = Table('videos', metadata,
    Column('output_filename', String, nullable=False, primary_key=True),
    Column('source', String, nullable=False),
    Column('status', Integer, nullable=False, default=TaskStatus.WAITING),
    Column('progress', Integer, default=0)
)

uploads = Table('source_videos', metadata,
    Column('filename', String, nullable=False, primary_key=True),
    Column('title', String, nullable=False),
    Column('status', Integer, nullable=False)
)