"""Legacy роутер DNS (парсинг отключён в пользу открытых источников данных)."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import PriceHistory

router = APIRouter()


@router.post("/fetch-dns-price/{product_id}")
async def fetch_dns_price(
    product_id: int,
    db: Session = Depends(get_db),
):
    """Парсинг DNS отключён."""
    raise HTTPException(
        status_code=410,
        detail=(
            "DNS parsing is disabled. Use open-data import via "
            "`python data_pipeline/import_open_prices.py --url <csv_url>`."
        ),
    )


@router.post("/fetch-all-dns-prices")
async def fetch_all_dns_prices(
    db: Session = Depends(get_db),
):
    """Массовый парсинг DNS отключён."""
    raise HTTPException(
        status_code=410,
        detail=(
            "Bulk DNS parsing is disabled. Use open-data import via "
            "`python data_pipeline/import_open_prices.py`."
        ),
    )


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
