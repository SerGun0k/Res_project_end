"""add cascade delete on product relationships

Revision ID: 002_cascade_delete
Revises: 001_initial
Create Date: 2026-04-10

"""
from typing import Sequence, Union

from alembic import op


revision: str = '002_cascade_delete'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # PostgreSQL: добавляем ON DELETE CASCADE на внешние ключи
    op.drop_constraint('price_history_product_id_fkey', 'price_history', type_='foreignkey')
    op.create_foreign_key(None, 'price_history', 'products', ['product_id'], ['id'], ondelete='CASCADE')

    op.drop_constraint('cost_estimates_product_id_fkey', 'cost_estimates', type_='foreignkey')
    op.create_foreign_key(None, 'cost_estimates', 'products', ['product_id'], ['id'], ondelete='CASCADE')

    op.drop_constraint('reviews_quality_product_id_fkey', 'reviews_quality', type_='foreignkey')
    op.create_foreign_key(None, 'reviews_quality', 'products', ['product_id'], ['id'], ondelete='CASCADE')

    op.drop_constraint('popularity_stats_product_id_fkey', 'popularity_stats', type_='foreignkey')
    op.create_foreign_key(None, 'popularity_stats', 'products', ['product_id'], ['id'], ondelete='CASCADE')


def downgrade() -> None:
    op.drop_constraint('popularity_stats_product_id_fkey', 'popularity_stats', type_='foreignkey')
    op.create_foreign_key('popularity_stats_product_id_fkey', 'popularity_stats', 'products', ['product_id'], ['id'])

    op.drop_constraint('reviews_quality_product_id_fkey', 'reviews_quality', type_='foreignkey')
    op.create_foreign_key('reviews_quality_product_id_fkey', 'reviews_quality', 'products', ['product_id'], ['id'])

    op.drop_constraint('cost_estimates_product_id_fkey', 'cost_estimates', type_='foreignkey')
    op.create_foreign_key('cost_estimates_product_id_fkey', 'cost_estimates', 'products', ['product_id'], ['id'])

    op.drop_constraint('price_history_product_id_fkey', 'price_history', type_='foreignkey')
    op.create_foreign_key('price_history_product_id_fkey', 'price_history', 'products', ['product_id'], ['id'])
