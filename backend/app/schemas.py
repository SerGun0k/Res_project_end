"""Pydantic схемы для API запросов и ответов"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


# === Product Schemas ===

class ProductSpecs(BaseModel):
    """Характеристики товара (гибкая структура)"""
    class Config:
        extra = "allow"


class ProductBase(BaseModel):
    category: str = Field(..., min_length=2, max_length=50, description="Категория: GPU, CPU, RAM, SSD, HDD, PSU, COOLING")
    subcategory: Optional[str] = Field(None, max_length=50, description="Подкатегория: M2, SATA, NVMe для SSD")
    brand: str = Field(..., min_length=1, max_length=100)
    model: str = Field(..., min_length=1, max_length=200)
    specs: Optional[Dict[str, Any]] = None
    release_date: Optional[datetime] = None


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    specs: Optional[Dict[str, Any]] = None
    release_date: Optional[datetime] = None


class ProductRead(ProductBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# === Price History Schemas ===

class PriceHistoryBase(BaseModel):
    source: str
    price: float
    date: Optional[datetime] = None


class PriceHistoryRead(PriceHistoryBase):
    id: int
    product_id: int

    class Config:
        from_attributes = True


# === Cost Estimate Schemas ===

class CostEstimateBase(BaseModel):
    materials_cost: float
    logistics_cost: float
    labor_cost: float
    total: float


class CostEstimateRead(CostEstimateBase):
    id: int
    product_id: int
    last_updated: Optional[datetime]

    class Config:
        from_attributes = True


# === Review Quality Schemas ===

class ReviewQualityBase(BaseModel):
    avg_rating: Optional[float] = None
    defect_rate: Optional[float] = None
    reviews_count: Optional[int] = None
    source: Optional[str] = None


class ReviewQualityRead(ReviewQualityBase):
    id: int
    product_id: int
    last_updated: Optional[datetime]

    class Config:
        from_attributes = True


# === Popularity Stats Schemas ===

class PopularityStatsBase(BaseModel):
    daily_views: int = 0
    total_views: int = 0
    daily_searches: int = 0


class PopularityStatsRead(PopularityStatsBase):
    id: int
    product_id: int
    last_updated: Optional[datetime]

    class Config:
        from_attributes = True


# === Price Prediction Schemas ===

class PricePredictionRead(BaseModel):
    current_price: float
    predicted_1m: Optional[float]
    predicted_3m: Optional[float]
    trend: Optional[str]
    recommendation: Optional[str]
    target_price: Optional[float]
    price_gap_pct: Optional[float]
    confidence: Optional[float]
    last_updated: Optional[datetime]

    class Config:
        from_attributes = True


# === Composite Schemas ===

class ProductFullRead(ProductRead):
    """Полная информация о товаре со всеми связанными данными"""
    price_history: list[PriceHistoryRead] = []
    cost_estimate: Optional[CostEstimateRead] = None
    review_quality: Optional[ReviewQualityRead] = None
    popularity_stats: Optional[PopularityStatsRead] = None
    price_prediction: Optional[PricePredictionRead] = None


class ProductWithMarkup(ProductFullRead):
    """Товар с расчётом наценки"""
    market_price: Optional[float] = None
    markup_percent: Optional[float] = None
    adjusted_markup: Optional[float] = None
    markup_status: Optional[str] = None


# === Search & Filter Schemas ===

class SearchParams(BaseModel):
    query: str = Field(..., min_length=1, description="Поисковый запрос")
    category: Optional[str] = Field(None, description="Фильтр по категории")
    brand: Optional[str] = Field(None, description="Фильтр по бренду")
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    page: int = Field(1, ge=1)
    per_page: int = Field(20, ge=1, le=100)


class SearchResult(BaseModel):
    total: int
    page: int
    per_page: int
    items: list[ProductWithMarkup]


# === Alternatives Schemas ===

class AlternativeRequest(BaseModel):
    product_id: int
    category: str
    max_count: int = Field(5, ge=1, le=20)


class AlternativeProduct(BaseModel):
    product_id: int
    brand: str
    model: str
    price: float
    quality_factor: float
    markup_percent: float
    score: float
    recommendation: str


class AlternativesResponse(BaseModel):
    product_id: int
    category: str
    alternatives_count: int
    alternatives: list[AlternativeProduct]


# === Daily Products Schema ===

class DailyProductItem(BaseModel):
    product: ProductRead
    daily_views: int
    avg_price: float


class DailyProductsResponse(BaseModel):
    date: str
    products: list[DailyProductItem]
