"""Create tables download_videos,videos,records, source_files

Revision ID: 80a0a91c6342
Revises: 
Create Date: 2021-10-14 13:14:47.137583

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '80a0a91c6342'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('download_videos',
    sa.Column('video_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('link', sa.String(), nullable=False),
    sa.Column('title', sa.String(), nullable=True),
    sa.Column('quality', sa.String(), nullable=True),
    sa.Column('task_begin', sa.DateTime(), nullable=True),
    sa.Column('task_end', sa.DateTime(), nullable=True),
    sa.Column('status', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('video_id')
    )
    op.create_table('source_videos',
    sa.Column('filename', sa.String(), nullable=False),
    sa.Column('title', sa.String(), nullable=False),
    sa.Column('status', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('filename')
    )
    op.create_table('videos',
    sa.Column('output_filename', sa.String(), nullable=False),
    sa.Column('source', sa.String(), nullable=False),
    sa.Column('task_begin', sa.DateTime(), nullable=True),
    sa.Column('task_end', sa.DateTime(), nullable=True),
    sa.Column('status', sa.Integer(), nullable=False),
    sa.Column('progress', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('output_filename')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('videos')
    op.drop_table('source_videos')
    op.drop_table('download_videos')
    # ### end Alembic commands ###
