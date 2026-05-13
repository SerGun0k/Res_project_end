"""Тесты статических страниц"""

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.mark.asyncio
async def test_privacy_page():
    """GET /privacy — страница политики конфиденциальности"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/privacy")
    assert r.status_code == 200
    assert "Политика конфиденциальности" in r.text
    assert "152" in r.text  # Упоминание закона
    assert "text/html" in r.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_about_page():
    """GET /about — страница о проекте"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/about")
    assert r.status_code == 200
    assert "О проекте" in r.text
    assert "PC Parts Advisor" in r.text
    assert "text/html" in r.headers.get("content-type", "")
