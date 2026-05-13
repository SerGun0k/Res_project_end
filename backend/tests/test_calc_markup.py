"""Тесты для модуля расчёта наценки"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "data_pipeline"))

from calc_markup import calculate_markup, WEIGHTS, MARKUP_THRESHOLD


class TestCalculateMarkup:
    """Тесты функции calculate_markup"""

    def test_basic_markup(self):
        """Базовый расчёт наценки"""
        result = calculate_markup(
            product_id=1,
            market_price=30000,
            cost_estimate=20000,
        )

        assert result["product_id"] == 1
        assert result["market_price"] == 30000
        assert result["cost_estimate"] == 20000
        assert result["markup_pct"] == 50.0  # (30000-20000)/20000 * 100
        assert result["weighted_factor"] == 1.0  # все факторы = 1.0
        assert result["adjusted_markup"] == 50.0
        assert result["threshold"] == MARKUP_THRESHOLD
        assert result["status"] == "завышена"

    def test_low_markup(self):
        """Низкая наценка — статус 'нормальная'"""
        result = calculate_markup(
            product_id=2,
            market_price=22000,
            cost_estimate=20000,
        )

        assert result["markup_pct"] == 10.0
        assert result["adjusted_markup"] == 10.0
        assert result["status"] == "нормальная"

    def test_zero_cost(self):
        """Нулевая себестоимость — ошибка"""
        result = calculate_markup(
            product_id=3,
            market_price=30000,
            cost_estimate=0,
        )

        assert "error" in result
        assert result["error"] == "Себестоимость должна быть больше нуля"

    def test_negative_cost(self):
        """Отрицательная себестоимость — ошибка"""
        result = calculate_markup(
            product_id=4,
            market_price=30000,
            cost_estimate=-100,
        )

        assert "error" in result

    def test_weighted_factors(self):
        """Влияние весовых факторов"""
        result = calculate_markup(
            product_id=5,
            market_price=40000,
            cost_estimate=20000,
            brand_factor=1.5,
            quality_factor=1.2,
            relevance_factor=0.8,
            popularity_factor=1.0,
        )

        # markup_pct = 100%
        # weighted = 1.5*0.25 + 1.2*0.30 + 0.8*0.20 + 1.0*0.25 = 0.375 + 0.36 + 0.16 + 0.25 = 1.145
        # adjusted = 100 * 1.145 = 114.5
        expected_weighted = round(
            1.5 * WEIGHTS["brand"] +
            1.2 * WEIGHTS["quality"] +
            0.8 * WEIGHTS["relevance"] +
            1.0 * WEIGHTS["popularity"],
            3
        )

        assert result["weighted_factor"] == expected_weighted
        assert result["adjusted_markup"] == 114.5

    def test_all_factors_zero(self):
        """Все факторы = 0 — наценка тоже 0"""
        result = calculate_markup(
            product_id=6,
            market_price=50000,
            cost_estimate=10000,
            brand_factor=0,
            quality_factor=0,
            relevance_factor=0,
            popularity_factor=0,
        )

        assert result["markup_pct"] == 400.0
        assert result["weighted_factor"] == 0.0
        assert result["adjusted_markup"] == 0.0
        assert result["status"] == "нормальная"  # adjusted < threshold

    def test_threshold_boundary(self):
        """Наценка точно на пороге"""
        # adjusted_markup = 40.0 = threshold
        result = calculate_markup(
            product_id=7,
            market_price=28000,
            cost_estimate=20000,
        )

        # markup = 40%, weighted = 1.0, adjusted = 40.0
        assert result["adjusted_markup"] == 40.0
        assert result["status"] == "нормальная"  # <= threshold

    def test_rounding(self):
        """Проверка округления до 2 знаков"""
        result = calculate_markup(
            product_id=8,
            market_price=33333,
            cost_estimate=20000,
        )

        assert result["markup_pct"] == round((33333 - 20000) / 20000 * 100, 2)
        assert isinstance(result["adjusted_markup"], float)
        assert len(str(result["adjusted_markup"]).split(".")[-1]) <= 2

    def test_high_markup_with_low_factors(self):
        """Высокая базовая наценка, но низкие факторы — статус нормальная"""
        result = calculate_markup(
            product_id=9,
            market_price=100000,
            cost_estimate=10000,
            brand_factor=0.3,
            quality_factor=0.3,
            relevance_factor=0.3,
            popularity_factor=0.3,
        )

        # markup = 900%, weighted = 0.3, adjusted = 270%
        # 270 > 40 → завышена
        assert result["status"] == "завышена"

    def test_default_factors(self):
        """Факторы по умолчанию = 1.0"""
        result = calculate_markup(
            product_id=10,
            market_price=25000,
            cost_estimate=20000,
        )

        assert result["weighted_factor"] == 1.0


class TestWeights:
    """Тесты весовых коэффициентов"""

    def test_weights_sum_to_one(self):
        """Сумма весов = 1.0"""
        assert sum(WEIGHTS.values()) == pytest.approx(1.0)

    def test_weights_positive(self):
        """Все веса положительные"""
        for key, value in WEIGHTS.items():
            assert value > 0, f"Вес {key} должен быть > 0"

    def test_quality_is_highest(self):
        """Качество — самый высокий вес (0.30)"""
        assert WEIGHTS["quality"] == 0.30
        assert WEIGHTS["quality"] == max(WEIGHTS.values())


class TestMarkupThreshold:
    """Тесты порога наценки"""

    def test_threshold_is_40(self):
        assert MARKUP_THRESHOLD == 40.0
