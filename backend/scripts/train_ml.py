import os
import sys


def main() -> int:
    """
    Обучение всех ML моделей (кластеризация + предиктор цены).

    Запуск:
      python scripts/train_ml.py

    Требует доступную БД (в docker compose: service "postgres") и заполненные данные.
    """
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

    from ml.models import train_all_models

    train_all_models()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

