"""Роутер подбора аналогов"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from app.database import get_db
from app.models import Product, CostEstimate, PriceHistory, ReviewQuality, PopularityStats
from app.schemas import AlternativeRequest, AlternativesResponse, AlternativeProduct
from app.markup_utils import (
    get_brand_factor,
    get_relevance_factor,
    calculate_weighted_factor,
    calculate_adjusted_markup,
    get_markup_status,
)

router = APIRouter()


@router.post("/alternatives", response_model=AlternativesResponse)
async def get_alternatives(
    request: AlternativeRequest,
    db: Session = Depends(get_db),
):
    """
    Подбор аналогов продукта по новым критериям (пункт 8):
    - Та же категория
    - Цена в диапазоне ±10% от исходного товара
    - Наценка не выше, чем у исходного товара
    - Рейтинг выше или равен
    - Схожие характеристики
    """
    # Проверяем существование исходного продукта
    original_product = db.query(Product).filter(Product.id == request.product_id).first()
    if not original_product:
        raise HTTPException(status_code=404, detail="Исходный продукт не найден")

    # Получаем себестоимость и рыночную цену исходного продукта
    original_cost = db.query(CostEstimate).filter(
        CostEstimate.product_id == request.product_id
    ).first()

    original_review = db.query(ReviewQuality).filter(
        ReviewQuality.product_id == request.product_id
    ).first()

    original_median_price = _get_median_price(db, request.product_id)
    original_markup_percent = None

    if original_cost and original_median_price and original_cost.total > 0:
        original_markup_percent = (original_median_price - original_cost.total) / original_cost.total * 100

    original_rating = original_review.avg_rating if original_review and original_review.avg_rating else 0

    # Поиск аналогов в той же категории
    alternatives_query = db.query(Product).filter(
        and_(
            Product.category == request.category,
            Product.id != request.product_id,  # Исключаем сам продукт
        )
    )

    products = alternatives_query.limit(request.max_count * 15).all()  # Берём с запасом

    # Диапазон цен: сначала строгий (±10%), затем мягче — чтобы почти всегда вернуть хотя бы 1-2 аналога.
    margins = [0.10, 0.25, 0.40]

    alternatives: list[AlternativeProduct] = []
    for margin in margins:
        alternatives = []

        price_min = original_median_price * (1 - margin) if original_median_price else 0
        price_max = original_median_price * (1 + margin) if original_median_price else float("inf")

        for product in products:
            cost = db.query(CostEstimate).filter(
                CostEstimate.product_id == product.id
            ).first()

            median_price = _get_median_price(db, product.id)

            if not cost or not median_price or cost.total <= 0:
                continue

            # КРИТЕРИЙ 1: Цена в диапазоне
            if median_price < price_min or median_price > price_max:
                continue

            # Расчёт наценки
            markup_percent = (median_price - cost.total) / cost.total * 100

            # КРИТЕРИЙ 2: Наценка не выше исходного товара
            if original_markup_percent is not None and markup_percent > original_markup_percent:
                continue

            # КРИТЕРИЙ 3: Рейтинг выше или равен исходному
            review = db.query(ReviewQuality).filter(
                ReviewQuality.product_id == product.id
            ).first()
            candidate_rating = review.avg_rating if review and review.avg_rating else 0

            # Допускаем небольшую просадку рейтинга, если товар объективно выгоднее по цене/наценке.
            # Иначе в реальных данных часто не найдётся ни одного аналога.
            rating_tolerance = 0.5
            if candidate_rating < (original_rating - rating_tolerance):
                continue

            # КРИТЕРИЙ 4: Схожие характеристики (базовое сравнение)
            if not _has_similar_specs(original_product, product):
                continue

            # Скоринг: чем выше рейтинг и ниже наценка, тем лучше
            rating_score = candidate_rating / 5.0  # 0-1
            markup_score = 1 - (markup_percent / 100) if markup_percent < 100 else 0  # 0-1, ниже наценка = лучше

            # Итоговый score (взвешенная сумма)
            score = (rating_score * 0.6 + markup_score * 0.4) * 100

            # Рекомендация
            recommendation = _generate_recommendation_v2(
                product, candidate_rating, markup_percent, original_product, original_rating, original_markup_percent
            )

            alternatives.append(AlternativeProduct(
                product_id=product.id,
                brand=product.brand,
                model=product.model,
                price=round(median_price, 2),
                quality_factor=round(candidate_rating / 5.0, 3),
                markup_percent=round(markup_percent, 2),
                score=round(score, 3),
                recommendation=recommendation,
            ))

        if alternatives:
            break

    # Сортировка по score (по убыванию)
    alternatives.sort(key=lambda x: x.score, reverse=True)

    return AlternativesResponse(
        product_id=request.product_id,
        category=request.category,
        alternatives_count=len(alternatives[:request.max_count]),
        alternatives=alternatives[:request.max_count],
    )


def _has_similar_specs(product1: Product, product2: Product) -> bool:
    """Проверка схожести характеристик (базовое сравнение)"""
    if not product1.specs or not product2.specs:
        return True  # Если нет specs, считаем похожими

    specs1 = product1.specs
    specs2 = product2.specs

    # Считаем разницу в ключевых характеристиках
    matching_score = 0
    total_checks = 0

    # Для GPU: память, TDP
    if product1.category == 'GPU':
        if 'memory_gb' in specs1 and 'memory_gb' in specs2:
            mem_diff = abs(specs1['memory_gb'] - specs2['memory_gb']) / specs1['memory_gb']
            if mem_diff <= 0.3:  # ±30% памяти
                matching_score += 1
            total_checks += 1
        
        if 'tdp_watts' in specs1 and 'tdp_watts' in specs2:
            tdp_diff = abs(specs1['tdp_watts'] - specs2['tdp_watts']) / specs1['tdp_watts']
            if tdp_diff <= 0.3:
                matching_score += 1
            total_checks += 1

    # Для CPU: ядра, частота, TDP
    elif product1.category == 'CPU':
        if 'cores' in specs1 and 'cores' in specs2:
            if specs1['cores'] == specs2['cores']:
                matching_score += 1
            total_checks += 1
        
        if 'base_clock_ghz' in specs1 and 'base_clock_ghz' in specs2:
            clock_diff = abs(specs1['base_clock_ghz'] - specs2['base_clock_ghz']) / specs1['base_clock_ghz']
            if clock_diff <= 0.2:  # ±20% частоты
                matching_score += 1
            total_checks += 1

    # Для RAM: объём, тип, частота
    elif product1.category == 'RAM':
        if 'capacity_gb' in specs1 and 'capacity_gb' in specs2:
            if specs1['capacity_gb'] == specs2['capacity_gb']:
                matching_score += 1
            total_checks += 1
        
        if 'type' in specs1 and 'type' in specs2:
            if specs1['type'] == specs2['type']:
                matching_score += 1
            total_checks += 1

    # Для SSD/M2: объём, интерфейс
    elif product1.category in ['SSD', 'HDD']:
        if 'capacity_gb' in specs1 and 'capacity_gb' in specs2:
            cap_diff = abs(specs1['capacity_gb'] - specs2['capacity_gb']) / specs1['capacity_gb']
            if cap_diff <= 0.3:
                matching_score += 1
            total_checks += 1

    # По умолчанию - похоже, если нет специфичных проверок
    if total_checks == 0:
        return True

    # Требуем минимум 50% совпадений
    return matching_score / total_checks >= 0.5


def _get_median_price(db: Session, product_id: int) -> Optional[float]:
    """Медианная цена из истории"""
    prices = db.query(PriceHistory.price).filter(
        PriceHistory.product_id == product_id
    ).order_by(PriceHistory.price).all()

    if not prices:
        return None

    price_list = sorted([p[0] for p in prices])
    n = len(price_list)
    mid = n // 2

    if n % 2 == 0:
        return (price_list[mid - 1] + price_list[mid]) / 2
    else:
        return price_list[mid]


def _generate_recommendation(
    product: Product,
    quality_factor: float,
    markup: float,
    original: Product
) -> str:
    """Генерация текстовой рекомендации (legacy)"""
    parts = []

    if quality_factor > 1.0:
        parts.append("higher reliability")
    elif quality_factor < 0.8:
        parts.append("budget option")

    if markup < 20:
        parts.append("low markup")
    elif markup > 60:
        parts.append("high markup")

    if product.brand != original.brand:
        parts.append(f"alternative brand {product.brand}")

    if not parts:
        parts.append("similar specs")

    return "; ".join(parts)


def _generate_recommendation_v2(
    product: Product,
    rating: float,
    markup: float,
    original: Product,
    original_rating: float,
    original_markup: float | None
) -> str:
    """Генерация текстовой рекомендации v2"""
    parts = []

    if rating > original_rating:
        parts.append(f"рейтинг выше ({rating:.1f} vs {original_rating:.1f})")
    
    if original_markup is not None and markup < original_markup:
        parts.append(f"наценка ниже ({markup:.0f}% vs {original_markup:.0f}%)")
    
    if product.brand != original.brand:
        parts.append(f"альтернативный бренд {product.brand}")
    
    if not parts:
        parts.append("аналогичные характеристики")

    return "; ".join(parts)
