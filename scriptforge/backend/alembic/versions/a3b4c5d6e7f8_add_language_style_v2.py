"""Add language_style_v2 to persona

Revision ID: a3b4c5d6e7f8
Revises: b2c3d4e5f6a7
Create Date: 2026-05-02
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

revision = "a3b4c5d6e7f8"
down_revision = "b2c3d4e5f6a7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("personas", sa.Column("language_style_v2", JSON, nullable=True))


def downgrade() -> None:
    op.drop_column("personas", "language_style_v2")
