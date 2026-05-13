"""Тесты API эндпоинтов FastAPI"""

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.database import SessionLocal, Base, engine
from app.models import (
    Product,
    PriceHistory,
    CostEstimate,
    ReviewQuality,
    PopularityStats,
    PricePrediction,
    UserFeedback,
    UserBehavior,
)


@pytest.fixture(autouse=True)
def setup_db():
    """Создание и очистка БД для каждого теста"""
    Base.metadata.create_all(bind=engine)
    yield
    # Очистка в обратном порядке зависимостей
    db = SessionLocal()
    try:
        db.query(UserFeedback).delete()
        db.query(UserBehavior).delete()
        db.query(PricePrediction).delete()
        db.query(PopularityStats).delete()
        db.query(ReviewQuality).delete()
        db.query(PriceHistory).delete()
        db.query(CostEstimate).delete()
        db.query(Product).delete()
        db.commit()
    finally:
        db.close()


@pytest.fixture
def seed_data():
    """Фикстура: тестовые данные"""
    db = SessionLocal()
    try:
        # Продукт 1 - NVIDIA GPU
        p1 = Product(
            category="GPU", brand="NVIDIA", model="GeForce RTX 4060",
            specs={"memory_gb": 8, "tdp_watts": 115},
        )
        db.add(p1)
        db.flush()

        # Продукт 2 - AMD GPU (аналог)
        p2 = Product(
            category="GPU", brand="AMD", model="Radeon RX 7600",
            specs={"memory_gb": 8, "tdp_watts": 165},
        )
        db.add(p2)
        db.flush()

        # Цены
        db.add_all([
            PriceHistory(product_id=p1.id, source="DNS", price=40000),
            PriceHistory(product_id=p1.id, source="Ozon", price=42000),
            PriceHistory(product_id=p2.id, source="DNS", price=32000),
            PriceHistory(product_id=p2.id, source="Ozon", price=33000),
        ])

        # Себестоимость
        db.add_all([
            CostEstimate(product_id=p1.id, materials_cost=10000, logistics_cost=3000, labor_cost=2000, total=15000),
            CostEstimate(product_id=p2.id, materials_cost=8000, logistics_cost=2500, labor_cost=1500, total=12000),
        ])

        # Отзывы
        db.add_all([
            ReviewQuality(product_id=p1.id, avg_rating=4.5, defect_rate=2.0, reviews_count=100, source="DNS"),
            ReviewQuality(product_id=p2.id, avg_rating=4.0, defect_rate=3.0, reviews_count=80, source="Ozon"),
        ])

        # Популярность
        db.add_all([
            PopularityStats(product_id=p1.id, daily_views=500, total_views=15000, daily_searches=150),
            PopularityStats(product_id=p2.id, daily_views=300, total_views=9000, daily_searches=90),
        ])

        db.commit()
        return {"p1_id": p1.id, "p2_id": p2.id}
    finally:
        db.close()


@pytest.mark.asyncio
async def test_health():
    """GET /api/health"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/api/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_list_products(seed_data):
    """GET /api/v1/products/"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/api/v1/products/")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 2
    assert data[0]["category"] == "GPU"


@pytest.mark.asyncio
async def test_get_product(seed_data):
    """GET /api/v1/products/{id}"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get(f"/api/v1/products/{seed_data['p1_id']}")
    assert r.status_code == 200
    data = r.json()
    assert data["brand"] == "NVIDIA"
    assert len(data["price_history"]) == 2
    assert data["cost_estimate"]["total"] == 15000
    assert data["review_quality"]["avg_rating"] == 4.5


@pytest.mark.asyncio
async def test_get_product_not_found():
    """GET /api/v1/products/{id} — несуществующий"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/api/v1/products/9999")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_search(seed_data):
    """GET /api/v1/search?query=RTX"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/api/v1/search", params={"query": "RTX"})
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 1
    assert "NVIDIA" in data["items"][0]["brand"]
    assert data["items"][0]["markup_percent"] is not None
    assert data["items"][0]["markup_status"] in ("normal", "high")


@pytest.mark.asyncio
async def test_search_empty():
    """GET /api/v1/search — пустой результат"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/api/v1/search", params={"query": "nonexistent"})
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 0
    assert data["items"] == []


@pytest.mark.asyncio
async def test_alternatives(seed_data):
    """POST /api/v1/alternatives"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post("/api/v1/alternatives", json={
            "product_id": seed_data["p1_id"],
            "category": "GPU",
            "max_count": 3,
        })
    assert r.status_code == 200
    data = r.json()
    assert data["product_id"] == seed_data["p1_id"]
    assert data["category"] == "GPU"
    assert data["alternatives_count"] == 1
    assert data["alternatives"][0]["brand"] == "AMD"


@pytest.mark.asyncio
async def test_alternatives_not_found(seed_data):
    """POST /api/v1/alternatives — нет аналогов"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post("/api/v1/alternatives", json={
            "product_id": 9999,
            "category": "GPU",
            "max_count": 3,
        })
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_daily(seed_data):
    """GET /api/v1/daily"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/api/v1/daily")
    assert r.status_code == 200
    data = r.json()
    assert len(data["products"]) == 2
    # Сортировка по daily_views (убывание)
    assert data["products"][0]["daily_views"] >= data["products"][1]["daily_views"]


@pytest.mark.asyncio
async def test_create_product():
    """POST /api/v1/products/"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post("/api/v1/products/", json={
            "category": "SSD",
            "brand": "Samsung",
            "model": "980 PRO 1TB",
            "specs": {"capacity_gb": 1000},
        })
    assert r.status_code == 201
    data = r.json()
    assert data["brand"] == "Samsung"
    assert data["model"] == "980 PRO 1TB"


@pytest.mark.asyncio
async def test_create_duplicate(seed_data):
    """POST /api/v1/products/ — дубликат"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post("/api/v1/products/", json={
            "category": "GPU",
            "brand": "NVIDIA",
            "model": "GeForce RTX 4060",
        })
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_delete_product(seed_data):
    """DELETE /api/v1/products/{id}"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.delete(f"/api/v1/products/{seed_data['p2_id']}")
    assert r.status_code == 204
