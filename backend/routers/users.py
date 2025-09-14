from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend.database import SessionLocal
from backend import models, schemas
from backend.services.security import get_password_hash, can_manage_users, get_current_user, can_manage_forwarders_and_clients


router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/", response_model=List[schemas.UserOut])
def list_users(_: models.User = Depends(can_manage_users), db: Session = Depends(get_db)):
    """Получить список всех пользователей (только для администратора)"""
    return db.query(models.User).order_by(models.User.id).all()


@router.get("/me", response_model=schemas.UserOut)
def get_current_user_info(current_user: models.User = Depends(get_current_user)):
    """Получить информацию о текущем пользователе"""
    return current_user


@router.post("/", response_model=schemas.UserOut)
def create_user(payload: schemas.UserCreate, _: models.User = Depends(can_manage_users), db: Session = Depends(get_db)):
    """Создать нового пользователя (только для администратора)"""
    exists = db.query(models.User).filter(models.User.username == payload.username).first()
    if exists:
        raise HTTPException(status_code=400, detail="Пользователь с таким логином уже существует")
    
    user = models.User(
        username=payload.username,
        password_hash=get_password_hash(payload.password),
        role=payload.role,
        full_name=payload.full_name,
        email=payload.email,
        phone=payload.phone,
        company_name=payload.company_name,
        responsible_person=payload.responsible_person,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.put("/{user_id}", response_model=schemas.UserOut)
def update_user(user_id: int, payload: schemas.UserUpdate, _: models.User = Depends(can_manage_users), db: Session = Depends(get_db)):
    """Обновить пользователя (только для администратора)"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    if payload.password:
        user.password_hash = get_password_hash(payload.password)
    if payload.role is not None:
        user.role = payload.role
    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.email is not None:
        user.email = payload.email
    if payload.phone is not None:
        user.phone = payload.phone
    if payload.company_name is not None:
        user.company_name = payload.company_name
    if payload.responsible_person is not None:
        user.responsible_person = payload.responsible_person
    
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}")
def delete_user(user_id: int, _: models.User = Depends(can_manage_users), db: Session = Depends(get_db)):
    """Удалить пользователя (только для администратора)"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # Проверяем, что не удаляем последнего администратора
    if user.role == models.UserRole.admin:
        admin_count = db.query(models.User).filter(models.User.role == models.UserRole.admin).count()
        if admin_count <= 1:
            raise HTTPException(status_code=400, detail="Нельзя удалить последнего администратора")
    
    db.delete(user)
    db.commit()
    return {"deleted": True}


@router.get("/roles", response_model=List[str])
def get_available_roles(_: models.User = Depends(can_manage_users)):
    """Получить список доступных ролей"""
    return [role.value for role in models.UserRole]


# Endpoints для сотрудников (управление экспедиторами и клиентами)
@router.get("/forwarders-and-clients", response_model=List[schemas.UserOut])
def list_forwarders_and_clients(_: models.User = Depends(can_manage_forwarders_and_clients), db: Session = Depends(get_db)):
    """Получить список экспедиторов и клиентов (для сотрудников и администраторов)"""
    return db.query(models.User).filter(
        models.User.role.in_([models.UserRole.forwarder, models.UserRole.client])
    ).order_by(models.User.id).all()


@router.post("/forwarder", response_model=schemas.UserOut)
def create_forwarder(payload: schemas.UserCreate, _: models.User = Depends(can_manage_forwarders_and_clients), db: Session = Depends(get_db)):
    """Создать нового экспедитора (для сотрудников и администраторов)"""
    if payload.role not in [models.UserRole.forwarder, models.UserRole.client]:
        raise HTTPException(status_code=400, detail="Можно создавать только экспедиторов и клиентов")
    
    exists = db.query(models.User).filter(models.User.username == payload.username).first()
    if exists:
        raise HTTPException(status_code=400, detail="Пользователь с таким логином уже существует")
    
    user = models.User(
        username=payload.username,
        password_hash=get_password_hash(payload.password),
        role=payload.role,
        full_name=payload.full_name,
        email=payload.email,
        phone=payload.phone,
        company_name=payload.company_name,
        responsible_person=payload.responsible_person,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.put("/forwarder/{user_id}", response_model=schemas.UserOut)
def update_forwarder(user_id: int, payload: schemas.UserUpdate, _: models.User = Depends(can_manage_forwarders_and_clients), db: Session = Depends(get_db)):
    """Обновить экспедитора или клиента (для сотрудников и администраторов)"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    if user.role not in [models.UserRole.forwarder, models.UserRole.client]:
        raise HTTPException(status_code=403, detail="Можно редактировать только экспедиторов и клиентов")
    
    if payload.role and payload.role not in [models.UserRole.forwarder, models.UserRole.client]:
        raise HTTPException(status_code=400, detail="Можно устанавливать только роли экспедитора и клиента")
    
    # Обновляем только переданные поля
    update_data = payload.dict(exclude_unset=True)
    if 'password' in update_data:
        update_data['password_hash'] = get_password_hash(update_data.pop('password'))
    
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    return user


@router.delete("/forwarder/{user_id}")
def delete_forwarder(user_id: int, _: models.User = Depends(can_manage_forwarders_and_clients), db: Session = Depends(get_db)):
    """Удалить экспедитора или клиента (для сотрудников и администраторов)"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    if user.role not in [models.UserRole.forwarder, models.UserRole.client]:
        raise HTTPException(status_code=403, detail="Можно удалять только экспедиторов и клиентов")
    
    db.delete(user)
    db.commit()
    return {"message": "Пользователь удален"}
