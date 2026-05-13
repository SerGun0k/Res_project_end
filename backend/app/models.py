from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, JSON, Text, UniqueConstraint
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Product(Base):
    """Основная таблица товаров"""
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String(50), nullable=False, index=True)  # GPU, CPU, RAM, SSD, HDD, PSU, COOLING
    subcategory = Column(String(50), nullable=True, index=True)  # M2, SATA, NVMe для SSD
    brand = Column(String(100), nullable=False, index=True)
    model = Column(String(200), nullable=False)
    specs = Column(JSON, nullable=True)  # Гибкое хранилище характеристик
    release_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Отношения
    price_history = relationship("PriceHistory", back_populates="product", lazy="select", cascade="all, delete-orphan")
    cost_estimate = relationship("CostEstimate", back_populates="product", uselist=False, lazy="select", cascade="all, delete-orphan")
    review_quality = relationship("ReviewQuality", back_populates="product", uselist=False, lazy="select", cascade="all, delete-orphan")
    popularity_stats = relationship("PopularityStats", back_populates="product", uselist=False, lazy="select", cascade="all, delete-orphan")
    price_predictions = relationship("PricePrediction", back_populates="product", uselist=False, lazy="select", cascade="all, delete-orphan")
    user_feedback = relationship("UserFeedback", back_populates="product", lazy="select", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("category", "brand", "model", name="uq_product_cat_brand_model"),
    )


class PriceHistory(Base):
    """История цен по источникам"""
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    source = Column(String(100), nullable=False)  # Ozon, DNS, Yandex Market и т.д.
    price = Column(Float, nullable=False)
    date = Column(DateTime, default=datetime.utcnow, index=True)

    product = relationship("Product", back_populates="price_history")


class CostEstimate(Base):
    """Расчётная себестоимость"""
    __tablename__ = "cost_estimates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, unique=True)
    materials_cost = Column(Float, nullable=False, comment="Стоимость материалов")
    logistics_cost = Column(Float, nullable=False, comment="Логистика и таможня")
    labor_cost = Column(Float, nullable=False, comment="Сборка и тестирование")
    total = Column(Float, nullable=False, comment="Итоговая себестоимость")
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    product = relationship("Product", back_populates="cost_estimate")


class ReviewQuality(Base):
    """Метрики качества на основе отзывов"""
    __tablename__ = "reviews_quality"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, unique=True)
    avg_rating = Column(Float, nullable=True, comment="Средний рейтинг")
    defect_rate = Column(Float, nullable=True, comment="Процент брака")
    reviews_count = Column(Integer, nullable=True, comment="Количество отзывов")
    source = Column(String(100), nullable=True, comment="Источник отзывов")
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    product = relationship("Product", back_populates="review_quality")


class PopularityStats(Base):
    """Статистика популярности"""
    __tablename__ = "popularity_stats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, unique=True)
    daily_views = Column(Integer, default=0, comment="Просмотры за день")
    total_views = Column(Integer, default=0, comment="Всего просмотров")
    daily_searches = Column(Integer, default=0, comment="Поисковые запросы за день")
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    product = relationship("Product", back_populates="popularity_stats")


class PricePrediction(Base):
    """Предсказание цен"""
    __tablename__ = "price_predictions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, unique=True)
    current_price = Column(Float, nullable=False, comment="Текущая цена")
    predicted_1m = Column(Float, nullable=True, comment="Прогноз на 1 месяц")
    predicted_3m = Column(Float, nullable=True, comment="Прогноз на 3 месяца")
    trend = Column(String(20), nullable=True, comment="Тренд: rising, falling, stable")
    recommendation = Column(String(50), nullable=True, comment="Рекомендация: buy_now, wait, no_rush")
    confidence = Column(Float, nullable=True, comment="Уверенность прогноза (0-1)")
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    product = relationship("Product", back_populates="price_predictions")


class UserFeedback(Base):
    """Обратная связь пользователей"""
    __tablename__ = "user_feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_session = Column(String(100), nullable=False, index=True, comment="ID сессии пользователя")
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    feedback_type = Column(String(20), nullable=False, comment="Тип: useful, not_useful, click, bookmark")
    alternative_id = Column(Integer, nullable=True, comment="ID рекомендованного товара")
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    product = relationship("Product", back_populates="user_feedback")


class UserBehavior(Base):
    """Трекинг поведения пользователя"""
    __tablename__ = "user_behavior"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_session = Column(String(100), nullable=False, index=True)
    action = Column(String(50), nullable=False, comment="Действие: search, view_product, click_alternative, compare")
    search_query = Column(String(200), nullable=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    target_product_id = Column(Integer, nullable=True, comment="Целевой товар (для альтернатив)")
    category = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
