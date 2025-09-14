"""
API роутер для автоматического создания тарифов из файлов.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from backend.database import SessionLocal
from backend import models, schemas
from backend.services.security import get_current_user
from backend.services.text_extractor import extract_text_from_file, get_supported_formats, is_format_supported
from backend.services.adaptive_analyzer import analyze_tariff_text_adaptive
from backend.services.enhanced_aviation_analyzer import analyze_aviation_file_enhanced
from backend.services.context_analyzer import analyze_with_context

logger = logging.getLogger(__name__)

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
UPLOAD_DIR = os.path.abspath(os.path.join(BASE_DIR, "uploaded_files"))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/supported-formats")
async def get_supported_file_formats():
    """
    Получить список поддерживаемых форматов файлов для автоматического создания тарифов.
    """
    formats = get_supported_formats()
    return {
        "supported_formats": formats,
        "description": "Форматы файлов, из которых можно автоматически создать тарифы"
    }


@router.post("/extract-tariff-data")
async def extract_tariff_data_from_file(
    file: UploadFile = File(...),
    supplier_id: int = Form(...),
    transport_type: str = Form("auto"),  # Добавляем параметр типа транспорта
    use_llm: bool = Form(False),
    llm_api_key: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    """
    Извлечь данные тарифа из загруженного файла и заполнить форму.
    
    Поддерживаемые форматы: DOCX, XLSX, XLS, CSV, PDF, PNG, JPG, JPEG
    
    Args:
        file: Загружаемый файл
        supplier_id: ID поставщика
    """
    # Проверяем существование поставщика
    supplier = db.query(models.Supplier).filter(models.Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Поставщик не найден")
    
    # Проверяем формат файла
    if not is_format_supported(file.filename):
        supported = get_supported_formats()
        raise HTTPException(
            status_code=400,
            detail=f"Неподдерживаемый формат файла. Поддерживаемые форматы: {', '.join(supported)}"
        )
    
    # Создаем директорию для загрузок если её нет
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    # Сохраняем файл временно
    safe_name = file.filename.replace("..", "_")
    save_path = os.path.join(UPLOAD_DIR, safe_name)
    
    try:
        # Сохраняем файл
        with open(save_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        logger.info(f"Файл сохранен: {save_path}")
        
        # Извлекаем текст
        result = extract_text_from_file(save_path)
        
        if not result["success"]:
            raise HTTPException(
                status_code=400,
                detail=f"Ошибка извлечения текста: {result.get('error', 'Неизвестная ошибка')}"
            )
        
        # Используем специализированные парсеры в зависимости от типа транспорта
        logger.info(f"Анализируем файл для типа транспорта: {transport_type}")
        
        try:
            if transport_type == "auto":
                # Автоматическое определение типа транспорта
                from backend.services.parser_factory import ParserFactory
                extracted_data = ParserFactory.parse_with_auto_detection(save_path, supplier_id)
            else:
                # Используем специализированный парсер
                from backend.services.parser_factory import ParserFactory
                try:
                    parser = ParserFactory.get_parser(transport_type)
                    extracted_data = parser.parse_tariff_data(save_path, supplier_id)
                    
                    # Преобразуем результат в формат, ожидаемый фронтендом
                    if isinstance(extracted_data, list):
                        # Если парсер вернул список строк, преобразуем в формат с routes
                        routes = []
                        for row in extracted_data:
                            route = {
                                "origin_city": row.get("origin_city"),
                                "destination_city": row.get("destination_city"),
                                "transport_type": row.get("transport_type", transport_type),
                                "basis": row.get("basis", "EXW"),
                                "vehicle_type": row.get("vehicle_type"),
                                "price_rub": row.get("price_rub"),
                                "price_usd": row.get("price_usd"),
                                "transit_time_days": row.get("transit_time_days"),
                                "origin_country": row.get("origin_country"),
                                "destination_country": row.get("destination_country")
                            }
                            routes.append(route)
                        extracted_data = {"routes": routes}
                    else:
                        # Если парсер вернул словарь, убеждаемся что есть routes
                        if "routes" not in extracted_data:
                            extracted_data = {"routes": []}
                            
                except ValueError as e:
                    logger.warning(f"Парсер для типа {transport_type} не найден, используем автоопределение: {e}")
                    # Fallback к автоопределению
                    from backend.services.parser_factory import ParserFactory
                    extracted_data = ParserFactory.parse_with_auto_detection(save_path, supplier_id)
            
            logger.info(f"Анализ успешен, найдено маршрутов: {len(extracted_data.get('routes', []))}")
            
        except Exception as e:
            logger.error(f"Ошибка анализа: {e}, используем fallback")
            # Fallback к старому методу
            extracted_data = analyze_tariff_text_adaptive(result["text"])
        
        # Формируем ответ с данными для формы
        response = {
            "success": True,
            "filename": file.filename,
            "file_size": len(content),
            "extracted_text": result["text"][:1000] + "..." if len(result["text"]) > 1000 else result["text"],
            "tariff_data": extracted_data,
            "supplier": {
                "id": supplier.id,
                "name": supplier.name
            },
            "llm_used": use_llm
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Ошибка обработки файла {file.filename}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка обработки файла: {str(e)}"
        )
    finally:
        # Удаляем временный файл
        if os.path.exists(save_path):
            try:
                os.remove(save_path)
            except:
                pass


@router.post("/save-tariff")
async def save_extracted_tariff(
    tariff_data: schemas.TariffIn,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    """
    Сохранить извлеченный тариф в базу данных.
    
    Args:
        tariff_data: Данные тарифа для сохранения
    """
    try:
        # Проверяем существование поставщика
        supplier = db.query(models.Supplier).filter(models.Supplier.id == tariff_data.supplier_id).first()
        if not supplier:
            raise HTTPException(status_code=404, detail="Поставщик не найден")
        
        # Обрабатываем данные тарифа
        tariff_dict = tariff_data.dict()
        
        # Обрабатываем дату валидности
        validity_date = tariff_dict.get("validity_date")
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
        
        tariff_dict["validity_date"] = validity_date
        
        # Ищем существующие тарифы с теми же параметрами для архивирования
        existing_tariffs = db.query(models.Tariff).filter(
            models.Tariff.supplier_id == tariff_data.supplier_id,
            models.Tariff.transport_type == tariff_data.transport_type,
            models.Tariff.basis == tariff_data.basis,
            models.Tariff.origin_country == tariff_data.origin_country,
            models.Tariff.origin_city == tariff_data.origin_city,
            models.Tariff.destination_country == tariff_data.destination_country,
            models.Tariff.destination_city == tariff_data.destination_city,
            models.Tariff.vehicle_type == tariff_data.vehicle_type
        ).all()
        
        archived_count = 0
        if existing_tariffs:
            # Архивируем старые тарифы
            from backend.services.tariff_archive import TariffArchiveService
            archive_service = TariffArchiveService(db)
            
            for old_tariff in existing_tariffs:
                archive_service.archive_tariff(old_tariff, "Замена новым тарифом из auto-tariff")
                archived_count += 1
                logger.info(f"Архивирован старый тариф ID {old_tariff.id}")
            
            # Удаляем старые тарифы
            for old_tariff in existing_tariffs:
                db.delete(old_tariff)
            
            db.commit()
            logger.info(f"Архивировано {archived_count} старых тарифов")
        
        # Создаем новый тариф
        db_tariff = models.Tariff(**tariff_dict)
        db.add(db_tariff)
        db.commit()
        db.refresh(db_tariff)
        
        logger.info(f"Тариф сохранен: ID {db_tariff.id}")
        
        return {
            "success": True,
            "message": "Тариф успешно сохранен",
            "tariff_id": db_tariff.id,
            "archived_count": archived_count
        }
        
    except Exception as e:
        logger.error(f"Ошибка сохранения тарифа: {e}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка сохранения тарифа: {str(e)}"
        )



