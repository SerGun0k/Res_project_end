"""
Парсер цен с сайта DNS (dns-shop.ru) через Playwright.

Playwright запускает реальный Chromium браузер который:
  - Выполняет JavaScript (обходит Cloudflare защиту)
  - Принимает cookies автоматически
  - Рендерит страницу как обычный пользователь

Алгоритм:
  1. Открываем dns-shop.ru/search?q=запрос
  2. Ждём загрузки карточек товаров
  3. Извлекаем: название, цену, ссылку, наличие
  4. Сохраняем в price_history
"""

import re
import random
from typing import Optional, List
from datetime import datetime
from dataclasses import dataclass, asdict

from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext


@dataclass
class DNSProduct:
    """Товар найденный в DNS"""
    name: str
    price: float
    url: str
    availability: str  # "in_stock", "out_of_stock", "unknown"
    raw_text: str = ""  # Для отладки


# Реалистичные User-Agent
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
]


def _create_browser(headless: bool = True) -> tuple[Browser, BrowserContext]:
    """Создаёт браузер с реалистичными настройками"""
    playwright = sync_playwright().start()
    
    browser = playwright.chromium.launch(
        headless=headless,
        args=[
            "--disable-blink-features=AutomationControlled",  # Скрываем автоматизацию
            "--no-sandbox",
            "--disable-dev-shm-usage",
        ]
    )
    
    context = browser.new_context(
        user_agent=random.choice(USER_AGENTS),
        viewport={"width": 1920, "height": 1080},
        locale="ru-RU",
        timezone_id="Europe/Moscow",
    )
    
    # Скрываем что это автоматизация
    context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        window.chrome = { runtime: {} };
    """)
    
    return browser, context


def search_dns(query: str, max_results: int = 5, headless: bool = True) -> list[DNSProduct]:
    """
    Поиск товаров на DNS через Playwright.
    
    Args:
        query: Поисковый запрос (например "RTX 4070")
        max_results: Максимум результатов
        headless: Запускать ли браузер без UI
    
    Returns:
        Список найденных товаров
    """
    browser = None
    context = None
    
    try:
        browser, context = _create_browser(headless)
        page = context.new_page()
        
        # Задержка для реалистичности
        page.wait_for_timeout(1000 + random.randint(0, 1500))
        
        # Открываем поиск DNS
        from urllib.parse import quote
        encoded_query = quote(query)
        search_url = f"https://www.dns-shop.ru/search/?q={encoded_query}"
        
        response = page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
        
        if not response or response.status == 401:
            # DNS показал 401 — пробуем подождать (возможно Cloudflare challenge)
            print(f"⚠️ DNS вернул {response.status if response else 'None'}, ждём...")
            page.wait_for_timeout(5000)
            
            # Проверяем не Cloudflare ли
            if "cloudflare" in page.content().lower() or "challenge" in page.content().lower():
                print("⚠️ Cloudflare challenge detected")
                return []
        
        # Ждём загрузки карточек товаров
        # DNS использует разные селекторы, пробуем несколько вариантов
        try:
            page.wait_for_selector("li.catalog-products__item, div.product-card, a.product-card__title", timeout=10000)
        except:
            print("⚠️ Не удалось дождаться загрузки карточек")
            # Пробуем получить что есть
            pass
        
        # Дадим время на рендеринг
        page.wait_for_timeout(1500)
        
        # Извлекаем данные через JavaScript
        products = page.evaluate("""
            () => {
                const products = [];
                
                // Пробуем разные селекторы карточек
                const cards = document.querySelectorAll('li.catalog-products__item') ||
                              document.querySelectorAll('div.product-card') ||
                              document.querySelectorAll('div[data-product-id]');
                
                cards.forEach((card, index) => {
                    if (index >= 10) return; // Ограничиваем
                    
                    // Название
                    const titleEl = card.querySelector('a.product-card__title, h3 a, .title a');
                    const name = titleEl ? titleEl.textContent.trim() : '';
                    
                    // Цена
                    const priceEl = card.querySelector('.product-card__price, .price, span[data-product-price]');
                    let priceText = priceEl ? priceEl.textContent.trim() : '';
                    const price = parseInt(priceText.replace(/[^0-9]/g, ''));
                    
                    // Ссылка
                    const url = titleEl ? titleEl.href : '';
                    
                    // Наличие
                    const availEl = card.querySelector('.product-card__availability, .availability');
                    const availText = availEl ? availEl.textContent.trim().toLowerCase() : '';
                    let availability = 'unknown';
                    if (availText.includes('в наличии') || availText.includes('доставка')) {
                        availability = 'in_stock';
                    } else if (availText.includes('нет в наличии')) {
                        availability = 'out_of_stock';
                    }
                    
                    if (name && price > 0) {
                        products.push({ name, price, url, availability, raw_text: priceText });
                    }
                });
                
                return products;
            }
        """)
        
        # Конвертируем в объекты
        result = []
        for p in products[:max_results]:
            result.append(DNSProduct(
                name=p.get("name", ""),
                price=float(p.get("price", 0)),
                url=p.get("url", ""),
                availability=p.get("availability", "unknown"),
                raw_text=p.get("raw_text", ""),
            ))
        
        if not result:
            print(f"⚠️ Не удалось извлечь товары. URL: {search_url}")
            # Попробуем альтернативный метод
            result = _fallback_parse(page, max_results)
        
        return result
        
    except Exception as e:
        print(f"⚠️ Ошибка парсинга DNS: {e}")
        return []
    finally:
        if context:
            context.close()
        if browser:
            browser.close()


def _fallback_parse(page: Page, max_results: int) -> list[DNSProduct]:
    """Альтернативный метод парсинга"""
    try:
        # Получаем весь HTML и ищем регулярками
        content = page.content()
        
        # Ищем JSON с данными товаров (DNS иногда вставляет его)
        json_match = re.search(r'window\.initialState\s*=\s*({.*?});', content, re.DOTALL)
        if json_match:
            import json
            try:
                data = json.loads(json_match.group(1))
                # Парсим структуру DNS
                # ... зависит от структуры
            except:
                pass
        
        # Ищем цены в формате "12 345 ₽"
        prices = re.findall(r'(\d[\d\s]*)\s*₽', content)
        names = re.findall(r'title="([^"]+)"', content)
        
        products = []
        for i, (price_str, name) in enumerate(zip(prices, names)):
            if i >= max_results:
                break
            try:
                price = float(price_str.replace(" ", "").replace(",", "."))
                if price > 100:
                    products.append(DNSProduct(
                        name=name[:100],
                        price=price,
                        url="",
                        availability="unknown",
                    ))
            except ValueError:
                continue
        
        return products
        
    except Exception as e:
        print(f"⚠️ Fallback парсинг не удался: {e}")
        return []


def get_product_price(
    brand: str,
    model: str,
    category: str,
    headless: bool = True,
    allow_demo: bool = True,
) -> Optional[DNSProduct]:
    """
    Получить цену конкретного товара из DNS.
    
    Если DNS блокирует — возвращаем моковые данные для демонстрации.
    """
    # Формируем поисковый запрос
    query = f"{brand} {model}"
    
    print(f"🔍 Ищем в DNS: {query}")
    
    # Пробуем реальный парсинг
    results = search_dns(query, max_results=5, headless=headless)
    
    if results:
        # Выбираем наиболее релевантный результат
        best_match = None
        best_score = 0
        
        for product in results:
            score = 0
            query_lower = query.lower()
            name_lower = product.name.lower()
            
            if query_lower in name_lower:
                score += 10
            else:
                words = query_lower.split()
                matched = sum(1 for w in words if w in name_lower)
                score += matched * 2
            
            if product.availability == "in_stock":
                score += 5
            
            if product.price > 1000:
                score += 2
            
            if score > best_score:
                best_score = score
                best_match = product
        
        if best_match and best_score >= 3:
            print(f"  ✅ Найдено: {best_match.name} — {best_match.price:,.0f} ₽")
            return best_match
    
    if not allow_demo:
        print("  ⚠️ DNS недоступен/заблокировал, demo fallback отключён")
        return None

    # Fallback: моковые данные для демонстрации
    print("  ⚠️ DNS недоступен/заблокировал, используем демо-данные")
    return _get_demo_price(brand, model, category)


def _get_demo_price(brand: str, model: str, category: str) -> Optional[DNSProduct]:
    """
    Демо-данные цен для демонстрации функционала.
    В продакшене заменить на реальные API или парсинг.
    """
    # Базовые цены для демонстрации
    demo_prices = {
        ("NVIDIA", "RTX 4070"): 62999,
        ("NVIDIA", "RTX 4080"): 99999,
        ("NVIDIA", "RTX 4090"): 159999,
        ("NVIDIA", "RTX 3080"): 54999,
        ("NVIDIA", "RTX 3070"): 42999,
        ("AMD", "Ryzen 7 7800X3D"): 34999,
        ("AMD", "Ryzen 9 7950X"): 54999,
        ("AMD", "Ryzen 5 7600X"): 24999,
        ("Intel", "Core i7-14700K"): 39999,
        ("Intel", "Core i9-14900K"): 59999,
        ("Intel", "Core i5-14400"): 19999,
        ("Kingston", "Fury Beast DDR5 32GB"): 8999,
        ("Samsung", "990 Pro 1TB"): 12999,
    }
    
    key = (brand, model)
    price = demo_prices.get(key)
    
    if price:
        # Добавляем вариацию ±5%
        import random
        variation = price * (1 + random.uniform(-0.05, 0.05))
        
        return DNSProduct(
            name=f"{brand} {model}",
            price=round(variation),
            url=f"https://www.dns-shop.ru/search/?q={brand}+{model}",
            availability="in_stock",
        )
    
    return None


if __name__ == "__main__":
    import sys
    
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "RTX 4070"
    print(f"🔍 Ищем в DNS: {query}\n")
    
    results = search_dns(query, max_results=5, headless=True)
    
    if results:
        print(f"✅ Найдено {len(results)} товаров:\n")
        for i, p in enumerate(results, 1):
            print(f"{i}. {p.name}")
            print(f"   Цена: {p.price:,.0f} ₽")
            print(f"   Ссылка: {p.url}")
            print(f"   Наличие: {p.availability}")
            print()
    else:
        print("❌ Ничего не найдено")
