# API Contract для системы рекомендаций по оценке цен

## Base URL
- Development: `http://localhost:8000`
- Production: `https://api.yourdomain.com`

---

## Endpoints

### 1. Health Check
```
GET /api/health
```
**Response:**
```json
{"status": "ok", "version": "0.1.0"}
```

---

### 2. Список товаров
```
GET /api/v1/products/?category=GPU&brand=NVIDIA&skip=0&limit=20
```
**Query Parameters:**
| Параметр | Тип | Обязательный | Описание |
|----------|-----|--------------|----------|
| category | string | Нет | GPU, CPU, RAM, SSD, HDD, M.2 |
| brand | string | Нет | NVIDIA, AMD, Intel и т.д. |
| skip | int | Нет | Пропуск (пагинация) |
| limit | int | Нет | Лимит (1-100) |

**Response:** `200 OK` — массив `ProductRead`

---

### 3. Создание товара
```
POST /api/v1/products/
```
**Body:**
```json
{
  "category": "GPU",
  "brand": "NVIDIA",
  "model": "RTX 4060",
  "specs": {"memory_gb": 8, "memory_type": "GDDR6", "tdp_watts": 115},
  "release_date": "2023-06-29T00:00:00"
}
```
**Response:** `201 Created` — `ProductRead`

---

### 4. Детали товара
```
GET /api/v1/products/{product_id}
```
**Response:** `200 OK` — `ProductFullRead`
```json
{
  "id": 1,
  "category": "GPU",
  "brand": "NVIDIA",
  "model": "RTX 4060",
  "specs": {"memory_gb": 8, "tdp_watts": 115},
  "release_date": "2023-06-29T00:00:00",
  "created_at": "2026-04-09T12:00:00",
  "updated_at": "2026-04-09T12:00:00",
  "price_history": [
    {"id": 1, "product_id": 1, "source": "DNS", "price": 32990, "date": "2026-04-09"}
  ],
  "cost_estimate": {
    "id": 1,
    "product_id": 1,
    "materials_cost": 15000,
    "logistics_cost": 3000,
    "labor_cost": 2000,
    "total": 20000,
    "last_updated": "2026-04-09"
  },
  "review_quality": {"avg_rating": 4.5, "defect_rate": 2.1, "reviews_count": 150},
  "popularity_stats": {"daily_views": 523, "total_views": 15000, "daily_searches": 89}
}
```

---

### 5. Поиск товаров
```
GET /api/v1/search?query=RTX+4060&category=GPU&min_price=25000&max_price=40000&page=1&per_page=20
```
**Response:** `200 OK` — `SearchResult`
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
      "markup_status": "завышена"
    }
  ]
}
```

---

### 6. Подбор аналогов
```
POST /api/v1/alternatives
```
**Body:**
```json
{
  "product_id": 1,
  "category": "GPU",
  "max_count": 5
}
```
**Response:** `200 OK` — `AlternativesResponse`
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
      "recommendation": "более высокая надёжность; низкая наценка"
    }
  ]
}
```

---

### 7. Товары дня
```
GET /api/v1/daily?top_n=5
```
**Response:** `200 OK` — `DailyProductsResponse`
```json
{
  "date": "2026-04-09",
  "products": [
    {
      "product": {"id": 1, "category": "GPU", "brand": "NVIDIA", "model": "RTX 4060"},
      "daily_views": 523,
      "avg_price": 32990
    }
  ]
}
```

---

## Error Responses

| Код | Описание |
|-----|----------|
| 400 | Неверные параметры запроса |
| 404 | Ресурс не найден |
| 409 | Конфликт (дубликат товара) |
| 500 | Внутренняя ошибка сервера |

---

## Модели данных

### Product
| Поле | Тип | Описание |
|------|-----|----------|
| id | int | Уникальный ID |
| category | string | Категория комплектующей |
| brand | string | Производитель |
| model | string | Модель |
| specs | JSON | Гибкие характеристики |
| release_date | datetime | Дата выхода |

### PriceHistory
| Поле | Тип | Описание |
|------|-----|----------|
| id | int | Уникальный ID |
| product_id | int | Ссылка на товар |
| source | string | Источник цены |
| price | float | Цена в RUB |
| date | datetime | Дата записи |

### CostEstimate
| Поле | Тип | Описание |
|------|-----|----------|
| materials_cost | float | Стоимость материалов |
| logistics_cost | float | Логистика и таможня |
| labor_cost | float | Сборка и тестирование |
| total | float | Итоговая себестоимость |
