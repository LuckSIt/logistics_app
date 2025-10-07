from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import logging
import re
from datetime import datetime

logger = logging.getLogger(__name__)

class BaseParser(ABC):
    """
    Базовый класс для всех специализированных парсеров тарифов
    """
    
    def __init__(self, transport_type: str = None):
        self.transport_type = transport_type
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @abstractmethod
    def parse_tariff_data(self, file_path: str, supplier_id: int) -> List[Dict[str, Any]]:
        """
        Основной метод парсинга тарифных данных
        Должен быть реализован в каждом специализированном парсере
        """
        pass

    def parse_text_direct(self, text: str) -> Dict[str, Any]:
        """
        Парсинг текста напрямую (без файла)
        Реализация по умолчанию использует базовые паттерны
        """
        try:
            # Очищаем текст
            cleaned_text = self.clean_text(text)

            # Используем базовые паттерны для извлечения данных
            data = {}

            # Паттерны для извлечения данных
            patterns = {
                'origin_city': r'(?:от|из|откуда|origin|departure)[\s:]*([А-Яа-я\w\s\-]+)',
                'destination_city': r'(?:до|в|куда|destination|arrival)[\s:]*([А-Яа-я\w\s\-]+)',
                'price_rub': r'(\d+(?:[.,]\d+)?)\s*(?:руб|рубл|₽|RUB)',
                'price_usd': r'(\d+(?:[.,]\d+)?)\s*(?:долл|\$|USD)',
                'price_eur': r'(\d+(?:[.,]\d+)?)\s*(?:евро|€|EUR)',
                'transit_time_days': r'(\d+)\s*(?:дней|дня|день|days)',
                'basis': r'(EXW|FCA|FOB|CIF|CFR|DAP|DDP)',
                'weight_kg': r'(\d+(?:[.,]\d+)?)\s*(?:кг|kg|тонн)',
                'volume_m3': r'(\d+(?:[.,]\d+)?)\s*(?:м³|m3|cbm)'
            }

            for field, pattern in patterns.items():
                matches = re.findall(pattern, cleaned_text, re.IGNORECASE)
                if matches:
                    data[field] = matches[0].strip()

            # Если не нашли маршрут отдельно, попробуем найти города
            if 'origin_city' not in data or 'destination_city' not in data:
                cities = re.findall(r'\b[A-ZА-Я][a-zа-я]+(?:\s+[A-ZА-Я][a-zа-я]+)*\b', cleaned_text)
                cities = [city for city in cities if len(city) > 2]
                if len(cities) >= 2:
                    data['origin_city'] = cities[0]
                    data['destination_city'] = cities[-1]

            # Добавляем метаданные
            data['parsed_at'] = datetime.now().isoformat()
            data['parsing_method'] = 'direct_text_parsing'

            return data

        except Exception as e:
            logger.error(f"Ошибка парсинга текста: {e}")
            return {}
    
    def extract_text_from_file(self, file_path: str) -> str:
        """
        Универсальная функция для извлечения текста из файлов
        """
        from parsers import extract_text_from_file
        return extract_text_from_file(file_path)
    
    def clean_text(self, text: str) -> str:
        """
        Очистка текста от лишних символов и форматирования
        """
        if not text:
            return ""
        
        # Удаляем лишние пробелы и переносы строк
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Удаляем специальные символы, но оставляем цифры, буквы и основные знаки
        text = re.sub(r'[^\w\s\-\.\,\:\;\+\=\%\$\€\₽\¥\£\(\)\[\]\{\}]', '', text)
        
        return text
    
    def extract_numbers(self, text: str) -> List[float]:
        """
        Извлечение чисел из текста
        """
        if not text:
            return []
        
        # Ищем числа с десятичными знаками и разделителями тысяч
        numbers = re.findall(r'[\d\s\,\.]+', text)
        result = []
        
        for num_str in numbers:
            try:
                # Убираем пробелы и заменяем запятую на точку
                clean_num = num_str.replace(' ', '').replace(',', '.')
                # Убираем лишние точки (оставляем только последнюю)
                if clean_num.count('.') > 1:
                    parts = clean_num.split('.')
                    clean_num = ''.join(parts[:-1]) + '.' + parts[-1]
                
                num = float(clean_num)
                if num > 0:  # Исключаем нули и отрицательные числа
                    result.append(num)
            except ValueError:
                continue
        
        return result
    
    def extract_currency(self, text: str) -> Optional[str]:
        """
        Извлечение валюты из текста
        """
        if not text:
            return None
        
        currency_patterns = {
            'RUB': r'руб|рубл|₽|RUB',
            'USD': r'\$|USD|доллар|долл',
            'EUR': r'€|EUR|евро',
            'CNY': r'¥|CNY|юань',
            'GBP': r'£|GBP|фунт'
        }
        
        text_upper = text.upper()
        for currency, pattern in currency_patterns.items():
            if re.search(pattern, text_upper, re.IGNORECASE):
                return currency
        
        return None
    
    def extract_weight_volume(self, text: str) -> Dict[str, Optional[float]]:
        """
        Извлечение веса и объёма из текста
        """
        result = {'weight': None, 'volume': None}
        
        if not text:
            return result
        
        # Паттерны для веса
        weight_patterns = [
            r'(\d+(?:[.,]\d+)?)\s*(кг|kg|тонн|т)',
            r'вес[:\s]*(\d+(?:[.,]\d+)?)',
            r'масса[:\s]*(\d+(?:[.,]\d+)?)'
        ]
        
        # Паттерны для объёма
        volume_patterns = [
            r'(\d+(?:[.,]\d+)?)\s*(м³|м3|cbm|cbm³)',
            r'объём[:\s]*(\d+(?:[.,]\d+)?)',
            r'объем[:\s]*(\d+(?:[.,]\d+)?)'
        ]
        
        # Ищем вес
        for pattern in weight_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    weight = float(match.group(1).replace(',', '.'))
                    result['weight'] = weight
                    break
                except ValueError:
                    continue
        
        # Ищем объём
        for pattern in volume_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    volume = float(match.group(1).replace(',', '.'))
                    result['volume'] = volume
                    break
                except ValueError:
                    continue
        
        return result
    
    def extract_route(self, text: str) -> Dict[str, Optional[str]]:
        """
        Извлечение маршрута из текста
        """
        result = {'origin': None, 'destination': None}
        
        if not text:
            return result
        
        # Паттерны для маршрутов
        route_patterns = [
            r'([А-Я][а-я]+(?:\s+[А-Я][а-я]+)*)\s*[-→→]\s*([А-Я][а-я]+(?:\s+[А-Я][а-я]+)*)',
            r'от\s+([А-Я][а-я]+(?:\s+[А-Я][а-я]+)*)\s+до\s+([А-Я][а-я]+(?:\s+[А-Я][а-я]+)*)',
            r'([А-Я][а-я]+(?:\s+[А-Я][а-я]+)*)\s*/\s*([А-Я][а-я]+(?:\s+[А-Я][а-я]+)*)'
        ]
        
        for pattern in route_patterns:
            match = re.search(pattern, text)
            if match:
                result['origin'] = match.group(1).strip()
                result['destination'] = match.group(2).strip()
                break
        
        return result
    
    def extract_price(self, text: str) -> Optional[float]:
        """
        Извлечение цены из текста
        """
        if not text:
            return None
        
        # Паттерны для цен
        price_patterns = [
            r'(\d+(?:[.,]\d+)?)\s*(руб|рубл|₽|RUB|долл|\$|USD|евро|€|EUR)',
            r'цена[:\s]*(\d+(?:[.,]\d+)?)',
            r'стоимость[:\s]*(\d+(?:[.,]\d+)?)',
            r'тариф[:\s]*(\d+(?:[.,]\d+)?)'
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    price = float(match.group(1).replace(',', '.'))
                    return price
                except ValueError:
                    continue
        
        return None
    
    def validate_parsed_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Валидация распарсенных данных
        """
        validated_data = []
        
        for item in data:
            # Проверяем обязательные поля
            if not item.get('origin_city') or not item.get('destination_city'):
                self.logger.warning(f"Пропущена запись без маршрута: {item}")
                continue
            
            if not item.get('price') and not item.get('price_rub'):
                self.logger.warning(f"Пропущена запись без цены: {item}")
                continue
            
            # Добавляем тип транспорта
            item['transport_type'] = self.transport_type
            
            # Добавляем временную метку
            item['parsed_at'] = datetime.now().isoformat()
            
            validated_data.append(item)
        
        return validated_data
    
    def log_parsing_results(self, file_path: str, data: List[Dict[str, Any]]):
        """
        Логирование результатов парсинга
        """
        self.logger.info(f"Парсинг файла {file_path} завершен")
        self.logger.info(f"Извлечено {len(data)} записей")
        
        if data:
            self.logger.info(f"Пример записи: {data[0]}")
