"""add user feedback and behavior tables

Revision ID: 005
Revises: 004
Create Date: 2026-04-10
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '005_add_feedback_and_behavior'
down_revision: Union[str, None] = '004_add_price_predictions'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'user_feedback',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_session', sa.String(100), nullable=False),
        sa.Column('product_id', sa.Integer(), sa.ForeignKey('products.id'), nullable=False),
        sa.Column('feedback_type', sa.String(20), nullable=False),
        sa.Column('alternative_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.utcnow()),
    )
    op.create_index(op.f('ix_user_feedback_user_session'), 'user_feedback', ['user_session'], unique=False)
    op.create_index(op.f('ix_user_feedback_product_id'), 'user_feedback', ['product_id'], unique=False)
    op.create_index(op.f('ix_user_feedback_created_at'), 'user_feedback', ['created_at'], unique=False)

    op.create_table(
        'user_behavior',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_session', sa.String(100), nullable=False),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('search_query', sa.String(200), nullable=True),
        sa.Column('product_id', sa.Integer(), sa.ForeignKey('products.id'), nullable=True),
        sa.Column('target_product_id', sa.Integer(), nullable=True),
        sa.Column('category', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.utcnow()),
    )
    op.create_index(op.f('ix_user_behavior_user_session'), 'user_behavior', ['user_session'], unique=False)
    op.create_index(op.f('ix_user_behavior_action'), 'user_behavior', ['action'], unique=False)
    op.create_index(op.f('ix_user_behavior_created_at'), 'user_behavior', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_user_behavior_created_at'), table_name='user_behavior')
    op.drop_index(op.f('ix_user_behavior_action'), table_name='user_behavior')
    op.drop_index(op.f('ix_user_behavior_user_session'), table_name='user_behavior')
    op.drop_table('user_behavior')
    op.drop_index(op.f('ix_user_feedback_created_at'), table_name='user_feedback')
    op.drop_index(op.f('ix_user_feedback_product_id'), table_name='user_feedback')
    op.drop_index(op.f('ix_user_feedback_user_session'), table_name='user_feedback')
    op.drop_table('user_feedback')
