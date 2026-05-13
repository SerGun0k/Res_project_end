"""Роутер для импорта цен из CSV"""

import csv
import io
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Product, PriceHistory

router = APIRouter()


@router.post("/import-prices-csv")
async def import_prices_csv(
    file: UploadFile = File(...),
    source: str = Query("Manual", description="Источник цен (DNS, Ozon, etc)"),
    db: Session = Depends(get_db),
):
    """
    Импорт цен из CSV файла.
    
    Формат CSV:
      brand,model,price,date,url
    
    Пример:
      NVIDIA,RTX 4070,62999,2026-04-10,https://...
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Файл должен быть CSV")
    
    content = await file.read()
    text = content.decode('utf-8-sig')  # UTF-8 with BOM support
    
    stats = {
        "total": 0,
        "imported": 0,
        "skipped": 0,
        "errors": 0,
        "products_not_found": 0,
    }
    
    try:
        reader = csv.DictReader(io.StringIO(text))
        
        for row_num, row in enumerate(reader, start=2):
            stats["total"] += 1
            
            try:
                brand = row.get("brand", "").strip()
                model = row.get("model", "").strip()
                price_str = row.get("price", "").strip().replace(" ", "").replace("₽", "").replace(",", ".")
                date_str = row.get("date", "").strip()
                
                # Валидация
                if not brand or not model or not price_str:
                    stats["skipped"] += 1
                    continue
                
                try:
                    price = float(price_str)
                except ValueError:
                    stats["errors"] += 1
                    continue
                
                # Дата
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
                    stats["products_not_found"] += 1
                    stats["skipped"] += 1
                    continue
                
                # Сохраняем
                price_record = PriceHistory(
                    product_id=product.id,
                    source=source,
                    price=price,
                    date=date,
                )
                db.add(price_record)
                stats["imported"] += 1
                
            except Exception:
                stats["errors"] += 1
        
        db.commit()
        
        return {
            "status": "success",
            "message": f"Импортировано {stats['imported']} цен из {stats['total']} строк",
            "stats": stats,
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка импорта: {str(e)}")


@router.get("/import-prices-template")
async def get_csv_template():
    """
    Скачать шаблон CSV для импорта цен.
    """
    template = """brand,model,source,price,date,url
NVIDIA,RTX 4070,DNS,62999,2026-04-10,https://www.dns-shop.ru/search/?q=RTX+4070
AMD,Ryzen 7 7800X3D,DNS,34999,2026-04-10,https://www.dns-shop.ru/search/?q=Ryzen+7
"""
    
    return JSONResponse(
        content={"template": template, "instructions": """
1. Скачайте шаблон CSV
2. Заполните brand, model, price (остальные поля опциональны)
3. Загрузите файл через POST /api/v1/import-prices-csv
4. Формат даты: YYYY-MM-DD
5. Цена: число без пробелов (62999, не 62 999)
        """}
    )


@router.get("/price-sources")
async def get_price_sources(db: Session = Depends(get_db)):
    """
    Показать все источники цен и количество записей.
    """
    from sqlalchemy import func
    
    sources = (
        db.query(
            PriceHistory.source,
            func.count(PriceHistory.id).label("count"),
            func.min(PriceHistory.date).label("first_date"),
            func.max(PriceHistory.date).label("last_date"),
        )
        .group_by(PriceHistory.source)
        .all()
    )
    
    return {
        "sources": [
            {
                "source": s.source,
                "count": s.count,
                "first_date": s.first_date.isoformat() if s.first_date else None,
                "last_date": s.last_date.isoformat() if s.last_date else None,
            }
            for s in sources
        ]
    }
