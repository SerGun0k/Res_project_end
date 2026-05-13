"""Роутер ML рекомендаций"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models import Product, PriceHistory, UserBehavior

router = APIRouter()


@router.get("/similar/{product_id}")
async def get_similar_products(
    product_id: int,
    top_k: int = Query(5, ge=1, le=10),
    db: Session = Depends(get_db),
):
    """
    Поиск похожих товаров через ML (косинусное сходство).
    """
    try:
        from ml.models import find_similar_products, ProductClusterer

        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Товар не найден")

        all_products = db.query(Product).all()

        similar = find_similar_products(product, all_products, top_k)

        results = []
        for prod, similarity in similar:
            prices = db.query(PriceHistory.price).filter(
                PriceHistory.product_id == prod.id
            ).all()
            avg_price = sum(p[0] for p in prices) / len(prices) if prices else None

            clusterer = ProductClusterer()
            clusterer.load()
            cluster_id = clusterer.predict(prod) if clusterer.is_fitted else None

            results.append({
                "product": {
                    "id": prod.id,
                    "category": prod.category,
                    "brand": prod.brand,
                    "model": prod.model,
                    "specs": prod.specs,
                },
                "similarity": round(similarity, 3),
                "avg_price": round(avg_price, 2) if avg_price else None,
                "segment": ProductClusterer.cluster_name(cluster_id) if cluster_id is not None else None,
            })

        return {
            "product_id": product_id,
            "similar_count": len(results),
            "similar": results,
        }

    except ImportError:
        raise HTTPException(status_code=503, detail="ML модели не обучены")


@router.get("/explain/{product_id}")
async def explain_ml_result(
    product_id: int,
    db: Session = Depends(get_db),
):
    """
    Объяснение ML результатов: почему товар попал в свой кластер,
    какие признаки повлияли на результат.
    """
    try:
        from ml.models import ProductClusterer, PricePredictor

        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Товар не найден")

        specs = product.specs or {}
        explanation = {
            "product_id": product_id,
            "product_name": f"{product.brand} {product.model}",
            "category": product.category,
            "features": {},
            "cluster_result": None,
            "price_prediction_result": None,
        }

        # 1. Извлечённые признаки
        features = {
            "Объём памяти/накопителя": specs.get('memory_gb', specs.get('capacity_gb', 0)) or 0,
            "TDP / Мощность": specs.get('tdp_watts', specs.get('watts', 0)) or 0,
            "Количество ядер": specs.get('cores', 0) or 0,
            "Частота": specs.get('speed_mhz', specs.get('base_clock_ghz', 0)) or 0,
            "Скорость чтения": specs.get('read_mbps', 0) or 0,
        }
        explanation["features"] = features

        # 2. Кластеризация
        clusterer = ProductClusterer()
        loaded = clusterer.load()

        if loaded:
            cluster_id = clusterer.predict(product)
            explanation["cluster_result"] = {
                "cluster_id": cluster_id,
                "cluster_name": ProductClusterer.cluster_name(cluster_id),
                "explanation": _explain_cluster(cluster_id, features),
            }
        else:
            explanation["cluster_result"] = {"error": "Модель не загружена"}

        # 3. Предсказание цены
        predictor = PricePredictor()
        if predictor.load():
            predicted_price = predictor.predict(product)
            if predicted_price:
                # Средняя реальная цена
                prices = db.query(PriceHistory.price).filter(
                    PriceHistory.product_id == product_id
                ).all()
                avg_real = sum(p[0] for p in prices) / len(prices) if prices else None

                diff_pct = ((predicted_price - avg_real) / avg_real * 100) if avg_real else None

                explanation["price_prediction_result"] = {
                    "predicted_price": round(predicted_price, 2),
                    "actual_avg_price": round(avg_real, 2) if avg_real else None,
                    "difference_pct": round(diff_pct, 1) if diff_pct else None,
                    "explanation": _explain_price_prediction(predicted_price, avg_real, diff_pct),
                }
            else:
                explanation["price_prediction_result"] = {"error": "Не удалось предсказать"}
        else:
            explanation["price_prediction_result"] = {"error": "Модель не загружена"}

        return explanation

    except ImportError:
        raise HTTPException(status_code=503, detail="ML модели не обучены")


def _explain_cluster(cluster_id: int, features: dict) -> str:
    """Объяснение почему товар попал в кластер"""
    volume = features.get("Объём памяти/накопителя", 0)
    tdp = features.get("TDP / Мощность", 0)
    cores = features.get("Количество ядер", 0)

    if cluster_id == 0:  # Бюджет
        return (
            f"Товар отнесён к 💰 Бюджетному сегменту. "
            f"Основные признаки: объём {volume} ГБ, TDP {tdp} Вт, {cores} ядер. "
            f"Эти характеристики типичны для недорогих решений."
        )
    elif cluster_id == 1:  # Средний
        return (
            f"Товар отнесён к 📦 Среднему сегменту. "
            f"Объём {volume} ГБ, TDP {tdp} Вт, {cores} ядер — "
            f"оптимальный баланс цены и производительности."
        )
    else:  # Премиум
        return (
            f"Товар отнесён к 💎 Премиум сегменту. "
            f"Высокие характеристики: {volume} ГБ, {tdp} Вт TDP, {cores} ядер. "
            f"Это флагманское решение с максимальной производительностью."
        )


def _explain_price_prediction(predicted: float, actual: float | None, diff_pct: float | None) -> str:
    """Объяснение предсказания цены"""
    if actual is None or diff_pct is None:
        return "Недостаточно данных для сравнения с реальной ценой."

    if diff_pct > 10:
        return (
            f"Модель предсказывает цену {predicted:,.0f} ₽, что на {diff_pct:.0f}% выше средней реальной {actual:,.0f} ₽. "
            f"Возможно, товар переоценён или модель ожидает рост цен."
        )
    elif diff_pct < -10:
        return (
            f"Модель предсказывает цену {predicted:,.0f} ₽, что на {abs(diff_pct):.0f}% ниже средней реальной {actual:,.0f} ₽. "
            f"Товар может быть выгодной покупкой — его цена выше справедливой."
        )
    else:
        return (
            f"Предсказанная цена {predicted:,.0f} ₽ близка к реальной {actual:,.0f} ₽ (разница {diff_pct:.0f}%). "
            f"Модель считает цену адекватной."
        )


@router.get("/personalized/{user_session}")
async def get_personalized_recommendations(
    user_session: str,
    top_k: int = 5,
    db: Session = Depends(get_db),
):
    """
    Персонализированные рекомендации (Collaborative Filtering).
    """
    try:
        from ml.advanced import collaborative_filtering
        results = collaborative_filtering(user_session, top_k)
        return {"user_session": user_session, "recommendations": results}
    except ImportError:
        raise HTTPException(status_code=503, detail="ML зависимости не установлены")


@router.get("/tfidf-search")
async def tfidf_product_search(
    q: str = Query(..., min_length=1),
    top_k: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """
    Поиск товаров через TF-IDF по названиям и характеристикам.
    """
    try:
        from ml.advanced import tfidf_search
        results = tfidf_search(q, top_k)
        return {"query": q, "results": results}
    except ImportError:
        raise HTTPException(status_code=503, detail="ML зависимости не установлены")
