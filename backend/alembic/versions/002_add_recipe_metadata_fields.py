"""Add recipe metadata fields

Revision ID: 002
Revises: 001
Create Date: 2025-01-26 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create the complexity enum type
    complexity_enum = sa.Enum(
        'very_easy', 'easy', 'medium', 'hard', 'very_hard',
        name='recipecomplexity'
    )
    complexity_enum.create(op.get_bind(), checkfirst=True)

    # Add new columns to recipes table
    op.add_column('recipes', sa.Column('complexity',
        sa.Enum('very_easy', 'easy', 'medium', 'hard', 'very_hard', name='recipecomplexity'),
        nullable=True))
    op.add_column('recipes', sa.Column('special_equipment',
        postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column('recipes', sa.Column('source_author', sa.String(255), nullable=True))
    op.add_column('recipes', sa.Column('source_url', sa.String(2048), nullable=True))


def downgrade() -> None:
    op.drop_column('recipes', 'source_url')
    op.drop_column('recipes', 'source_author')
    op.drop_column('recipes', 'special_equipment')
    op.drop_column('recipes', 'complexity')
    op.execute('DROP TYPE IF EXISTS recipecomplexity')
