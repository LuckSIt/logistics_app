"""
Улучшенный сервис для распознавания текста и структурирования данных
Интегрируется с существующими шаблонами и формами проекта
"""

import os
import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, date
import json
import traceback

# OCR библиотеки
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import cv2
import numpy as np

# Документы
import pdfplumber
from docx import Document
import pandas as pd

# AI/ML для улучшения распознавания
try:
    import easyocr
    EASYOCR_AVAILABLE = True
except (ImportError, AttributeError, Exception) as e:
    EASYOCR_AVAILABLE = False
    logging.warning(f"EasyOCR недоступен: {e}. Будет использоваться только Tesseract.")

logger = logging.getLogger(__name__)

class EnhancedOCRService:
    """
    Улучшенный сервис OCR с поддержкой различных форматов и интеллектуальным парсингом
    """
    
    def __init__(self):
        self.setup_tesseract()
        self.setup_easyocr()
        
        # Шаблоны для распознавания структурированных данных
        self.template_patterns = self._load_template_patterns()
        
        # Словари для нормализации данных
        self.city_normalization = self._load_city_normalization()
        self.currency_patterns = self._load_currency_patterns()
        
    def setup_tesseract(self):
        """Настройка Tesseract OCR"""
        possible_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            "/usr/bin/tesseract",
            "/usr/local/bin/tesseract"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                logger.info(f"Tesseract найден по пути: {path}")
                break
        else:
            logger.warning("Tesseract не найден. OCR будет недоступен.")
    
    def setup_easyocr(self):
        """Настройка EasyOCR"""
        if EASYOCR_AVAILABLE:
            try:
                self.easyocr_reader = easyocr.Reader(['ru', 'en'], gpu=False)
                logger.info("EasyOCR инициализирован успешно")
            except Exception as e:
                logger.warning(f"Не удалось инициализировать EasyOCR: {e}")
                self.easyocr_reader = None
        else:
            self.easyocr_reader = None
    
    def _load_template_patterns(self) -> Dict[str, Dict[str, str]]:
        """Загрузка паттернов для распознавания структурированных данных"""
        return {
            'auto': {
                'route': r'(?:маршрут|route|от|до|из|в)\s*:?\s*([А-Яа-я\w\s\-]+)\s*[-→→]\s*([А-Яа-я\w\s\-]+)',
                'price': r'(?:цена|стоимость|тариф|price|cost|rate)\s*:?\s*(\d+(?:[.,]\d+)?)\s*(руб|рубл|₽|RUB|долл|\$|USD|евро|€|EUR)',
                'vehicle_type': r'(?:тип\s+транспорта|vehicle|автомобиль|фура|грузовик)\s*:?\s*([А-Яа-я\w\s\-]+)',
                'transit_time': r'(?:срок|время|transit|delivery)\s*:?\s*(\d+)\s*(?:дней|дня|день|days|day)',
                'validity': r'(?:действительно|валидно|valid|до)\s*:?\s*(\d{1,2}[./]\d{1,2}[./]\d{2,4})',
                'basis': r'(?:базис|basis)\s*:?\s*(EXW|FCA|FOB|CIF|DAP|DDP)',
            },
            'sea': {
                'route': r'(?:порт|port|от|до|из|в)\s*:?\s*([А-Яа-я\w\s\-]+)\s*[-→→]\s*([А-Яа-я\w\s\-]+)',
                'price': r'(?:фрахт|freight|стоимость|цена)\s*:?\s*(\d+(?:[.,]\d+)?)\s*(USD|долл|\$|руб|₽)',
                'container_type': r'(?:контейнер|container|тип)\s*:?\s*(20|40|45|20GP|40GP|40HC|45HC)',
                'transit_time': r'(?:срок|время|transit)\s*:?\s*(\d+)\s*(?:дней|дня|день|days)',
                'validity': r'(?:действительно|валидно|valid|до)\s*:?\s*(\d{1,2}[./]\d{1,2}[./]\d{2,4})',
                'basis': r'(?:базис|basis)\s*:?\s*(EXW|FCA|FOB|CIF|CFR)',
            },
            'air': {
                'route': r'(?:аэропорт|airport|от|до|из|в)\s*:?\s*([А-Яа-я\w\s\-]+)\s*[-→→]\s*([А-Яа-я\w\s\-]+)',
                'price': r'(?:авиа\s+фрахт|air\s+freight|стоимость|цена)\s*:?\s*(\d+(?:[.,]\d+)?)\s*(USD|долл|\$|руб|₽)',
                'weight_volume': r'(?:вес|weight|объем|volume)\s*:?\s*(\d+(?:[.,]\d+)?)\s*(кг|kg|м³|m3|cbm)',
                'transit_time': r'(?:срок|время|transit)\s*:?\s*(\d+)\s*(?:дней|дня|день|days)',
                'validity': r'(?:действительно|валидно|valid|до)\s*:?\s*(\d{1,2}[./]\d{1,2}[./]\d{2,4})',
                'basis': r'(?:базис|basis)\s*:?\s*(EXW|FCA|FOB)',
            },
            'rail': {
                'route': r'(?:станция|station|от|до|из|в)\s*:?\s*([А-Яа-я\w\s\-]+)\s*[-→→]\s*([А-Яа-я\w\s\-]+)',
                'price': r'(?:тариф|tariff|стоимость|цена)\s*:?\s*(\d+(?:[.,]\d+)?)\s*(руб|₽|RUB|USD|\$)',
                'container_type': r'(?:контейнер|container|вагон|wagon)\s*:?\s*(20|40|45|20GP|40GP|40HC)',
                'transit_time': r'(?:срок|время|transit)\s*:?\s*(\d+)\s*(?:дней|дня|день|days)',
                'validity': r'(?:действительно|валидно|valid|до)\s*:?\s*(\d{1,2}[./]\d{1,2}[./]\d{2,4})',
                'basis': r'(?:базис|basis)\s*:?\s*(EXW|FCA|FOB)',
            }
        }
    
    def _load_city_normalization(self) -> Dict[str, str]:
        """Словарь для нормализации названий городов"""
        return {
            'москва': 'Москва',
            'спб': 'Санкт-Петербург',
            'питер': 'Санкт-Петербург',
            'нск': 'Новосибирск',
            'екатеринбург': 'Екатеринбург',
            'казань': 'Казань',
            'нижний новгород': 'Нижний Новгород',
            'челябинск': 'Челябинск',
            'омск': 'Омск',
            'самара': 'Самара',
            'ростов': 'Ростов-на-Дону',
            'уфа': 'Уфа',
            'красноярск': 'Красноярск',
            'пермь': 'Пермь',
            'волгоград': 'Волгоград',
            'воронеж': 'Воронеж',
            'саратов': 'Саратов',
            'краснодар': 'Краснодар',
            'тольятти': 'Тольятти',
            'барнаул': 'Барнаул',
        }
    
    def _load_currency_patterns(self) -> Dict[str, str]:
        """Паттерны для распознавания валют"""
        return {
            'RUB': r'руб|рубл|₽|RUB|р\.',
            'USD': r'\$|USD|доллар|долл|usd',
            'EUR': r'€|EUR|евро|eur',
            'CNY': r'¥|CNY|юань|yuan',
            'GBP': r'£|GBP|фунт|pound'
        }
    
    def extract_text_from_file(self, file_path: str) -> str:
        """
        Извлечение текста из файла с улучшенным OCR
        """
        try:
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext in ['.pdf']:
                return self._extract_from_pdf(file_path)
            elif file_ext in ['.docx', '.doc']:
                return self._extract_from_docx(file_path)
            elif file_ext in ['.xlsx', '.xls']:
                return self._extract_from_excel(file_path)
            elif file_ext in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff']:
                return self._extract_from_image(file_path)
            else:
                logger.warning(f"Неподдерживаемый формат файла: {file_ext}")
                return ""
                
        except Exception as e:
            logger.error(f"Ошибка извлечения текста из файла {file_path}: {e}")
            return ""
    
    def _extract_from_pdf(self, file_path: str) -> str:
        """Извлечение текста из PDF"""
        text = ""
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                    else:
                        # Если текст не извлекается, пробуем OCR
                        try:
                            img = page.to_image()
                            pil_image = Image.fromarray(img.original)
                            ocr_text = self._ocr_image(pil_image)
                            text += ocr_text + "\n"
                        except Exception as e:
                            logger.warning(f"OCR для PDF страницы не удался: {e}")
        except Exception as e:
            logger.error(f"Ошибка извлечения текста из PDF: {e}")
        
        return text
    
    def _extract_from_docx(self, file_path: str) -> str:
        """Извлечение текста из DOCX"""
        try:
            doc = Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            logger.error(f"Ошибка извлечения текста из DOCX: {e}")
            return ""
    
    def _extract_from_excel(self, file_path: str) -> str:
        """Извлечение текста из Excel"""
        try:
            df = pd.read_excel(file_path)
            # Преобразуем DataFrame в текст
            text = df.to_string(index=False)
            return text
        except Exception as e:
            logger.error(f"Ошибка извлечения текста из Excel: {e}")
            return ""
    
    def _extract_from_image(self, file_path: str) -> str:
        """Извлечение текста из изображения с улучшенным OCR"""
        try:
            # Загружаем изображение
            image = Image.open(file_path)
            
            # Пробуем разные методы OCR
            texts = []
            
            # 1. Tesseract с разными настройками
            tesseract_text = self._ocr_with_tesseract(image)
            if tesseract_text:
                texts.append(('tesseract', tesseract_text))
            
            # 2. EasyOCR если доступен
            if self.easyocr_reader:
                easyocr_text = self._ocr_with_easyocr(image)
                if easyocr_text:
                    texts.append(('easyocr', easyocr_text))
            
            # 3. Выбираем лучший результат
            if texts:
                # Выбираем текст с наибольшей длиной
                best_text = max(texts, key=lambda x: len(x[1]))
                logger.info(f"Выбран лучший OCR результат: {best_text[0]}")
                return best_text[1]
            
            return ""
            
        except Exception as e:
            logger.error(f"Ошибка OCR для изображения {file_path}: {e}")
            return ""
    
    def _ocr_with_tesseract(self, image: Image.Image) -> str:
        """OCR с помощью Tesseract"""
        try:
            # Пробуем разные настройки
            configs = [
                '--oem 3 --psm 6 -l rus+eng',  # Стандартные настройки
                '--oem 3 --psm 3 -l rus+eng',  # Автоматическое определение страницы
                '--oem 1 --psm 6 -l rus+eng',  # Legacy OCR engine
                '--oem 3 --psm 8 -l rus+eng',  # Одна строка текста
                '--oem 3 --psm 13 -l rus+eng', # Необработанная строка
            ]
            
            best_text = ""
            for config in configs:
                try:
                    text = pytesseract.image_to_string(image, config=config)
                    if text and len(text.strip()) > len(best_text.strip()):
                        best_text = text
                except Exception as e:
                    logger.warning(f"Tesseract OCR с конфигурацией {config} не удался: {e}")
            
            return best_text
            
        except Exception as e:
            logger.error(f"Ошибка Tesseract OCR: {e}")
            return ""
    
    def _ocr_with_easyocr(self, image: Image.Image) -> str:
        """OCR с помощью EasyOCR"""
        try:
            # Конвертируем PIL Image в numpy array
            img_array = np.array(image)
            
            # Распознаем текст
            results = self.easyocr_reader.readtext(img_array)
            
            # Объединяем результаты
            text = ""
            for (bbox, text_item, confidence) in results:
                if confidence > 0.5:  # Фильтруем по уверенности
                    text += text_item + " "
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"Ошибка EasyOCR: {e}")
            return ""
    
    def _ocr_image(self, image: Image.Image) -> str:
        """Универсальный OCR для изображения"""
        return self._extract_from_image_data(image)
    
    def _extract_from_image_data(self, image: Image.Image) -> str:
        """Извлечение текста из данных изображения"""
        # Пробуем улучшить качество изображения
        enhanced_image = self._enhance_image(image)
        
        # OCR с улучшенным изображением
        return self._ocr_with_tesseract(enhanced_image)
    
    def _enhance_image(self, image: Image.Image) -> Image.Image:
        """Улучшение качества изображения для лучшего OCR"""
        try:
            # Конвертируем в RGB если нужно
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Увеличиваем контраст
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2.0)
            
            # Увеличиваем резкость
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(2.0)
            
            # Увеличиваем яркость
            enhancer = ImageEnhance.Brightness(image)
            image = enhancer.enhance(1.2)
            
            return image
            
        except Exception as e:
            logger.warning(f"Не удалось улучшить изображение: {e}")
            return image
    
    def parse_structured_data(self, text: str, transport_type: str = 'auto') -> Dict[str, Any]:
        """
        Парсинг структурированных данных из текста согласно шаблонам
        """
        try:
            # Очищаем текст
            clean_text = self._clean_text(text)
            
            # Получаем паттерны для типа транспорта
            patterns = self.template_patterns.get(transport_type, self.template_patterns['auto'])
            
            # Извлекаем данные
            parsed_data = {}
            
            # Маршрут
            route_match = re.search(patterns['route'], clean_text, re.IGNORECASE)
            if route_match:
                origin = self._normalize_city(route_match.group(1).strip())
                destination = self._normalize_city(route_match.group(2).strip())
                parsed_data.update({
                    'origin_city': origin,
                    'destination_city': destination,
                    'origin_country': self._extract_country(origin),
                    'destination_country': self._extract_country(destination)
                })
            
            # Цена
            price_match = re.search(patterns['price'], clean_text, re.IGNORECASE)
            if price_match:
                price_value = float(price_match.group(1).replace(',', '.'))
                currency = self._normalize_currency(price_match.group(2))
                
                if currency == 'RUB':
                    parsed_data['price_rub'] = price_value
                elif currency == 'USD':
                    parsed_data['price_usd'] = price_value
                else:
                    parsed_data['price'] = price_value
                    parsed_data['currency'] = currency
            
            # Тип транспорта/контейнера
            if transport_type in ['auto']:
                vehicle_match = re.search(patterns['vehicle_type'], clean_text, re.IGNORECASE)
                if vehicle_match:
                    parsed_data['vehicle_type'] = vehicle_match.group(1).strip()
            elif transport_type in ['sea', 'rail']:
                container_match = re.search(patterns['container_type'], clean_text, re.IGNORECASE)
                if container_match:
                    parsed_data['vehicle_type'] = container_match.group(1).strip()
            
            # Срок доставки
            transit_match = re.search(patterns['transit_time'], clean_text, re.IGNORECASE)
            if transit_match:
                parsed_data['transit_time_days'] = int(transit_match.group(1))
            
            # Валидность
            validity_match = re.search(patterns['validity'], clean_text, re.IGNORECASE)
            if validity_match:
                parsed_data['validity_date'] = self._parse_date(validity_match.group(1))
            
            # Базис
            basis_match = re.search(patterns['basis'], clean_text, re.IGNORECASE)
            if basis_match:
                parsed_data['basis'] = basis_match.group(1).upper()
            
            # Дополнительные поля для авиа
            if transport_type == 'air':
                weight_volume_match = re.search(patterns['weight_volume'], clean_text, re.IGNORECASE)
                if weight_volume_match:
                    value = float(weight_volume_match.group(1).replace(',', '.'))
                    unit = weight_volume_match.group(2).lower()
                    if unit in ['кг', 'kg']:
                        parsed_data['weight_kg'] = value
                    elif unit in ['м³', 'm3', 'cbm']:
                        parsed_data['volume_m3'] = value
            
            # Добавляем метаданные
            parsed_data.update({
                'transport_type': transport_type,
                'parsed_at': datetime.now().isoformat(),
                'source_text_length': len(clean_text)
            })
            
            return parsed_data
            
        except Exception as e:
            logger.error(f"Ошибка парсинга структурированных данных: {e}")
            return {}
    
    def _clean_text(self, text: str) -> str:
        """Очистка текста"""
        if not text:
            return ""
        
        # Удаляем лишние пробелы и переносы
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Удаляем специальные символы, но оставляем нужные
        text = re.sub(r'[^\w\s\-\.\,\:\;\+\=\%\$\€\₽\¥\£\(\)\[\]\{\}\/]', '', text)
        
        return text
    
    def _normalize_city(self, city: str) -> str:
        """Нормализация названия города"""
        city_lower = city.lower().strip()
        return self.city_normalization.get(city_lower, city.strip())
    
    def _normalize_currency(self, currency: str) -> str:
        """Нормализация валюты"""
        currency_upper = currency.upper().strip()
        for curr, pattern in self.currency_patterns.items():
            if re.search(pattern, currency_upper, re.IGNORECASE):
                return curr
        return 'RUB'  # По умолчанию
    
    def _extract_country(self, city: str) -> str:
        """Извлечение страны из названия города"""
        # Простая логика - можно расширить
        russian_cities = ['москва', 'санкт-петербург', 'новосибирск', 'екатеринбург', 'казань']
        if any(ru_city in city.lower() for ru_city in russian_cities):
            return 'Россия'
        return 'Неизвестно'
    
    def _parse_date(self, date_str: str) -> str:
        """Парсинг даты"""
        try:
            # Пробуем разные форматы
            formats = ['%d.%m.%Y', '%d/%m/%Y', '%d.%m.%y', '%d/%m/%y']
            for fmt in formats:
                try:
                    parsed_date = datetime.strptime(date_str, fmt).date()
                    return parsed_date.isoformat()
                except ValueError:
                    continue
            return date_str
        except Exception:
            return date_str
    
    def process_file(self, file_path: str, transport_type: str = 'auto') -> Dict[str, Any]:
        """
        Полная обработка файла: извлечение текста + парсинг структурированных данных
        """
        try:
            logger.info(f"Начинаем обработку файла: {file_path}")
            
            # Извлекаем текст
            text = self.extract_text_from_file(file_path)
            if not text:
                logger.warning(f"Не удалось извлечь текст из файла: {file_path}")
                return {'error': 'Не удалось извлечь текст из файла'}
            
            # Парсим структурированные данные
            structured_data = self.parse_structured_data(text, transport_type)
            
            # Добавляем исходный текст
            structured_data['raw_text'] = text
            
            logger.info(f"Обработка файла завершена. Извлечено {len(structured_data)} полей")
            return structured_data
            
        except Exception as e:
            logger.error(f"Ошибка обработки файла {file_path}: {e}")
            logger.error(traceback.format_exc())
            return {'error': str(e)}


# Создаем глобальный экземпляр сервиса
enhanced_ocr_service = EnhancedOCRService()
