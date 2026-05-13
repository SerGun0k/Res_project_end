"""
Объединяющий скрипт заполнения БД тестовыми данными.

Порядок выполнения:
  1. seed_data.py — товары из JSON
  2. seed_costs.py — расчёт себестоимости
  3. seed_prices.py — история рыночных цен
  4. seed_reviews.py — отзывы и популярность

Запуск: python backend/data_pipeline/seed_all.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from data_pipeline import seed_data, seed_costs, seed_prices, seed_reviews
from app.database import SessionLocal, Base, engine


def main():
    print("=" * 60)
    print("🚀 Заполнение БД тестовыми данными")
    print("=" * 60)

    # Создаём таблицы
    print("\n📋 Шаг 0: Создание таблиц")
    Base.metadata.create_all(bind=engine)
    print("  ✅ Таблицы готовы")

    # Шаг 1: Загрузка товаров
    print("\n📦 Шаг 1: Загрузка спецификаций")
    # Путь относительно директории проекта (/app в Docker)
    specs_file = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "data", "gpu_specs.json"
    )
    specs = seed_data.load_specs(specs_file)
    db = SessionLocal()
    try:
        created, skipped = seed_data.seed_products(specs, db)
        print(f"  Создано: {created}, пропущено: {skipped}")
    finally:
        db.close()

    # Шаг 2: Себестоимость
    print("\n💰 Шаг 2: Расчёт себестоимости")
    db = SessionLocal()
    try:
        updated, errors = seed_costs.seed_costs(db)
        print(f"  Обновлено: {updated}, ошибок: {errors}")
    finally:
        db.close()

    # Шаг 3: Рыночные цены
    print("\n📊 Шаг 3: Генерация рыночных цен")
    db = SessionLocal()
    try:
        created, skipped = seed_prices.generate_price_history(db)
        print(f"  Создано: {created}, пропущено: {skipped}")
    finally:
        db.close()

    # Шаг 4: Отзывы и популярность
    print("\n⭐ Шаг 4: Отзывы и статистика популярности")
    db = SessionLocal()
    try:
        reviews = seed_reviews.generate_reviews(db)
        print(f"  Отзывы: {reviews}")
        popularity = seed_reviews.generate_popularity(db)
        print(f"  Популярность: {popularity}")
    finally:
        db.close()

    print("\n" + "=" * 60)
    print("✅ Заполнение БД завершено!")
    print("=" * 60)


if __name__ == "__main__":
    main()
