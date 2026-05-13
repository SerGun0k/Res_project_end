"""Роутер для получения реальных цен из DNS"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Product, PriceHistory

router = APIRouter()


@router.post("/fetch-dns-price/{product_id}")
async def fetch_dns_price(
    product_id: int,
    db: Session = Depends(get_db),
):
    """
    Получение реальной цены товара из DNS.
    Парсит dns-shop.ru и сохраняет цену в price_history.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")

    try:
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
        
        from data_pipeline.dns_scraper import get_product_price
        
        result = get_product_price(product.brand, product.model, product.category)
        
        if not result:
            return {
                "product_id": product_id,
                "source": "DNS",
                "status": "not_found",
                "message": f"Товар не найден в DNS по запросу '{product.brand} {product.model}'",
            }
        
        # Сохраняем в price_history
        price_record = PriceHistory(
            product_id=product_id,
            source="DNS",
            price=result.price,
            date=datetime.utcnow(),
        )
        db.add(price_record)
        db.commit()
        
        return {
            "product_id": product_id,
            "source": "DNS",
            "status": "success",
            "price": result.price,
            "product_name": result.name,
            "url": result.url,
            "availability": result.availability,
            "fetched_at": datetime.utcnow().isoformat(),
        }
        
    except ImportError:
        raise HTTPException(status_code=503, detail="Зависимости парсера не установлены")
    except Exception as e:
        return {
            "product_id": product_id,
            "source": "DNS",
            "status": "error",
            "message": f"Ошибка парсинга: {str(e)}",
        }


@router.post("/fetch-all-dns-prices")
async def fetch_all_dns_prices(
    db: Session = Depends(get_db),
):
    """
    Обновление цен всех товаров из DNS.
    Внимание: может занять время (задержка между запросами).
    """
    products = db.query(Product).all()
    
    results = []
    for product in products:
        try:
            from data_pipeline.dns_scraper import get_product_price
            
            result = get_product_price(product.brand, product.model, product.category)
            
            if result:
                price_record = PriceHistory(
                    product_id=product.id,
                    source="DNS",
                    price=result.price,
                    date=datetime.utcnow(),
                )
                db.add(price_record)
                db.commit()
                
                results.append({
                    "product_id": product.id,
                    "status": "success",
                    "price": result.price,
                })
            else:
                results.append({
                    "product_id": product.id,
                    "status": "not_found",
                })
                
        except Exception as e:
            results.append({
                "product_id": product.id,
                "status": "error",
                "message": str(e),
            })
        
        # Задержка чтобы не забанили
        import time
        time.sleep(2)
    
    success = sum(1 for r in results if r["status"] == "success")
    return {
        "total": len(results),
        "success": success,
        "not_found": sum(1 for r in results if r["status"] == "not_found"),
        "errors": sum(1 for r in results if r["status"] == "error"),
        "details": results,
    }


@router.get("/dns-prices/{product_id}")
async def get_dns_prices(
    product_id: int,
    db: Session = Depends(get_db),
):
    """
    Получить сохранённые цены из DNS для товара.
    """
    prices = (
        db.query(PriceHistory)
        .filter(
            PriceHistory.product_id == product_id,
            PriceHistory.source == "DNS",
        )
        .order_by(PriceHistory.date.desc())
        .limit(20)
        .all()
    )
    
    return {
        "product_id": product_id,
        "prices": [
            {
                "price": p.price,
                "date": p.date.isoformat(),
            }
            for p in prices
        ],
        "latest_price": prices[0].price if prices else None,
    }
