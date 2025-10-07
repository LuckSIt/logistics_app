from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
import models, schemas
from services.security import can_set_markups

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/suppliers", response_model=List[schemas.SupplierOut])
def list_suppliers_with_markups(_: models.User = Depends(can_set_markups), db: Session = Depends(get_db)):
    """Получить список поставщиков с наценками (только для админа и сотрудника)"""
    return db.query(models.Supplier).order_by(models.Supplier.id).all()


@router.put("/suppliers/{supplier_id}/markup")
def update_supplier_markup(
    supplier_id: int,
    markup_percent: float = None,
    markup_fixed: float = None,
    _: models.User = Depends(can_set_markups),
    db: Session = Depends(get_db)
):
    """Обновить наценки поставщика (только для админа и сотрудника)"""
    supplier = db.query(models.Supplier).filter(models.Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Поставщик не найден")
    
    if markup_percent is not None:
        supplier.markup_percent = markup_percent
    if markup_fixed is not None:
        supplier.markup_fixed = markup_fixed
    
    db.commit()
    db.refresh(supplier)
    return {"message": "Наценки обновлены", "supplier": supplier}


@router.get("/discounts", response_model=List[schemas.DiscountOut])
def list_discounts(_: models.User = Depends(can_set_markups), db: Session = Depends(get_db)):
    """Получить список скидок (только для админа и сотрудника)"""
    return db.query(models.Discount).order_by(models.Discount.id).all()


@router.post("/discounts", response_model=schemas.DiscountOut)
def create_discount(
    user_id: int,
    supplier_id: int,
    discount_percent: float,
    _: models.User = Depends(can_set_markups),
    db: Session = Depends(get_db)
):
    """Создать скидку для пользователя (только для админа и сотрудника)"""
    # Проверяем существование пользователя и поставщика
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    supplier = db.query(models.Supplier).filter(models.Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Поставщик не найден")
    
    # Проверяем, не существует ли уже скидка
    existing_discount = db.query(models.Discount).filter(
        models.Discount.user_id == user_id,
        models.Discount.supplier_id == supplier_id
    ).first()
    
    if existing_discount:
        existing_discount.discount_percent = discount_percent
        db.commit()
        db.refresh(existing_discount)
        return existing_discount
    
    # Создаем новую скидку
    discount = models.Discount(
        user_id=user_id,
        supplier_id=supplier_id,
        discount_percent=discount_percent
    )
    db.add(discount)
    db.commit()
    db.refresh(discount)
    return discount


@router.put("/discounts/{discount_id}")
def update_discount(
    discount_id: int,
    discount_percent: float,
    _: models.User = Depends(can_set_markups),
    db: Session = Depends(get_db)
):
    """Обновить скидку (только для админа и сотрудника)"""
    discount = db.query(models.Discount).filter(models.Discount.id == discount_id).first()
    if not discount:
        raise HTTPException(status_code=404, detail="Скидка не найдена")
    
    discount.discount_percent = discount_percent
    db.commit()
    db.refresh(discount)
    return {"message": "Скидка обновлена", "discount": discount}


@router.delete("/discounts/{discount_id}")
def delete_discount(
    discount_id: int,
    _: models.User = Depends(can_set_markups),
    db: Session = Depends(get_db)
):
    """Удалить скидку (только для админа и сотрудника)"""
    discount = db.query(models.Discount).filter(models.Discount.id == discount_id).first()
    if not discount:
        raise HTTPException(status_code=404, detail="Скидка не найдена")
    
    db.delete(discount)
    db.commit()
    return {"deleted": True}
