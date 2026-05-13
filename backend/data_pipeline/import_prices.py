"""
Импорт цен из CSV файла в price_history.

Формат CSV:
  brand,model,source,price,date,url

Пример:
  NVIDIA,RTX 4070,DNS,62999,2026-04-10,https://www.dns-shop.ru/product/...
  AMD,Ryzen 7 7800X3D,Ozon,34999,2026-04-10,https://www.ozon.ru/product/...

Запуск:
  python data_pipeline/import_prices.py backend/data/dns_prices.csv
"""

import csv
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Product, PriceHistory


def import_prices_from_csv(filepath: str, db: Session, dry_run: bool = False) -> dict:
    """
    Импорт цен из CSV.
    
    Returns:
        Статистика импорта
    """
    stats = {
        "total": 0,
        "imported": 0,
        "skipped": 0,
        "errors": 0,
        "products_not_found": 0,
    }
    
    if not os.path.exists(filepath):
        print(f"❌ Файл не найден: {filepath}")
        return stats
    
    print(f"📂 Импорт цен из: {filepath}")
    
    with open(filepath, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        
        for row_num, row in enumerate(reader, start=2):  # row 1 = headers
            stats["total"] += 1
            
            try:
                brand = row.get("brand", "").strip()
                model = row.get("model", "").strip()
                source = row.get("source", "Manual").strip()
                price_str = row.get("price", "").strip().replace(" ", "").replace("₽", "").replace(",", ".")
                date_str = row.get("date", "").strip()
                url = row.get("url", "").strip()
                
                # Валидация
                if not brand or not model or not price_str:
                    print(f"  ⏭ Строка {row_num}: пропущено (нет brand/model/price)")
                    stats["skipped"] += 1
                    continue
                
                try:
                    price = float(price_str)
                except ValueError:
                    print(f"  ⏭ Строка {row_num}: неверная цена '{price_str}'")
                    stats["errors"] += 1
                    continue
                
                # Парсим дату
                if date_str:
                    try:
                        date = datetime.strptime(date_str, "%Y-%m-%d")
                    except ValueError:
                        date = datetime.utcnow()
                else:
                    date = datetime.utcnow()
                
                # Ищем товар
                product = db.query(Product).filter(
                    Product.brand == brand,
                    Product.model == model,
                ).first()
                
                if not product:
                    print(f"  ⚠️ Строка {row_num}: товар не найден — {brand} {model}")
                    stats["products_not_found"] += 1
                    stats["skipped"] += 1
                    continue
                
                # Сохраняем цену
                if not dry_run:
                    price_record = PriceHistory(
                        product_id=product.id,
                        source=source,
                        price=price,
                        date=date,
                    )
                    db.add(price_record)
                    db.commit()
                
                stats["imported"] += 1
                print(f"  ✅ {brand} {model} → {price:,.0f} ₽ ({source})")
                
            except Exception as e:
                print(f"  ❌ Строка {row_num}: ошибка — {e}")
                stats["errors"] += 1
                if not dry_run:
                    db.rollback()
    
    return stats


def main():
    if len(sys.argv) < 2:
        print("Использование: python import_prices.py <файл.csv> [--dry-run]")
        print("\nФормат CSV:")
        print("  brand,model,source,price,date,url")
        print("\nПример:")
        print("  NVIDIA,RTX 4070,DNS,62999,2026-04-10,https://...")
        return
    
    filepath = sys.argv[1]
    dry_run = "--dry-run" in sys.argv
    
    if dry_run:
        print("🔍 Режим проверки (без сохранения)")
    
    db = SessionLocal()
    try:
        stats = import_prices_from_csv(filepath, db, dry_run)
        
        print("\n" + "=" * 50)
        print("📊 Итог импорта:")
        print(f"  Всего строк:     {stats['total']}")
        print(f"  Импортировано:   {stats['imported']}")
        print(f"  Пропущено:       {stats['skipped']}")
        print(f"  Товар не найден: {stats['products_not_found']}")
        print(f"  Ошибок:          {stats['errors']}")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()
