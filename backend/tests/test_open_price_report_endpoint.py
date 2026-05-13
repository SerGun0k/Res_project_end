import os
from pathlib import Path

import pytest

from app.routers.csv_import import get_latest_open_prices_report


@pytest.mark.asyncio
async def test_latest_open_price_report_empty_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("OPEN_PRICE_REPORTS_DIR", str(tmp_path))
    result = await get_latest_open_prices_report()
    assert result["status"] == "empty"


@pytest.mark.asyncio
async def test_latest_open_price_report_returns_latest_file(tmp_path, monkeypatch):
    monkeypatch.setenv("OPEN_PRICE_REPORTS_DIR", str(tmp_path))

    first = Path(tmp_path) / "open_prices_report_20260101_000001.md"
    second = Path(tmp_path) / "open_prices_report_20260101_000002.md"
    first.write_text("old report", encoding="utf-8")
    second.write_text("new report", encoding="utf-8")

    os.utime(first, (1, 1))
    os.utime(second, (2, 2))

    result = await get_latest_open_prices_report()
    assert result["status"] == "ok"
    assert result["filename"] == second.name
    assert "new report" in result["content"]
