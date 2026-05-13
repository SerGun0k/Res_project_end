"""
Импорт цен из открытых источников (CSV/TSV по URL) без веб-парсинга.

Формат файла должен содержать колонки:
- brand
- model
- price
- source (опционально, по умолчанию OPEN_DATA)
- date (опционально, ISO8601)

Пример:
python data_pipeline/import_open_prices.py --url "https://example.com/prices.csv"
python data_pipeline/import_open_prices.py --url "https://example.com/prices.csv" --dry-run
"""

from __future__ import annotations

import argparse
import csv
import io
import os
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import httpx

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.database import SessionLocal
from app.models import Product, PriceHistory
from app.config import settings


def _parse_date(raw: str | None) -> datetime:
    if not raw:
        return datetime.utcnow()
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return datetime.utcnow()


def _download_rows(url: str) -> list[dict]:
    with httpx.Client(timeout=30.0, follow_redirects=True) as client:
        resp = client.get(url)
        resp.raise_for_status()

    payload = resp.text
    delimiter = "\t" if "\t" in payload.splitlines()[0] else ","
    reader = csv.DictReader(io.StringIO(payload), delimiter=delimiter)
    return list(reader)


def _is_url_allowed(url: str, allowed_domains: list[str]) -> bool:
    if not allowed_domains:
        return True
    host = (urlparse(url).hostname or "").lower()
    return any(host == d or host.endswith(f".{d}") for d in allowed_domains)


def _write_quality_report(report: dict) -> None:
    reports_dir = Path(os.path.dirname(__file__)) / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    out = reports_dir / f"open_prices_report_{stamp}.md"
    out.write_text(
        "\n".join(
            [
                "# Open Prices Import Report",
                "",
                f"- Generated at (UTC): {datetime.utcnow().isoformat()}",
                f"- Sources: {', '.join(report['sources'])}",
                f"- Total rows: {report['rows_total']}",
                f"- Saved: {report['saved']}",
                f"- Skipped: {report['skipped']}",
                f"- Duplicates: {report['duplicates']}",
                f"- Unknown products: {report['unknown_products']}",
                f"- Invalid price rows: {report['invalid_price']}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(f"quality_report={out}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", action="append", help="URL открытого CSV/TSV с ценами (можно несколько)")
    parser.add_argument("--use-env-sources", action="store_true", help="Использовать OPEN_PRICE_SOURCES из .env")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--max-age-days", type=int, default=settings.OPEN_PRICE_MAX_AGE_DAYS)
    parser.add_argument(
        "--fail-on-quality-threshold",
        action="store_true",
        help="Падать с кодом 2, если качество импорта ниже порога",
    )
    parser.add_argument("--max-unknown-ratio", type=float, default=0.2)
    parser.add_argument("--max-invalid-ratio", type=float, default=0.1)
    args = parser.parse_args()
    urls: list[str] = args.url or []
    if args.use_env_sources and settings.OPEN_PRICE_SOURCES.strip():
        urls.extend([u.strip() for u in settings.OPEN_PRICE_SOURCES.split(",") if u.strip()])
    if not urls:
        raise SystemExit("No sources provided. Use --url or --use-env-sources with OPEN_PRICE_SOURCES.")
    allowed_domains = [d.strip().lower() for d in settings.OPEN_PRICE_ALLOWED_DOMAINS.split(",") if d.strip()]

    db = SessionLocal()
    try:
        saved = 0
        skipped = 0
        duplicates = 0
        unknown_products = 0
        invalid_price = 0
        rows_total = 0
        dedup_key_seen: set[tuple[int, str, str]] = set()

        for url in urls:
            if not _is_url_allowed(url, allowed_domains):
                print(f"skip source (domain not allowed): {url}")
                skipped += 1
                continue
            rows = _download_rows(url)
            rows_total += len(rows)
            for row in rows:
                brand = (row.get("brand") or "").strip()
                model = (row.get("model") or "").strip()
                price_raw = row.get("price")
                source = (row.get("source") or "OPEN_DATA").strip()[:100]

                if not brand or not model or not price_raw:
                    skipped += 1
                    continue

                try:
                    price = float(str(price_raw).replace(" ", "").replace(",", "."))
                except ValueError:
                    invalid_price += 1
                    skipped += 1
                    continue

                product = db.query(Product).filter(
                    Product.brand == brand,
                    Product.model == model,
                ).first()

                if not product:
                    unknown_products += 1
                    skipped += 1
                    continue

                parsed_date = _parse_date(row.get("date"))
                age_days = (datetime.utcnow() - parsed_date).days
                if args.max_age_days >= 0 and age_days > args.max_age_days:
                    skipped += 1
                    continue
                dedup_key = (product.id, source, parsed_date.date().isoformat())
                if dedup_key in dedup_key_seen:
                    duplicates += 1
                    skipped += 1
                    continue
                dedup_key_seen.add(dedup_key)

                if not args.dry_run:
                    existing = db.query(PriceHistory).filter(
                        PriceHistory.product_id == product.id,
                        PriceHistory.source == source,
                        PriceHistory.date >= datetime(parsed_date.year, parsed_date.month, parsed_date.day),
                        PriceHistory.date < datetime(parsed_date.year, parsed_date.month, parsed_date.day, 23, 59, 59),
                    ).first()
                    if existing:
                        duplicates += 1
                        skipped += 1
                        continue

                    db.add(
                        PriceHistory(
                            product_id=product.id,
                            source=source,
                            price=price,
                            date=parsed_date,
                        )
                    )
                    db.commit()

                saved += 1

        report = {
            "sources": urls,
            "rows_total": rows_total,
            "saved": saved,
            "skipped": skipped,
            "duplicates": duplicates,
            "unknown_products": unknown_products,
            "invalid_price": invalid_price,
        }
        _write_quality_report(report)
        print(f"done: saved={saved} skipped={skipped} duplicates={duplicates} dry_run={args.dry_run}")
        if args.fail_on_quality_threshold and rows_total > 0:
            unknown_ratio = unknown_products / rows_total
            invalid_ratio = invalid_price / rows_total
            if unknown_ratio > args.max_unknown_ratio or invalid_ratio > args.max_invalid_ratio:
                print(
                    "quality gate failed: "
                    f"unknown_ratio={unknown_ratio:.3f} invalid_ratio={invalid_ratio:.3f}"
                )
                return 2
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
