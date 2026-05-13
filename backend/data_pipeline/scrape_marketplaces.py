"""
Manual marketplace scraping into price_history (best-effort).

Идея:
- выбираем из БД товары по категориям
- для каждого товара пробуем найти цену в DNS/Ozon/Citilink (по поиску brand+model)
- сохраняем результаты в price_history

Запуск (в Docker):
  docker compose exec -T backend python data_pipeline/scrape_marketplaces.py --stores dns,ozon,citilink --limit 100 --headless true

Важно:
- без официальных API Ozon/Citilink могут блокировать (капча). Скрипт не падает, просто пропускает.
- DNS парсится через Playwright; demo fallback выключен (чтобы не подмешивать синтетику).
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Product, PriceHistory
from data_pipeline.dns_scraper import get_product_price
from data_pipeline.market_scrapers import fetch_ozon_price, fetch_citilink_price


DEFAULT_CATEGORIES = ["GPU", "CPU", "RAM", "SSD", "HDD", "PSU", "COOLING"]


def _pick_products(db: Session, category: str, limit: int) -> list[Product]:
    return (
        db.query(Product)
        .filter(Product.category == category)
        .order_by(Product.id.desc())
        .limit(limit)
        .all()
    )


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--stores", default="dns,ozon,citilink", help="dns,ozon,citilink")
    p.add_argument("--categories", default=",".join(DEFAULT_CATEGORIES))
    p.add_argument("--limit", type=int, default=100, help="сколько товаров на категорию")
    p.add_argument("--headless", default="true", choices=["true", "false"])
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    stores = [s.strip().lower() for s in args.stores.split(",") if s.strip()]
    categories = [c.strip().upper() for c in args.categories.split(",") if c.strip()]
    headless = args.headless == "true"

    db = SessionLocal()
    try:
        total_attempts = 0
        total_saved = 0
        total_skipped = 0

        for category in categories:
            products = _pick_products(db, category, args.limit)
            print(f"\n== Category {category}: products={len(products)} (limit={args.limit}) ==")

            for prod in products:
                query = f"{prod.brand} {prod.model}".strip()

                for store in stores:
                    total_attempts += 1
                    price = None

                    if store == "dns":
                        result = get_product_price(
                            prod.brand,
                            prod.model,
                            prod.category,
                            headless=headless,
                            allow_demo=False,
                        )
                        if result:
                            price = float(result.price)
                            source = "DNS"
                    elif store == "ozon":
                        result = fetch_ozon_price(query, headless=headless)
                        if result:
                            price = float(result.price)
                            source = "Ozon"
                    elif store == "citilink":
                        result = fetch_citilink_price(query, headless=headless)
                        if result:
                            price = float(result.price)
                            source = "Citilink"
                    else:
                        total_skipped += 1
                        continue

                    if not price:
                        total_skipped += 1
                        continue

                    if not args.dry_run:
                        db.add(
                            PriceHistory(
                                product_id=prod.id,
                                source=source,
                                price=price,
                                date=datetime.utcnow(),
                            )
                        )
                        db.commit()

                    total_saved += 1
                    print(f"  ✅ [{source}] {query} -> {price:,.0f} ₽")

        print("\n==== DONE ====")
        print(f"attempts={total_attempts} saved={total_saved} skipped={total_skipped} dry_run={args.dry_run}")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())

