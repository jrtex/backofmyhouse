"""Add ai_usage_logs table

Revision ID: 004
Revises: 003
Create Date: 2026-02-14 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'ai_usage_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('provider', sa.String(20), nullable=False),
        sa.Column('model', sa.String(100), nullable=False),
        sa.Column('input_type', sa.String(20), nullable=False),
        sa.Column('input_tokens', sa.Integer(), nullable=True),
        sa.Column('output_tokens', sa.Integer(), nullable=True),
        sa.Column('total_tokens', sa.Integer(), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
    )
    op.create_index(op.f('ix_ai_usage_logs_user_id'), 'ai_usage_logs', ['user_id'])
    op.create_index(op.f('ix_ai_usage_logs_provider'), 'ai_usage_logs', ['provider'])
    op.create_index(op.f('ix_ai_usage_logs_created_at'), 'ai_usage_logs', ['created_at'])


def downgrade() -> None:
    op.drop_index(op.f('ix_ai_usage_logs_created_at'), table_name='ai_usage_logs')
    op.drop_index(op.f('ix_ai_usage_logs_provider'), table_name='ai_usage_logs')
    op.drop_index(op.f('ix_ai_usage_logs_user_id'), table_name='ai_usage_logs')
    op.drop_table('ai_usage_logs')
