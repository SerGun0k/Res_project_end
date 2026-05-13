"""
Скрипт расчёта себестоимости для всех товаров в БД.

Модель оценки основана на реальных данных о стоимости сырья (2024-2025):
  - Кремниевые пластины (300мм): ~$5000-10000 за пластину
  - Медь: ~$8.5/кг
  - Алюминий: ~$2.5/кг
  - PCB: ~$5-50 в зависимости от сложности
  - Память (GDDR6): ~$8-12/ГБ
  - Логистика: Китай→Россия ~$2-5/кг + таможня 15-20%

Источники данных:
  - TechInsights: разбор стоимости GPU/CPU
  - IC Insights: стоимость кремниевых пластин
  - Shanghai Metals Market: цены на медь/алюминий

Запуск: python backend/data_pipeline/seed_costs.py
"""

import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import and_
from app.database import SessionLocal
from app.models import Product, CostEstimate

# === Реальные коэффициенты себестоимости (обновлённые 2025) ===

COST_COEFFICIENTS = {
    "GPU": {
        # Базовая стоимость: PCB + кремний + разъёмы
        "base_materials": 8000,
        # GDDR6 память: ~$10/ГБ = ~900₽/ГБ (курс ~90₽/$)
        "per_memory_gb": 900,
        # Система охлаждения (медь + алюминий)
        "per_tdp": 25,
        # Логистика: доставка 1-2кг + таможня 15%
        "logistics": 4500,
        # Сборка, тестирование, упаковка
        "labor": 3000,
    },
    "CPU": {
        # Кремний + подложка + крышка
        "base_materials": 5000,
        "per_core": 600,
        "per_tdp": 12,
        "logistics": 2500,
        "labor": 2000,
    },
    "RAM": {
        # PCB + контроллер
        "base_materials": 800,
        # DDR4/DDR5 чипы: ~350₽/ГБ
        "per_capacity_gb": 350,
        "logistics": 600,
        "labor": 400,
    },
    "SSD": {
        # PCB + контроллер NAND
        "base_materials": 1200,
        # NAND TLC: ~8₽/ГБ
        "per_capacity_gb": 8,
        "logistics": 800,
        "labor": 500,
    },
    "HDD": {
        # Механика + пластины + корпус
        "base_materials": 2500,
        "per_capacity_gb": 1.8,
        "logistics": 2000,
        "labor": 1000,
    },
    "M2": {
        # Компактный PCB + NAND
        "base_materials": 1000,
        "per_capacity_gb": 9,
        "logistics": 600,
        "labor": 400,
    },
    "PSU": {
        # Компоненты: конденсаторы, трансформаторы, радиаторы
        "base_materials": 1500,
        "per_watt": 12,
        "logistics": 2000,
        "labor": 1200,
    },
    "COOLING": {
        # Медные теплотрубки + алюминиевый радиатор
        "base_materials": 1200,
        "per_tdp": 15,
        "logistics": 1500,
        "labor": 800,
    },
}


def calculate_product_cost(product: Product) -> dict:
    """
    Расчёт себестоимости одного товара.
    Возвращает dict с materials_cost, logistics_cost, labor_cost, total.
    """
    category = product.category
    specs = product.specs or {}
    coeffs = COST_COEFFICIENTS.get(category)

    if not coeffs:
        return None

    # Материалы
    materials = coeffs["base_materials"]

    if category == "GPU":
        mem = specs.get("memory_gb")
        if mem:
            materials += mem * coeffs["per_memory_gb"]
        tdp = specs.get("tdp_watts")
        if tdp:
            materials += tdp * coeffs.get("per_tdp", 25)
    elif category == "CPU":
        cores = specs.get("cores")
        if cores:
            materials += cores * coeffs["per_core"]
        tdp = specs.get("tdp_watts")
        if tdp:
            materials += tdp * coeffs.get("per_tdp", 12)
    elif category == "RAM":
        cap = specs.get("capacity_gb")
        if cap:
            materials += cap * coeffs["per_capacity_gb"]
    elif category in ("SSD", "M2"):
        cap = specs.get("capacity_gb")
        if cap:
            materials += cap * coeffs["per_capacity_gb"]
    elif category == "HDD":
        cap = specs.get("capacity_gb")
        if cap:
            materials += cap * coeffs["per_capacity_gb"]
    elif category == "PSU":
        watts = specs.get("watts")
        if watts:
            materials += watts * coeffs.get("per_watt", 12)
    elif category == "COOLING":
        tdp = specs.get("tdp_watts") or specs.get("max_tdp_watts")
        if tdp:
            materials += tdp * coeffs.get("per_tdp", 15)

    logistics = coeffs["logistics"]
    labor = coeffs["labor"]
    total = materials + logistics + labor

    return {
        "materials_cost": round(materials, 2),
        "logistics_cost": round(logistics, 2),
        "labor_cost": round(labor, 2),
        "total": round(total, 2),
    }


def seed_costs(db: SessionLocal) -> tuple[int, int]:
    """
    Расчёт и сохранение себестоимости для всех товаров.
    Возвращает (обновлено, ошибок).
    """
    products = db.query(Product).all()
    updated = 0
    errors = 0

    for product in products:
        cost_data = calculate_product_cost(product)

        if not cost_data:
            print(f"  ⚠️ Нет коэффициентов для {product.category}: {product.model}")
            errors += 1
            continue

        # Проверяем существующую запись
        existing = db.query(CostEstimate).filter(
            CostEstimate.product_id == product.id
        ).first()

        if existing:
            existing.materials_cost = cost_data["materials_cost"]
            existing.logistics_cost = cost_data["logistics_cost"]
            existing.labor_cost = cost_data["labor_cost"]
            existing.total = cost_data["total"]
            existing.last_updated = datetime.utcnow()
            print(f"  🔄 Обновлено: {product.brand} {product.model}")
        else:
            estimate = CostEstimate(
                product_id=product.id,
                **cost_data,
            )
            db.add(estimate)
            print(f"  ✅ Создано: {product.brand} {product.model} = {cost_data['total']} RUB")

        updated += 1

    db.commit()
    return updated, errors


def main():
    print("📊 Расчёт себестоимости товаров")
    db = SessionLocal()

    try:
        updated, errors = seed_costs(db)
        print(f"\n📊 Итого: обновлено={updated}, ошибок={errors}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
