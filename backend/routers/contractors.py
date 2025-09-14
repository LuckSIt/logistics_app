from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import os
import re
from pathlib import Path
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


def require_admin(user: models.User = Depends(get_current_user)):
    if user.role != models.UserRole.admin:
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    return user


@router.post("/", response_model=schemas.SupplierOut)
def create_supplier(data: schemas.SupplierCreate, _: models.User = Depends(require_admin), db: Session = Depends(get_db)):
    exists = db.query(models.Supplier).filter(models.Supplier.name == data.name).first()
    if exists:
        raise HTTPException(status_code=400, detail="Такой поставщик уже существует")
    supplier = models.Supplier(**data.dict())
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier


@router.post("/client", response_model=schemas.SupplierOut)
def create_supplier_by_client(data: schemas.SupplierCreate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Создание поставщика клиентом (без прав администратора)"""
    # Проверяем, что пользователь не администратор (только клиенты могут создавать поставщиков)
    if current_user.role == models.UserRole.admin:
        raise HTTPException(status_code=403, detail="Администраторы не могут создавать поставщиков через этот endpoint")
    
    exists = db.query(models.Supplier).filter(models.Supplier.name == data.name).first()
    if exists:
        raise HTTPException(status_code=400, detail="Такой поставщик уже существует")
    
    supplier = models.Supplier(**data.dict())
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier


@router.get("/", response_model=List[schemas.SupplierOut])
def list_suppliers(_: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(models.Supplier).order_by(models.Supplier.name).all()


@router.patch("/{supplier_id}/markup", response_model=schemas.SupplierOut)
def set_markup(supplier_id: int, markup_percent: float = 0.0, markup_fixed: float = 0.0, _: models.User = Depends(require_admin), db: Session = Depends(get_db)):
    supplier = db.query(models.Supplier).filter(models.Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Поставщик не найден")
    supplier.markup_percent = markup_percent
    supplier.markup_fixed = markup_fixed
    db.commit()
    db.refresh(supplier)
    return supplier


@router.patch("/{supplier_id}/markup/client", response_model=schemas.SupplierOut)
def update_supplier_markup_client(
    supplier_id: int,
    data: schemas.SupplierMarkupUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Обновление наценок поставщика клиентом"""
    supplier = db.query(models.Supplier).filter(models.Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Поставщик не найден")
    
    # Обновляем наценки
    if data.markup_percent is not None:
        supplier.markup_percent = data.markup_percent
    if data.markup_fixed is not None:
        supplier.markup_fixed = data.markup_fixed
    
    db.commit()
    db.refresh(supplier)
    return supplier


def extract_supplier_name_from_filename(filename):
    """Извлекает название поставщика из имени файла"""
    # Убираем расширение файла
    name_without_ext = os.path.splitext(filename)[0]
    
    # Убираем временные файлы Excel
    if name_without_ext.startswith('~$'):
        return None
    
    # Убираем лишние пробелы
    name_clean = name_without_ext.strip()
    
    # Если название пустое или слишком короткое, возвращаем None
    if not name_clean or len(name_clean) < 2:
        return None
    
    return name_clean


@router.post("/scan-files", response_model=dict)
def scan_files_and_create_suppliers(_: models.User = Depends(require_admin), db: Session = Depends(get_db)):
    """Сканирует файлы в папке uploaded_files и создает поставщиков из названий файлов"""
    uploaded_files_path = Path("uploaded_files")
    
    if not uploaded_files_path.exists():
        raise HTTPException(status_code=404, detail="Папка uploaded_files не найдена")
    
    # Получаем существующих поставщиков
    existing_suppliers = {supplier.name for supplier in db.query(models.Supplier).all()}
    
    suppliers_to_add = set()
    scanned_files = []
    
    # Сканируем все папки
    for transport_type_dir in uploaded_files_path.iterdir():
        if not transport_type_dir.is_dir():
            continue
            
        for file_path in transport_type_dir.iterdir():
            if not file_path.is_file():
                continue
                
            supplier_name = extract_supplier_name_from_filename(file_path.name)
            scanned_files.append({
                "file": file_path.name,
                "folder": transport_type_dir.name,
                "extracted_name": supplier_name
            })
            
            if supplier_name and supplier_name not in existing_suppliers:
                suppliers_to_add.add(supplier_name)
    
    # Добавляем новых поставщиков в базу данных
    added_suppliers = []
    for supplier_name in sorted(suppliers_to_add):
        try:
            new_supplier = models.Supplier(name=supplier_name)
            db.add(new_supplier)
            added_suppliers.append(supplier_name)
        except Exception as e:
            continue
    
    if added_suppliers:
        db.commit()
    
    return {
        "message": f"Сканирование завершено. Добавлено {len(added_suppliers)} новых поставщиков",
        "added_suppliers": added_suppliers,
        "total_suppliers": db.query(models.Supplier).count(),
        "scanned_files": scanned_files
    }


