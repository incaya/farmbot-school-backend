"""Add create and update dates on each table

Revision ID: 3116425a9f9d
Revises: b1b8b93e81c5
Create Date: 2021-08-31 15:19:24.784814

"""
from alembic import op
import sqlalchemy as sa
import datetime

# revision identifiers, used by Alembic.
revision = '3116425a9f9d'
down_revision = 'b1b8b93e81c5'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('challenge', sa.Column('created_at', sa.DateTime(), nullable=False))
    op.add_column('challenge', sa.Column('updated_at', sa.DateTime(), nullable=False))
    op.add_column('pin', sa.Column('created_at', sa.DateTime(), nullable=False))
    op.add_column('pin', sa.Column('updated_at', sa.DateTime(), nullable=False))
    op.add_column('sequence', sa.Column('created_at', sa.DateTime(), nullable=False))
    op.add_column('sequence', sa.Column('updated_at', sa.DateTime(), nullable=False))
    op.add_column('user', sa.Column('created_at', sa.DateTime(), nullable=False))
    op.add_column('user', sa.Column('updated_at', sa.DateTime(), nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user', 'updated_at')
    op.drop_column('user', 'created_at')
    op.drop_column('sequence', 'updated_at')
    op.drop_column('sequence', 'created_at')
    op.drop_column('pin', 'updated_at')
    op.drop_column('pin', 'created_at')
    op.drop_column('challenge', 'updated_at')
    op.drop_column('challenge', 'created_at')
    # ### end Alembic commands ###