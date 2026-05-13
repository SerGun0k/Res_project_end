"""
Скрипт генерации отзывов и статистики популярности.

Создаёт записи в review_quality и popularity_stats для всех товаров.
Запуск: python backend/data_pipeline/seed_reviews.py
"""

import os
import sys
import random
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.database import SessionLocal
from app.models import Product, ReviewQuality, PopularityStats

# Источники отзывов
REVIEW_SOURCES = ["DNS", "Ozon", "Citilink", "M.Video", "Ситилинк"]

# Диапазоны рейтингов по брендам (реалистичные)
BRAND_RATING_RANGES = {
    "NVIDIA": (4.2, 4.8),
    "AMD": (4.0, 4.6),
    "Intel": (4.1, 4.7),
    "Samsung": (4.3, 4.9),
    "WD": (3.8, 4.5),
    "Seagate": (3.5, 4.2),
    "Corsair": (4.0, 4.7),
    "G.Skill": (4.2, 4.8),
    "Kingston": (3.9, 4.5),
    "Crucial": (4.0, 4.6),
}


def generate_reviews(db: SessionLocal) -> int:
    """Генерация записей review_quality"""
    products = db.query(Product).all()
    created = 0

    for product in products:
        # Проверяем существующую запись
        existing = db.query(ReviewQuality).filter(
            ReviewQuality.product_id == product.id
        ).first()

        if existing:
            print(f"  ⏭ Пропуск отзывов: {product.brand} {product.model}")
            continue

        # Рейтинг бренда
        rating_range = BRAND_RATING_RANGES.get(product.brand, (3.5, 4.5))
        avg_rating = round(random.uniform(*rating_range), 2)

        # Процент брака (обратная зависимость от рейтинга)
        defect_rate = round(max(0.5, (5.0 - avg_rating) * 2 + random.uniform(0, 1)), 2)

        # Количество отзывов (зависит от категории)
        category_review_count = {
            "GPU": (50, 300),
            "CPU": (40, 250),
            "RAM": (20, 150),
            "SSD": (30, 200),
            "HDD": (15, 100),
            "M2": (25, 180),
        }
        min_rev, max_rev = category_review_count.get(product.category, (20, 150))
        reviews_count = random.randint(min_rev, max_rev)

        source = random.choice(REVIEW_SOURCES)

        review = ReviewQuality(
            product_id=product.id,
            avg_rating=avg_rating,
            defect_rate=defect_rate,
            reviews_count=reviews_count,
            source=source,
        )
        db.add(review)
        created += 1
        print(f"  ✅ Отзыв: {product.brand} {product.model} рейтинг={avg_rating} отзывы={reviews_count}")

    db.commit()
    return created


def generate_popularity(db: SessionLocal) -> int:
    """Генерация статистики популярности"""
    products = db.query(Product).all()
    created = 0

    for product in products:
        existing = db.query(PopularityStats).filter(
            PopularityStats.product_id == product.id
        ).first()

        if existing:
            print(f"  ⏭ Пропуск популярности: {product.brand} {product.model}")
            continue

        # Популярные товары получают больше просмотров
        category_views = {
            "GPU": (100, 800),
            "CPU": (80, 600),
            "RAM": (30, 300),
            "SSD": (50, 400),
            "HDD": (20, 150),
            "M2": (40, 350),
        }
        min_views, max_views = category_views.get(product.category, (30, 300))
        daily_views = random.randint(min_views, max_views)

        # Общие просмотры = daily_views * случайное число дней
        total_days = random.randint(30, 180)
        total_views = daily_views * total_days + random.randint(0, daily_views * 10)

        # Поисковые запросы ~30% от просмотров
        daily_searches = int(daily_views * random.uniform(0.2, 0.5))

        stats = PopularityStats(
            product_id=product.id,
            daily_views=daily_views,
            total_views=total_views,
            daily_searches=daily_searches,
        )
        db.add(stats)
        created += 1
        print(f"  📈 Популярность: {product.brand} {product.model} просмотры/день={daily_views}")

    db.commit()
    return created


def main():
    print("⭐ Генерация отзывов и статистики популярности")
    db = SessionLocal()

    try:
        reviews_created = generate_reviews(db)
        print(f"\n📊 Отзывы: создано={reviews_created}")

        popularity_created = generate_popularity(db)
        print(f"📊 Популярность: создано={popularity_created}")

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
