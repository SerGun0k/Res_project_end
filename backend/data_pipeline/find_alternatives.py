"""
Скрипт подбора аналогов с лучшим соотношением цена/качество.
Вызывается через MCP-сервер python или напрямую.

Вход: JSON с параметрами product_id, category, max_count
Выход: JSON со списком рекомендаций
"""

import json
import sys


def find_alternatives(product_id: int, category: str, max_count: int = 5,
                     current_markup: float = 0.0, current_quality: float = 1.0) -> dict:
    """
    Поиск аналогов продукта с лучшим соотношением цена/качество.
    
    Формула score = (1/markup) * quality_factor * relevance
    """
    # Заглушка: в реальности здесь будет запрос к БД
    # для получения продуктов той же категории
    mock_alternatives = [
        {
            "product_id": product_id + 1,
            "brand": "Альтернативный бренд A",
            "model": f"Model-{category}-001",
            "price": 25000.0,
            "quality_factor": 1.1,
            "markup_pct": current_markup * 0.8,
            "score": 1.2
        },
        {
            "product_id": product_id + 2,
            "brand": "Альтернативный бренд B",
            "model": f"Model-{category}-002",
            "price": 23000.0,
            "quality_factor": 0.95,
            "markup_pct": current_markup * 0.7,
            "score": 1.35
        }
    ]

    # Фильтрация и сортировка по score
    alternatives = sorted(
        mock_alternatives[:max_count],
        key=lambda x: x["score"],
        reverse=True
    )

    return {
        "product_id": product_id,
        "category": category,
        "alternatives_count": len(alternatives),
        "alternatives": alternatives
    }


if __name__ == "__main__":
    # Чтение параметров из stdin или args
    if len(sys.argv) > 1:
        data = json.loads(sys.argv[1])
    else:
        input_data = sys.stdin.read()
        data = json.loads(input_data)

    result = find_alternatives(**data)
    print(json.dumps(result, ensure_ascii=False, indent=2))
