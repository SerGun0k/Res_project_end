"""add target price fields to price predictions

Revision ID: 006
Revises: 005
Create Date: 2026-05-13
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '006_add_target_price_fields'
down_revision: Union[str, None] = '005_add_feedback_and_behavior'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('price_predictions', sa.Column('target_price', sa.Float(), nullable=True))
    op.add_column('price_predictions', sa.Column('price_gap_pct', sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column('price_predictions', 'price_gap_pct')
    op.drop_column('price_predictions', 'target_price')
