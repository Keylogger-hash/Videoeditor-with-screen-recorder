"""empty message

Revision ID: 237a4f6df3cd
Revises: 
Create Date: 2021-10-01 15:51:44.479248

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '237a4f6df3cd'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('records',
    sa.Column('video_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('output_name', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('video_id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('records')
    # ### end Alembic commands ###
