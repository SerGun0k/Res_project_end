"""
Скрипт расчёта наценки на продукт с учётом весовых факторов.
Вызывается через MCP-сервер python или напрямую.

Вход: JSON с параметрами product_id, market_price, cost_estimate
Выход: JSON с результатом расчёта
"""

import json
import sys

# Весовые коэффициенты факторов
WEIGHTS = {
    "brand": 0.25,
    "quality": 0.30,
    "relevance": 0.20,
    "popularity": 0.25
}

# Порог наценки для пометки "завышена"
MARKUP_THRESHOLD = 40.0


def calculate_markup(product_id: int, market_price: float, cost_estimate: float,
                    brand_factor: float = 1.0, quality_factor: float = 1.0,
                    relevance_factor: float = 1.0, popularity_factor: float = 1.0) -> dict:
    """
    Расчёт наценки и скорректированной наценки по факторам.
    """
    if cost_estimate <= 0:
        return {"error": "Себестоимость должна быть больше нуля"}

    # Базовая наценка %
    markup_pct = (market_price - cost_estimate) / cost_estimate * 100

    # Средневзвешенный фактор
    weighted_factor = (
        brand_factor * WEIGHTS["brand"] +
        quality_factor * WEIGHTS["quality"] +
        relevance_factor * WEIGHTS["relevance"] +
        popularity_factor * WEIGHTS["popularity"]
    )

    # Скорректированная наценка
    adjusted_markup = markup_pct * weighted_factor

    # Определение статуса
    status = "нормальная" if adjusted_markup <= MARKUP_THRESHOLD else "завышена"

    return {
        "product_id": product_id,
        "market_price": market_price,
        "cost_estimate": cost_estimate,
        "markup_pct": round(markup_pct, 2),
        "weighted_factor": round(weighted_factor, 3),
        "adjusted_markup": round(adjusted_markup, 2),
        "threshold": MARKUP_THRESHOLD,
        "status": status
    }


if __name__ == "__main__":
    # Чтение параметров из stdin или args
    if len(sys.argv) > 1:
        data = json.loads(sys.argv[1])
    else:
        input_data = sys.stdin.read()
        data = json.loads(input_data)

    result = calculate_markup(**data)
    print(json.dumps(result, ensure_ascii=False, indent=2))
