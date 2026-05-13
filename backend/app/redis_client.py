"""Redis клиент и утилиты"""

import json
from typing import Optional

import redis

from app.config import settings

# Глобальный клиент (ленивая инициализация)
_redis_client: Optional[redis.Redis] = None


def get_redis() -> redis.Redis:
    """Получение Redis клиента (ленивое подключение)"""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=5,
        )
    return _redis_client


def cache_price(product_id: int, price: float, source: str, ttl: int = 3600):
    """Кэширование цены товара"""
    client = get_redis()
    key = f"price:{product_id}:{source}"
    client.setex(key, ttl, json.dumps({"price": price, "source": source}))


def get_cached_price(product_id: int, source: str) -> Optional[float]:
    """Получение кэшированной цены"""
    client = get_redis()
    key = f"price:{product_id}:{source}"
    data = client.get(key)
    if data:
        return json.loads(data)["price"]
    return None


def increment_views(product_id: int) -> int:
    """Увеличение счётчика просмотров"""
    client = get_redis()
    key = f"views:{product_id}"
    return client.incr(key)


def get_daily_views(product_id: int) -> int:
    """Получение дневных просмотров"""
    client = get_redis()
    key = f"views:{product_id}"
    views = client.get(key)
    return int(views) if views else 0


def reset_daily_views():
    """Сброс дневных просмотров (вызывать раз в день)"""
    client = get_redis()
    for key in client.scan_iter("views:*"):
        client.delete(key)


def cache_search_results(query: str, results: list, ttl: int = 1800):
    """Кэширование результатов поиска"""
    client = get_redis()
    key = f"search:{query}"
    client.setex(key, ttl, json.dumps(results))


def get_cached_search_results(query: str) -> Optional[list]:
    """Получение кэшированных результатов поиска"""
    client = get_redis()
    key = f"search:{query}"
    data = client.get(key)
    if data:
        return json.loads(data)
    return None
