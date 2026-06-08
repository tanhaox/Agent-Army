"""add_source_tracing_to_persona

Revision ID: a1b2c3d4e5f6
Revises: f9a1b2c3d4e5
Create Date: 2026-05-02 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'f9a1b2c3d4e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('personas', sa.Column('source_anchor_name', sa.String(200), nullable=True))
    op.add_column('personas', sa.Column('source_anchor_id', sa.String(100), nullable=True))
    op.add_column('personas', sa.Column('source_homepage_url', sa.String(500), nullable=True))


def downgrade() -> None:
    op.drop_column('personas', 'source_homepage_url')
    op.drop_column('personas', 'source_anchor_id')
    op.drop_column('personas', 'source_anchor_name')
