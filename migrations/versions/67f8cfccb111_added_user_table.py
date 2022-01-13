"""Added user table

Revision ID: 67f8cfccb111
Revises: 188cb8e2a3a6
Create Date: 2022-01-13 15:13:14.565492

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '67f8cfccb111'
down_revision = '188cb8e2a3a6'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('source_videos')
    op.add_column('records', sa.Column('output_filename', sa.String(), nullable=False))
    op.add_column('records', sa.Column('title', sa.String(), nullable=True))
    op.add_column('records', sa.Column('type', sa.String(), nullable=False))
    op.add_column('records', sa.Column('source', sa.String(), nullable=False))
    op.add_column('records', sa.Column('status', sa.Integer(), nullable=False))
    op.add_column('records', sa.Column('task_begin', sa.DateTime(), nullable=True))
    op.add_column('records', sa.Column('task_end', sa.DateTime(), nullable=True))
    op.add_column('records', sa.Column('progress', sa.Integer(), nullable=True))
    op.drop_column('records', 'output_name')
    op.drop_column('records', 'video_id')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('records', sa.Column('video_id', postgresql.UUID(), autoincrement=False, nullable=False))
    op.add_column('records', sa.Column('output_name', sa.TEXT(), autoincrement=False, nullable=True))
    op.drop_column('records', 'progress')
    op.drop_column('records', 'task_end')
    op.drop_column('records', 'task_begin')
    op.drop_column('records', 'status')
    op.drop_column('records', 'source')
    op.drop_column('records', 'type')
    op.drop_column('records', 'title')
    op.drop_column('records', 'output_filename')
    op.create_table('source_videos',
    sa.Column('filename', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('title', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('status', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('filename', name='source_videos_pkey')
    )
    # ### end Alembic commands ###
