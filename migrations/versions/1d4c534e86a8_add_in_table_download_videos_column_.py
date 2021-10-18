"""Add in table download_videos column filename

Revision ID: 1d4c534e86a8
Revises: 80a0a91c6342
Create Date: 2021-10-15 15:48:34.737514

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1d4c534e86a8'
down_revision = '80a0a91c6342'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('download_videos', sa.Column('filename', sa.String(), nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('download_videos', 'filename')
    # ### end Alembic commands ###
