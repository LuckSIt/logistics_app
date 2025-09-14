from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import SessionLocal
from backend import models, schemas
from backend.services.security import get_current_user, can_add_tariffs, can_view_archive
from backend.services.tariff_archive import TariffArchiveService

router = APIRouter()


def _format_route(archive):
    """Форматирует маршрут из данных архива"""
    route_parts = []
    
    # Добавляем город отправления
    if archive.origin_city:
        route_parts.append(archive.origin_city)
    elif archive.origin_country:
        route_parts.append(archive.origin_country)
    
    # Добавляем город назначения
    if archive.destination_city:
        route_parts.append(archive.destination_city)
    elif archive.destination_country:
        route_parts.append(archive.destination_country)
    
    # Если есть транзитный порт или станции
    if archive.transit_port:
        route_parts.append(f"через {archive.transit_port}")
    elif archive.departure_station and archive.arrival_station:
        route_parts.append(f"{archive.departure_station} → {archive.arrival_station}")
    
    if len(route_parts) >= 2:
        return " → ".join(route_parts)
    elif len(route_parts) == 1:
        return route_parts[0]
    else:
        return "-"


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/", response_model=List[schemas.TariffOut])
def list_tariffs(
    supplier_id: Optional[int] = None,
    transport_type: Optional[schemas.TransportType] = None,
    origin_city: Optional[str] = None,
    destination_city: Optional[str] = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Получить список тарифов (доступно всем пользователям)"""
    query = db.query(models.Tariff)
    if supplier_id:
        query = query.filter(models.Tariff.supplier_id == supplier_id)
    if transport_type:
        query = query.filter(models.Tariff.transport_type == transport_type)
    if origin_city:
        query = query.filter(models.Tariff.origin_city == origin_city)
    if destination_city:
        query = query.filter(models.Tariff.destination_city == destination_city)
    return query.order_by(models.Tariff.id.desc()).all()


@router.get("/id/{tariff_id}", response_model=schemas.TariffOut)
def get_tariff(tariff_id: int, _: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Получить тариф по ID (доступно всем пользователям)"""
    t = db.query(models.Tariff).filter(models.Tariff.id == tariff_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Тариф не найден")
    return t


@router.put("/id/{tariff_id}", response_model=schemas.TariffOut)
def update_tariff(tariff_id: int, payload: schemas.TariffIn, _: models.User = Depends(can_add_tariffs), db: Session = Depends(get_db)):
    """Обновить тариф (доступно всем кроме клиентов)"""
    t = db.query(models.Tariff).filter(models.Tariff.id == tariff_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Тариф не найден")
    for k, v in payload.dict().items():
        setattr(t, k, v)
    db.commit()
    db.refresh(t)
    return t


@router.delete("/id/{tariff_id}")
def delete_tariff(tariff_id: int, _: models.User = Depends(can_add_tariffs), db: Session = Depends(get_db)):
    """Удалить тариф (доступно всем кроме клиентов)"""
    t = db.query(models.Tariff).filter(models.Tariff.id == tariff_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Тариф не найден")
    db.delete(t)
    db.commit()
    return {"deleted": True}


@router.get("/archive", response_model=List[schemas.TariffArchiveOut])
def list_archived_tariffs(
    supplier_id: Optional[int] = None,
    transport_type: Optional[schemas.TransportType] = None,
    origin_city: Optional[str] = None,
    destination_city: Optional[str] = None,
    _: models.User = Depends(can_view_archive),
    db: Session = Depends(get_db),
):
    """Получить список архивных тарифов (только для админа и сотрудника)"""
    query = db.query(models.TariffArchive)
    if supplier_id:
        query = query.filter(models.TariffArchive.supplier_id == supplier_id)
    if transport_type:
        query = query.filter(models.TariffArchive.transport_type == transport_type)
    if origin_city:
        query = query.filter(models.TariffArchive.origin_city == origin_city)
    if destination_city:
        query = query.filter(models.TariffArchive.destination_city == destination_city)
    return query.order_by(models.TariffArchive.id.desc()).all()


@router.post("/id/{tariff_id}/archive")
def archive_tariff(tariff_id: int, _: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    t = db.query(models.Tariff).filter(models.Tariff.id == tariff_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Тариф не найден")
    
    archive_service = TariffArchiveService(db)
    archived_tariff = archive_service.archive_tariff(t, "Ручное архивирование")
    
    return {"archived": True, "archive_id": archived_tariff.id}


@router.get("/archive", response_model=List[dict])
def list_archive(_: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Получает полные данные архивных тарифов для отображения"""
    archived_tariffs = db.query(models.TariffArchive).filter(
        models.TariffArchive.is_active == True
    ).order_by(models.TariffArchive.archived_at.desc()).all()
    
    # Получаем данные поставщиков и пользователей
    suppliers = {s.id: s for s in db.query(models.Supplier).all()}
    users = {u.id: u for u in db.query(models.User).all()}
    
    result = []
    for archive in archived_tariffs:
        supplier = suppliers.get(archive.supplier_id)
        creator = users.get(archive.created_by_user_id) if archive.created_by_user_id else None
        
        result.append({
            "id": archive.id,
            "archived_at": archive.archived_at.isoformat() if archive.archived_at else None,
            "supplier_name": supplier.name if supplier else f"ID: {archive.supplier_id}",
            "transport_type": archive.transport_type.value if archive.transport_type else None,
            "route": _format_route(archive),
            "basis": archive.basis,
            "price_rub": archive.price_rub,
            "price_usd": archive.price_usd,
            "archive_reason": archive.archive_reason,
            "original_tariff_id": archive.original_tariff_id,
            "created_by": creator.username if creator else "Система",
            "created_by_role": creator.role.value if creator else None
        })
    
    return result


@router.post("/archive/{tariff_id}/restore")
def restore_tariff(tariff_id: int, _: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    a = db.query(models.TariffArchive).filter(models.TariffArchive.original_tariff_id == tariff_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Запись архива не найдена")
    db.delete(a)
    db.commit()
    return {"restored": True}


@router.post("/bulk")
def create_bulk_tariffs(
    supplier_id: int,
    tariffs: List[dict],
    _: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Массовое создание тарифов из отредактированных данных с автоматическим архивированием"""
    supplier = db.query(models.Supplier).filter(models.Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Поставщик не найден")
    
    archive_service = TariffArchiveService(db)
    created = 0
    archived = 0
    
    for tariff_data in tariffs:
        try:
            # Конвертация валюты если нужно
            price_rub = tariff_data.get("price_rub")
            if price_rub is None and tariff_data.get("price_usd") is not None:
                from backend.services import cbr
                rate = cbr.get_usd_rate()
                price_rub = float(tariff_data["price_usd"]) * rate
            
            # Проверяем, есть ли уже тарифы с такими же параметрами
            existing_tariffs = db.query(models.Tariff).filter(
                models.Tariff.supplier_id == supplier_id,
                models.Tariff.transport_type == tariff_data.get("transport_type"),
                models.Tariff.basis == tariff_data.get("basis"),
                models.Tariff.origin_city == tariff_data.get("origin_city"),
                models.Tariff.destination_city == tariff_data.get("destination_city"),
                models.Tariff.vehicle_type == tariff_data.get("vehicle_type")
            ).all()
            
            # Архивируем существующие тарифы
            if existing_tariffs:
                archive_service.archive_tariffs_batch(
                    existing_tariffs, 
                    f"Замена новым тарифом от {supplier.name}"
                )
                archived += len(existing_tariffs)
                
                # Удаляем старые тарифы
                for old_tariff in existing_tariffs:
                    db.delete(old_tariff)
            
            # Создаем новый тариф
            # Обрабатываем дату валидности
            validity_date = tariff_data.get("validity_date")
            if validity_date and isinstance(validity_date, str):
                try:
                    from datetime import datetime
                    # Пробуем разные форматы даты
                    for fmt in ["%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S"]:
                        try:
                            validity_date = datetime.strptime(validity_date, fmt).date()
                            break
                        except ValueError:
                            continue
                    else:
                        # Если не удалось распарсить, устанавливаем None
                        validity_date = None
                except Exception:
                    validity_date = None
            
            tariff = models.Tariff(
                supplier_id=supplier_id,
                transport_type=tariff_data.get("transport_type"),
                basis=tariff_data.get("basis"),
                origin_country=tariff_data.get("origin_country"),
                origin_city=tariff_data.get("origin_city"),
                border_point=tariff_data.get("border_point"),
                destination_country=tariff_data.get("destination_country"),
                destination_city=tariff_data.get("destination_city"),
                vehicle_type=tariff_data.get("vehicle_type"),
                price_rub=price_rub,
                price_usd=tariff_data.get("price_usd"),
                validity_date=validity_date,
                currency_conversion=tariff_data.get("currency_conversion"),
                transit_time_days=tariff_data.get("transit_time_days"),
                source_file=tariff_data.get("source_file"),
                # Дополнительные поля
                transit_port=tariff_data.get("transit_port"),
                departure_station=tariff_data.get("departure_station"),
                arrival_station=tariff_data.get("arrival_station"),
                rail_tariff_rub=tariff_data.get("rail_tariff_rub"),
                cbx_cost=tariff_data.get("cbx_cost"),
                terminal_handling_cost=tariff_data.get("terminal_handling_cost"),
                auto_pickup_cost=tariff_data.get("auto_pickup_cost"),
                security_cost=tariff_data.get("security_cost"),
                precarriage_cost=tariff_data.get("precarriage_cost"),
                created_by_user_id=current_user.id,  # Сохраняем создателя тарифа
            )
            db.add(tariff)
            created += 1
        except Exception as e:
            print(f"Ошибка создания тарифа: {e}")
            continue
    
    db.commit()
    return {
        "created": created, 
        "archived": archived,
        "total": len(tariffs)
    }


