import os
from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from database import SessionLocal
import models, schemas
from services.security import get_current_user
from services.documents import generate_docx, generate_pdf

router = APIRouter()


BASE_DIR = os.path.dirname(os.path.dirname(__file__))
OUT_DIR = os.path.abspath(os.path.join(BASE_DIR, "generated_docs"))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/generate", response_model=schemas.OfferOut)
def generate_offer(payload: schemas.OfferGenerateRequest, current: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Генерация коммерческого предложения"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Берём результаты расчёта из payload.request.results, если есть
        options = []
        req = payload.request or {}
        
        if isinstance(req, dict):
            options = req.get("results", [])
            selected_tariffs = req.get("selected_tariffs", [])
            # Если results пустой, используем selected_tariffs
            if not options and selected_tariffs:
                options = selected_tariffs
        else:
            req = {}
            options = []
        
        logger.info(f"Генерируем КП для пользователя {current.id}, тарифов: {len(options)}")
        
        # Создаем уникальное имя файла с временной меткой
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"offer_{current.id}_{timestamp}.pdf"
        out_path = os.path.join(OUT_DIR, filename)
        os.makedirs(OUT_DIR, exist_ok=True)
        
        # Генерируем PDF с данными запроса
        generate_pdf(options, out_path, request_data=req if isinstance(req, dict) else {})
        
        # Сохраняем в базу данных
        offer = models.CommercialOffer(user_id=current.id, request_id=None, file_path=out_path)
        db.add(offer)
        db.commit()
        db.refresh(offer)
        
        logger.info(f"КП сгенерирован: {filename}, ID: {offer.id}")
        return offer
        
    except Exception as e:
        logger.error(f"Ошибка генерации КП: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка генерации КП: {str(e)}")


@router.get("/{offer_id}/download")
def download_offer(offer_id: int, current: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Скачивание коммерческого предложения"""
    import logging
    logger = logging.getLogger(__name__)
    
    offer = db.query(models.CommercialOffer).filter(
        models.CommercialOffer.id == offer_id,
        models.CommercialOffer.user_id == current.id
    ).first()
    
    if not offer:
        logger.warning(f"КП {offer_id} не найдено для пользователя {current.id}")
        raise HTTPException(status_code=404, detail="КП не найдено")
    
    if not os.path.exists(offer.file_path):
        logger.error(f"Файл КП не найден: {offer.file_path}")
        raise HTTPException(status_code=404, detail="Файл КП не найден")
    
    # Создаем читаемое имя файла
    filename = f"Коммерческое_предложение_{offer_id}.pdf"
    
    logger.info(f"Скачивание КП {offer_id} пользователем {current.id}")
    return FileResponse(
        offer.file_path, 
        filename=filename,
        media_type='application/pdf'
    )


