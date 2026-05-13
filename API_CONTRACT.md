# API Contract: система рекомендаций по оценке цен

## Base URL
- Development: `http://localhost:8000`
- Production: `https://api.yourdomain.com`

## Версионирование
- Актуальная версия: `v1` (`/api/v1/...`)

## Endpoints

### 1) Health
`GET /api/health`

Response `200 OK`:
```json
{"status": "ok", "version": "0.1.0"}
```

---

### 2) Список товаров
`GET /api/v1/products/?category=GPU&subcategory=M2&brand=NVIDIA&skip=0&limit=20`

Query params:
- `category` (optional)
- `subcategory` (optional)
- `brand` (optional)
- `skip` (default `0`)
- `limit` (default `100`, max `200`)

---

### 3) Создание товара
`POST /api/v1/products/`

Response: `201 Created` (`ProductRead`)

---

### 4) Детали товара
`GET /api/v1/products/{product_id}`

Response `200 OK`: `ProductFullRead` с блоком прогноза `price_prediction`.

Ключевые поля блока `price_prediction`:
- `current_price`
- `predicted_1m`
- `predicted_3m`
- `trend`
- `recommendation`
- `recommendation_reason`
- `target_price`
- `price_gap_pct`
- `confidence`

---

### 5) Поиск товаров
`GET /api/v1/search?query=RTX+4060&category=GPU&page=1&per_page=20`

Response `200 OK`: `SearchResult`.

Поля результата по товару:
- `market_price`
- `markup_percent`
- `adjusted_markup`
- `markup_status` (`normal` / `high`)

---

### 6) Подбор аналогов
`POST /api/v1/alternatives`

Response `200 OK`: `AlternativesResponse`.

---

### 7) Товары дня
`GET /api/v1/daily?top_n=5`

Response `200 OK`: `DailyProductsResponse`.

---

### 8) Импорт цен CSV (manual upload)
`POST /api/v1/import-prices-csv`

Multipart form-data:
- `file`: CSV
- `source`: optional query (`Manual` по умолчанию)

---

### 9) Отчёт по open-data импорту
`GET /api/v1/import-open-prices-report/latest`

Response:
- `{"status": "empty", "message": ...}` если отчётов нет
- `{"status": "ok", "filename": ..., "generated_at": ..., "content": ...}` если найден последний отчёт

---

### 10) Legacy DNS endpoints (disabled)
- `POST /api/v1/fetch-dns-price/{product_id}` -> `410 Gone`
- `POST /api/v1/fetch-all-dns-prices` -> `410 Gone`

## Error codes
- `400 BAD_REQUEST`
- `404 NOT_FOUND`
- `409 CONFLICT`
- `410 GONE`
- `422 VALIDATION_ERROR`
- `500 INTERNAL_ERROR`

## Non-functional notes
- Runtime web-scraping отключён; поддерживается только open-data import pipeline.
- Рекомендуется логировать quality-report каждого импорта и использовать quality-gates.
