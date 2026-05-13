"""Роутер обратной связи"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models import UserFeedback, UserBehavior

router = APIRouter()


# === Request Schemas ===

class FeedbackRequest(BaseModel):
    product_id: int
    feedback_type: str  # useful, not_useful
    alternative_id: Optional[int] = None


class BehaviorRequest(BaseModel):
    action: str  # search, view_product, click_alternative, compare
    search_query: Optional[str] = None
    product_id: Optional[int] = None
    target_product_id: Optional[int] = None
    category: Optional[str] = None


# === Endpoints ===

@router.post("/feedback", status_code=200)
async def submit_feedback(
    request: FeedbackRequest,
    db: Session = Depends(get_db),
):
    """
    Отправка обратной связи по товару/рекомендации.
    feedback_type: useful | not_useful
    """
    feedback = UserFeedback(
        user_session="anonymous",  # В продакшене — из cookies/session
        product_id=request.product_id,
        feedback_type=request.feedback_type,
        alternative_id=request.alternative_id,
    )
    db.add(feedback)
    db.commit()

    return {"message": "Feedback received", "type": request.feedback_type}


@router.post("/behavior", status_code=200)
async def track_behavior(
    request: BehaviorRequest,
    db: Session = Depends(get_db),
):
    """
    Трекинг поведения пользователя.
    action: search | view_product | click_alternative | compare
    """
    behavior = UserBehavior(
        user_session="anonymous",
        action=request.action,
        search_query=request.search_query,
        product_id=request.product_id,
        target_product_id=request.target_product_id,
        category=request.category,
    )
    db.add(behavior)
    db.commit()

    return {"message": "Behavior tracked", "action": request.action}


@router.get("/feedback/stats/{product_id}")
async def get_feedback_stats(
    product_id: int,
    db: Session = Depends(get_db),
):
    """
    Статистика обратной связи по товару.
    """
    useful = db.query(UserFeedback).filter(
        UserFeedback.product_id == product_id,
        UserFeedback.feedback_type == "useful",
    ).count()

    not_useful = db.query(UserFeedback).filter(
        UserFeedback.product_id == product_id,
        UserFeedback.feedback_type == "not_useful",
    ).count()

    total = useful + not_useful
    useful_pct = (useful / total * 100) if total > 0 else 0

    return {
        "product_id": product_id,
        "useful": useful,
        "not_useful": not_useful,
        "total": total,
        "useful_pct": round(useful_pct, 1),
    }
