"""DEPRECATED: web scraping disabled by project policy.

Используйте `data_pipeline/import_open_prices.py` и открытые CSV/TSV источники.
"""

def main() -> int:
    print(
        "scrape_marketplaces.py is deprecated and intentionally disabled. "
        "Use: python data_pipeline/import_open_prices.py --url <csv_url>"
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
