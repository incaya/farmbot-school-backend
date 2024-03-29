"""add sequence table

Revision ID: 515dc4055d63
Revises: 226dde11a138
Create Date: 2021-01-28 14:53:00.618099

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '515dc4055d63'
down_revision = '226dde11a138'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('sequence',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('challenge_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('status', sa.Enum('WIP', 'TO_PROCESS', 'PROCESS_WIP', 'PROCESSED', name='sequencestatus'), nullable=False),
    sa.ForeignKeyConstraint(['challenge_id'], ['challenge.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('sequence')
    # ### end Alembic commands ###
