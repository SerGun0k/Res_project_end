"""create initial tables

Revision ID: 001_initial
Revises: 
Create Date: 2026-04-09

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Создание всех таблиц"""

    # products
    op.create_table(
        'products',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('brand', sa.String(100), nullable=False),
        sa.Column('model', sa.String(200), nullable=False),
        sa.Column('specs', sa.JSON(), nullable=True),
        sa.Column('release_date', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('category', 'brand', 'model', name='uq_product_cat_brand_model'),
    )
    op.create_index('ix_products_category', 'products', ['category'])
    op.create_index('ix_products_brand', 'products', ['brand'])

    # price_history
    op.create_table(
        'price_history',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('product_id', sa.Integer(), sa.ForeignKey('products.id'), nullable=False),
        sa.Column('source', sa.String(100), nullable=False),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('date', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_price_history_product_id', 'price_history', ['product_id'])
    op.create_index('ix_price_history_date', 'price_history', ['date'])

    # cost_estimates
    op.create_table(
        'cost_estimates',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('product_id', sa.Integer(), sa.ForeignKey('products.id'), nullable=False, unique=True),
        sa.Column('materials_cost', sa.Float(), nullable=False, comment='Стоимость материалов'),
        sa.Column('logistics_cost', sa.Float(), nullable=False, comment='Логистика и таможня'),
        sa.Column('labor_cost', sa.Float(), nullable=False, comment='Сборка и тестирование'),
        sa.Column('total', sa.Float(), nullable=False, comment='Итоговая себестоимость'),
        sa.Column('last_updated', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # reviews_quality
    op.create_table(
        'reviews_quality',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('product_id', sa.Integer(), sa.ForeignKey('products.id'), nullable=False, unique=True),
        sa.Column('avg_rating', sa.Float(), nullable=True, comment='Средний рейтинг'),
        sa.Column('defect_rate', sa.Float(), nullable=True, comment='Процент брака'),
        sa.Column('reviews_count', sa.Integer(), nullable=True, comment='Количество отзывов'),
        sa.Column('source', sa.String(100), nullable=True, comment='Источник отзывов'),
        sa.Column('last_updated', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # popularity_stats
    op.create_table(
        'popularity_stats',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('product_id', sa.Integer(), sa.ForeignKey('products.id'), nullable=False, unique=True),
        sa.Column('daily_views', sa.Integer(), server_default='0', comment='Просмотры за день'),
        sa.Column('total_views', sa.Integer(), server_default='0', comment='Всего просмотров'),
        sa.Column('daily_searches', sa.Integer(), server_default='0', comment='Поисковые запросы за день'),
        sa.Column('last_updated', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )


def downgrade() -> None:
    """Удаление всех таблиц"""
    op.drop_table('popularity_stats')
    op.drop_table('reviews_quality')
    op.drop_table('cost_estimates')
    op.drop_table('price_history')
    op.drop_table('products')
