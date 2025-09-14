"""
API роутер для получения статистики системы.
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta
from backend.database import SessionLocal
from backend import models
from backend.services.security import get_current_user

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/", response_model=Dict[str, Any])
def get_system_stats(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Получить статистику системы
    """
    
    # Общее количество тарифов
    total_tariffs = db.query(models.Tariff).count()
    
    # Количество архивных тарифов
    archived_tariffs = db.query(models.TariffArchive).filter(
        models.TariffArchive.is_active == True
    ).count()
    
    # Общее количество тарифов (активные + архивные)
    all_tariffs = total_tariffs + archived_tariffs
    
    # Количество поставщиков
    total_suppliers = db.query(models.Supplier).count()
    
    # Количество пользователей по ролям
    total_users = db.query(models.User).count()
    admin_users = db.query(models.User).filter(models.User.role == models.UserRole.admin).count()
    employee_users = db.query(models.User).filter(models.User.role == models.UserRole.employee).count()
    forwarder_users = db.query(models.User).filter(models.User.role == models.UserRole.forwarder).count()
    client_users = db.query(models.User).filter(models.User.role == models.UserRole.client).count()
    
    # Количество коммерческих предложений
    total_offers = db.query(models.CommercialOffer).count()
    
    # Количество запросов
    total_requests = db.query(models.Request).count()
    
    # Статистика за последний месяц
    month_ago = datetime.utcnow() - timedelta(days=30)
    
    # Тарифы за последний месяц
    tariffs_this_month = db.query(models.Tariff).filter(
        models.Tariff.created_at >= month_ago
    ).count()
    
    # Архивные тарифы за последний месяц
    archived_this_month = db.query(models.TariffArchive).filter(
        and_(
            models.TariffArchive.archived_at >= month_ago,
            models.TariffArchive.is_active == True
        )
    ).count()
    
    # Коммерческие предложения за последний месяц
    offers_this_month = db.query(models.CommercialOffer).filter(
        models.CommercialOffer.created_at >= month_ago
    ).count()
    
    # Запросы за последний месяц
    requests_this_month = db.query(models.Request).filter(
        models.Request.created_at >= month_ago
    ).count()
    
    # Статистика за последнюю неделю
    week_ago = datetime.utcnow() - timedelta(days=7)
    
    # Коммерческие предложения за последнюю неделю
    offers_this_week = db.query(models.CommercialOffer).filter(
        models.CommercialOffer.created_at >= week_ago
    ).count()
    
    # Новые пользователи за последний месяц
    new_users_this_month = db.query(models.User).filter(
        models.User.created_at >= month_ago
    ).count()
    
    # Новые поставщики за последний месяц
    new_suppliers_this_month = db.query(models.Supplier).filter(
        models.Supplier.id.isnot(None)  # Все поставщики считаем новыми, так как нет поля created_at
    ).count()
    
    return {
        "tariffs": all_tariffs,
        "active_tariffs": total_tariffs,
        "archived_tariffs": archived_tariffs,
        "suppliers": total_suppliers,
        "users": total_users,
        "admin_users": admin_users,
        "employee_users": employee_users,
        "forwarder_users": forwarder_users,
        "client_users": client_users,
        "offers": total_offers,
        "requests": total_requests,
        "trends": {
            "tariffs_this_month": tariffs_this_month + archived_this_month,
            "offers_this_week": offers_this_week,
            "offers_this_month": offers_this_month,
            "requests_this_month": requests_this_month,
            "new_users_this_month": new_users_this_month,
            "new_suppliers_this_month": new_suppliers_this_month
        }
    }
