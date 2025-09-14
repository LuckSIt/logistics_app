import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from backend.database import SessionLocal
from backend import models


SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось проверить учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(models.User).filter(models.User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    return user


def require_admin(user: models.User = Depends(get_current_user)) -> models.User:
    """
    Проверка прав администратора
    """
    if user.role != models.UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Требуются права администратора"
        )
    return user


def require_employee_or_admin(user: models.User = Depends(get_current_user)) -> models.User:
    """
    Проверка прав сотрудника или администратора
    """
    if user.role not in [models.UserRole.admin, models.UserRole.employee]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Требуются права сотрудника или администратора"
        )
    return user


def require_forwarder_or_above(user: models.User = Depends(get_current_user)) -> models.User:
    """
    Проверка прав экспедитора или выше
    """
    if user.role not in [models.UserRole.admin, models.UserRole.employee, models.UserRole.forwarder]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Требуются права экспедитора или выше"
        )
    return user


def require_client_or_above(user: models.User = Depends(get_current_user)) -> models.User:
    """
    Проверка прав клиента или выше (все пользователи)
    """
    return user


def can_manage_users(user: models.User = Depends(get_current_user)) -> models.User:
    """
    Проверка прав на управление пользователями (только админ)
    """
    if user.role != models.UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только администратор может управлять пользователями"
        )
    return user


def can_manage_forwarders_and_clients(user: models.User = Depends(get_current_user)) -> models.User:
    """
    Проверка прав на управление экспедиторами и клиентами (сотрудник или администратор)
    """
    if user.role not in [models.UserRole.admin, models.UserRole.employee]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только сотрудник или администратор может управлять экспедиторами и клиентами"
        )
    return user


def can_set_markups(user: models.User = Depends(get_current_user)) -> models.User:
    """
    Проверка прав на установку наценок (админ и сотрудник)
    """
    if user.role not in [models.UserRole.admin, models.UserRole.employee]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только администратор и сотрудник могут устанавливать наценки"
        )
    return user


def can_view_archive(user: models.User = Depends(get_current_user)) -> models.User:
    """
    Проверка прав на просмотр архива тарифов (админ и сотрудник)
    """
    if user.role not in [models.UserRole.admin, models.UserRole.employee]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только администратор и сотрудник могут просматривать архив тарифов"
        )
    return user


def can_view_request_history(user: models.User = Depends(get_current_user)) -> models.User:
    """
    Проверка прав на просмотр истории запросов (админ и сотрудник)
    """
    if user.role not in [models.UserRole.admin, models.UserRole.employee]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только администратор и сотрудник могут просматривать историю запросов"
        )
    return user


def can_add_tariffs(user: models.User = Depends(get_current_user)) -> models.User:
    """
    Проверка прав на добавление тарифов (все кроме клиента)
    """
    if user.role == models.UserRole.client:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Клиенты не могут добавлять тарифы"
        )
    return user


def can_choose_transport(user: models.User = Depends(get_current_user)) -> models.User:
    """
    Проверка прав на выбор транспорта (все пользователи)
    """
    return user


def can_download_kp(user: models.User = Depends(get_current_user)) -> models.User:
    """
    Проверка прав на скачивание КП (все пользователи)
    """
    return user


