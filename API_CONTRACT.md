# API Contract: система рекомендаций по оценке цен

## Base URL
- Development: `http://localhost:8000`
- Production: `https://api.yourdomain.com`

## Версионирование
- Актуальная версия: `v1` (`/api/v1/...`)
- Обратная совместимость в рамках одной минорной версии.

## Единый формат ошибок
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Некорректные параметры запроса",
    "details": [{"field": "limit", "issue": "must be <= 100"}],
    "request_id": "9f3c..."
  }
}
```

## Endpoints

### 1) Health
`GET /api/health`

Response `200 OK`:
```json
{"status": "ok", "version": "0.1.0"}
```

---

### 2) Список товаров
`GET /api/v1/products?category=GPU&brand=NVIDIA&skip=0&limit=20&sort=created_at&order=desc`

Query params:
- `category` (string, optional)
- `brand` (string, optional)
- `skip` (int, optional, default=0, min=0)
- `limit` (int, optional, default=20, min=1, max=100)
- `sort` (string, optional: `created_at|release_date|brand|model`)
- `order` (string, optional: `asc|desc`)

Response `200 OK`: массив `ProductRead`.

---

### 3) Создание товара
`POST /api/v1/products`

Body:
```json
{
  "category": "GPU",
  "brand": "NVIDIA",
  "model": "RTX 4060",
  "specs": {"memory_gb": 8, "memory_type": "GDDR6", "tdp_watts": 115},
  "release_date": "2023-06-29T00:00:00"
}
```

Response `201 Created`: `ProductRead`.

---

### 4) Детали товара
`GET /api/v1/products/{product_id}`

Response `200 OK`: `ProductFullRead`.

Ключевые блоки:
- `price_history[]`
- `cost_estimate`
- `review_quality`
- `popularity_stats`

---

### 5) Поиск товаров
`GET /api/v1/search?query=RTX+4060&category=GPU&min_price=25000&max_price=40000&page=1&per_page=20`

Rules:
- `page >= 1`
- `per_page in [1..100]`
- `min_price <= max_price`

Response `200 OK`:
```json
{
  "total": 5,
  "page": 1,
  "per_page": 20,
  "items": [
    {
      "id": 1,
      "category": "GPU",
      "brand": "NVIDIA",
      "model": "RTX 4060",
      "market_price": 32990,
      "markup_percent": 64.95,
      "adjusted_markup": 64.95,
      "markup_status": "overpriced",
      "explain": {
        "brand_weight": 0.25,
        "quality_weight": 0.30,
        "relevance_weight": 0.20,
        "popularity_weight": 0.25
      }
    }
  ]
}
```

---

### 6) Подбор аналогов
`POST /api/v1/alternatives`

Body:
```json
{
  "product_id": 1,
  "category": "GPU",
  "max_count": 5
}
```

Response `200 OK`:
```json
{
  "product_id": 1,
  "category": "GPU",
  "alternatives_count": 3,
  "alternatives": [
    {
      "product_id": 2,
      "brand": "AMD",
      "model": "RX 7600",
      "price": 28500,
      "quality_factor": 0.92,
      "markup_percent": 45.2,
      "score": 1.85,
      "recommendation": "better reliability; lower markup"
    }
  ]
}
```

---

### 7) Товары дня
`GET /api/v1/daily?top_n=5`

Response `200 OK`:
```json
{
  "date": "2026-05-13",
  "products": [
    {
      "product": {"id": 1, "category": "GPU", "brand": "NVIDIA", "model": "RTX 4060"},
      "daily_views": 523,
      "avg_price": 32990
    }
  ]
}
```

## Error codes
- `400 BAD_REQUEST`
- `401 UNAUTHORIZED`
- `403 FORBIDDEN`
- `404 NOT_FOUND`
- `409 CONFLICT`
- `422 VALIDATION_ERROR`
- `429 RATE_LIMITED`
- `500 INTERNAL_ERROR`

## Non-functional requirements
- p95 latency: до 500ms для `/search` и `/alternatives` при типовой нагрузке.
- Request timeout: 5s.
- Логирование `request_id` для трассировки ошибок.
