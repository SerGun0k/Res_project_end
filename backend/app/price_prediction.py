"""
Модуль предсказания цен на основе линейной регрессии.

Алгоритм:
  1. Берём историю цен за последние N записей
  2. Рассчитываем линейный тренд (метод наименьших квадратов)
  3. Прогноз на 1 и 3 месяца
  4. Определяем тренд: rising (>2%), falling (<-2%), stable
  5. Рекомендация: buy_now, wait, no_rush
"""

from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.models import Product, PriceHistory, PricePrediction


def calculate_price_prediction(db: Session, product_id: int) -> Optional[dict]:
    """
    Расчёт прогноза цен для товара.
    Возвращает dict с predicted_1m, predicted_3m, trend, recommendation, confidence.
    """
    # Получаем историю цен, сортированную по дате
    prices = (
        db.query(PriceHistory)
        .filter(PriceHistory.product_id == product_id)
        .order_by(PriceHistory.date.asc())
        .all()
    )

    if len(prices) < 3:
        return None  # Недостаточно данных

    # Берём последние 20 записей для стабильности
    recent_prices = prices[-20:]

    # Преобразуем в числовые данные (дни от начальной точки)
    base_date = recent_prices[0].date
    data_points = []
    for p in recent_prices:
        days = (p.date - base_date).total_seconds() / 86400  # дни
        data_points.append((days, p.price))

    # Линейная регрессия: y = ax + b
    n = len(data_points)
    sum_x = sum(d[0] for d in data_points)
    sum_y = sum(d[1] for d in data_points)
    sum_xy = sum(d[0] * d[1] for d in data_points)
    sum_x2 = sum(d[0] ** 2 for d in data_points)

    denominator = n * sum_x2 - sum_x ** 2
    if denominator == 0:
        return None

    a = (n * sum_xy - sum_x * sum_y) / denominator
    b = (sum_y - a * sum_x) / n

    # Текущая цена (последняя)
    current_price = recent_prices[-1].price
    current_day = data_points[-1][0]

    # Прогноз: 30 дней и 90 дней
    predicted_1m = a * (current_day + 30) + b
    predicted_3m = a * (current_day + 90) + b

    # Убедимся что цена не отрицательная
    predicted_1m = max(predicted_1m, current_price * 0.5)
    predicted_3m = max(predicted_3m, current_price * 0.5)

    # Определяем тренд (% изменения за 30 дней)
    change_pct = ((predicted_1m - current_price) / current_price) * 100

    if change_pct > 2:
        trend = "rising"
        recommendation = "buy_now"
    elif change_pct < -2:
        trend = "falling"
        recommendation = "wait"
    else:
        trend = "stable"
        recommendation = "no_rush"

    # Уверенность: зависит от R² (коэффициент детерминации)
    y_mean = sum_y / n
    ss_tot = sum((d[1] - y_mean) ** 2 for d in data_points)
    ss_res = sum((d[1] - (a * d[0] + b)) ** 2 for d in data_points)

    if ss_tot > 0:
        r_squared = 1 - (ss_res / ss_tot)
        confidence = max(0, min(1, r_squared))
    else:
        confidence = 0.5

    return {
        "current_price": round(current_price, 2),
        "predicted_1m": round(predicted_1m, 2),
        "predicted_3m": round(predicted_3m, 2),
        "trend": trend,
        "recommendation": recommendation,
        "confidence": round(confidence, 3),
    }


def seed_predictions(db: Session) -> tuple[int, int]:
    """
    Генерация прогнозов для всех товаров с историей цен.
    Возвращает (создано, ошибок).
    """
    from app.models import CostEstimate

    products = db.query(Product).all()
    created = 0
    errors = 0

    for product in products:
        # Проверяем что есть история цен
        price_count = db.query(PriceHistory).filter(
            PriceHistory.product_id == product.id
        ).count()

        if price_count < 3:
            continue

        prediction = calculate_price_prediction(db, product.id)
        if not prediction:
            errors += 1
            continue

        # Сохраняем или обновляем
        existing = db.query(PricePrediction).filter(
            PricePrediction.product_id == product.id
        ).first()

        if existing:
            existing.current_price = prediction["current_price"]
            existing.predicted_1m = prediction["predicted_1m"]
            existing.predicted_3m = prediction["predicted_3m"]
            existing.trend = prediction["trend"]
            existing.recommendation = prediction["recommendation"]
            existing.confidence = prediction["confidence"]
            existing.last_updated = datetime.utcnow()
        else:
            pred = PricePrediction(
                product_id=product.id,
                **prediction,
            )
            db.add(pred)

        created += 1

    db.commit()
    return created, errors


def get_prediction_label(recommendation: str) -> str:
    """Человекочитаемая рекомендация"""
    labels = {
        "buy_now": "🟢 Покупать сейчас — цена растёт",
        "wait": "🟡 Подождать — цена снижается",
        "no_rush": "⚪ Можно не спешить — цена стабильна",
    }
    return labels.get(recommendation, "Нет данных")
