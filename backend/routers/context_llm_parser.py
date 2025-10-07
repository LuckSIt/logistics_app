"""
Роутер для контекстного LLM парсинга
Использует OCR для извлечения текста и LLM для понимания контекста
"""

import os
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..database import SessionLocal
from .. import models, schemas
from ..services.security import get_current_user, can_add_tariffs
from ..services.enhanced_ocr_service import enhanced_ocr_service
from ..services.context_llm_analyzer import context_llm_analyzer
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class ContextParseRequest(BaseModel):
    text: str
    transport_type: str = "auto"
    supplier_name: str = ""

class ContextParseResponse(BaseModel):
    success: bool
    data: Dict[str, Any]
    message: str
    parsing_method: str
    missing_fields: List[str] = []

def get_supplier_by_id(db: Session, supplier_id: int) -> Optional[models.Supplier]:
    """Получение поставщика по ID"""
    return db.query(models.Supplier).filter(models.Supplier.id == supplier_id).first()

@router.post("/upload", response_model=ContextParseResponse)
async def upload_with_context_llm(
    file: UploadFile = File(...),
    transport_type: str = Form("auto"),
    supplier_id: int = Form(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Загрузка и контекстный LLM парсинг файлов тарифов
    """
    try:
        # Проверяем права пользователя
        if not can_add_tariffs(current_user):
            raise HTTPException(status_code=403, detail="Недостаточно прав для добавления тарифов")
        
        # Получаем поставщика
        supplier = get_supplier_by_id(db, supplier_id)
        if not supplier:
            raise HTTPException(status_code=404, detail="Поставщик не найден")
        
        # Сохраняем файл
        upload_dir = "backend/uploaded_files"
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = os.path.join(upload_dir, file.filename)
        content = await file.read()
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        logger.info(f"Файл сохранен: {file_path}")
        
        # Извлекаем текст с помощью OCR
        logger.info(f"Начинаем извлечение текста из файла: {file_path}")
        extracted_text = enhanced_ocr_service.extract_text_from_file(file_path)
        
        if not extracted_text or not extracted_text.strip():
            return JSONResponse(
                status_code=200,
                content={
                    "success": False,
                    "data": {},
                    "message": "Не удалось извлечь текст из файла. Проверьте качество изображения.",
                    "parsing_method": "ocr_failed",
                    "missing_fields": []
                }
            )
        
        logger.info(f"Текст извлечен успешно: {len(extracted_text)} символов")
        
        # Анализируем контекст и структурируем данные с помощью LLM
        logger.info(f"Начинаем LLM анализ контекста для типа транспорта: {transport_type}")
        structured_data = context_llm_analyzer.analyze_context_and_structure(
            extracted_text, 
            transport_type, 
            supplier.name
        )
        
        if not structured_data.get('success', True):  # Если success не False, считаем успешным
            return JSONResponse(
                status_code=200,
                content={
                    "success": False,
                    "data": structured_data,
                    "message": "LLM не смог проанализировать контекст файла. Попробуйте другой файл.",
                    "parsing_method": "llm_context_analysis_failed",
                    "missing_fields": structured_data.get('missing_required_fields', [])
                }
            )
        
        # Подготавливаем данные для формы
        form_data = {
            "supplier_id": supplier_id,
            "transport_type": transport_type,
            "source_file": file_path,
            "parsed_at": datetime.now().isoformat(),
            **structured_data
        }
        
        # Удаляем служебные поля
        form_data.pop('parsing_method', None)
        form_data.pop('missing_required_fields', None)
        
        logger.info(f"LLM контекстный анализ завершен. Извлечено полей: {len(form_data)}")
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": form_data,
                "message": f"Файл успешно проанализирован. Извлечено {len(form_data)} полей.",
                "parsing_method": "llm_context_analysis",
                "missing_fields": structured_data.get('missing_required_fields', [])
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка контекстного LLM парсинга файла {file.filename}: {e}")
        return JSONResponse(
            status_code=200,
            content={
                "success": False,
                "data": {},
                "message": f"Ошибка обработки файла: {str(e)}",
                "parsing_method": "error",
                "missing_fields": []
            }
        )

@router.post("/parse-text", response_model=ContextParseResponse)
async def parse_text_with_context_llm(
    request: ContextParseRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Контекстный LLM парсинг текста без загрузки файла
    """
    try:
        # Проверяем права пользователя
        if not can_add_tariffs(current_user):
            raise HTTPException(status_code=403, detail="Недостаточно прав для добавления тарифов")
        
        if not request.text.strip():
            return JSONResponse(
                status_code=200,
                content={
                    "success": False,
                    "data": {},
                    "message": "Текст для анализа не предоставлен.",
                    "parsing_method": "no_text",
                    "missing_fields": []
                }
            )
        
        logger.info(f"Начинаем LLM анализ контекста текста для типа транспорта: {request.transport_type}")
        
        # Анализируем контекст и структурируем данные с помощью LLM
        structured_data = context_llm_analyzer.analyze_context_and_structure(
            request.text, 
            request.transport_type, 
            request.supplier_name
        )
        
        if not structured_data.get('success', True):
            return JSONResponse(
                status_code=200,
                content={
                    "success": False,
                    "data": structured_data,
                    "message": "LLM не смог проанализировать контекст текста.",
                    "parsing_method": "llm_context_analysis_failed",
                    "missing_fields": structured_data.get('missing_required_fields', [])
                }
            )
        
        # Подготавливаем данные для формы
        form_data = {
            "transport_type": request.transport_type,
            "parsed_at": datetime.now().isoformat(),
            **structured_data
        }
        
        # Удаляем служебные поля
        form_data.pop('parsing_method', None)
        form_data.pop('missing_required_fields', None)
        
        logger.info(f"LLM контекстный анализ текста завершен. Извлечено полей: {len(form_data)}")
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": form_data,
                "message": f"Текст успешно проанализирован. Извлечено {len(form_data)} полей.",
                "parsing_method": "llm_context_analysis",
                "missing_fields": structured_data.get('missing_required_fields', [])
            }
        )
        
    except Exception as e:
        logger.error(f"Ошибка контекстного LLM парсинга текста: {e}")
        return JSONResponse(
            status_code=200,
            content={
                "success": False,
                "data": {},
                "message": f"Ошибка анализа текста: {str(e)}",
                "parsing_method": "error",
                "missing_fields": []
            }
        )

@router.get("/status")
async def get_context_llm_status():
    """
    Получение статуса LLM сервиса
    """
    try:
        status = {
            "llm_available": context_llm_analyzer.llm_available,
            "service_name": "Context LLM Analyzer",
            "description": "Использует OCR для извлечения текста и LLM для понимания контекста",
            "supported_transport_types": ["auto", "air", "sea", "rail"],
            "features": [
                "Контекстный анализ текста",
                "Структурирование данных согласно шаблонам форм",
                "Валидация обязательных полей",
                "Fallback на intelligent_parser при недоступности LLM"
            ]
        }
        
        return JSONResponse(status_code=200, content=status)
        
    except Exception as e:
        logger.error(f"Ошибка получения статуса: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )
