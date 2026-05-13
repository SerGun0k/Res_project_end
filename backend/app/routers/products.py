"""CRUD роутер для товаров"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import Product, PriceHistory, CostEstimate, ReviewQuality, PopularityStats, PricePrediction
from app.schemas import (
    ProductCreate,
    ProductRead,
    ProductFullRead,
    ProductUpdate,
    PriceHistoryRead,
    CostEstimateRead,
)

router = APIRouter()


@router.get("/", response_model=list[ProductRead])
async def list_products(
    category: Optional[str] = Query(None, description="Фильтр по категории"),
    subcategory: Optional[str] = Query(None, description="Фильтр по подкатегории (M2, SATA, NVMe)"),
    brand: Optional[str] = Query(None, description="Фильтр по бренду"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Список товаров с фильтрацией"""
    query = db.query(Product)

    if category:
        query = query.filter(Product.category == category)
    if subcategory:
        query = query.filter(Product.subcategory == subcategory)
    if brand:
        query = query.filter(Product.brand == brand)

    products = query.offset(skip).limit(limit).all()
    return products


@router.post("/", response_model=ProductRead, status_code=201)
async def create_product(
    product_data: ProductCreate,
    db: Session = Depends(get_db),
):
    """Создание нового товара"""
    # Проверка на дубликат
    existing = db.query(Product).filter(
        Product.category == product_data.category,
        Product.brand == product_data.brand,
        Product.model == product_data.model,
    ).first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Товар {product_data.brand} {product_data.model} уже существует в категории {product_data.category}",
        )

    product = Product(**product_data.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.get("/{product_id}", response_model=ProductFullRead)
async def get_product(
    product_id: int,
    db: Session = Depends(get_db),
):
    """Детальная информация о товаре"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")

    # Загрузка связанных данных
    price_history = db.query(PriceHistory).filter(
        PriceHistory.product_id == product_id
    ).order_by(PriceHistory.date.desc()).all()

    cost_estimate = db.query(CostEstimate).filter(
        CostEstimate.product_id == product_id
    ).first()

    review_quality = db.query(ReviewQuality).filter(
        ReviewQuality.product_id == product_id
    ).first()

    popularity_stats = db.query(PopularityStats).filter(
        PopularityStats.product_id == product_id
    ).first()

    price_prediction = db.query(PricePrediction).filter(
        PricePrediction.product_id == product_id
    ).first()

    # Если prediction нет — создаём
    if not price_prediction:
        from app.price_prediction import calculate_price_prediction
        pred_data = calculate_price_prediction(db, product_id)
        if pred_data:
            price_prediction = PricePrediction(
                product_id=product_id,
                **pred_data,
            )
            db.add(price_prediction)
            db.commit()
            db.refresh(price_prediction)

    # Формируем ответ
    result = ProductFullRead(
        **_product_to_dict(product),
        price_history=[_price_to_dict(p) for p in price_history],
        cost_estimate=_cost_to_dict(cost_estimate) if cost_estimate else None,
        review_quality=_review_to_dict(review_quality) if review_quality else None,
        popularity_stats=_popularity_to_dict(popularity_stats) if popularity_stats else None,
        price_prediction=_prediction_to_dict(price_prediction) if price_prediction else None,
    )
    return result


@router.patch("/{product_id}", response_model=ProductRead)
async def update_product(
    product_id: int,
    update_data: ProductUpdate,
    db: Session = Depends(get_db),
):
    """Обновление товара"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")

    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(product, key, value)

    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=204)
async def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
):
    """Удаление товара"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")

    db.delete(product)
    db.commit()


# === Helper functions ===

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


def _price_to_dict(ph: PriceHistory) -> dict:
    return {
        "id": ph.id,
        "product_id": ph.product_id,
        "source": ph.source,
        "price": ph.price,
        "date": ph.date,
    }


def _cost_to_dict(ce: CostEstimate) -> dict:
    return {
        "id": ce.id,
        "product_id": ce.product_id,
        "materials_cost": ce.materials_cost,
        "logistics_cost": ce.logistics_cost,
        "labor_cost": ce.labor_cost,
        "total": ce.total,
        "last_updated": ce.last_updated,
    }


def _review_to_dict(rq: ReviewQuality) -> dict:
    return {
        "id": rq.id,
        "product_id": rq.product_id,
        "avg_rating": rq.avg_rating,
        "defect_rate": rq.defect_rate,
        "reviews_count": rq.reviews_count,
        "source": rq.source,
        "last_updated": rq.last_updated,
    }


def _popularity_to_dict(ps: PopularityStats) -> dict:
    return {
        "id": ps.id,
        "product_id": ps.product_id,
        "daily_views": ps.daily_views,
        "total_views": ps.total_views,
        "daily_searches": ps.daily_searches,
        "last_updated": ps.last_updated,
    }


def _prediction_to_dict(pred: PricePrediction) -> dict:
    return {
        "id": pred.id,
        "product_id": pred.product_id,
        "current_price": pred.current_price,
        "predicted_1m": pred.predicted_1m,
        "predicted_3m": pred.predicted_3m,
        "trend": pred.trend,
        "recommendation": pred.recommendation,
        "target_price": pred.target_price,
        "price_gap_pct": pred.price_gap_pct,
        "confidence": pred.confidence,
        "last_updated": pred.last_updated,
    }
