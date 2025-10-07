"""
API endpoints для улучшенного OCR сервиса и интеллектуального парсинга
"""

import os
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Form, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import SessionLocal
import models, schemas
from services.security import get_current_user, can_add_tariffs
from services.enhanced_ocr_service import enhanced_ocr_service
from services.intelligent_parser import intelligent_parser
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic модели для API
class OCRResult(BaseModel):
    success: bool
    text: Optional[str] = None
    structured_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class ParseResult(BaseModel):
    success: bool
    parsed_data: Optional[Dict[str, Any]] = None
    tariff_id: Optional[int] = None
    error: Optional[str] = None

class BatchProcessResult(BaseModel):
    success: bool
    processed_files: int
    successful_files: int
    failed_files: int
    results: List[Dict[str, Any]]

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/extract-text", response_model=OCRResult)
async def extract_text_from_file(
    file: UploadFile = File(...),
    use_easyocr: bool = Form(False),
    enhance_image: bool = Form(True),
    current_user: models.User = Depends(get_current_user)
):
    """
    Извлечение текста из загруженного файла с помощью улучшенного OCR
    """
    try:
        # Сохраняем временный файл
        temp_file_path = f"temp_{file.filename}"
        with open(temp_file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        try:
            # Извлекаем текст
            text = enhanced_ocr_service.extract_text_from_file(temp_file_path)
            
            if text:
                return OCRResult(
                    success=True,
                    text=text,
                    structured_data=None
                )
            else:
                return OCRResult(
                    success=False,
                    error="Не удалось извлечь текст из файла"
                )
                
        finally:
            # Удаляем временный файл
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                
    except Exception as e:
        logger.error(f"Ошибка извлечения текста: {e}")
        return OCRResult(
            success=False,
            error=str(e)
        )

@router.post("/parse-structured", response_model=ParseResult)
async def parse_structured_data(
    file: UploadFile = File(...),
    transport_type: str = Form("auto"),
    supplier_id: int = Form(...),
    save_to_db: bool = Form(False),
    current_user: models.User = Depends(can_add_tariffs)
):
    """
    Парсинг структурированных данных из файла с сохранением в БД
    """
    try:
        # Сохраняем временный файл
        temp_file_path = f"temp_{file.filename}"
        with open(temp_file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        try:
            # Парсим данные
            parsed_data = intelligent_parser.parse_file(
                file_path=temp_file_path,
                transport_type=transport_type,
                supplier_id=supplier_id
            )
            
            if not parsed_data.get('success', False):
                return ParseResult(
                    success=False,
                    error=parsed_data.get('error', 'Ошибка парсинга')
                )
            
            tariff_id = None
            if save_to_db:
                tariff_id = intelligent_parser.save_to_database(
                    parsed_data=parsed_data,
                    user_id=current_user.id
                )
            
            return ParseResult(
                success=True,
                parsed_data=parsed_data,
                tariff_id=tariff_id
            )
                
        finally:
            # Удаляем временный файл
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                
    except Exception as e:
        logger.error(f"Ошибка парсинга структурированных данных: {e}")
        return ParseResult(
            success=False,
            error=str(e)
        )

@router.post("/batch-process", response_model=BatchProcessResult)
async def batch_process_files(
    files: List[UploadFile] = File(...),
    transport_type: str = Form("auto"),
    supplier_id: int = Form(...),
    save_to_db: bool = Form(False),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: models.User = Depends(can_add_tariffs)
):
    """
    Пакетная обработка нескольких файлов
    """
    try:
        results = []
        successful_files = 0
        failed_files = 0
        
        for file in files:
            try:
                # Сохраняем временный файл
                temp_file_path = f"temp_{file.filename}"
                with open(temp_file_path, "wb") as buffer:
                    content = await file.read()
                    buffer.write(content)
                
                try:
                    # Парсим данные
                    parsed_data = intelligent_parser.parse_file(
                        file_path=temp_file_path,
                        transport_type=transport_type,
                        supplier_id=supplier_id
                    )
                    
                    if parsed_data.get('success', False):
                        successful_files += 1
                        
                        tariff_id = None
                        if save_to_db:
                            tariff_id = intelligent_parser.save_to_database(
                                parsed_data=parsed_data,
                                user_id=current_user.id
                            )
                        
                        results.append({
                            'filename': file.filename,
                            'success': True,
                            'parsed_data': parsed_data,
                            'tariff_id': tariff_id
                        })
                    else:
                        failed_files += 1
                        results.append({
                            'filename': file.filename,
                            'success': False,
                            'error': parsed_data.get('error', 'Ошибка парсинга')
                        })
                        
                finally:
                    # Удаляем временный файл
                    if os.path.exists(temp_file_path):
                        os.remove(temp_file_path)
                        
            except Exception as e:
                failed_files += 1
                results.append({
                    'filename': file.filename,
                    'success': False,
                    'error': str(e)
                })
        
        return BatchProcessResult(
            success=True,
            processed_files=len(files),
            successful_files=successful_files,
            failed_files=failed_files,
            results=results
        )
        
    except Exception as e:
        logger.error(f"Ошибка пакетной обработки: {e}")
        return BatchProcessResult(
            success=False,
            processed_files=0,
            successful_files=0,
            failed_files=0,
            results=[]
        )

@router.post("/parse-text", response_model=ParseResult)
async def parse_text_data(
    text: str = Form(...),
    transport_type: str = Form("auto"),
    supplier_id: int = Form(...),
    save_to_db: bool = Form(False),
    current_user: models.User = Depends(can_add_tariffs)
):
    """
    Парсинг структурированных данных из текста
    """
    try:
        # Парсим данные из текста
        parsed_data = intelligent_parser._parse_with_patterns(text, transport_type)
        validated_data = intelligent_parser._validate_parsed_data(parsed_data)
        
        # Добавляем метаданные
        validated_data.update({
            'supplier_id': supplier_id,
            'parsed_at': intelligent_parser._parse_date(datetime.now().isoformat()),
            'transport_type': transport_type,
            'success': True
        })
        
        tariff_id = None
        if save_to_db:
            tariff_id = intelligent_parser.save_to_database(
                parsed_data=validated_data,
                user_id=current_user.id
            )
        
        return ParseResult(
            success=True,
            parsed_data=validated_data,
            tariff_id=tariff_id
        )
        
    except Exception as e:
        logger.error(f"Ошибка парсинга текста: {e}")
        return ParseResult(
            success=False,
            error=str(e)
        )

@router.get("/supported-formats")
async def get_supported_formats():
    """
    Получение списка поддерживаемых форматов файлов
    """
    return {
        "supported_formats": [
            ".pdf", ".docx", ".doc", ".xlsx", ".xls", 
            ".png", ".jpg", ".jpeg", ".bmp", ".tiff"
        ],
        "transport_types": [
            "auto", "sea", "air", "rail", "multimodal"
        ],
        "ocr_engines": {
            "tesseract": True,
            "easyocr": enhanced_ocr_service.easyocr_reader is not None
        }
    }

@router.get("/parse-status/{task_id}")
async def get_parse_status(task_id: str):
    """
    Получение статуса задачи парсинга (для асинхронной обработки)
    """
    # Здесь можно реализовать систему очередей для отслеживания статуса
    return {
        "task_id": task_id,
        "status": "completed",  # pending, processing, completed, failed
        "progress": 100,
        "result": None
    }

@router.post("/validate-data")
async def validate_parsed_data(
    data: Dict[str, Any],
    transport_type: str = Form("auto")
):
    """
    Валидация распарсенных данных
    """
    try:
        validated_data = intelligent_parser._validate_parsed_data(data)
        
        return {
            "success": True,
            "validated_data": validated_data,
            "validation_errors": []
        }
        
    except Exception as e:
        logger.error(f"Ошибка валидации данных: {e}")
        return {
            "success": False,
            "validated_data": None,
            "validation_errors": [str(e)]
        }
