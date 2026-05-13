"""
Дополнительные ML функции: Collaborative Filtering + TF-IDF
"""

import os
import sys
import numpy as np
from typing import Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.database import SessionLocal
from app.models import Product, UserBehavior


def collaborative_filtering(user_session: str, top_k: int = 5) -> list[dict]:
    """
    Персонализированные рекомендации на основе истории просмотров.
    Алгоритм:
    1. Находим товары которые пользователь уже смотрел
    2. Находим других пользователей которые смотрели те же товары
    3. Рекоменуем товары которые они смотрели но текущий пользователь ещё нет
    """
    db = SessionLocal()
    try:
        # Товары которые пользователь уже смотрел
        viewed_ids = set(
            r.product_id for r in db.query(UserBehavior.product_id).filter(
                UserBehavior.user_session == user_session,
                UserBehavior.action == 'view_product',
                UserBehavior.product_id.isnot(None),
            ).all() if r.product_id
        )

        if not viewed_ids:
            return []

        # Другие пользователи которые смотрели те же товары
        similar_users = db.query(UserBehavior.user_session).filter(
            UserBehavior.product_id.in_(viewed_ids),
            UserBehavior.user_session != user_session,
            UserBehavior.action == 'view_product',
        ).distinct().all()

        similar_user_ids = [r[0] for r in similar_users]

        if not similar_user_ids:
            # Fallback: просто популярные товары
            popular = db.query(UserBehavior.product_id).filter(
                UserBehavior.action == 'view_product',
                UserBehavior.product_id.isnot(None),
            ).all()

            counts = {}
            for r in popular:
                counts[r[0]] = counts.get(r[0], 0) + 1

            sorted_ids = sorted(counts.keys(), key=lambda x: counts[x], reverse=True)
            results = []
            for pid in sorted_ids[:top_k]:
                if pid not in viewed_ids:
                    product = db.query(Product).filter(Product.id == pid).first()
                    if product:
                        results.append({
                            "product_id": pid,
                            "brand": product.brand,
                            "model": product.model,
                            "category": product.category,
                            "reason": "Популярное",
                        })
            return results

        # Товары которые смотрели похожие пользователи
        candidate_products = db.query(UserBehavior.product_id).filter(
            UserBehavior.user_session.in_(similar_user_ids),
            UserBehavior.action == 'view_product',
            UserBehavior.product_id.isnot(None),
            ~UserBehavior.product_id.in_(viewed_ids),
        ).all()

        counts = {}
        for r in candidate_products:
            counts[r[0]] = counts.get(r[0], 0) + 1

        # Топ-K по количеству упоминаний
        sorted_ids = sorted(counts.keys(), key=lambda x: counts[x], reverse=True)
        results = []
        for pid in sorted_ids[:top_k]:
            product = db.query(Product).filter(Product.id == pid).first()
            if product:
                results.append({
                    "product_id": pid,
                    "brand": product.brand,
                    "model": product.model,
                    "category": product.category,
                    "reason": f"Пользователи со схожими интересами смотрели ({counts[pid]} раз)",
                })

        return results

    finally:
        db.close()


def tfidf_search(query: str, top_k: int = 10) -> list[dict]:
    """
    Поиск товаров через TF-IDF по названиям.
    Извлекает признаки из brand + model + category.
    """
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    db = SessionLocal()
    try:
        products = db.query(Product).all()

        # Создаём текстовые описания
        docs = []
        for p in products:
            specs = p.specs or {}
            doc = f"{p.brand} {p.model} {p.category}"
            # Добавляем ключевые specs
            for key in ['type', 'memory_type', 'nand_type', 'efficiency']:
                if key in specs:
                    doc += f" {specs[key]}"
            docs.append(doc)

        # TF-IDF
        vectorizer = TfidfVectorizer(ngram_range=(1, 2))
        tfidf_matrix = vectorizer.fit_transform(docs)

        # Query
        query_vec = vectorizer.transform([query])
        similarities = cosine_similarity(query_vec, tfidf_matrix).flatten()

        # Топ-K
        top_indices = similarities.argsort()[-top_k:][::-1]

        results = []
        for idx in top_indices:
            p = products[idx]
            results.append({
                "product_id": p.id,
                "brand": p.brand,
                "model": p.model,
                "category": p.category,
                "similarity": round(float(similarities[idx]), 3),
            })

        return results

    finally:
        db.close()
