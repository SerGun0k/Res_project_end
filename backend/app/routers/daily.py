"""Роутер товаров дня (топ по популярности)"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.models import Product, PriceHistory, PopularityStats
from app.schemas import DailyProductsResponse, DailyProductItem, ProductRead

router = APIRouter()


@router.post("/track-view/{product_id}", status_code=200)
async def track_product_view(
    product_id: int,
    db: Session = Depends(get_db),
):
    """
    Отслеживание просмотра товара.
    Увеличивает daily_views и total_views на 1.
    """
    stats = db.query(PopularityStats).filter(
        PopularityStats.product_id == product_id
    ).first()

    if not stats:
        # Создаём запись если нет
        stats = PopularityStats(
            product_id=product_id,
            daily_views=1,
            total_views=1,
            daily_searches=0,
        )
        db.add(stats)
    else:
        stats.daily_views += 1
        stats.total_views += 1

    db.commit()
    return {"message": "View tracked", "daily_views": stats.daily_views, "total_views": stats.total_views}


@router.get("/daily", response_model=DailyProductsResponse)
async def get_daily_products(
    top_n: int = Query(5, ge=1, le=20, description="Количество товаров"),
    db: Session = Depends(get_db),
):
    """
    Товары дня — топ-N по количеству просмотров за день.
    В продакшене данные берутся из Redis, здесь — из БД.
    """
    # Получаем топ-N по daily_views
    popular_stats = (
        db.query(PopularityStats)
        .order_by(desc(PopularityStats.daily_views))
        .limit(top_n)
        .all()
    )

    products = []
    for stats in popular_stats:
        product = db.query(Product).filter(Product.id == stats.product_id).first()
        if not product:
            continue

        # Средняя цена
        avg_price = _get_avg_price(db, product.id)

        products.append(DailyProductItem(
            product=ProductRead(
                id=product.id,
                category=product.category,
                brand=product.brand,
                model=product.model,
                specs=product.specs,
                release_date=product.release_date,
                created_at=product.created_at,
                updated_at=product.updated_at,
            ),
            daily_views=stats.daily_views,
            avg_price=round(avg_price, 2) if avg_price else 0,
        ))

    return DailyProductsResponse(
        date=datetime.utcnow().strftime("%Y-%m-%d"),
        products=products,
    )


def _get_avg_price(db: Session, product_id: int) -> Optional[float]:
    """Средняя цена из истории"""
    prices = db.query(PriceHistory.price).filter(
        PriceHistory.product_id == product_id
    ).all()

    if not prices:
        return None

    price_list = [p[0] for p in prices]
    return sum(price_list) / len(price_list)
