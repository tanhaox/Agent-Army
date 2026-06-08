"""add_assets_table

Revision ID: c5424ebbe6b4
Revises: 68ca99e69ca4
Create Date: 2026-05-02 11:51:26.897722

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c5424ebbe6b4'
down_revision: Union[str, Sequence[str], None] = '68ca99e69ca4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('assets',
        sa.Column('id', sa.String(length=36), server_default=sa.text("gen_random_uuid()::text"), nullable=False),
        sa.Column('task_id', sa.String(length=36), nullable=False),
        sa.Column('anchor_name', sa.String(length=200), server_default=sa.text("''::character varying"), nullable=False),
        sa.Column('video_title', sa.String(length=500), server_default=sa.text("''::character varying"), nullable=False),
        sa.Column('asset_type', sa.Enum('video', 'audio', 'transcript', name='asset_type_enum'), nullable=False),
        sa.Column('file_path', sa.String(length=1000), server_default=sa.text("''::character varying"), nullable=False),
        sa.Column('file_size', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('duration', sa.Float(precision=53), server_default=sa.text('0.0'), nullable=False),
        sa.Column('transcription_text', sa.Text(), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_assets_task_id', 'assets', ['task_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('assets')
    op.execute("DROP TYPE IF EXISTS asset_type_enum")
