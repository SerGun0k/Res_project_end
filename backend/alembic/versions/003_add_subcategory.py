"""add subcategory to products

Revision ID: 003_add_subcategory
Revises: 002_cascade_delete
Create Date: 2026-04-10
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '003_add_subcategory'
down_revision: Union[str, None] = '002_cascade_delete'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('products', sa.Column('subcategory', sa.String(length=50), nullable=True))
    op.create_index(op.f('ix_products_subcategory'), 'products', ['subcategory'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_products_subcategory'), table_name='products')
    op.drop_column('products', 'subcategory')
