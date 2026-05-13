"""FastAPI приложение"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.config import settings
from app.database import engine, init_db
from app.routers import products, search, alternatives, daily, static_pages, feedback, marketplace, ml_recommendations, dns_prices, csv_import
from app.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle приложения"""
    # Startup
    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    init_db()
    start_scheduler()
    yield
    # Shutdown
    stop_scheduler()
    print("Shutting down application")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Система рекомендаций по оценке цен на компьютерные комплектующие",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(products.router, prefix="/api/v1/products", tags=["products"])
app.include_router(search.router, prefix="/api/v1", tags=["search"])
app.include_router(alternatives.router, prefix="/api/v1", tags=["alternatives"])
app.include_router(daily.router, prefix="/api/v1", tags=["daily"])
app.include_router(feedback.router, prefix="/api/v1", tags=["feedback"])
app.include_router(marketplace.router, prefix="/api/v1", tags=["marketplace"])
app.include_router(ml_recommendations.router, prefix="/api/v1", tags=["ml"])
app.include_router(dns_prices.router, prefix="/api/v1", tags=["dns"])
app.include_router(csv_import.router, prefix="/api/v1", tags=["csv-import"])
app.include_router(static_pages.router, tags=["pages"])


@app.get("/api/health")
async def health_check():
    """Проверка работоспособности"""
    return {"status": "ok", "version": settings.APP_VERSION}


@app.get("/")
async def root():
    """Редирект на Swagger документацию"""
    return RedirectResponse(url="/docs")
