from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..database import SessionLocal
from .. import models, schemas
from ..services.security import get_current_user


router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def require_admin(user: models.User = Depends(get_current_user)):
    if user.role != models.UserRole.admin:
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    return user


@router.get("/", response_model=List[schemas.DiscountOut])
def list_discounts(_: models.User = Depends(require_admin), db: Session = Depends(get_db)):
    return db.query(models.Discount).order_by(models.Discount.id).all()


@router.post("/", response_model=schemas.DiscountOut)
def create_discount(payload: schemas.DiscountCreate, _: models.User = Depends(require_admin), db: Session = Depends(get_db)):
    # Проверяем существование пользователя и поставщика
    user = db.query(models.User).filter(models.User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    supplier = db.query(models.Supplier).filter(models.Supplier.id == payload.supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Поставщик не найден")
    
    # Проверяем, не существует ли уже скидка для этой пары
    existing = db.query(models.Discount).filter(
        models.Discount.user_id == payload.user_id,
        models.Discount.supplier_id == payload.supplier_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Скидка для этого пользователя и поставщика уже существует")
    
    discount = models.Discount(
        user_id=payload.user_id,
        supplier_id=payload.supplier_id,
        discount_percent=payload.discount_percent,
    )
    db.add(discount)
    db.commit()
    db.refresh(discount)
    return discount


@router.put("/{discount_id}", response_model=schemas.DiscountOut)
def update_discount(discount_id: int, payload: schemas.DiscountUpdate, _: models.User = Depends(require_admin), db: Session = Depends(get_db)):
    discount = db.query(models.Discount).filter(models.Discount.id == discount_id).first()
    if not discount:
        raise HTTPException(status_code=404, detail="Скидка не найдена")
    
    if payload.discount_percent is not None:
        discount.discount_percent = payload.discount_percent
    
    db.commit()
    db.refresh(discount)
    return discount


@router.delete("/{discount_id}")
def delete_discount(discount_id: int, _: models.User = Depends(require_admin), db: Session = Depends(get_db)):
    discount = db.query(models.Discount).filter(models.Discount.id == discount_id).first()
    if not discount:
        raise HTTPException(status_code=404, detail="Скидка не найдена")
    
    db.delete(discount)
    db.commit()
    return {"deleted": True}
