import os
from datetime import date
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Form
from sqlalchemy.orm import Session
from typing import List
from backend.database import SessionLocal
from backend import models, schemas
from backend.services import parsers, cbr
from backend.services.security import get_current_user, can_add_tariffs
import logging
from typing import List

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
async def upload_tariffs(
    supplier_id: int = Form(...),
    file: UploadFile = File(...),
    transport_type: str = Form("auto"),  # Добавляем параметр типа транспорта
    use_llm: bool = Form(False),  # Флаг для использования LLM парсера
    llm_model: str = Form("mistral"),  # Модель LLM
    db: Session = Depends(get_db),
    _: models.User = Depends(can_add_tariffs),
):
    """
    Загрузка и парсинг файлов тарифов
    Автоматически архивирует старые тарифы при совпадении маршрута
    """
    supplier = db.query(models.Supplier).filter(models.Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Поставщик не найден")

    # Проверяем расширение файла
    file_ext = os.path.splitext(file.filename)[1].lower()
    allowed_extensions = ['.xls', '.xlsx', '.csv', '.pdf', '.docx', '.png', '.jpg', '.jpeg']
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Неподдерживаемый формат файла. Разрешены: {', '.join(allowed_extensions)}"
        )

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    safe_name = file.filename.replace("..", "_")
    save_path = os.path.join(UPLOAD_DIR, safe_name)
    
    try:
        with open(save_path, "wb") as f:
            f.write(await file.read())

        # Парсим файл с учетом типа транспорта
        logger.info(f"Начинаем парсинг файла: {file.filename} для типа транспорта: {transport_type}, LLM: {use_llm}")
        
        if use_llm:
            # Используем LLM парсер
            from backend.services.llm_parser import LLMTariffParser
            try:
                llm_parser = LLMTariffParser(model=llm_model)
                rows = llm_parser.parse_tariff_data(save_path, supplier_id)
                logger.info(f"LLM парсинг завершен с моделью {llm_model}")
            except Exception as e:
                logger.error(f"Ошибка LLM парсинга: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Ошибка LLM парсинга: {str(e)}"
                )
        elif transport_type == "auto":
            # Автоматическое определение типа транспорта
            rows = parsers.parse_tariff_file(save_path, supplier_id)
        else:
            # Используем специализированный парсер
            from backend.services.parser_factory import ParserFactory
            try:
                parser = ParserFactory.get_parser(transport_type)
                rows = parser.parse_tariff_data(save_path, supplier_id)
                
                # Устанавливаем тип транспорта для всех строк, если он не был определен парсером
                for row in rows:
                    if not row.get("transport_type"):
                        row["transport_type"] = transport_type
                        
            except ValueError as e:
                logger.warning(f"Парсер для типа {transport_type} не найден, используем автоопределение: {e}")
                rows = parsers.parse_tariff_file(save_path, supplier_id)
        
        logger.info(f"Результат парсинга: {len(rows)} записей")
        
        if not rows:
            logger.warning(f"Не удалось извлечь данные из файла {file.filename}")
            raise HTTPException(
                status_code=400, 
                detail="Не удалось распознать данные из файла. Проверьте формат файла и убедитесь, что файл содержит табличные данные."
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
                from backend.services.tariff_archive import TariffArchiveService
                archive_service = TariffArchiveService(db)
                
                for old_tariff in existing_tariffs:
                    archive_service.archive_tariff(old_tariff, "Замена новым тарифом из файла")
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
                    "transport_type": row.get("transport_type", "auto"),
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
            "parsed_rows": len(formatted_rows),
            "archived_count": archived_count,
            "saved_count": saved_count,
            "data": formatted_rows
        }
        
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


