from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database import SessionLocal
from backend import models, schemas
from backend.services.security import get_current_user

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/", response_model=List[schemas.RequestOut])
def my_requests(current: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = db.query(models.Request).filter(models.Request.user_id == current.id).order_by(models.Request.created_at.desc()).all()
    return q


@router.post("/save", response_model=schemas.RequestOut)
def save_request(body: schemas.RequestIn, current: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    r = models.Request(user_id=current.id, request_data=body.request_data)
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


