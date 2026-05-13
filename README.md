# PC Parts Advisor

Система рекомендаций по оценке цен на компьютерные комплектующие.

## Описание

Веб-сервис для сравнения себестоимости и рыночной цены ПК-компонентов. Пользователь ищет товар, получает оценку обоснованности наценки на основе факторов (бренд, качество, актуальность, популярность) и рекомендации аналогов с лучшей ценой/качеством.

## Быстрый старт

### Docker (рекомендуемый способ)

```bash
# Запуск всего стека
docker compose up -d

# Заполнение БД тестовыми данными
docker compose exec backend python data_pipeline/seed_all.py

# (опционально) Обучение ML моделей (кластеризация + предиктор цены)
docker compose exec backend python scripts/train_ml.py
```

Откройте:
- **http://localhost:5173** — веб-интерфейс
- **http://localhost:8000/docs** — Swagger API

### Локальная разработка

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## Структура проекта

```
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI приложение
│   │   ├── models.py         # SQLAlchemy модели
│   │   ├── schemas.py        # Pydantic схемы
│   │   ├── database.py       # Подключение к БД
│   │   ├── config.py         # Настройки
│   │   ├── markup_utils.py   # Алгоритм расчёта наценки
│   │   ├── redis_client.py   # Redis клиент
│   │   ├── scheduler.py      # APScheduler
│   │   └── routers/
│   │       ├── products.py   # CRUD товаров
│   │       ├── search.py     # Поиск с наценкой
│   │       ├── alternatives.py # Подбор аналогов
│   │       ├── daily.py      # Товары дня
│   │       └── static_pages.py # Статические страницы
│   ├── data_pipeline/
│   │   ├── seed_all.py       # Заполнение БД
│   │   ├── seed_data.py      # Загрузка спецификаций
│   │   ├── seed_costs.py     # Расчёт себестоимости
│   │   ├── seed_prices.py    # Генерация цен
│   │   └── seed_reviews.py   # Отзывы и популярность
│   ├── tests/                # Тесты (pytest)
│   ├── alembic/              # Миграции БД
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── api/              # API клиент
│       ├── components/       # React компоненты
│       ├── pages/            # Страницы
│       └── types/            # TypeScript типы
├── data/                     # JSON спецификации
├── docker-compose.yml        # Оркестрация
├── render.yaml               # Деплой на Render
└── .github/workflows/ci.yml  # CI/CD
```

## API

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/api/health` | Проверка работоспособности |
| GET | `/api/v1/products/` | Список товаров |
| GET | `/api/v1/products/{id}` | Детали товара |
| GET | `/api/v1/search?query=` | Поиск с наценкой |
| POST | `/api/v1/alternatives` | Подбор аналогов |
| GET | `/api/v1/daily` | Товары дня |
| GET | `/about` | О проекте |
| GET | `/privacy` | Политика конфиденциальности |

## Алгоритм наценки

Наценка рассчитывается по формуле:

```
markup % = (market_price - cost_estimate) / cost_estimate * 100
adjusted_markup = markup % × weighted_factor

weighted_factor = brand×0.25 + quality×0.30 + relevance×0.20 + popularity×0.25
```

Порог: 40%. Если `adjusted_markup > 40%` — наценка завышена.


## Метрики и валидация рекомендательной системы

Для полноценной защиты диплома рекомендуется фиксировать следующие метрики:

- **Оценка цены:** MAE, MAPE
- **Качество рекомендаций:** Precision@K, HitRate@K
- **Покрытие каталога:** доля товаров, для которых система способна предложить релевантные аналоги
- **Производительность API:** p50/p95 latency для `/api/v1/search` и `/api/v1/alternatives`

Минимальный экспериментальный протокол:

1. Подготовить отложенную выборку товаров по категориям GPU/CPU/RAM/SSD.
2. Сравнить базовую детерминированную модель (веса факторов) и ML-вариант (при наличии датасета).
3. Зафиксировать результаты в таблице (CSV/Markdown) и добавить выводы в отчёт.

## Тесты

```bash
cd backend
python -m pytest tests/ -v
```

## Политика источников цен

В проекте отключён runtime web-scraping маркетплейсов.  
Актуальная политика: только импорт из открытых CSV/TSV источников через `data_pipeline/import_open_prices.py`.


## Импорт цен из открытых источников (без парсинга)

Проект использует open-data импорт и не выполняет web-scraping маркетплейсов в runtime.

### Операционный сценарий

1. Подготовьте CSV/TSV с колонками: `brand`, `model`, `price`, (опционально) `source`, `date`.
2. Запустите проверочный прогон:

```bash
docker compose exec backend python data_pipeline/import_open_prices.py --url "https://example.com/prices.csv" --dry-run
```

3. Запустите импорт с quality-gate:

```bash
docker compose exec backend python data_pipeline/import_open_prices.py \
  --url "https://example.com/prices.csv" \
  --max-age-days 14 \
  --fail-on-quality-threshold \
  --max-unknown-ratio 0.20 \
  --max-invalid-ratio 0.10
```

4. Получите последний отчёт качества:

```bash
curl http://localhost:8000/api/v1/import-open-prices-report/latest
```


## Импорт цен из открытых источников (без парсинга)

Проект использует open-data импорт и не выполняет web-scraping маркетплейсов в runtime.

### Операционный сценарий

1. Подготовьте CSV/TSV с колонками: `brand`, `model`, `price`, (опционально) `source`, `date`.
2. Запустите проверочный прогон:

```bash
docker compose exec backend python data_pipeline/import_open_prices.py --url "https://example.com/prices.csv" --dry-run
```

3. Запустите импорт с quality-gate:

```bash
docker compose exec backend python data_pipeline/import_open_prices.py \
  --url "https://example.com/prices.csv" \
  --max-age-days 14 \
  --fail-on-quality-threshold \
  --max-unknown-ratio 0.20 \
  --max-invalid-ratio 0.10
```

4. Получите последний отчёт качества:

```bash
curl http://localhost:8000/api/v1/import-open-prices-report/latest
```

## Деплой на Render

1. Создайте репозиторий на GitHub
2. Подключите к Render (render.com)
3. Render автоматически прочитает `render.yaml`

## Технологии

- **Frontend:** React 19, TypeScript, Vite, Tailwind CSS
- **Backend:** FastAPI, Python 3.11, SQLAlchemy
- **База данных:** PostgreSQL 15, Alembic
- **Кэш:** Redis 7
- **Планировщик:** APScheduler
- **Тесты:** pytest, httpx
- **Деплой:** Docker, Render

## Лицензия

MIT
