"""
Market scrapers (best-effort) via Playwright.

Важно:
- без официальных API сайты могут показывать капчу/блокировать/менять верстку
- поэтому эти функции должны быть устойчивыми к ошибкам и возвращать None при сбое
"""

from __future__ import annotations

import random
import re
from dataclasses import dataclass
from typing import Optional

from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page


@dataclass
class MarketPrice:
    source: str
    price: float
    url: str
    title: str = ""
    raw_text: str = ""


USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
]


def _create_browser(headless: bool = True) -> tuple[Browser, BrowserContext]:
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(
        headless=headless,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-dev-shm-usage",
        ],
    )
    context = browser.new_context(
        user_agent=random.choice(USER_AGENTS),
        viewport={"width": 1920, "height": 1080},
        locale="ru-RU",
        timezone_id="Europe/Moscow",
    )
    context.add_init_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
    )
    return browser, context


def _parse_rub_price(text: str) -> Optional[float]:
    if not text:
        return None
    # берём первое похожее число, удаляем пробелы/₽
    m = re.search(r"(\d[\d\s]{2,})", text)
    if not m:
        return None
    val = re.sub(r"[^\d]", "", m.group(1))
    if not val:
        return None
    try:
        price = float(val)
    except ValueError:
        return None
    return price if price > 100 else None


def _looks_like_captcha(html: str) -> bool:
    h = (html or "").lower()
    return any(s in h for s in ["captcha", "робот", "are you a robot", "cloudflare", "challenge"])


def fetch_ozon_price(query: str, headless: bool = True) -> Optional[MarketPrice]:
    """
    Best-effort: поиск по Ozon и попытка вытащить цену первого товара.
    Может не сработать из-за капчи/антибота.
    """
    browser = None
    context = None
    try:
        browser, context = _create_browser(headless=headless)
        page = context.new_page()

        from urllib.parse import quote

        url = f"https://www.ozon.ru/search/?text={quote(query)}"
        page.goto(url, wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(1500)

        html = page.content()
        if _looks_like_captcha(html):
            return None

        # Ozon часто меняет селекторы; используем несколько подходов
        # 1) пробуем найти любой видимый элемент цены "₽"
        price_text = page.evaluate(
            """
            () => {
              const candidates = [];
              const nodes = Array.from(document.querySelectorAll('span, div'));
              for (const n of nodes) {
                const t = (n.textContent || '').trim();
                if (!t) continue;
                if (t.includes('₽') && /\\d/.test(t) && t.length <= 40) {
                  candidates.push(t);
                }
              }
              return candidates.length ? candidates[0] : '';
            }
            """
        )

        price = _parse_rub_price(price_text or "")
        if not price:
            return None

        return MarketPrice(source="Ozon", price=price, url=url, raw_text=str(price_text))
    except Exception:
        return None
    finally:
        if context:
            context.close()
        if browser:
            browser.close()


def fetch_citilink_price(query: str, headless: bool = True) -> Optional[MarketPrice]:
    """
    Best-effort: поиск по Citilink и попытка вытащить цену первого товара.
    """
    browser = None
    context = None
    try:
        browser, context = _create_browser(headless=headless)
        page = context.new_page()

        from urllib.parse import quote

        url = f"https://www.citilink.ru/search/?text={quote(query)}"
        page.goto(url, wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(1500)

        html = page.content()
        if _looks_like_captcha(html):
            return None

        # Пытаемся достать цену из типичных блоков
        price_text = page.evaluate(
            """
            () => {
              const selectors = [
                '[data-meta-name="Price"]',
                '[class*="ProductPrice"]',
                '[class*="price"]',
              ];
              for (const sel of selectors) {
                const el = document.querySelector(sel);
                if (el && el.textContent) return el.textContent;
              }
              // fallback: любой текст с ₽
              const nodes = Array.from(document.querySelectorAll('span, div'));
              for (const n of nodes) {
                const t = (n.textContent || '').trim();
                if (t.includes('₽') && /\\d/.test(t) && t.length <= 40) return t;
              }
              return '';
            }
            """
        )

        price = _parse_rub_price(price_text or "")
        if not price:
            return None

        return MarketPrice(source="Citilink", price=price, url=url, raw_text=str(price_text))
    except Exception:
        return None
    finally:
        if context:
            context.close()
        if browser:
            browser.close()

