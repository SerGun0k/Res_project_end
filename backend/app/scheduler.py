"""Планировщик фоновых задач"""

from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

from app.redis_client import reset_daily_views
from app.config import settings

scheduler = BackgroundScheduler()


def update_prices_job():
    """Периодическое обновление цен (заглушка)"""
    print(f"[{datetime.now()}] Запуск обновления цен...")
    if not settings.ENABLE_DNS_SCRAPER:
        print(f"[{datetime.now()}] DNS scraper disabled (ENABLE_DNS_SCRAPER=false)")
        return

    try:
        from sqlalchemy import desc
        from app.database import SessionLocal
        from app.models import Product, PriceHistory
        from data_pipeline.dns_scraper import get_product_price

        db = SessionLocal()
        try:
            # Берём товары с наибольшим количеством просмотров (если есть поле/таблица),
            # а если нет — просто последние добавленные.
            products = (
                db.query(Product)
                .order_by(desc(Product.id))
                .limit(settings.PRICE_REFRESH_MAX_PRODUCTS)
                .all()
            )

            updated = 0
            for p in products:
                result = get_product_price(p.brand, p.model, p.category, headless=settings.DNS_SCRAPER_HEADLESS)
                if not result:
                    continue

                db.add(
                    PriceHistory(
                        product_id=p.id,
                        source="DNS",
                        price=result.price,
                        date=datetime.utcnow(),
                    )
                )
                db.commit()
                updated += 1

            print(f"[{datetime.now()}] Обновление цен завершено: updated={updated}")
        finally:
            db.close()

    except Exception as e:
        print(f"[{datetime.now()}] Ошибка обновления цен: {e}")


def reset_views_job():
    """Ежедневный сброс просмотров"""
    print(f"[{datetime.now()}] Сброс дневных просмотров")
    try:
        reset_daily_views()
        print("Просмотры сброшены")
    except Exception as e:
        print(f"Ошибка сброса просмотров: {e}")


def retrain_ml_job():
    """Еженедельное переобучение ML моделей"""
    print(f"[{datetime.now()}] 🤖 Переобучение ML моделей...")
    try:
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
        from ml.models import train_all_models
        train_all_models()
        print(f"[{datetime.now()}] ✅ ML модели переобучены")
    except Exception as e:
        print(f"[{datetime.now()}] ❌ Ошибка переобучения ML: {e}")


def start_scheduler():
    """Запуск планировщика"""
    # Обновление цен: каждый понедельник в 03:00
    scheduler.add_job(
        update_prices_job,
        "cron",
        day_of_week="mon",
        hour=3,
        minute=0,
        id="update_prices",
        replace_existing=True,
    )

    # Сброс просмотров: каждый день в 00:00
    scheduler.add_job(
        reset_views_job,
        "cron",
        hour=0,
        minute=0,
        id="reset_views",
        replace_existing=True,
    )

    # Переобучение ML: каждое воскресенье в 04:00
    scheduler.add_job(
        retrain_ml_job,
        "cron",
        day_of_week="sun",
        hour=4,
        minute=0,
        id="retrain_ml",
        replace_existing=True,
    )

    scheduler.start()
    print("Планировщик запущен")


def stop_scheduler():
    """Остановка планировщика"""
    scheduler.shutdown()
