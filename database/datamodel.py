import datetime
import uuid
from typing import List, Union, Tuple, Dict, Mapping, Any, Optional
from enum import IntEnum
from sqlalchemy import Table, MetaData, Column, Integer, Numeric, String, Text, DateTime, Boolean, ForeignKeyConstraint
from sqlalchemy.dialects.postgresql import UUID

metadata = MetaData()


class VideoStatus(IntEnum):
    PENDING = 0
    PROCESSING = 1
    COMPLETED = 2
    FAILED = 3

records = Table('records', metadata,
    Column('video_id', UUID(as_uuid=True), nullable=False, primary_key=True),
    Column('output_name', Text, nullable=True)
)


def add_video(dbe: Any, filename: str) -> None:
    video_id = uuid.uuid4()
    dbe.execute(records.insert().values(
        video_id=video_id,
        output_name=filename
    ))

