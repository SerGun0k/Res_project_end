"""Тесты для модуля markup_utils"""

import pytest
from datetime import datetime, timedelta

from app.markup_utils import (
    get_brand_factor,
    get_relevance_factor,
    calculate_weighted_factor,
    calculate_adjusted_markup,
    get_markup_status,
    BRAND_PREMIUM,
)
from app.config import settings


class TestBrandFactor:
    """Тесты фактора бренда"""

    def test_nvidia_premium(self):
        assert get_brand_factor("NVIDIA") == 1.3

    def test_amd_no_premium(self):
        assert get_brand_factor("AMD") == 1.0

    def test_unknown_brand(self):
        assert get_brand_factor("UnknownBrand") == 1.0

    def test_samsung_premium(self):
        assert get_brand_factor("Samsung") == 1.2

    def test_seagate_discount(self):
        assert get_brand_factor("Seagate") == 0.9

    def test_all_brands_positive(self):
        """Все факторы брендов > 0"""
        for brand, factor in BRAND_PREMIUM.items():
            assert factor > 0, f"Фактор {brand} должен быть > 0"


class TestRelevanceFactor:
    """Тесты фактора актуальности"""

    def test_newer_candidate(self):
        """Кандидат новее — фактор = 1.0"""
        now = datetime.utcnow()
        factor = get_relevance_factor(
            product_release=now - timedelta(days=365),
            candidate_release=now - timedelta(days=180),
        )
        assert factor == 1.0

    def test_same_age(self):
        """Одинаковый возраст — фактор = 1.0"""
        now = datetime.utcnow()
        factor = get_relevance_factor(
            product_release=now - timedelta(days=300),
            candidate_release=now - timedelta(days=300),
        )
        assert factor == 1.0

    def test_older_candidate(self):
        """Кандидат старше — фактор < 1.0"""
        now = datetime.utcnow()
        factor = get_relevance_factor(
            product_release=now - timedelta(days=180),
            candidate_release=now - timedelta(days=365),
        )
        assert factor < 1.0
        assert factor >= 0.7  # Не ниже минимума

    def test_very_old_candidate(self):
        """Очень старый кандидат — фактор ≈ 0.7 (минимум)"""
        now = datetime.utcnow()
        factor = get_relevance_factor(
            product_release=now - timedelta(days=30),
            candidate_release=now - timedelta(days=730),
        )
        # age_diff = 700, factor = 1 - 700/730*0.3 = 0.712, min = 0.7
        assert factor >= 0.7
        assert factor <= 0.72

    def test_no_release_dates(self):
        """Нет данных — заглушка 0.8"""
        factor = get_relevance_factor(None, None)
        assert factor == 0.8

    def test_partial_release_dates(self):
        """Только одна дата — заглушка"""
        now = datetime.utcnow()
        assert get_relevance_factor(now, None) == 0.8
        assert get_relevance_factor(None, now) == 0.8


class TestWeightedFactor:
    """Тесты средневзвешенного фактора"""

    def test_all_ones(self):
        """Все факторы = 1 → результат = 1"""
        result = calculate_weighted_factor(1.0, 1.0, 1.0, 1.0)
        assert result == 1.0

    def test_all_zeros(self):
        """Все факторы = 0 → результат = 0"""
        result = calculate_weighted_factor(0, 0, 0, 0)
        assert result == 0.0

    def test_weights_sum(self):
        """Проверка что веса суммируются корректно"""
        result = calculate_weighted_factor(2.0, 0, 0, 0)
        expected = 2.0 * settings.WEIGHT_BRAND
        assert result == pytest.approx(expected)

    def test_realistic_values(self):
        """Реалистичные значения"""
        result = calculate_weighted_factor(
            brand_factor=1.3,
            quality_factor=0.9,
            relevance_factor=0.85,
            popularity_factor=1.1,
        )
        # Все факторы близки к 1, результат должен быть ~1.0
        assert 0.5 < result < 1.5


class TestAdjustedMarkup:
    """Тесты скорректированной наценки"""

    def test_basic(self):
        result = calculate_adjusted_markup(100.0, 1.0)
        assert result == 100.0

    def test_high_weight(self):
        result = calculate_adjusted_markup(50.0, 1.5)
        assert result == 75.0

    def test_low_weight(self):
        result = calculate_adjusted_markup(80.0, 0.5)
        assert result == 40.0

    def test_rounding(self):
        result = calculate_adjusted_markup(33.333, 1.111)
        assert isinstance(result, float)
        # Проверяем что округлено до 2 знаков
        assert len(str(result).split(".")[-1]) <= 2


class TestMarkupStatus:
    """Тесты статуса наценки"""

    def test_normal(self):
        assert get_markup_status(30.0) == "normal"

    def test_high(self):
        assert get_markup_status(50.0) == "high"

    def test_boundary(self):
        assert get_markup_status(40.0) == "normal"  # <= threshold

    def test_just_above(self):
        assert get_markup_status(40.1) == "high"
