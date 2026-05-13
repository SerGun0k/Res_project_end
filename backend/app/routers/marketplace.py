"""Роутер сравнения цен по маркетплейсам"""

from typing import Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.models import Product, PriceHistory
from app.schemas import ProductRead

router = APIRouter()


class MarketplacePrice:
    def __init__(self, source: str, price: float, date: datetime, url: str = ""):
        self.source = source
        self.price = price
        self.date = date
        self.url = url


@router.get("/marketplace-prices/{product_id}")
async def get_marketplace_prices(
    product_id: int,
    db: Session = Depends(get_db),
):
    """
    Получение цен товара по разным маркетплейсам.
    Возвращает последние цены из каждого источника.
    """
    # Получаем товар
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return {"error": "Товар не найден"}

    # Получаем последние цены из каждого источника
    sources = ["DNS", "Ozon", "Citilink", "Yandex.Market", "M.Video", "EMEX"]
    
    prices = []
    for source in sources:
        latest = (
            db.query(PriceHistory)
            .filter(
                PriceHistory.product_id == product_id,
                PriceHistory.source == source,
            )
            .order_by(desc(PriceHistory.date))
            .first()
        )
        
        if latest:
            # Генерируем ссылку на товар
            url = _generate_marketplace_url(source, product.brand, product.model)
            prices.append({
                "source": source,
                "price": latest.price,
                "date": latest.date.isoformat(),
                "url": url,
                "logo": _get_marketplace_logo(source),
            })

    # Сортируем по цене
    prices.sort(key=lambda x: x["price"])

    # Находим лучшую цену
    best_price = prices[0]["price"] if prices else None

    return {
        "product_id": product_id,
        "product_name": f"{product.brand} {product.model}",
        "prices": prices,
        "best_price": best_price,
        "best_source": prices[0]["source"] if prices else None,
        "price_diff": round(prices[-1]["price"] - prices[0]["price"], 2) if len(prices) > 1 else 0,
    }


def _generate_marketplace_url(source: str, brand: str, model: str) -> str:
    """Генерация ссылки на товар в маркетплейсе"""
    query = f"{brand} {model}".replace(" ", "+")
    
    urls = {
        "DNS": f"https://www.dns-shop.ru/search/?q={query}",
        "Ozon": f"https://www.ozon.ru/search/?text={query}",
        "Citilink": f"https://www.citilink.ru/search/?text={query}",
        "Yandex.Market": f"https://market.yandex.ru/search?text={query}",
        "M.Video": f"https://www.mvideo.ru/search?text={query}",
        "EMEX": f"https://www.emex.ru/f/SEARCH?keyword={query}",
    }
    
    return urls.get(source, "")


def _get_marketplace_logo(source: str) -> str:
    """Эмодзи-логотип маркетплейса"""
    logos = {
        "DNS": "🟡",
        "Ozon": "🔵",
        "Citilink": "🔴",
        "Yandex.Market": "🟢",
        "M.Video": "🟣",
        "EMEX": "⚫",
    }
    return logos.get(source, "🏪")
