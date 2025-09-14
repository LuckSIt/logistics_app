from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import SessionLocal
import models, schemas
from services.security import get_current_user

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/")
def my_requests(current: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Администраторы и сотрудники видят запросы всех клиентов
    if current.role in [models.UserRole.admin, models.UserRole.employee]:
        # Получаем всех клиентов
        client_ids = db.query(models.User.id).filter(models.User.role == models.UserRole.client).all()
        client_ids = [client_id[0] for client_id in client_ids]
        
        if client_ids:
            # Получаем запросы с информацией о пользователях
            q = db.query(models.Request, models.User).join(
                models.User, models.Request.user_id == models.User.id
            ).filter(models.Request.user_id.in_(client_ids)).order_by(models.Request.created_at.desc()).all()
        else:
            q = []
    else:
        # Клиенты и экспедиторы видят только свои запросы
        q = db.query(models.Request, models.User).join(
            models.User, models.Request.user_id == models.User.id
        ).filter(models.Request.user_id == current.id).order_by(models.Request.created_at.desc()).all()
    
    # Формируем результат с информацией о пользователе
    result = []
    for request, user in q:
        result.append({
            "id": request.id,
            "user_id": request.user_id,
            "request_data": request.request_data,
            "created_at": request.created_at,
            "user": {
                "id": user.id,
                "username": user.username,
                "full_name": user.full_name,
                "role": user.role.value if user.role else None,
                "company_name": user.company_name
            }
        })
    
    return result


@router.post("/save", response_model=schemas.RequestOut)
def save_request(body: schemas.RequestIn, current: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    r = models.Request(user_id=current.id, request_data=body.request_data)
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


