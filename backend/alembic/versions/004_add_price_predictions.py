"""add price predictions table

Revision ID: 004
Revises: 003
Create Date: 2026-04-10
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '004_add_price_predictions'
down_revision: Union[str, None] = '003_add_subcategory'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'price_predictions',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('product_id', sa.Integer(), sa.ForeignKey('products.id'), nullable=False, unique=True),
        sa.Column('current_price', sa.Float(), nullable=False),
        sa.Column('predicted_1m', sa.Float(), nullable=True),
        sa.Column('predicted_3m', sa.Float(), nullable=True),
        sa.Column('trend', sa.String(20), nullable=True),
        sa.Column('recommendation', sa.String(50), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('last_updated', sa.DateTime(), default=sa.func.utcnow()),
    )
    op.create_index(op.f('ix_price_predictions_product_id'), 'price_predictions', ['product_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_price_predictions_product_id'), table_name='price_predictions')
    op.drop_table('price_predictions')
