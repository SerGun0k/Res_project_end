"""
ML модуль для кластеризации товаров и улучшения рекомендаций.

Использует scikit-learn для:
  1. Кластеризации товаров по сегментам (бюджет, средний, премиум)
  2. Улучшения предсказания цен через Ridge регрессию
  3. Поиска похожих товаров через косинусное сходство

Запуск: python backend/ml/train_models.py
"""

import json
import os
import sys
from typing import Optional

import joblib
import numpy as np
from sklearn.cluster import KMeans
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.database import SessionLocal
from app.models import Product, PriceHistory


class ProductClusterer:
    """Кластеризация товаров по сегментам"""

    MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "clusterer.joblib")
    SCALER_PATH = os.path.join(os.path.dirname(__file__), "models", "scaler.joblib")

    def __init__(self, n_clusters=3):
        self.n_clusters = n_clusters
        self.kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        self.scaler = StandardScaler()
        self.is_fitted = False

    def _extract_features(self, products: list[Product]) -> np.ndarray:
        """Извлечение признаков для кластеризации"""
        features = []
        for p in products:
            specs = p.specs or {}

            # Нормализуем признаки
            feature_vec = [
                float(specs.get('memory_gb', specs.get('capacity_gb', 0)) or 0),
                float(specs.get('tdp_watts', specs.get('watts', 0)) or 0),
                float(specs.get('cores', 0) or 0),
                float(specs.get('speed_mhz', specs.get('base_clock_ghz', 0)) or 0),
                float(specs.get('read_mbps', 0) or 0),
            ]
            features.append(feature_vec)

        return np.array(features)

    def fit(self, products: list[Product]):
        """Обучение кластеризатора"""
        X = self._extract_features(products)

        # Удаляем пустые строки
        mask = ~np.all(X == 0, axis=1)
        X = X[mask]

        if len(X) < self.n_clusters:
            print(f"⚠️ Недостаточно данных для кластеризации: {len(X)} < {self.n_clusters}")
            return

        X_scaled = self.scaler.fit_transform(X)
        self.kmeans.fit(X_scaled)
        self.is_fitted = True

        # Сохраняем модели
        os.makedirs(os.path.dirname(self.MODEL_PATH), exist_ok=True)
        joblib.dump(self.kmeans, self.MODEL_PATH)
        joblib.dump(self.scaler, self.SCALER_PATH)

        print(f"✅ Кластеризатор обучен: {len(X)} товаров, {self.n_clusters} кластеров")

    def load(self):
        """Загрузка модели"""
        if os.path.exists(self.MODEL_PATH):
            self.kmeans = joblib.load(self.MODEL_PATH)
            self.scaler = joblib.load(self.SCALER_PATH)
            self.is_fitted = True
            return True
        return False

    def predict(self, product: Product) -> int:
        """Предсказание кластера для товара"""
        if not self.is_fitted:
            return 0

        X = self._extract_features([product])
        X_scaled = self.scaler.transform(X)
        return int(self.kmeans.predict(X_scaled)[0])

    @staticmethod
    def cluster_name(cluster_id: int) -> str:
        """Название кластера"""
        names = {
            0: "💰 Бюджетный сегмент",
            1: "📦 Средний сегмент",
            2: "💎 Премиум сегмент",
        }
        return names.get(cluster_id, "📊 Не определено")


class PricePredictor:
    """Gradient Boosting для предсказания цен (лучше Ridge)"""

    MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "price_predictor.joblib")
    SCALER_PATH = os.path.join(os.path.dirname(__file__), "models", "price_scaler.joblib")

    def __init__(self):
        # GradientBoosting: мощный алгоритм, хорошо работает на табличных данных
        self.model = GradientBoostingRegressor(
            n_estimators=200,
            max_depth=5,
            learning_rate=0.1,
            subsample=0.8,
            random_state=42,
        )
        self.scaler = StandardScaler()
        self.is_fitted = False

    def _extract_features(self, products: list[Product]) -> tuple[np.ndarray, np.ndarray]:
        """Извлечение признаков и целевых значений"""
        features = []
        targets = []

        for p in products:
            specs = p.specs or {}

            feature_vec = [
                float(specs.get('memory_gb', specs.get('capacity_gb', 0)) or 0),
                float(specs.get('tdp_watts', specs.get('watts', 0)) or 0),
                float(specs.get('cores', 0) or 0),
                float(specs.get('speed_mhz', specs.get('base_clock_ghz', 0)) or 0),
                float(specs.get('read_mbps', 0) or 0),
                # Категория как one-hot
                1 if p.category == 'GPU' else 0,
                1 if p.category == 'CPU' else 0,
                1 if p.category == 'RAM' else 0,
                1 if p.category == 'SSD' else 0,
            ]

            # Средняя цена из истории
            avg_price = get_avg_price_for_product(p)
            if avg_price and avg_price > 0:
                features.append(feature_vec)
                targets.append(avg_price)

        return np.array(features), np.array(targets)

    def fit(self, products: list[Product]):
        """Обучение модели цен"""
        X, y = self._extract_features(products)

        if len(X) < 10:
            print(f"⚠️ Недостаточно данных для обучения: {len(X)} < 10")
            return

        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y)
        self.is_fitted = True

        os.makedirs(os.path.dirname(self.MODEL_PATH), exist_ok=True)
        joblib.dump(self.model, self.MODEL_PATH)
        joblib.dump(self.scaler, self.SCALER_PATH)

        score = self.model.score(X_scaled, y)
        print(f"✅ Модель цен обучена: R² = {score:.3f}")

    def load(self):
        """Загрузка модели"""
        if os.path.exists(self.MODEL_PATH):
            self.model = joblib.load(self.MODEL_PATH)
            self.scaler = joblib.load(self.SCALER_PATH)
            self.is_fitted = True
            return True
        return False

    def predict(self, product: Product) -> Optional[float]:
        """Предсказание цены товара"""
        if not self.is_fitted:
            return None

        X = np.array([[
            float(product.specs.get('memory_gb', product.specs.get('capacity_gb', 0)) or 0),
            float(product.specs.get('tdp_watts', product.specs.get('watts', 0)) or 0),
            float(product.specs.get('cores', 0) or 0),
            float(product.specs.get('speed_mhz', product.specs.get('base_clock_ghz', 0)) or 0),
            float(product.specs.get('read_mbps', 0) or 0),
            1 if product.category == 'GPU' else 0,
            1 if product.category == 'CPU' else 0,
            1 if product.category == 'RAM' else 0,
            1 if product.category == 'SSD' else 0,
        ]])

        X_scaled = self.scaler.transform(X)
        pred = self.model.predict(X_scaled)[0]
        return max(0, float(pred))


def get_avg_price_for_product(product: Product) -> Optional[float]:
    """Получение средней цены из истории"""
    from app.database import SessionLocal
    from app.models import PriceHistory

    db = SessionLocal()
    try:
        prices = db.query(PriceHistory.price).filter(
            PriceHistory.product_id == product.id
        ).all()

        if not prices:
            return None

        return sum(p[0] for p in prices) / len(prices)
    finally:
        db.close()


def find_similar_products(product: Product, all_products: list[Product], top_k=5) -> list[tuple[Product, float]]:
    """Поиск похожих товаров через косинусное сходство"""
    clusterer = ProductClusterer()
    clusterer.load()

    if not clusterer.is_fitted:
        return []

    # Извлекаем признаки
    features = clusterer._extract_features(all_products)
    target_features = clusterer._extract_features([product])

    # Скейлим
    target_scaled = clusterer.scaler.transform(target_features)
    all_scaled = clusterer.scaler.transform(features)

    # Косинусное сходство
    similarities = cosine_similarity(target_scaled, all_scaled)[0]

    # Сортируем по убыванию сходства (исключая сам товар)
    scored = [(i, sim) for i, sim in enumerate(similarities) if all_products[i].id != product.id]
    scored.sort(key=lambda x: x[1], reverse=True)

    # Возвращаем топ-K
    result = [(all_products[idx], float(sim)) for idx, sim in scored[:top_k]]
    return result


def train_all_models():
    """Обучение всех ML моделей"""
    print("🤖 Обучение ML моделей...")

    db = SessionLocal()
    try:
        products = db.query(Product).all()
        print(f"📦 Загружено {len(products)} товаров")

        # Кластеризация
        print("\n🔵 Кластеризация...")
        clusterer = ProductClusterer(n_clusters=3)
        clusterer.fit(products)

        # Модель цен
        print("\n💰 Модель цен...")
        predictor = PricePredictor()
        predictor.fit(products)

        print("\n✅ Обучение завершено!")

    finally:
        db.close()


if __name__ == "__main__":
    train_all_models()
