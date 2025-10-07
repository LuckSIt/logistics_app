"""
API роутер для извлечения текста из файлов различных форматов.
"""

import os
import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from ..database import SessionLocal
from .. import models
from ..services.security import get_current_user
from ..services.text_extractor import extract_text_from_file, get_supported_formats, is_format_supported

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
    Получить список поддерживаемых форматов файлов для извлечения текста.
    """
    formats = get_supported_formats()
    return {
        "supported_formats": formats,
        "description": "Форматы файлов, из которых можно извлечь текст"
    }


@router.post("/extract-text")
async def extract_text_from_uploaded_file(
    file: UploadFile = File(...),
    include_metadata: bool = Form(False),
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    """
    Извлечь текст из загруженного файла.
    
    Поддерживаемые форматы: DOCX, XLSX, XLS, CSV, PDF, PNG, JPG, JPEG
    
    Args:
        file: Загружаемый файл
        include_metadata: Включить метаданные в ответ (количество страниц, таблиц и т.д.)
    """
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
        
        # Формируем ответ
        response = {
            "success": result["success"],
            "filename": file.filename,
            "file_size": len(content),
            "text_length": len(result.get("text", "")),
        }
        
        if include_metadata:
            response.update({
                "format": result.get("format"),
                "pages": result.get("pages", 0),
                "tables": result.get("tables", 0),
                "images": result.get("images", 0),
            })
        
        if result["success"]:
            response["text"] = result["text"]
            response["preview"] = result["text"][:500] + "..." if len(result["text"]) > 500 else result["text"]
        else:
            response["error"] = result.get("error", "Неизвестная ошибка")
        
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


@router.post("/extract-text-batch")
async def extract_text_from_multiple_files(
    files: List[UploadFile] = File(...),
    include_metadata: bool = Form(False),
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    """
    Извлечь текст из нескольких загруженных файлов.
    
    Args:
        files: Список загружаемых файлов
        include_metadata: Включить метаданные в ответ
    """
    if not files:
        raise HTTPException(status_code=400, detail="Не указаны файлы для обработки")
    
    if len(files) > 10:  # Ограничиваем количество файлов
        raise HTTPException(status_code=400, detail="Максимальное количество файлов: 10")
    
    results = []
    
    for file in files:
        try:
            # Проверяем формат файла
            if not is_format_supported(file.filename):
                results.append({
                    "filename": file.filename,
                    "success": False,
                    "error": "Неподдерживаемый формат файла"
                })
                continue
            
            # Сохраняем файл временно
            safe_name = file.filename.replace("..", "_")
            save_path = os.path.join(UPLOAD_DIR, safe_name)
            
            try:
                # Сохраняем файл
                with open(save_path, "wb") as f:
                    content = await file.read()
                    f.write(content)
                
                # Извлекаем текст
                result = extract_text_from_file(save_path)
                
                # Формируем результат
                file_result = {
                    "filename": file.filename,
                    "success": result["success"],
                    "file_size": len(content),
                    "text_length": len(result.get("text", "")),
                }
                
                if include_metadata:
                    file_result.update({
                        "format": result.get("format"),
                        "pages": result.get("pages", 0),
                        "tables": result.get("tables", 0),
                        "images": result.get("images", 0),
                    })
                
                if result["success"]:
                    file_result["text"] = result["text"]
                    file_result["preview"] = result["text"][:500] + "..." if len(result["text"]) > 500 else result["text"]
                else:
                    file_result["error"] = result.get("error", "Неизвестная ошибка")
                
                results.append(file_result)
                
            finally:
                # Удаляем временный файл
                if os.path.exists(save_path):
                    try:
                        os.remove(save_path)
                    except:
                        pass
                        
        except Exception as e:
            logger.error(f"Ошибка обработки файла {file.filename}: {e}")
            results.append({
                "filename": file.filename,
                "success": False,
                "error": str(e)
            })
    
    return {
        "total_files": len(files),
        "processed_files": len([r for r in results if r["success"]]),
        "failed_files": len([r for r in results if not r["success"]]),
        "results": results
    }


@router.post("/analyze-text")
async def analyze_extracted_text(
    text: str = Form(...),
    analysis_type: str = Form("general"),  # general, logistics, pricing
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    """
    Анализировать извлеченный текст и найти структурированную информацию.
    
    Args:
        text: Текст для анализа
        analysis_type: Тип анализа (general, logistics, pricing)
    """
    if not text.strip():
        raise HTTPException(status_code=400, detail="Текст не может быть пустым")
    
    try:
        # Простой анализ текста
        analysis_result = {
            "text_length": len(text),
            "word_count": len(text.split()),
            "line_count": len(text.splitlines()),
            "characters_without_spaces": len(text.replace(" ", "")),
        }
        
        # Анализ в зависимости от типа
        if analysis_type == "logistics":
            analysis_result.update(_analyze_logistics_text(text))
        elif analysis_type == "pricing":
            analysis_result.update(_analyze_pricing_text(text))
        else:  # general
            analysis_result.update(_analyze_general_text(text))
        
        return analysis_result
        
    except Exception as e:
        logger.error(f"Ошибка анализа текста: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка анализа текста: {str(e)}"
        )


def _analyze_general_text(text: str) -> Dict[str, Any]:
    """Общий анализ текста."""
    import re
    
    # Поиск email адресов
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    
    # Поиск телефонных номеров
    phone_pattern = r'[\+]?[1-9][\d]{0,15}'
    phones = re.findall(phone_pattern, text)
    
    # Поиск дат
    date_pattern = r'\d{1,2}[./-]\d{1,2}[./-]\d{2,4}'
    dates = re.findall(date_pattern, text)
    
    return {
        "emails_found": emails,
        "phones_found": phones,
        "dates_found": dates,
        "has_numbers": bool(re.search(r'\d', text)),
        "has_currency": bool(re.search(r'[₽$€¥]|\b(руб|доллар|евро|юань)\b', text, re.IGNORECASE)),
    }


def _analyze_logistics_text(text: str) -> Dict[str, Any]:
    """Анализ логистического текста."""
    import re
    
    # Поиск городов
    city_pattern = r'\b(Москва|Санкт-Петербург|Новосибирск|Екатеринбург|Казань|Нижний Новгород|Челябинск|Самара|Уфа|Ростов-на-Дону|Омск|Красноярск|Воронеж|Пермь|Волгоград)\b'
    cities = re.findall(city_pattern, text, re.IGNORECASE)
    
    # Поиск типов транспорта
    transport_pattern = r'\b(авто|автомобильный|жд|железнодорожный|море|морской|авиа|воздушный|мульти|мультимодальный)\b'
    transport_types = re.findall(transport_pattern, text, re.IGNORECASE)
    
    # Поиск базисов поставки
    basis_pattern = r'\b(EXW|FCA|FOB|CFR|CIF|CIP|CPT|DAP|DDP)\b'
    bases = re.findall(basis_pattern, text)
    
    return {
        "cities_found": list(set(cities)),
        "transport_types": list(set(transport_types)),
        "incoterms_bases": list(set(bases)),
        "has_route_info": bool(re.search(r'[-→>]\s*[А-Яа-я]', text)),
        "has_container_info": bool(re.search(r'\b(20|40|HC|DC|RF)\b', text)),
    }


def _analyze_pricing_text(text: str) -> Dict[str, Any]:
    """Анализ текста с ценами."""
    import re
    
    # Поиск цен в разных валютах
    price_patterns = {
        "rub": r'(\d+(?:[.,]\d+)?)\s*(?:руб|₽|RUB)',
        "usd": r'(\d+(?:[.,]\d+)?)\s*(?:доллар|USD|\$)',
        "eur": r'(\d+(?:[.,]\d+)?)\s*(?:евро|EUR|€)',
        "cny": r'(\d+(?:[.,]\d+)?)\s*(?:юань|CNY|¥)',
    }
    
    prices = {}
    for currency, pattern in price_patterns.items():
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            prices[currency] = [float(m.replace(',', '.')) for m in matches]
    
    # Поиск диапазонов цен
    range_pattern = r'(\d+(?:[.,]\d+)?)\s*[-–—]\s*(\d+(?:[.,]\d+)?)'
    price_ranges = re.findall(range_pattern, text)
    
    return {
        "prices_found": prices,
        "price_ranges": price_ranges,
        "total_price_mentions": sum(len(prices.get(c, [])) for c in prices),
        "has_currency_info": bool(prices),
        "min_price": min([min(prices[c]) for c in prices if prices[c]], default=None),
        "max_price": max([max(prices[c]) for c in prices if prices[c]], default=None),
    }
