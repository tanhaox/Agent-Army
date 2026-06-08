"""add_task_records_table

Revision ID: f9a1b2c3d4e5
Revises: c5424ebbe6b4
Create Date: 2026-05-02 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f9a1b2c3d4e5'
down_revision: Union[str, Sequence[str], None] = 'd7a1f3e8b2c5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'task_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('task_id', sa.String(36), unique=True, nullable=False),
        sa.Column('trigger', sa.String(20), nullable=False, server_default='stream'),
        sa.Column('url', sa.String(1000), nullable=False, server_default=''),
        sa.Column('anchor_name', sa.String(200), nullable=False, server_default=''),
        sa.Column('anchor_avatar', sa.String(500), nullable=True),
        sa.Column('follower_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(20), nullable=False, server_default='running'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('video_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('downloaded_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('transcribed_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('persona_id', sa.String(36), nullable=True),
        sa.Column('persona_name', sa.String(100), nullable=True),
        sa.Column('result_summary', postgresql.JSON(), nullable=True),
    )
    op.create_index('ix_task_records_task_id', 'task_records', ['task_id'], unique=True)
    op.create_index('ix_task_records_status', 'task_records', ['status'])
    op.create_index('ix_task_records_persona_id', 'task_records', ['persona_id'])


def downgrade() -> None:
    op.drop_index('ix_task_records_persona_id')
    op.drop_index('ix_task_records_status')
    op.drop_index('ix_task_records_task_id')
    op.drop_table('task_records')
