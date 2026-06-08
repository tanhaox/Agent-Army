"""add_is_template_to_persona

Revision ID: d7a1f3e8b2c5
Revises: c5424ebbe6b4
Create Date: 2026-05-02 14:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'd7a1f3e8b2c5'
down_revision: Union[str, None] = 'c5424ebbe6b4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('personas', sa.Column('is_template', sa.Boolean(), nullable=True, server_default='false'))


def downgrade() -> None:
    op.drop_column('personas', 'is_template')
