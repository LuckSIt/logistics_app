import os
import logging
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from database import SessionLocal
import models, schemas
from services.security import get_current_user
from services.llm_parser import LLMTariffParser
from ..services import cbr

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


@router.post("/upload")
async def upload_with_llm_parser(
    supplier_id: int = Form(...),
    file: UploadFile = File(...),
    transport_type: str = Form("auto"),
    model: str = Form("mistral"),  # Модель Ollama
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Загрузка и парсинг файлов тарифов с помощью LLM (Ollama)
    """
    supplier = db.query(models.Supplier).filter(models.Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Поставщик не найден")

    # Проверяем расширение файла
    file_ext = os.path.splitext(file.filename)[1].lower()
    allowed_extensions = ['.pdf', '.docx', '.xlsx', '.xls', '.png', '.jpg', '.jpeg']
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Неподдерживаемый формат файла. Разрешены: {', '.join(allowed_extensions)}"
        )

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    safe_name = file.filename.replace("..", "_")
    save_path = os.path.join(UPLOAD_DIR, safe_name)
    
    try:
        # Сохраняем файл
        with open(save_path, "wb") as f:
            f.write(await file.read())

        logger.info(f"Начинаем LLM парсинг файла: {file.filename} с моделью: {model}")
        
        # Создаем LLM парсер
        llm_parser = LLMTariffParser(model=model)
        
        # Парсим файл
        rows = llm_parser.parse_tariff_data(save_path, supplier_id)
        
        logger.info(f"LLM парсинг завершен. Извлечено {len(rows)} записей")
        
        if not rows:
            logger.warning(f"LLM не смог извлечь данные из файла {file.filename}")
            # Возвращаем пустой результат вместо ошибки
            return JSONResponse(
                status_code=200,
                content={
                    "message": "LLM не смог распознать данные из файла. Попробуйте другой файл или используйте обычный парсер.",
                    "success": False,
                    "data": [],
                    "supplier_name": supplier.name,
                    "file_name": file.filename
                }
            )
        
        # Конвертируем валюту если нужно
        for row in rows:
            if row.get("price_rub") is None and row.get("price_usd") is not None:
                try:
                    rate = cbr.get_usd_rate()
                    row["price_rub"] = float(row["price_usd"]) * rate
                except Exception as e:
                    logger.warning(f"Ошибка конвертации валюты: {e}")
                    row["price_rub"] = None

        # Проверяем на дубликаты и архивируем старые тарифы
        archived_count = 0
        for row in rows:
            if row.get("origin_city") and row.get("destination_city"):
                # Ищем существующие тарифы с таким же маршрутом
                existing_tariffs = db.query(models.Tariff).filter(
                    models.Tariff.supplier_id == supplier_id,
                    models.Tariff.transport_type == row.get("transport_type"),
                    models.Tariff.origin_city == row.get("origin_city"),
                    models.Tariff.destination_city == row.get("destination_city"),
                    models.Tariff.vehicle_type == row.get("vehicle_type")
                ).all()
                
                # Архивируем старые тарифы
                from services.tariff_archive import TariffArchiveService
                archive_service = TariffArchiveService(db)
                
                for old_tariff in existing_tariffs:
                    archive_service.archive_tariff(old_tariff, "Замена новым тарифом из LLM парсера")
                    archived_count += 1
                    logger.info(f"Архивирован старый тариф ID {old_tariff.id}")

        if archived_count > 0:
            db.commit()
            logger.info(f"Архивировано {archived_count} старых тарифов")

        # Приводим данные к единому формату и сохраняем в базу
        saved_count = 0
        formatted_rows = []
        for row in rows:
            try:
                # Обрабатываем дату валидности
                validity_date = row.get("validity_date")
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
                
                # Создаем объект тарифа
                tariff_data = {
                    "supplier_id": supplier_id,
                    "transport_type": row.get("transport_type", transport_type),
                    "basis": row.get("basis", "EXW"),
                    "origin_country": row.get("origin_country"),
                    "origin_city": row.get("origin_city"),
                    "destination_country": row.get("destination_country"),
                    "destination_city": row.get("destination_city"),
                    "vehicle_type": row.get("vehicle_type"),
                    "price_rub": row.get("price_rub"),
                    "price_usd": row.get("price_usd"),
                    "validity_date": validity_date,
                    "transit_time_days": row.get("transit_time_days"),
                    "source_file": file.filename
                }
                
                # Убираем None значения
                tariff_data = {k: v for k, v in tariff_data.items() if v is not None}
                
                # Создаем тариф в базе данных
                tariff = models.Tariff(**tariff_data)
                tariff.created_by_user_id = current_user.id  # Сохраняем создателя тарифа
                db.add(tariff)
                saved_count += 1
                
                # Добавляем в форматированный список для ответа
                formatted_rows.append(tariff_data)
                
            except Exception as e:
                logger.warning(f"Ошибка сохранения строки: {e}, данные: {row}")
                continue
        
        # Сохраняем все изменения в базу
        try:
            db.commit()
            logger.info(f"Сохранено {saved_count} тарифов в базу данных")
        except Exception as e:
            db.rollback()
            logger.error(f"Ошибка сохранения в базу: {e}")
            raise HTTPException(
                status_code=500,
                detail="Ошибка сохранения данных в базу"
            )
        
        return {
            "message": "Файл успешно обработан с помощью LLM",
            "model_used": model,
            "parsed_rows": len(formatted_rows),
            "archived_count": archived_count,
            "saved_count": saved_count,
            "data": formatted_rows
        }
        
    except Exception as e:
        logger.error(f"Ошибка LLM обработки файла {file.filename}: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Ошибка LLM обработки файла: {str(e)}"
        )
    finally:
        # Удаляем временный файл
        if os.path.exists(save_path):
            try:
                os.remove(save_path)
            except:
                pass


@router.post("/parse-text")
async def parse_text_with_llm(
    supplier_id: int = Form(...),
    text: str = Form(...),
    transport_type: str = Form("auto"),
    model: str = Form("mistral"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Парсинг текста с помощью LLM без загрузки файла
    """
    supplier = db.query(models.Supplier).filter(models.Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Поставщик не найден")

    if not text.strip():
        raise HTTPException(status_code=400, detail="Текст не может быть пустым")

    try:
        logger.info(f"Начинаем LLM парсинг текста с моделью: {model}")
        
        # Создаем LLM парсер
        llm_parser = LLMTariffParser(model=model)
        
        # Парсим текст
        rows = llm_parser.llm_parser.extract_tariff_data(text, transport_type)
        
        # Добавляем supplier_id к каждой записи
        for row in rows:
            row["supplier_id"] = supplier_id
        
        logger.info(f"LLM парсинг текста завершен. Извлечено {len(rows)} записей")
        
        if not rows:
            return JSONResponse(
                status_code=200,
                content={
                    "message": "LLM не смог извлечь данные из текста. Попробуйте другой текст или используйте обычный парсер.",
                    "success": False,
                    "data": []
                }
            )
        
        # Конвертируем валюту если нужно
        for row in rows:
            if row.get("price_rub") is None and row.get("price_usd") is not None:
                try:
                    rate = cbr.get_usd_rate()
                    row["price_rub"] = float(row["price_usd"]) * rate
                except Exception as e:
                    logger.warning(f"Ошибка конвертации валюты: {e}")
                    row["price_rub"] = None

        return {
            "message": "Текст успешно обработан с помощью LLM",
            "model_used": model,
            "parsed_rows": len(rows),
            "data": rows
        }
        
    except Exception as e:
        logger.error(f"Ошибка LLM обработки текста: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Ошибка LLM обработки текста: {str(e)}"
        )


@router.get("/models")
async def get_available_models():
    """
    Получение списка доступных моделей Ollama
    """
    try:
        # LLM функционал отключен для стабильной версии
        return {
            "available_models": [],
            "default_model": "mistral",
            "message": "LLM функционал отключен для стабильной версии"
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения списка моделей: {e}")
        return {
            "available_models": [],
            "default_model": "mistral",
            "error": "LLM функционал отключен для стабильной версии"
        }
