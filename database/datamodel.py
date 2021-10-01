import datetime
import uuid
from typing import List, Union, Tuple, Dict, Mapping, Any, Optional
from sqlalchemy import Table, MetaData, Column, Integer, Numeric, String, Text, DateTime, Boolean, ForeignKeyConstraint
from sqlalchemy.dialects.postgresql import UUID

metadata = MetaData()


records = Table('records', metadata,
    Column('video_id', UUID(as_uuid=True), nullable=False, primary_key=True),
    Column('output_name', Text, nullable=True)
)

