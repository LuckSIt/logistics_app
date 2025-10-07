from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import SessionLocal
from .. import models, schemas
from ..services.security import get_current_user, require_admin

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# СВХ (Склад временного хранения)
@router.get("/svh", response_model=List[schemas.SVHOut])
def get_svh_list(db: Session = Depends(get_db)):
    """Получение списка СВХ"""
    return db.query(models.AuxiliarySVH).all()


@router.post("/svh", response_model=schemas.SVHOut)
def create_svh(
    svh: schemas.SVHCreate,
    _: models.User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Создание СВХ (только для администраторов)"""
    db_svh = models.AuxiliarySVH(**svh.dict())
    db.add(db_svh)
    db.commit()
    db.refresh(db_svh)
    return db_svh


# Автовывоз
@router.get("/trucking", response_model=List[schemas.TruckingOut])
def get_trucking_list(db: Session = Depends(get_db)):
    """Получение списка автовывоза"""
    trucking_list = db.query(models.AuxiliaryTrucking).all()
    
    # Вычисляем total_rate для каждого элемента
    for trucking in trucking_list:
        trucking.total_rate = trucking.base_rate + trucking.per_km_rate * trucking.km_from_svh
    
    return trucking_list


@router.post("/trucking", response_model=schemas.TruckingOut)
def create_trucking(
    trucking: schemas.TruckingCreate,
    _: models.User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Создание автовывоза (только для администраторов)"""
    # Вычисляем total_rate
    total_rate = trucking.base_rate + trucking.per_km_rate * trucking.km_from_svh
    
    db_trucking = models.AuxiliaryTrucking(
        **trucking.dict(),
        total_rate=total_rate
    )
    db.add(db_trucking)
    db.commit()
    db.refresh(db_trucking)
    return db_trucking


# Предперевозка ЖД
@router.get("/precarriage/rail", response_model=List[schemas.PrecarriageRailOut])
def get_precarriage_rail_list(db: Session = Depends(get_db)):
    """Получение списка предперевозки ЖД"""
    precarriage_list = db.query(models.AuxiliaryPrecarriageRail).all()
    
    # Вычисляем total_rate для каждого элемента
    for precarriage in precarriage_list:
        local_charges = precarriage.local_charges or 0
        precarriage.total_rate = (precarriage.base_rate + 
                                 precarriage.per_km_rate * precarriage.km_from_station + 
                                 local_charges)
    
    return precarriage_list


@router.post("/precarriage/rail", response_model=schemas.PrecarriageRailOut)
def create_precarriage_rail(
    precarriage: schemas.PrecarriageRailCreate,
    _: models.User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Создание предперевозки ЖД (только для администраторов)"""
    # Вычисляем total_rate согласно формуле из ТЗ
    local_charges = precarriage.local_charges or 0
    total_rate = (precarriage.base_rate + 
                  precarriage.per_km_rate * precarriage.km_from_station + 
                  local_charges)
    
    db_precarriage = models.AuxiliaryPrecarriageRail(
        **precarriage.dict(),
        total_rate=total_rate
    )
    db.add(db_precarriage)
    db.commit()
    db.refresh(db_precarriage)
    return db_precarriage


# Предперевозка море
@router.get("/precarriage/sea", response_model=List[schemas.PrecarriageSeaOut])
def get_precarriage_sea_list(db: Session = Depends(get_db)):
    """Получение списка предперевозки море"""
    precarriage_list = db.query(models.AuxiliaryPrecarriageSea).all()
    
    # Вычисляем total_rate для каждого элемента
    for precarriage in precarriage_list:
        thc_port = precarriage.thc_port or 0
        precarriage.total_rate = (precarriage.base_rate + 
                                 precarriage.per_km_rate * precarriage.km_from_port + 
                                 thc_port)
    
    return precarriage_list


@router.post("/precarriage/sea", response_model=schemas.PrecarriageSeaOut)
def create_precarriage_sea(
    precarriage: schemas.PrecarriageSeaCreate,
    _: models.User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Создание предперевозки море (только для администраторов)"""
    # Вычисляем total_rate согласно формуле из ТЗ
    thc_port = precarriage.thc_port or 0
    total_rate = (precarriage.base_rate + 
                  precarriage.per_km_rate * precarriage.km_from_port + 
                  thc_port)
    
    db_precarriage = models.AuxiliaryPrecarriageSea(
        **precarriage.dict(),
        total_rate=total_rate
    )
    db.add(db_precarriage)
    db.commit()
    db.refresh(db_precarriage)
    return db_precarriage


# Массовые операции для вспомогательных таблиц
@router.post("/trucking/bulk")
def create_trucking_bulk(
    trucking_list: List[schemas.TruckingCreate],
    _: models.User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Массовое создание автовывоза"""
    created_items = []
    for trucking in trucking_list:
        total_rate = trucking.base_rate + trucking.per_km_rate * trucking.km_from_svh
        db_trucking = models.AuxiliaryTrucking(
            **trucking.dict(),
            total_rate=total_rate
        )
        db.add(db_trucking)
        created_items.append(db_trucking)
    
    db.commit()
    for item in created_items:
        db.refresh(item)
    
    return {"message": f"Создано {len(created_items)} записей автовывоза"}


@router.post("/precarriage/rail/bulk")
def create_precarriage_rail_bulk(
    precarriage_list: List[schemas.PrecarriageRailCreate],
    _: models.User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Массовое создание предперевозки ЖД"""
    created_items = []
    for precarriage in precarriage_list:
        local_charges = precarriage.local_charges or 0
        total_rate = (precarriage.base_rate + 
                      precarriage.per_km_rate * precarriage.km_from_station + 
                      local_charges)
        db_precarriage = models.AuxiliaryPrecarriageRail(
            **precarriage.dict(),
            total_rate=total_rate
        )
        db.add(db_precarriage)
        created_items.append(db_precarriage)
    
    db.commit()
    for item in created_items:
        db.refresh(item)
    
    return {"message": f"Создано {len(created_items)} записей предперевозки ЖД"}


@router.post("/precarriage/sea/bulk")
def create_precarriage_sea_bulk(
    precarriage_list: List[schemas.PrecarriageSeaCreate],
    _: models.User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Массовое создание предперевозки море"""
    created_items = []
    for precarriage in precarriage_list:
        thc_port = precarriage.thc_port or 0
        total_rate = (precarriage.base_rate + 
                      precarriage.per_km_rate * precarriage.km_from_port + 
                      thc_port)
        db_precarriage = models.AuxiliaryPrecarriageSea(
            **precarriage.dict(),
            total_rate=total_rate
        )
        db.add(db_precarriage)
        created_items.append(db_precarriage)
    
    db.commit()
    for item in created_items:
        db.refresh(item)
    
    return {"message": f"Создано {len(created_items)} записей предперевозки море"}


# Получение данных для калькулятора
@router.get("/calculator/svh/{city}")
def get_svh_for_city(city: str, db: Session = Depends(get_db)):
    """Получение СВХ для конкретного города"""
    svh_list = db.query(models.AuxiliarySVH).filter(
        models.AuxiliarySVH.city.ilike(f"%{city}%")
    ).all()
    return svh_list


@router.get("/calculator/trucking/{destination_city}")
def get_trucking_for_city(destination_city: str, db: Session = Depends(get_db)):
    """Получение автовывоза для конкретного города назначения"""
    trucking_list = db.query(models.AuxiliaryTrucking).filter(
        models.AuxiliaryTrucking.destination_city.ilike(f"%{destination_city}%")
    ).all()
    
    # Вычисляем total_rate для каждого элемента
    for trucking in trucking_list:
        trucking.total_rate = trucking.base_rate + trucking.per_km_rate * trucking.km_from_svh
    
    return trucking_list


@router.get("/calculator/precarriage/rail/{origin_city}")
def get_precarriage_rail_for_city(origin_city: str, db: Session = Depends(get_db)):
    """Получение предперевозки ЖД для конкретного города отправления"""
    precarriage_list = db.query(models.AuxiliaryPrecarriageRail).filter(
        models.AuxiliaryPrecarriageRail.origin_city.ilike(f"%{origin_city}%")
    ).all()
    
    # Вычисляем total_rate для каждого элемента
    for precarriage in precarriage_list:
        local_charges = precarriage.local_charges or 0
        precarriage.total_rate = (precarriage.base_rate + 
                                 precarriage.per_km_rate * precarriage.km_from_station + 
                                 local_charges)
    
    return precarriage_list


@router.get("/calculator/precarriage/sea/{origin_city}")
def get_precarriage_sea_for_city(origin_city: str, db: Session = Depends(get_db)):
    """Получение предперевозки море для конкретного города отправления"""
    precarriage_list = db.query(models.AuxiliaryPrecarriageSea).filter(
        models.AuxiliaryPrecarriageSea.origin_city.ilike(f"%{origin_city}%")
    ).all()
    
    # Вычисляем total_rate для каждого элемента
    for precarriage in precarriage_list:
        thc_port = precarriage.thc_port or 0
        precarriage.total_rate = (precarriage.base_rate + 
                                 precarriage.per_km_rate * precarriage.km_from_port + 
                                 thc_port)
    
    return precarriage_list


