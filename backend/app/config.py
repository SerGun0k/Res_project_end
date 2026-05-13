"""Конфигурация приложения"""

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Настройки приложения"""

    # Приложение
    APP_NAME: str = "PC Parts Price Advisor"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    # База данных
    DATABASE_URL: str = "postgresql://diplom:diplom@localhost:5432/diplom"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 3600  # 1 час

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Пагинация
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    # Алгоритм наценки
    MARKUP_THRESHOLD: float = 40.0
    WEIGHT_BRAND: float = 0.25
    WEIGHT_QUALITY: float = 0.30
    WEIGHT_RELEVANCE: float = 0.20
    WEIGHT_POPULARITY: float = 0.25

    # Scrapers / marketplace prices
    # Без официальных API сайты могут блокировать запросы (капча/бан/смена верстки).
    # Поэтому включается явно флагом, чтобы прод/защита не ломались.
    ENABLE_DNS_SCRAPER: bool = False
    DNS_SCRAPER_HEADLESS: bool = True
    PRICE_REFRESH_MAX_PRODUCTS: int = 25
    OPEN_PRICE_SOURCES: str = ""
    OPEN_PRICE_MAX_AGE_DAYS: int = 14
    OPEN_PRICE_ALLOWED_DOMAINS: str = ""

    # Данные
    DATA_DIR: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
