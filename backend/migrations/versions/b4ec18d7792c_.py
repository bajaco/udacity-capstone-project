"""empty message

Revision ID: b4ec18d7792c
Revises: d6bb7ce4cb39
Create Date: 2020-10-29 01:21:11.482309

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b4ec18d7792c'
down_revision = 'd6bb7ce4cb39'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('unpublished_tutorials', sa.Column('published', sa.Boolean(), nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('unpublished_tutorials', 'published')
    # ### end Alembic commands ###
