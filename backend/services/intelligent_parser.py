"""
Интеллектуальный парсер для структурирования данных согласно формам проекта
Интегрируется с существующими шаблонами и моделями БД
"""

import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, date
import json
import traceback

from services.enhanced_ocr_service import enhanced_ocr_service
import models, schemas
from database import SessionLocal

logger = logging.getLogger(__name__)

class IntelligentParser:
    """
    Интеллектуальный парсер для структурирования данных согласно формам проекта
    """
    
    def __init__(self):
        self.ocr_service = enhanced_ocr_service
        
        # Загружаем шаблоны и паттерны
        self.template_patterns = self._load_advanced_patterns()
        self.field_mappings = self._load_field_mappings()
        self.validation_rules = self._load_validation_rules()
        
    def _load_advanced_patterns(self) -> Dict[str, Dict[str, str]]:
        """Загрузка продвинутых паттернов для распознавания"""
        return {
            'auto': {
                # Маршруты
                'route_full': r'(?:маршрут|route|от|до|из|в|откуда|куда)\s*:?\s*([А-Яа-я\w\s\-\.]+)\s*[-→→]\s*([А-Яа-я\w\s\-\.]+)',
                'route_simple': r'([А-Яа-я]+(?:\s+[А-Яа-я]+)*)\s*[-→→]\s*([А-Яа-я]+(?:\s+[А-Яа-я]+)*)',
                
                # Цены
                'price_rub': r'(?:цена|стоимость|тариф|price|cost|rate)\s*:?\s*(\d+(?:[.,]\d+)?)\s*(?:руб|рубл|₽|RUB)',
                'price_usd': r'(?:цена|стоимость|тариф|price|cost|rate)\s*:?\s*(\d+(?:[.,]\d+)?)\s*(?:долл|\$|USD)',
                'price_eur': r'(?:цена|стоимость|тариф|price|cost|rate)\s*:?\s*(\d+(?:[.,]\d+)?)\s*(?:евро|€|EUR)',
                
                # Тип транспорта
                'vehicle_type': r'(?:тип\s+транспорта|vehicle|автомобиль|фура|грузовик|тент|рефрижератор|изотерм)\s*:?\s*([А-Яа-я\w\s\-]+)',
                
                # Сроки
                'transit_time': r'(?:срок|время|transit|delivery|доставка)\s*:?\s*(\d+)\s*(?:дней|дня|день|days|day)',
                'validity_date': r'(?:действительно|валидно|valid|до|действует)\s*:?\s*(\d{1,2}[./]\d{1,2}[./]\d{2,4})',
                
                # Базис
                'basis': r'(?:базис|basis|условия)\s*:?\s*(EXW|FCA|FOB|CIF|DAP|DDP)',
                
                # Дополнительные поля
                'border_point': r'(?:пограничный\s+пункт|border|граница)\s*:?\s*([А-Яа-я\w\s\-]+)',
                'currency_conversion': r'(?:конвертация|conversion)\s*:?\s*(\d+(?:[.,]\d+)?)\s*%',
            },
            
            'sea': {
                # Порты
                'port_route': r'(?:порт|port|от|до|из|в)\s*:?\s*([А-Яа-я\w\s\-\.]+)\s*[-→→]\s*([А-Яа-я\w\s\-\.]+)',
                
                # Цены
                'freight_usd': r'(?:фрахт|freight|стоимость|цена|rate)\s*:?\s*(\d+(?:[.,]\d+)?)\s*(?:USD|долл|\$)',
                'freight_rub': r'(?:фрахт|freight|стоимость|цена|rate)\s*:?\s*(\d+(?:[.,]\d+)?)\s*(?:руб|₽|RUB)',
                
                # Контейнеры
                'container_type': r'(?:контейнер|container|тип)\s*:?\s*(20|40|45|20GP|40GP|40HC|45HC|20RF|40RF)',
                'container_size': r'(?:размер|size)\s*:?\s*(\d+)\s*(?:фут|ft|foot)',
                
                # Сроки
                'transit_time': r'(?:срок|время|transit|voyage)\s*:?\s*(\d+)\s*(?:дней|дня|день|days)',
                'validity_date': r'(?:действительно|валидно|valid|до)\s*:?\s*(\d{1,2}[./]\d{1,2}[./]\d{2,4})',
                
                # Базис
                'basis': r'(?:базис|basis)\s*:?\s*(EXW|FCA|FOB|CIF|CFR)',
                
                # Дополнительные поля
                'transit_port': r'(?:транзитный\s+порт|transit\s+port)\s*:?\s*([А-Яа-я\w\s\-]+)',
                'arrival_port': r'(?:порт\s+назначения|arrival\s+port)\s*:?\s*([А-Яа-я\w\s\-]+)',
            },
            
            'air': {
                # Аэропорты - более общие паттерны
                'airport_route': r'(?:аэропорт|airport|от|до|из|в)\s*:?\s*([А-Яа-я\w\s\-\.]+)\s*[-→→]\s*([А-Яа-я\w\s\-\.]+)',
                'route_full': r'(?:маршрут|route|от|до|из|в|откуда|куда)\s*:?\s*([А-Яа-я\w\s\-\.]+)\s*[-→→]\s*([А-Яа-я\w\s\-\.]+)',
                'route_simple': r'([А-Яа-я]+(?:\s+[А-Яа-я]+)*)\s*[-→→]\s*([А-Яа-я]+(?:\s+[А-Яа-я]+)*)',
                'city_pair': r'([А-Яа-я]{2,}(?:\s+[А-Яа-я]{2,})*)\s*[-→→]\s*([А-Яа-я]{2,}(?:\s+[А-Яа-я]{2,})*)',
                
                # Цены - более общие паттерны
                'air_freight': r'(?:авиа\s+фрахт|air\s+freight|стоимость|цена|тариф|price|cost|rate)\s*:?\s*(\d+(?:[.,]\d+)?)\s*(?:USD|долл|\$|руб|₽)',
                'price_rub': r'(?:цена|стоимость|тариф|price|cost|rate)\s*:?\s*(\d+(?:[.,]\d+)?)\s*(?:руб|рубл|₽|RUB)',
                'price_usd': r'(?:цена|стоимость|тариф|price|cost|rate)\s*:?\s*(\d+(?:[.,]\d+)?)\s*(?:долл|\$|USD)',
                'price_eur': r'(?:цена|стоимость|тариф|price|cost|rate)\s*:?\s*(\d+(?:[.,]\d+)?)\s*(?:евро|€|EUR)',
                'number_price': r'(\d+(?:[.,]\d+)?)\s*(?:руб|рубл|₽|RUB|USD|долл|\$|евро|€|EUR)',
                
                # Вес и объем
                'weight': r'(?:вес|weight|масса)\s*:?\s*(\d+(?:[.,]\d+)?)\s*(?:кг|kg|тонн|т)',
                'volume': r'(?:объем|volume|габариты)\s*:?\s*(\d+(?:[.,]\d+)?)\s*(?:м³|m3|cbm)',
                'volumetric_weight': r'(?:объемный\s+вес|volumetric\s+weight)\s*:?\s*(\d+(?:[.,]\d+)?)\s*(?:кг|kg)',
                
                # Сроки
                'transit_time': r'(?:срок|время|transit|flight)\s*:?\s*(\d+)\s*(?:дней|дня|день|days)',
                'validity_date': r'(?:действительно|валидно|valid|до)\s*:?\s*(\d{1,2}[./]\d{1,2}[./]\d{2,4})',
                
                # Базис
                'basis': r'(?:базис|basis)\s*:?\s*(EXW|FCA|FOB)',
                
                # Дополнительные поля
                'departure_airport': r'(?:аэропорт\s+отправления|departure\s+airport)\s*:?\s*([А-Яа-я\w\s\-]+)',
                'arrival_airport': r'(?:аэропорт\s+назначения|arrival\s+airport)\s*:?\s*([А-Яа-я\w\s\-]+)',
                'precarriage_cost': r'(?:прекерридж|precarriage)\s*:?\s*(\d+(?:[.,]\d+)?)',
                'terminal_handling_cost': r'(?:терминальная\s+обработка|terminal\s+handling)\s*:?\s*(\d+(?:[.,]\d+)?)',
            },
            
            'rail': {
                # Станции
                'station_route': r'(?:станция|station|от|до|из|в)\s*:?\s*([А-Яа-я\w\s\-\.]+)\s*[-→→]\s*([А-Яа-я\w\s\-\.]+)',
                
                # Цены
                'rail_tariff': r'(?:тариф|tariff|стоимость|цена|rate)\s*:?\s*(\d+(?:[.,]\d+)?)\s*(?:руб|₽|RUB|USD|\$)',
                
                # Контейнеры/вагоны
                'container_type': r'(?:контейнер|container|вагон|wagon)\s*:?\s*(20|40|45|20GP|40GP|40HC)',
                'wagon_type': r'(?:тип\s+вагона|wagon\s+type)\s*:?\s*([А-Яа-я\w\s\-]+)',
                
                # Сроки
                'transit_time': r'(?:срок|время|transit)\s*:?\s*(\d+)\s*(?:дней|дня|день|days)',
                'validity_date': r'(?:действительно|валидно|valid|до)\s*:?\s*(\d{1,2}[./]\d{1,2}[./]\d{2,4})',
                
                # Базис
                'basis': r'(?:базис|basis)\s*:?\s*(EXW|FCA|FOB)',
                
                # Дополнительные поля
                'departure_station': r'(?:станция\s+отправления|departure\s+station)\s*:?\s*([А-Яа-я\w\s\-]+)',
                'arrival_station': r'(?:станция\s+назначения|arrival\s+station)\s*:?\s*([А-Яа-я\w\s\-]+)',
                'cbx_cost': r'(?:свх|cbx|раскредитация)\s*:?\s*(\d+(?:[.,]\d+)?)',
                'auto_pickup_cost': r'(?:автовывоз|auto\s+pickup)\s*:?\s*(\d+(?:[.,]\d+)?)',
            },
            
            'multimodal': {
                # Комбинированные маршруты
                'multimodal_route': r'(?:маршрут|route|от|до|из|в)\s*:?\s*([А-Яа-я\w\s\-\.]+)\s*[-→→]\s*([А-Яа-я\w\s\-\.]+)',
                
                # Цены
                'price_usd': r'(?:стоимость|цена|price)\s*:?\s*(\d+(?:[.,]\d+)?)\s*(?:USD|долл|\$)',
                'price_rub': r'(?:стоимость|цена|price)\s*:?\s*(\d+(?:[.,]\d+)?)\s*(?:руб|₽|RUB)',
                
                # Контейнеры
                'container_type': r'(?:контейнер|container)\s*:?\s*(20|40|45|20GP|40GP|40HC)',
                
                # Сроки
                'transit_time': r'(?:срок|время|transit)\s*:?\s*(\d+)\s*(?:дней|дня|день|days)',
                'validity_date': r'(?:действительно|валидно|valid|до)\s*:?\s*(\d{1,2}[./]\d{1,2}[./]\d{2,4})',
                
                # Базис
                'basis': r'(?:базис|basis)\s*:?\s*(EXW|FCA|FOB)',
                
                # Дополнительные поля
                'transit_port': r'(?:транзитный\s+порт|transit\s+port)\s*:?\s*([А-Яа-я\w\s\-]+)',
                'departure_station': r'(?:станция\s+отправления|departure\s+station)\s*:?\s*([А-Яа-я\w\s\-]+)',
                'arrival_station': r'(?:станция\s+назначения|arrival\s+station)\s*:?\s*([А-Яа-я\w\s\-]+)',
                'rail_tariff_rub': r'(?:жд\s+тариф|rail\s+tariff)\s*:?\s*(\d+(?:[.,]\d+)?)',
                'cbx_cost': r'(?:свх|cbx)\s*:?\s*(\d+(?:[.,]\d+)?)',
                'terminal_handling_cost': r'(?:терминальная\s+обработка|terminal\s+handling)\s*:?\s*(\d+(?:[.,]\d+)?)',
                'auto_pickup_cost': r'(?:автовывоз|auto\s+pickup)\s*:?\s*(\d+(?:[.,]\d+)?)',
                'security_cost': r'(?:охрана|security)\s*:?\s*(\d+(?:[.,]\d+)?)',
                'precarriage_cost': r'(?:прекерридж|precarriage)\s*:?\s*(\d+(?:[.,]\d+)?)',
            }
        }
    
    def _load_field_mappings(self) -> Dict[str, str]:
        """Загрузка маппинга полей для соответствия моделям БД"""
        return {
            # Основные поля
            'origin_city': 'origin_city',
            'destination_city': 'destination_city',
            'origin_country': 'origin_country',
            'destination_country': 'destination_country',
            'price_rub': 'price_rub',
            'price_usd': 'price_usd',
            'vehicle_type': 'vehicle_type',
            'transit_time_days': 'transit_time_days',
            'validity_date': 'validity_date',
            'basis': 'basis',
            'transport_type': 'transport_type',
            
            # Дополнительные поля
            'border_point': 'border_point',
            'currency_conversion': 'currency_conversion',
            'transit_port': 'transit_port',
            'arrival_port': 'arrival_port',
            'departure_airport': 'departure_airport',
            'arrival_airport': 'arrival_airport',
            'departure_station': 'departure_station',
            'arrival_station': 'arrival_station',
            'rail_tariff_rub': 'rail_tariff_rub',
            'cbx_cost': 'cbx_cost',
            'terminal_handling_cost': 'terminal_handling_cost',
            'auto_pickup_cost': 'auto_pickup_cost',
            'security_cost': 'security_cost',
            'precarriage_cost': 'precarriage_cost',
        }
    
    def _load_validation_rules(self) -> Dict[str, Dict[str, Any]]:
        """Загрузка правил валидации"""
        return {
            'required_fields': ['origin_city', 'destination_city'],
            'price_fields': ['price_rub', 'price_usd'],
            'date_fields': ['validity_date'],
            'numeric_fields': ['price_rub', 'price_usd', 'transit_time_days', 'currency_conversion'],
            'text_fields': ['origin_city', 'destination_city', 'vehicle_type', 'basis'],
        }
    
    def parse_file(self, file_path: str, transport_type: str = 'auto', supplier_id: int = None) -> Dict[str, Any]:
        """
        Полный парсинг файла с интеллектуальным извлечением данных
        """
        try:
            logger.info(f"Начинаем интеллектуальный парсинг файла: {file_path}")
            
            # Извлекаем текст с помощью OCR
            text = self.ocr_service.extract_text_from_file(file_path)
            if not text:
                return {'error': 'Не удалось извлечь текст из файла', 'success': False}
            
            # Парсим структурированные данные
            parsed_data = self._parse_with_patterns(text, transport_type)
            
            # Валидируем данные
            validated_data = self._validate_parsed_data(parsed_data)
            
            # Добавляем метаданные
            validated_data.update({
                'supplier_id': supplier_id,
                'source_file': file_path,
                'parsed_at': datetime.now().isoformat(),
                'transport_type': transport_type,
                'success': True
            })
            
            logger.info(f"Интеллектуальный парсинг завершен. Извлечено {len(validated_data)} полей")
            return validated_data
            
        except Exception as e:
            logger.error(f"Ошибка интеллектуального парсинга файла {file_path}: {e}")
            logger.error(traceback.format_exc())
            return {'error': str(e), 'success': False}
    
    def _parse_with_patterns(self, text: str, transport_type: str) -> Dict[str, Any]:
        """Парсинг с использованием паттернов"""
        try:
            patterns = self.template_patterns.get(transport_type, self.template_patterns['auto'])
            parsed_data = {}
            
            # Очищаем текст
            clean_text = self._clean_text(text)
            logger.info(f"Очищенный текст для парсинга ({transport_type}): {clean_text[:200]}...")
            
            # Парсим каждое поле
            for field, pattern in patterns.items():
                matches = re.findall(pattern, clean_text, re.IGNORECASE | re.MULTILINE)
                if matches:
                    if isinstance(matches[0], tuple):
                        # Если паттерн возвращает несколько групп
                        parsed_data[field] = matches[0]
                        logger.info(f"Найдено совпадение для {field}: {matches[0]}")
                    else:
                        # Если паттерн возвращает одну группу
                        parsed_data[field] = matches[0]
                        logger.info(f"Найдено совпадение для {field}: {matches[0]}")
            
            logger.info(f"Найдено полей: {list(parsed_data.keys())}")
            
            # Обрабатываем специальные случаи
            parsed_data = self._process_special_cases(parsed_data, transport_type)
            
            return parsed_data
            
        except Exception as e:
            logger.error(f"Ошибка парсинга с паттернами: {e}")
            return {}
    
    def _process_special_cases(self, data: Dict[str, Any], transport_type: str) -> Dict[str, Any]:
        """Обработка специальных случаев"""
        try:
            # Обрабатываем маршруты - проверяем все возможные паттерны
            route_patterns = ['route_full', 'route_simple', 'airport_route', 'city_pair', 'port_route', 'station_route']
            
            for pattern in route_patterns:
                if pattern in data and isinstance(data[pattern], tuple) and len(data[pattern]) == 2:
                    origin, destination = data[pattern]
                    data['origin_city'] = self._normalize_city(origin)
                    data['destination_city'] = self._normalize_city(destination)
                    data['origin_country'] = self._extract_country(origin)
                    data['destination_country'] = self._extract_country(destination)
                    logger.info(f"Найден маршрут: {origin} -> {destination}")
                    break
            
            # Обрабатываем цены - проверяем все возможные паттерны
            price_patterns = ['price_rub', 'price_usd', 'price_eur', 'air_freight', 'freight_usd', 'freight_rub', 'rail_tariff', 'number_price']
            
            for pattern in price_patterns:
                if pattern in data:
                    price_value = self._parse_number(data[pattern])
                    if price_value:
                        # Определяем валюту по паттерну
                        if 'rub' in pattern or 'RUB' in str(data[pattern]):
                            data['price_rub'] = price_value
                        elif 'usd' in pattern or 'USD' in str(data[pattern]) or '$' in str(data[pattern]):
                            data['price_usd'] = price_value
                        elif 'eur' in pattern or 'EUR' in str(data[pattern]) or '€' in str(data[pattern]):
                            data['price_eur'] = price_value
                        else:
                            # Если валюта не определена, сохраняем как есть
                            data[f'{pattern}_value'] = price_value
                        logger.info(f"Найдена цена: {price_value} ({pattern})")
            
            # Обрабатываем даты
            if 'validity_date' in data:
                data['validity_date'] = self._parse_date(data['validity_date'])
            
            # Обрабатываем числовые поля
            numeric_fields = ['transit_time', 'transit_time_days', 'currency_conversion', 'rail_tariff_rub', 
                            'cbx_cost', 'terminal_handling_cost', 'auto_pickup_cost', 
                            'security_cost', 'precarriage_cost', 'weight', 'volume', 'volumetric_weight']
            
            for field in numeric_fields:
                if field in data:
                    parsed_value = self._parse_number(data[field])
                    if parsed_value:
                        data[field] = parsed_value
            
            # Обрабатываем веса и объемы для авиа
            if transport_type == 'air':
                if 'weight' in data:
                    data['weight_kg'] = self._parse_number(data['weight'])
                if 'volume' in data:
                    data['volume_m3'] = self._parse_number(data['volume'])
                if 'volumetric_weight' in data:
                    data['volumetric_weight_kg'] = self._parse_number(data['volumetric_weight'])
            
            return data
            
        except Exception as e:
            logger.error(f"Ошибка обработки специальных случаев: {e}")
            return data
    
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
        if not city:
            return ""
        
        city = city.strip()
        
        # Словарь нормализации
        normalization_map = {
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
        
        city_lower = city.lower()
        return normalization_map.get(city_lower, city)
    
    def _extract_country(self, city: str) -> str:
        """Извлечение страны из названия города"""
        if not city:
            return ""
        
        # Простая логика - можно расширить
        russian_cities = ['москва', 'санкт-петербург', 'новосибирск', 'екатеринбург', 'казань']
        if any(ru_city in city.lower() for ru_city in russian_cities):
            return 'Россия'
        return 'Неизвестно'
    
    def _parse_number(self, value: Any) -> Optional[float]:
        """Парсинг числа"""
        if value is None:
            return None
        
        try:
            if isinstance(value, (int, float)):
                return float(value)
            
            # Убираем пробелы и заменяем запятую на точку
            clean_value = str(value).replace(' ', '').replace(',', '.')
            
            # Убираем лишние точки
            if clean_value.count('.') > 1:
                parts = clean_value.split('.')
                clean_value = ''.join(parts[:-1]) + '.' + parts[-1]
            
            return float(clean_value)
        except (ValueError, TypeError):
            return None
    
    def _parse_date(self, date_str: Any) -> Optional[str]:
        """Парсинг даты"""
        if not date_str:
            return None
        
        try:
            if isinstance(date_str, (date, datetime)):
                return date_str.isoformat()
            
            date_str = str(date_str).strip()
            
            # Пробуем разные форматы
            formats = ['%d.%m.%Y', '%d/%m/%Y', '%d.%m.%y', '%d/%m/%y', '%Y-%m-%d']
            for fmt in formats:
                try:
                    parsed_date = datetime.strptime(date_str, fmt).date()
                    return parsed_date.isoformat()
                except ValueError:
                    continue
            
            return date_str
        except Exception:
            return None
    
    def _validate_parsed_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Валидация распарсенных данных"""
        try:
            validated_data = {}
            
            # Проверяем обязательные поля
            required_fields = self.validation_rules['required_fields']
            for field in required_fields:
                if field in data and data[field]:
                    validated_data[field] = data[field]
                else:
                    logger.warning(f"Отсутствует обязательное поле: {field}")
            
            # Проверяем наличие хотя бы одной цены
            price_fields = self.validation_rules['price_fields']
            has_price = any(field in data and data[field] for field in price_fields)
            if not has_price:
                logger.warning("Не найдена ни одна цена")
            
            # Копируем все остальные поля
            for field, value in data.items():
                if value is not None and value != "":
                    validated_data[field] = value
            
            return validated_data
            
        except Exception as e:
            logger.error(f"Ошибка валидации данных: {e}")
            return data
    
    def save_to_database(self, parsed_data: Dict[str, Any], user_id: int = None) -> Optional[int]:
        """
        Сохранение распарсенных данных в базу данных
        """
        try:
            if not parsed_data.get('success', False):
                logger.error("Нельзя сохранить невалидные данные")
                return None
            
            db = SessionLocal()
            try:
                # Создаем объект тарифа
                tariff = models.Tariff(
                    supplier_id=parsed_data.get('supplier_id'),
                    transport_type=parsed_data.get('transport_type', 'auto'),
                    basis=parsed_data.get('basis', 'EXW'),
                    origin_country=parsed_data.get('origin_country'),
                    origin_city=parsed_data.get('origin_city'),
                    destination_country=parsed_data.get('destination_country'),
                    destination_city=parsed_data.get('destination_city'),
                    vehicle_type=parsed_data.get('vehicle_type'),
                    price_rub=parsed_data.get('price_rub'),
                    price_usd=parsed_data.get('price_usd'),
                    validity_date=parsed_data.get('validity_date'),
                    currency_conversion=parsed_data.get('currency_conversion'),
                    transit_time_days=parsed_data.get('transit_time_days'),
                    source_file=parsed_data.get('source_file'),
                    created_by_user_id=user_id,
                    
                    # Дополнительные поля
                    border_point=parsed_data.get('border_point'),
                    transit_port=parsed_data.get('transit_port'),
                    departure_station=parsed_data.get('departure_station'),
                    arrival_station=parsed_data.get('arrival_station'),
                    rail_tariff_rub=parsed_data.get('rail_tariff_rub'),
                    cbx_cost=parsed_data.get('cbx_cost'),
                    terminal_handling_cost=parsed_data.get('terminal_handling_cost'),
                    auto_pickup_cost=parsed_data.get('auto_pickup_cost'),
                    security_cost=parsed_data.get('security_cost'),
                    precarriage_cost=parsed_data.get('precarriage_cost'),
                )
                
                db.add(tariff)
                db.commit()
                db.refresh(tariff)
                
                logger.info(f"Тариф сохранен в БД с ID: {tariff.id}")
                return tariff.id
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Ошибка сохранения в БД: {e}")
            logger.error(traceback.format_exc())
            return None


# Создаем глобальный экземпляр парсера
intelligent_parser = IntelligentParser()
