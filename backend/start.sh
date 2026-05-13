#!/bin/bash
# Скрипт инициализации БД при деплое

echo "Running Alembic migrations..."
cd /app
alembic upgrade head

echo "Starting application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
