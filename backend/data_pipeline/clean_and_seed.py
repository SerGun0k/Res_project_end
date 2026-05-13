"""
Скрипт замены фейковых данных на реальные.

Порядок:
  1. Очистка всех таблиц
  2. Загрузка характеристик из data/real_specs.json
  3. Расчёт себестоимости
  4. Генерация рыночных цен
  5. Генерация отзывов и популярности

Запуск: python backend/data_pipeline/clean_and_seed.py
"""

import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.database import SessionLocal, engine, Base
from app.models import Product, PriceHistory, CostEstimate, ReviewQuality, PopularityStats
from data_pipeline import seed_costs, seed_prices, seed_reviews


def clean_db(db: SessionLocal):
    """Очистка всех таблиц"""
    print("🧹 Очистка БД...")
    db.query(PopularityStats).delete()
    db.query(ReviewQuality).delete()
    db.query(PriceHistory).delete()
    db.query(CostEstimate).delete()
    db.query(Product).delete()
    db.commit()
    print("  ✅ БД очищена")


def load_real_specs(filepath: str) -> dict:
    """Загрузка real_specs.json"""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def seed_real_products(specs: dict, db: SessionLocal) -> tuple[int, int]:
    """Загрузка реальных товаров в БД"""
    created = 0
    skipped = 0

    for category, items in specs.items():
        category_upper = category.upper()

        for item in items:
            # Проверяем дубликат
            existing = db.query(Product).filter(
                Product.category == category_upper,
                Product.brand == item["brand"],
                Product.model == item["model"],
            ).first()

            if existing:
                print(f"  ⏭ Пропуск: {item['brand']} {item['model']}")
                skipped += 1
                continue

            specs_data = {k: v for k, v in item.get("specs", {}).items()
                          if k != "release_date"}

            release_date = None
            if item.get("release_date"):
                try:
                    release_date = datetime.strptime(
                        item["release_date"], "%Y-%m-%d"
                    )
                except ValueError:
                    pass

            product = Product(
                category=category_upper,
                brand=item["brand"],
                model=item["model"],
                specs=specs_data,
                release_date=release_date,
            )

            db.add(product)
            created += 1
            print(f"  ✅ {category_upper} {item['brand']} {item['model']}")

    db.commit()
    return created, skipped


def main():
    print("=" * 60)
    print("🔄 Замена фейковых данных на реальные")
    print("=" * 60)

    # Загрузка спецификаций
    # Путь: /app/data/real_specs.json в Docker, ../../data/real_specs.json локально
    specs_file = os.path.join("/app", "data", "real_specs.json")

    if not os.path.exists(specs_file):
        specs_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "data", "real_specs.json"
        )

    if not os.path.exists(specs_file):
        print(f"❌ Файл не найден: {specs_file}")
        print("  Запустите сначала download_specs.py")
        sys.exit(1)

    print(f"\n📂 Загрузка спецификаций из {specs_file}")
    specs = load_real_specs(specs_file)

    total_specs = sum(len(v) for v in specs.values())
    print(f"  📊 Всего товаров: {total_specs}")
    for cat, items in specs.items():
        print(f"    {cat}: {len(items)}")

    db = SessionLocal()
    try:
        # Шаг 1: Очистка
        clean_db(db)

        # Шаг 2: Загрузка товаров
        print("\n📦 Загрузка реальных товаров")
        created, skipped = seed_real_products(specs, db)
        print(f"  Создано: {created}, пропущено: {skipped}")

        # Шаг 3: Себестоимость
        print("\n💰 Расчёт себестоимости")
        updated, errors = seed_costs.seed_costs(db)
        print(f"  Обновлено: {updated}, ошибок: {errors}")

        # Шаг 4: Рыночные цены
        print("\n📊 Генерация рыночных цен")
        prices_created, prices_skipped = seed_prices.generate_price_history(db)
        print(f"  Создано: {prices_created}, пропущено: {prices_skipped}")

        # Шаг 5: Отзывы и популярность
        print("\n⭐ Отзывы и статистика популярности")
        reviews = seed_reviews.generate_reviews(db)
        print(f"  Отзывы: {reviews}")
        popularity = seed_reviews.generate_popularity(db)
        print(f"  Популярность: {popularity}")

        print("\n" + "=" * 60)
        print("✅ Замена данных завершена!")
        print("=" * 60)

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
