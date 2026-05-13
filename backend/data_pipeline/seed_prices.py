"""
Скрипт генерации рыночных цен для товаров в БД.

Имитирует данные из нескольких источников:
  - DNS
  - Ozon
  - Yandex Market
  - Citilink

Генерирует историю цен за последние 6 месяцев с реалистичными колебаниями.
Запуск: python backend/data_pipeline/seed_prices.py
"""

import os
import sys
import random
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.database import SessionLocal
from app.models import Product, PriceHistory

# Источники цен
SOURCES = ["DNS", "Ozon", "Yandex Market", "Citilink"]

# Базовые цены по категориям и характеристикам (имитация реальных цен в RUB)
BASE_PRICES = {
    "GPU": {
        "base": 15000,
        "per_memory_gb": 1500,
        "per_tdp": 50,
    },
    "CPU": {
        "base": 5000,
        "per_core": 800,
        "per_tdp": 30,
    },
    "RAM": {
        "base": 2000,
        "per_capacity_gb": 250,
    },
    "SSD": {
        "base": 2500,
        "per_capacity_gb": 5,
    },
    "HDD": {
        "base": 2500,
        "per_capacity_gb": 0.8,
    },
    "M2": {
        "base": 3000,
        "per_capacity_gb": 6,
    },
}

# Коэффициенты брендов (премиум/бюджет)
BRAND_MULTIPLIERS = {
    "NVIDIA": 1.3,
    "AMD": 1.0,
    "Intel": 1.1,
    "Samsung": 1.2,
    "WD": 1.0,
    "Seagate": 0.9,
    "Corsair": 1.15,
    "G.Skill": 1.2,
    "Kingston": 0.95,
    "Crucial": 1.0,
    "Noctua": 1.3,
    "be quiet!": 1.2,
    "Seasonic": 1.25,
    "EVGA": 1.1,
    "Deepcool": 0.9,
    "Arctic": 0.85,
    "TeamGroup": 1.0,
    "ADATA": 1.05,
    "Toshiba": 0.85,
    "SK Hynix": 1.0,
    "Thermaltake": 1.1,
    "Cooler Master": 1.05,
}


def calculate_base_price(product: Product) -> float:
    """Расчёт базовой рыночной цены товара"""
    category = product.category
    specs = product.specs or {}
    coeffs = BASE_PRICES.get(category)

    if not coeffs:
        return 10000  # Заглушка

    price = coeffs["base"]

    if category == "GPU":
        mem = specs.get("memory_gb")
        if mem:
            price += mem * coeffs["per_memory_gb"]
        tdp = specs.get("tdp_watts")
        if tdp:
            price += tdp * coeffs.get("per_tdp", 50)
    elif category == "CPU":
        cores = specs.get("cores")
        if cores:
            price += cores * coeffs["per_core"]
        tdp = specs.get("tdp_watts")
        if tdp:
            price += tdp * coeffs.get("per_tdp", 30)
    elif category == "RAM":
        cap = specs.get("capacity_gb")
        if cap:
            price += cap * coeffs["per_capacity_gb"]
    elif category in ("SSD", "M2", "HDD"):
        cap = specs.get("capacity_gb")
        if cap:
            price += cap * coeffs["per_capacity_gb"]
    elif category == "PSU":
        watts = specs.get("watts")
        if watts:
            price += watts * 25  # ~25 руб за ватт
    elif category == "COOLING":
        cooling_type = specs.get("type", "")
        if "AIO" in cooling_type:
            price += 8000  # Жидкостное дороже
        else:
            price += 4000  # Воздушное

    # Коэффициент бренда
    brand_mult = BRAND_MULTIPLIERS.get(product.brand, 1.0)
    price *= brand_mult

    return round(price)


def generate_price_history(db: SessionLocal) -> tuple[int, int]:
    """
    Генерация истории цен за последние 6 месяцев.
    Для каждого товара: 2-3 источника, 3-6 записей на источник.
    Возвращает (создано, пропущено).
    """
    products = db.query(Product).all()
    created = 0
    skipped = 0

    now = datetime.utcnow()
    six_months_ago = now - timedelta(days=180)

    for product in products:
        base_price = calculate_base_price(product)

        # Выбираем 2-4 источника
        num_sources = random.randint(2, 4)
        sources = random.sample(SOURCES, num_sources)

        for source in sources:
            # Количество записей на источник
            num_entries = random.randint(3, 6)

            for i in range(num_entries):
                # Случайная дата в пределах 6 месяцев
                days_ago = random.randint(0, 180)
                date = six_months_ago + timedelta(days=days_ago)

                # Вариация цены: ±15% от базовой
                variation = random.uniform(0.85, 1.15)
                price = round(base_price * variation)

                # Проверяем дубликат (тот же товар + источник + дата ±1 день)
                existing = db.query(PriceHistory).filter(
                    PriceHistory.product_id == product.id,
                    PriceHistory.source == source,
                    PriceHistory.date >= date - timedelta(days=1),
                    PriceHistory.date <= date + timedelta(days=1),
                ).first()

                if existing:
                    skipped += 1
                    continue

                entry = PriceHistory(
                    product_id=product.id,
                    source=source,
                    price=price,
                    date=date,
                )
                db.add(entry)
                created += 1

        print(f"  ✅ {product.brand} {product.model}: база={base_price} RUB, источников={len(sources)}")

    db.commit()
    return created, skipped


def main():
    print("💰 Генерация рыночных цен")
    db = SessionLocal()

    try:
        created, skipped = generate_price_history(db)
        print(f"\n📊 Итого: создано={created}, пропущено={skipped}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
