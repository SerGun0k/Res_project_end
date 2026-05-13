"""
Скрипт загрузки спецификаций из JSON в БД.

Читает data/gpu_specs.json и создаёт записи в таблице products.
Запуск: python backend/data_pipeline/seed_data.py
"""

import json
import os
import sys
from datetime import datetime

# Добавляем backend в путь для импорта
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.database import SessionLocal, engine, Base
from app.models import Product

# Создаём таблицы если нет
Base.metadata.create_all(bind=engine)


def load_specs(filepath: str) -> dict:
    """Чтение JSON файла спецификаций"""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def seed_products(specs: dict, db: SessionLocal) -> tuple[int, int]:
    """
    Загрузка товаров в БД.
    Возвращает (создано, пропущено).
    """
    created = 0
    skipped = 0

    # Дополнительные спецификации для обогащения данных
    gpu_extra = {
        'interface': 'PCIe 4.0 x16',
        'country': 'Китай',
        'warranty': '3 года',
        'memory_bus': '256 бит',
        'ray_tracing': True,
        'dlss': True,
        'connectors': 'HDMI 2.1 + 3x DisplayPort 1.4a',
        'length_mm': 285,
        'recommended_psu': '650 Вт',
        'base_clock_mhz': 1440,
        'boost_clock_mhz': 1800,
    }
    cpu_extra = {
        'country': 'Китай',
        'warranty': '3 года',
        'pcie_version': 'PCIe 5.0',
        'l3_cache_mb': 32,
        'lithography_nm': 5,
        'integrated_graphics': False,
        'unlocked': True,
    }
    ram_extra = {
        'country': 'Тайвань',
        'warranty': 'Пожизненная',
        'heatsink': True,
        'cas_latency': 36,
        'voltage': 1.35,
        'modules': 2,
        'ecc': False,
    }
    ssd_extra = {
        'country': 'Китай',
        'warranty': '5 лет',
        'nand_type': 'TLC',
        'form_factor': '2.5"',
        'interface': 'SATA III 6Gb/s',
        'iops_read': 90000,
        'iops_write': 80000,
        'tbw': 600,
    }
    hdd_extra = {
        'country': 'Таиланд',
        'warranty': '2 года',
        'interface': 'SATA III 6Gb/s',
        'cache_mb': 256,
        'form_factor': '3.5"',
    }
    psu_extra = {
        'country': 'Китай',
        'warranty': '7 лет',
        'pfc': True,
        'modular': 'Полная',
        'efficiency': '80 Plus Gold',
        'fan_size': 120,
        'atx_version': 'ATX 3.0',
    }
    cooling_extra = {
        'country': 'Китай',
        'warranty': '2 года',
        'fan_rpm': 1500,
        'noise_dba': 25,
        'height_mm': 155,
        'cooler_type': 'Башенный',
        'fan_count': 1,
    }

    category_extras = {
        'GPU': gpu_extra,
        'CPU': cpu_extra,
        'RAM': ram_extra,
        'SSD': ssd_extra,
        'HDD': hdd_extra,
        'M2': ssd_extra,
        'PSU': psu_extra,
        'COOLING': cooling_extra,
    }

    for category, items in specs.items():
        category_upper = category.upper()
        extras = category_extras.get(category_upper, {})

        # Определяем subcategory
        subcategory = None
        if category_upper == 'M2':
            subcategory = 'M2'
            category_upper = 'SSD'  # M2 теперь подкатегория SSD

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

            # Формируем specs — убираем id и release_date, остальное в JSON + enrichment
            specs_data = {k: v for k, v in item.items()
                          if k not in ("id", "brand", "model")}

            # Добавляем дополнительные характеристики
            specs_data.update(extras)

            # Специфичные для GPU: добавляем interface если нет
            if category_upper == 'GPU' and 'interface' not in specs_data:
                specs_data['interface'] = 'PCIe 4.0'
            if category_upper == 'GPU' and 'country' not in specs_data:
                specs_data['country'] = 'Китай'

            # Парсим дату
            release_date = None
            if "release_date" in item:
                try:
                    release_date = datetime.strptime(
                        item["release_date"], "%Y-%m-%d"
                    )
                except ValueError:
                    pass

            product = Product(
                category=category_upper,
                subcategory=subcategory,
                brand=item["brand"],
                model=item["model"],
                specs=specs_data,
                release_date=release_date,
            )

            db.add(product)
            created += 1
            print(f"  ✅ Добавлен: {category_upper}{f' → {subcategory}' if subcategory else ''} {item['brand']} {item['model']}")

    db.commit()
    return created, skipped


def main():
    # Определяем путь к JSON
    # В Docker Compose data монтируется как /app/data
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    specs_file = os.path.join(data_dir, "gpu_specs.json")

    if not os.path.exists(specs_file):
        print(f"❌ Файл не найден: {specs_file}")
        sys.exit(1)

    print(f"📂 Загрузка спецификаций из {specs_file}")
    specs = load_specs(specs_file)

    db = SessionLocal()
    try:
        created, skipped = seed_products(specs, db)
        print(f"\n📊 Итого: создано={created}, пропущено={skipped}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
