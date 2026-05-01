"""add narrative_style to persona

Revision ID: a8c3e2f1d09b
Revises: 5ba3bd4ff241
Create Date: 2026-04-25 23:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a8c3e2f1d09b'
down_revision: Union[str, Sequence[str], None] = '5ba3bd4ff241'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE personas ADD COLUMN IF NOT EXISTS narrative_style JSON DEFAULT NULL"
    )


def downgrade() -> None:
    op.drop_column('personas', 'narrative_style')
