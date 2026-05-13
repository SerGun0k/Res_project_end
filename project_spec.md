# Спецификация проекта: система рекомендаций оценки цен на онлайн-площадках

## 1. Назначение
Сервис оценивает рыночные цены комплектующих и формирует рекомендации:
- оценка наценки (normal/high),
- подбор альтернатив,
- рекомендация по покупке (`buy_now` / `wait` / `no_rush`) с объяснением.

## 2. Принципы данных
1. **Runtime web-scraping отключён**.
2. Источники цен: только открытые CSV/TSV/API выгрузки.
3. Импорт цен выполняется через `data_pipeline/import_open_prices.py`.
4. Каждый импорт формирует quality-report (saved/skipped/duplicates/invalid/unknown).

## 3. Технологический стек
- Frontend: React + Vite + Tailwind CSS
- Backend: FastAPI (Python 3.11+)
- DB: PostgreSQL + SQLAlchemy + Alembic
- Cache: Redis
- Scheduler: APScheduler
- Deploy: Docker / Render

## 4. Модель данных
Ключевые таблицы:
- `products` (категория, бренд, модель, `specs` JSON)
- `price_history` (история цен)
- `cost_estimates` (оценка себестоимости)
- `reviews_quality` (качество)
- `popularity_stats` (популярность)
- `price_predictions`:
  - `current_price`
  - `predicted_1m`
  - `predicted_3m`
  - `target_price`
  - `price_gap_pct`
  - `recommendation`
  - `recommendation_reason`

## 5. Алгоритм рекомендаций
### 5.1 Наценка
- `markup% = (market_price - cost_estimate) / cost_estimate * 100`
- `adjusted_markup = markup% * weighted_factor`
- Порог: `adjusted_markup > 40% => high`

### 5.2 Рекомендательная цена
`target_price` рассчитывается как blended-якорь:
- медиана последних цен,
- прогноз на 1 месяц,
- (опционально) cost-anchor.

`price_gap_pct = (current_price - target_price) / target_price * 100`

На основе `trend + price_gap_pct` формируется:
- `buy_now`
- `wait`
- `no_rush`

## 6. API-контракт (обязательные сценарии)
- `/api/v1/products/{id}`: включает поля прогноза и explainability
- `/api/v1/search`: возвращает markup-поля
- `/api/v1/alternatives`: возвращает альтернативы и score
- `/api/v1/import-prices-csv`: ручной CSV-импорт
- `/api/v1/import-open-prices-report/latest`: получение последнего quality-report
- legacy DNS fetch endpoints: `410 Gone`

## 7. Метрики для защиты
- Price prediction: MAE, MAPE
- Recommendations: Precision@K, HitRate@K
- Coverage: доля товаров с валидными рекомендациями
- Perf: p50/p95 latency

## 8. План развития
1. Расширить категорийные `specs` и их вклад в `target_price`.
2. Добавить quality-gates на CI для open-data импорта.
3. Сравнить deterministic baseline vs ML-модель.
4. Добавить наблюдаемость: structured logs + import dashboards.
