from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from database import SessionLocal
import models, schemas
from services.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_user,
)
import random
import string
from typing import Dict

router = APIRouter()

# Временное хранилище для SMS кодов (в продакшене использовать Redis)
sms_codes: Dict[str, str] = {}
reset_tokens: Dict[str, str] = {}


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/register", response_model=schemas.UserOut)
def register(payload: schemas.UserRegister, db: Session = Depends(get_db)):
    exists = db.query(models.User).filter(models.User.username == payload.username).first()
    if exists:
        raise HTTPException(status_code=400, detail="Пользователь с таким логином уже существует")
    user = models.User(
        username=payload.username,
        password_hash=get_password_hash(payload.password),
        role=models.UserRole.client,
        full_name=payload.full_name,
        email=payload.email,
        phone=payload.phone,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверные учетные данные")
    if not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверные учетные данные")
    expires_delta = timedelta(minutes=60 * 24)
    token = create_access_token({"sub": str(user.id), "role": user.role.value}, expires_delta)
    return schemas.Token(access_token=token)


@router.get("/me", response_model=schemas.UserOut)
def me(current: models.User = Depends(get_current_user)):
    return current


@router.post("/send-sms-code")
def send_sms_code(data: dict, db: Session = Depends(get_db)):
    """Отправка SMS кода для восстановления пароля (демо-версия)"""
    phone = data.get("phone")
    if not phone:
        raise HTTPException(status_code=400, detail="Номер телефона обязателен")
    
    # Проверяем, существует ли пользователь с таким номером телефона
    user = db.query(models.User).filter(models.User.phone == phone).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь с таким номером телефона не найден")
    
    # Генерируем 4-значный код
    code = ''.join(random.choices(string.digits, k=4))
    sms_codes[phone] = code
    
    # В демо-режиме выводим код в консоль
    print(f"🔐 ДЕМО: SMS код для номера {phone}: {code}")
    
    return {"message": "SMS код отправлен", "demo_code": code}


@router.post("/verify-sms-code")
def verify_sms_code(data: dict):
    """Проверка SMS кода"""
    phone = data.get("phone")
    code = data.get("code")
    
    if not phone or not code:
        raise HTTPException(status_code=400, detail="Номер телефона и код обязательны")
    
    stored_code = sms_codes.get(phone)
    if not stored_code or stored_code != code:
        raise HTTPException(status_code=400, detail="Неверный код подтверждения")
    
    # Удаляем использованный код
    del sms_codes[phone]
    
    # Генерируем временный токен для смены пароля
    reset_token = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
    reset_tokens[reset_token] = phone
    
    return {"message": "Код подтвержден", "token": reset_token}


@router.post("/reset-password")
def reset_password(data: dict, db: Session = Depends(get_db)):
    """Смена пароля по токену"""
    token = data.get("token")
    new_password = data.get("new_password")
    
    if not token or not new_password:
        raise HTTPException(status_code=400, detail="Токен и новый пароль обязательны")
    
    phone = reset_tokens.get(token)
    if not phone:
        raise HTTPException(status_code=400, detail="Недействительный токен")
    
    # Находим пользователя по номеру телефона
    user = db.query(models.User).filter(models.User.phone == phone).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # Обновляем пароль
    user.password_hash = get_password_hash(new_password)
    db.commit()
    
    # Удаляем использованный токен
    del reset_tokens[token]
    
    return {"message": "Пароль успешно изменен"}


