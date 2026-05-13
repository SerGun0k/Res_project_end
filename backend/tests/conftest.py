import pytest
import sys
import os

# Добавляем backend в path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.database import SessionLocal, engine, Base
from app.models import Product, PriceHistory, CostEstimate, ReviewQuality, PopularityStats


@pytest.fixture
def db_session():
    """Фикстура для тестовой сессии БД"""
    # Создаём таблицы для тестов
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def sample_product(db_session):
    """Фикстура: тестовый товар"""
    product = Product(
        category="GPU",
        brand="NVIDIA",
        model="Test GPU",
        specs={"memory_gb": 8, "tdp_watts": 150},
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product


@pytest.fixture
def sample_cost_estimate(db_session, sample_product):
    """Фикстура: себестоимость для тестового товара"""
    cost = CostEstimate(
        product_id=sample_product.id,
        materials_cost=10000,
        logistics_cost=3000,
        labor_cost=2000,
        total=15000,
    )
    db_session.add(cost)
    db_session.commit()
    return cost


@pytest.fixture
def sample_price_history(db_session, sample_product):
    """Фикстура: история цен для тестового товара"""
    prices = [
        PriceHistory(product_id=sample_product.id, source="DNS", price=30000, date="2026-01-01"),
        PriceHistory(product_id=sample_product.id, source="DNS", price=32000, date="2026-02-01"),
        PriceHistory(product_id=sample_product.id, source="Ozon", price=31000, date="2026-01-15"),
        PriceHistory(product_id=sample_product.id, source="Ozon", price=33000, date="2026-02-15"),
    ]
    db_session.add_all(prices)
    db_session.commit()
    return prices
