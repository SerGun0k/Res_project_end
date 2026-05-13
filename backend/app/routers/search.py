"""Роутер поиска товаров"""

from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from app.database import get_db
from app.models import Product, PriceHistory, CostEstimate
from app.schemas import SearchParams, SearchResult, ProductWithMarkup
from app.markup_utils import (
    get_brand_factor,
    calculate_weighted_factor,
    calculate_adjusted_markup,
    get_markup_status,
)
from app.config import settings

router = APIRouter()


@router.get("/search", response_model=SearchResult)
async def search_products(
    query: str = Query(..., min_length=1, description="Поисковый запрос"),
    category: Optional[str] = Query(None, description="Фильтр по категории"),
    subcategory: Optional[str] = Query(None, description="Фильтр по подкатегории"),
    brand: Optional[str] = Query(None, description="Фильтр по бренду"),
    min_price: Optional[float] = Query(None, description="Минимальная цена"),
    max_price: Optional[float] = Query(None, description="Максимальная цена"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Поиск товаров по названию, бренду и категории.
    Возвращает результаты с расчётом наценки.
    """
    # Базовый запрос
    search_pattern = f"%{query}%"
    stmt = db.query(Product).filter(
        or_(
            Product.model.ilike(search_pattern),
            Product.brand.ilike(search_pattern),
            Product.category.ilike(search_pattern),
        )
    )

    # Фильтры
    if category:
        stmt = stmt.filter(Product.category == category)
    if subcategory:
        stmt = stmt.filter(Product.subcategory == subcategory)
    if brand:
        stmt = stmt.filter(Product.brand == brand)

    # Подсчёт общего количества
    total = stmt.count()

    # Пагинация
    offset = (page - 1) * per_page
    products = stmt.offset(offset).limit(per_page).all()

    # Формируем результаты с наценкой
    items = []
    for product in products:
        # Средняя рыночная цена (медиана из price_history)
        median_price = _get_median_price(db, product.id)

        # Себестоимость
        cost = db.query(CostEstimate).filter(
            CostEstimate.product_id == product.id
        ).first()

        # Расчёт наценки
        markup_percent = None
        adjusted_markup = None
        markup_status = None

        if median_price and cost and cost.total > 0:
            markup_percent = round((median_price - cost.total) / cost.total * 100, 2)

            # Реальные факторы
            brand_factor = get_brand_factor(product.brand)

            quality_factor = 1.0
            if product.review_quality and product.review_quality.avg_rating:
                quality_factor = product.review_quality.avg_rating / 5.0

            relevance_factor = 1.0  # Будет пересчитан в alternatives

            popularity_factor = 1.0
            if product.popularity_stats and product.popularity_stats.daily_views:
                popularity_factor = min(product.popularity_stats.daily_views / 300, 2.0)

            weighted_factor = calculate_weighted_factor(
                brand_factor, quality_factor, relevance_factor, popularity_factor
            )

            adjusted_markup = calculate_adjusted_markup(markup_percent, weighted_factor)
            markup_status = get_markup_status(adjusted_markup)

        items.append(ProductWithMarkup(
            **_product_to_dict(product),
            price_history=[],
            cost_estimate=None,
            review_quality=None,
            popularity_stats=None,
            market_price=median_price,
            markup_percent=markup_percent,
            adjusted_markup=adjusted_markup,
            markup_status=markup_status,
        ))

    # Фильтрация по цене (после расчёта рыночной цены)
    if min_price is not None:
        items = [i for i in items if i.market_price and i.market_price >= min_price]
    if max_price is not None:
        items = [i for i in items if i.market_price and i.market_price <= max_price]

    return SearchResult(
        total=len(items),
        page=page,
        per_page=per_page,
        items=items,
    )


def _get_median_price(db: Session, product_id: int) -> Optional[float]:
    """Получение медианной цены из истории"""
    prices = db.query(PriceHistory.price).filter(
        PriceHistory.product_id == product_id
    ).order_by(PriceHistory.price).all()

    if not prices:
        return None

    price_list = [p[0] for p in prices]
    n = len(price_list)

    # Отсечение выбросов (квантили 5-95%)
    if n > 4:
        q5_idx = max(0, int(n * 0.05))
        q95_idx = min(n - 1, int(n * 0.95))
        price_list = price_list[q5_idx:q95_idx + 1]

    # Медиана
    mid = len(price_list) // 2
    if len(price_list) % 2 == 0:
        return (price_list[mid - 1] + price_list[mid]) / 2
    else:
        return price_list[mid]


def _product_to_dict(product: Product) -> dict:
    return {
        "id": product.id,
        "category": product.category,
        "subcategory": product.subcategory,
        "brand": product.brand,
        "model": product.model,
        "specs": product.specs,
        "release_date": product.release_date,
        "created_at": product.created_at,
        "updated_at": product.updated_at,
    }
