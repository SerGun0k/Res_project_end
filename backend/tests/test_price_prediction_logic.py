from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base, Product, PriceHistory, CostEstimate
from app.price_prediction import calculate_price_prediction, build_recommendation_reason


def _setup_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def _seed_product_with_prices(db, prices):
    product = Product(category="GPU", brand="NVIDIA", model="RTX Test", specs={})
    db.add(product)
    db.commit()
    db.refresh(product)

    base_date = datetime(2026, 1, 1)
    for idx, price in enumerate(prices):
        db.add(
            PriceHistory(
                product_id=product.id,
                source="test",
                price=price,
                date=base_date + timedelta(days=idx * 7),
            )
        )

    db.commit()
    return product


def test_prediction_includes_target_fields_and_valid_values():
    db = _setup_db()
    product = _seed_product_with_prices(db, [30000, 30200, 30400, 30600, 30800, 31000])
    db.add(CostEstimate(product_id=product.id, materials_cost=18000, logistics_cost=2000, labor_cost=1000, total=21000))
    db.commit()

    result = calculate_price_prediction(db, product.id)

    assert result is not None
    assert "target_price" in result
    assert "price_gap_pct" in result
    assert result["target_price"] > 0
    assert isinstance(result["price_gap_pct"], float)


def test_recommendation_buy_now_when_trend_rising():
    db = _setup_db()
    product = _seed_product_with_prices(db, [43000, 43500, 44000, 44600, 45200, 46000])
    db.add(CostEstimate(product_id=product.id, materials_cost=22000, logistics_cost=3000, labor_cost=2000, total=27000))
    db.commit()

    result = calculate_price_prediction(db, product.id)

    assert result is not None
    assert result["trend"] == "rising"
    assert result["recommendation"] == "buy_now"


def test_prediction_requires_enough_data_points():
    db = _setup_db()
    product = _seed_product_with_prices(db, [30000, 30100])

    result = calculate_price_prediction(db, product.id)

    assert result is None


def test_recommendation_reason_contains_target_price_context():
    reason = build_recommendation_reason(
        recommendation="buy_now",
        trend="rising",
        current_price=45000,
        target_price=44000,
        price_gap_pct=2.27,
    )
    assert "целевая" in reason
    assert "rising" in reason
