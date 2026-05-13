"""Конфигурация базы данных"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .models import Base

# URL базы данных (по умолчанию PostgreSQL для Docker)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://diplom:diplom@localhost:5432/diplom"
)

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Зависимость для получения сессии БД"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Инициализация БД (для разработки)"""
    Base.metadata.create_all(bind=engine)
