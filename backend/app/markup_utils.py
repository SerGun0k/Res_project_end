"""
Реальный алгоритм расчёта наценки с факторами из БД.

Используется в API и в скриптах data pipeline.
"""

from datetime import datetime
from typing import Optional

from app.config import settings

# Коэффициенты премиальности брендов (отраслевые данные)
BRAND_PREMIUM = {
    # GPU
    "NVIDIA": 1.3,
    "AMD": 1.0,
    # CPU
    "Intel": 1.15,
    # RAM/SSD
    "Samsung": 1.2,
    "Corsair": 1.15,
    "G.Skill": 1.2,
    "Kingston": 0.95,
    "Crucial": 1.0,
    "WD": 1.0,
    "Seagate": 0.9,
}


def get_brand_factor(brand: str) -> float:
    """Фактор премиальности бренда"""
    return BRAND_PREMIUM.get(brand, 1.0)


def get_relevance_factor(product_release: Optional[datetime],
                        candidate_release: Optional[datetime]) -> float:
    """
    Фактор актуальности: чем новее модель, тем выше.
    Сравниваем возраст кандидатов. Новее = релевантнее.
    """
    now = datetime.utcnow()

    if not product_release or not candidate_release:
        return 0.8  # Заглушка если нет данных

    # Возраст в днях
    product_age = (now - product_release).days
    candidate_age = (now - candidate_release).days

    # Если кандидат новее или того же возраста — фактор = 1.0
    if candidate_age <= product_age:
        return 1.0

    # Старше — снижаем пропорционально (макс -30% за 2 года)
    age_diff = candidate_age - product_age
    factor = max(0.7, 1.0 - (age_diff / 730) * 0.3)

    return round(factor, 3)


def calculate_weighted_factor(brand_factor: float,
                               quality_factor: float,
                               relevance_factor: float,
                               popularity_factor: float) -> float:
    """Средневзвешенный фактор наценки"""
    return (
        brand_factor * settings.WEIGHT_BRAND +
        quality_factor * settings.WEIGHT_QUALITY +
        relevance_factor * settings.WEIGHT_RELEVANCE +
        popularity_factor * settings.WEIGHT_POPULARITY
    )


def calculate_adjusted_markup(markup_pct: float,
                                weighted_factor: float) -> float:
    """Скорректированная наценка"""
    return round(markup_pct * weighted_factor, 2)


def get_markup_status(adjusted_markup: float) -> str:
    """Определение статуса наценки"""
    return "normal" if adjusted_markup <= settings.MARKUP_THRESHOLD else "high"
