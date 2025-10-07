from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import SessionLocal
from .. import models, schemas
from ..services.security import can_view_request_history

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/", response_model=List[schemas.RequestOut])
def list_requests(
    user_id: Optional[int] = None,
    limit: int = 100,
    offset: int = 0,
    _: models.User = Depends(can_view_request_history),
    db: Session = Depends(get_db)
):
    """Получить историю запросов (только для админа и сотрудника)"""
    query = db.query(models.Request)
    
    if user_id:
        query = query.filter(models.Request.user_id == user_id)
    
    return query.order_by(models.Request.created_at.desc()).offset(offset).limit(limit).all()


@router.get("/users", response_model=List[schemas.UserOut])
def list_users_with_requests(_: models.User = Depends(can_view_request_history), db: Session = Depends(get_db)):
    """Получить список пользователей, которые делали запросы (только для админа и сотрудника)"""
    # Получаем уникальных пользователей, которые делали запросы
    user_ids = db.query(models.Request.user_id).distinct().all()
    user_ids = [uid[0] for uid in user_ids]
    
    return db.query(models.User).filter(models.User.id.in_(user_ids)).order_by(models.User.full_name).all()


@router.get("/stats")
def get_request_stats(_: models.User = Depends(can_view_request_history), db: Session = Depends(get_db)):
    """Получить статистику запросов (только для админа и сотрудника)"""
    total_requests = db.query(models.Request).count()
    
    # Статистика по пользователям
    user_stats = db.query(
        models.User.full_name,
        models.User.role,
        db.func.count(models.Request.id).label('request_count')
    ).join(models.Request, models.User.id == models.Request.user_id)\
     .group_by(models.User.id, models.User.full_name, models.User.role)\
     .order_by(db.func.count(models.Request.id).desc()).all()
    
    # Статистика по дням (последние 30 дней)
    from datetime import datetime, timedelta
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    daily_stats = db.query(
        db.func.date(models.Request.created_at).label('date'),
        db.func.count(models.Request.id).label('count')
    ).filter(models.Request.created_at >= thirty_days_ago)\
     .group_by(db.func.date(models.Request.created_at))\
     .order_by(db.func.date(models.Request.created_at)).all()
    
    return {
        "total_requests": total_requests,
        "user_stats": [
            {
                "user_name": stat.full_name or "Не указано",
                "role": stat.role.value,
                "request_count": stat.request_count
            }
            for stat in user_stats
        ],
        "daily_stats": [
            {
                "date": stat.date.isoformat(),
                "count": stat.count
            }
            for stat in daily_stats
        ]
    }


@router.get("/commercial-offers", response_model=List[schemas.CommercialOfferOut])
def list_commercial_offers(
    user_id: Optional[int] = None,
    limit: int = 100,
    offset: int = 0,
    _: models.User = Depends(can_view_request_history),
    db: Session = Depends(get_db)
):
    """Получить список коммерческих предложений (только для админа и сотрудника)"""
    query = db.query(models.CommercialOffer)
    
    if user_id:
        query = query.filter(models.CommercialOffer.user_id == user_id)
    
    return query.order_by(models.CommercialOffer.created_at.desc()).offset(offset).limit(limit).all()
