"""Added column filesize in download videos

Revision ID: 4e7a7bb8bfd7
Revises:
Create Date: 2021-11-17 15:00:11.852009

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4e7a7bb8bfd7'
down_revision = 'ef7804b7aad7'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('download_videos', sa.Column('filesize', sa.BigInteger(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('download_videos', 'filesize')
    # ### end Alembic commands ###
