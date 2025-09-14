#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Контекстно-зависимый анализатор с ИИ для понимания и извлечения данных из файлов
"""

import re
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

# Локальная LLM библиотека (используем если OpenAI недоступна)
try:
    from transformers import pipeline, AutoTokenizer, AutoModel
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

# OpenAI для более точного анализа
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

@dataclass
class ExtractedRoute:
    """Структура извлеченного маршрута."""
    origin_city: str
    origin_country: str
    destination_city: str
    destination_country: str
    transport_type: str
    price_usd: Optional[float] = None
    price_cny: Optional[float] = None
    price_rub: Optional[float] = None
    transit_time: Optional[int] = None
    basis: str = 'EXW'
    vehicle_type: Optional[str] = None
    container_type: Optional[str] = None
    weight_limit: Optional[str] = None
    additional_costs: Optional[Dict] = None

class ContextAnalyzer:
    """Контекстно-зависимый анализатор с ИИ."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # База знаний городов и стран
        self.city_database = self._load_city_database()
        
        # Паттерны для различных валют
        self.currency_patterns = {
            'usd': [
                r'USD\s*(\d+(?:[\.,]\d+)?)',
                r'(\d+(?:[\.,]\d+)?)\s*USD',
                r'\$\s*(\d+(?:[\.,]\d+)?)',
                r'(\d+(?:[\.,]\d+)?)\s*\$',
                r'(\d+(?:[\.,]\d+)?)\s*долл',
                r'(\d+(?:[\.,]\d+)?)\s*dollar'
            ],
            'cny': [
                r'CNY\s*(\d+(?:[\.,]\d+)?)',
                r'(\d+(?:[\.,]\d+)?)\s*CNY',
                r'RMB\s*(\d+(?:[\.,]\d+)?)',
                r'(\d+(?:[\.,]\d+)?)\s*RMB',
                r'¥\s*(\d+(?:[\.,]\d+)?)',
                r'(\d+(?:[\.,]\d+)?)\s*¥',
                r'(\d+(?:[\.,]\d+)?)\s*юань'
            ],
            'rub': [
                r'RUB\s*(\d+(?:[\.,]\d+)?)',
                r'(\d+(?:[\.,]\d+)?)\s*RUB',
                r'₽\s*(\d+(?:[\.,]\d+)?)',
                r'(\d+(?:[\.,]\d+)?)\s*₽',
                r'(\d+(?:[\.,]\d+)?)\s*руб',
                r'(\d+(?:[\.,]\d+)?)\s*рубл'
            ]
        }
        
        # Паттерны времени в пути
        self.time_patterns = [
            r'(\d+)\s*(?:days?|дней?|дня|day)',
            r'(\d+)\s*(?:часов?|hours?|hrs?|ч\.?)',
            r'время\s*(?:в\s*пути|доставки)[:\s]*(\d+)\s*(?:дней?|days?)',
            r'transit\s*time[:\s]*(\d+)\s*(?:days?|дней?)',
            r'delivery\s*time[:\s]*(\d+)\s*(?:days?|дней?)'
        ]
        
    def _load_city_database(self) -> Dict[str, Dict]:
        """Загружает базу данных городов."""
        return {
            # Китайские города
            'beijing': {'ru': 'Пекин', 'en': 'Beijing', 'country': 'Китай', 'codes': ['PEK', 'BJS']},
            'shanghai': {'ru': 'Шанхай', 'en': 'Shanghai', 'country': 'Китай', 'codes': ['SHA', 'PVG']},
            'guangzhou': {'ru': 'Гуанчжоу', 'en': 'Guangzhou', 'country': 'Китай', 'codes': ['CAN']},
            'shenzhen': {'ru': 'Шэньчжэнь', 'en': 'Shenzhen', 'country': 'Китай', 'codes': ['SZX']},
            'tianjin': {'ru': 'Тяньцзинь', 'en': 'Tianjin', 'country': 'Китай', 'codes': ['TSN']},
            'dalian': {'ru': 'Далянь', 'en': 'Dalian', 'country': 'Китай', 'codes': ['DLC']},
            'qingdao': {'ru': 'Циндао', 'en': 'Qingdao', 'country': 'Китай', 'codes': ['TAO']},
            'ningbo': {'ru': 'Нинбо', 'en': 'Ningbo', 'country': 'Китай', 'codes': ['NGB']},
            'xiamen': {'ru': 'Сямэнь', 'en': 'Xiamen', 'country': 'Китай', 'codes': ['XMN']},
            'yiwu': {'ru': 'Иу', 'en': 'Yiwu', 'country': 'Китай', 'codes': ['YIW']},
            'chengdu': {'ru': 'Чэнду', 'en': 'Chengdu', 'country': 'Китай', 'codes': ['CTU']},
            'xian': {'ru': 'Сиань', 'en': 'Xian', 'country': 'Китай', 'codes': ['XIY']},
            'hangzhou': {'ru': 'Ханчжоу', 'en': 'Hangzhou', 'country': 'Китай', 'codes': ['HGH']},
            'wuhan': {'ru': 'Ухань', 'en': 'Wuhan', 'country': 'Китай', 'codes': ['WUH']},
            'chongqing': {'ru': 'Чунцин', 'en': 'Chongqing', 'country': 'Китай', 'codes': ['CKG']},
            'nanjing': {'ru': 'Нанкин', 'en': 'Nanjing', 'country': 'Китай', 'codes': ['NKG']},
            
            # Российские города
            'moscow': {'ru': 'Москва', 'en': 'Moscow', 'country': 'Россия', 'codes': ['MOS', 'SVO', 'DME']},
            'st.petersburg': {'ru': 'Санкт-Петербург', 'en': 'St.Petersburg', 'country': 'Россия', 'codes': ['SPB', 'LED']},
            'vladivostok': {'ru': 'Владивосток', 'en': 'Vladivostok', 'country': 'Россия', 'codes': ['VVO']},
            'novosibirsk': {'ru': 'Новосибирск', 'en': 'Novosibirsk', 'country': 'Россия', 'codes': ['OVB']},
            'yekaterinburg': {'ru': 'Екатеринбург', 'en': 'Yekaterinburg', 'country': 'Россия', 'codes': ['SVX']},
            'nizhny novgorod': {'ru': 'Нижний Новгород', 'en': 'Nizhny Novgorod', 'country': 'Россия', 'codes': ['GOJ']},
            'kazan': {'ru': 'Казань', 'en': 'Kazan', 'country': 'Россия', 'codes': ['KZN']},
            'rostov': {'ru': 'Ростов-на-Дону', 'en': 'Rostov', 'country': 'Россия', 'codes': ['ROV']},
            'krasnodar': {'ru': 'Краснодар', 'en': 'Krasnodar', 'country': 'Россия', 'codes': ['KRR']},
            'krasnoyarsk': {'ru': 'Красноярск', 'en': 'Krasnoyarsk', 'country': 'Россия', 'codes': ['KJA']},
            'ufa': {'ru': 'Уфа', 'en': 'Ufa', 'country': 'Россия', 'codes': ['UFA']},
            'novorossiysk': {'ru': 'Новороссийск', 'en': 'Novorossiysk', 'country': 'Россия', 'codes': ['NVS']},
            
            # Другие города
            'minsk': {'ru': 'Минск', 'en': 'Minsk', 'country': 'Беларусь', 'codes': ['MSQ']},
            'almaty': {'ru': 'Алматы', 'en': 'Almaty', 'country': 'Казахстан', 'codes': ['ALA']},
            'tashkent': {'ru': 'Ташкент', 'en': 'Tashkent', 'country': 'Узбекистан', 'codes': ['TAS']},
            'hamburg': {'ru': 'Гамбург', 'en': 'Hamburg', 'country': 'Германия', 'codes': ['HAM']},
            'rotterdam': {'ru': 'Роттердам', 'en': 'Rotterdam', 'country': 'Нидерланды', 'codes': ['RTM']},
        }
    
    def analyze_with_context(self, text: str, file_path: str = '') -> Dict[str, Any]:
        """Основная функция анализа с пониманием контекста."""
        try:
            # 1. Определяем тип документа и транспорта
            doc_context = self._analyze_document_context(text, file_path)
            
            # 2. Извлекаем структурированные данные
            extracted_data = self._extract_structured_data(text, doc_context)
            
            # 3. Постобработка и валидация
            validated_data = self._validate_and_clean_data(extracted_data, doc_context)
            
            return validated_data
            
        except Exception as e:
            self.logger.error(f"Ошибка анализа контекста: {e}")
            return self._fallback_analysis(text)
    
    def _analyze_document_context(self, text: str, file_path: str) -> Dict[str, Any]:
        """Анализирует контекст документа для понимания его типа."""
        context = {
            'transport_type': 'auto',  # по умолчанию
            'document_type': 'tariff',
            'language': 'mixed',
            'structure_type': 'unknown',
            'confidence': 0.0
        }
        
        text_lower = text.lower()
        
        # Определяем тип транспорта по ключевым словам и контексту
        transport_indicators = {
            'air': ['air', 'авиа', 'aircraft', 'airport', 'cargo', 'freight', 'aviation', 'flight', '✈', 'airway'],
            'sea': ['sea', 'море', 'морской', 'ship', 'port', 'fcl', 'lcl', 'container', '20ft', '40ft', 'vessel', 'ocean'],
            'rail': ['rail', 'жд', 'железнодорожный', 'railway', 'train', 'вагон', 'контейнер', 'станция', 'station'],
            'auto': ['truck', 'авто', 'автомобильный', 'ftl', 'ltl', 'грузовик', 'машина', 'дорога', 'highway'],
            'multimodal': ['мульти', 'multi', 'multimodal', 'комбинированный', 'combined', 'mixed']
        }
        
        # Подсчитываем вхождения для каждого типа
        scores = {}
        for transport, keywords in transport_indicators.items():
            score = sum(text_lower.count(keyword) for keyword in keywords)
            # Бонус за упоминание в названии файла
            if any(keyword in file_path.lower() for keyword in keywords):
                score += 10
            scores[transport] = score
        
        # Выбираем тип с наибольшим счетом
        if max(scores.values()) > 0:
            context['transport_type'] = max(scores, key=scores.get)
            context['confidence'] = min(max(scores.values()) / 10, 1.0)
        
        # Определяем структуру документа
        if '|' in text and text.count('|') > 5:
            context['structure_type'] = 'tabular'
        elif re.search(r'\d+\.\s+.*?\s+.*?\s+\d+', text):
            context['structure_type'] = 'numbered_list'
        elif re.search(r'[А-Я][а-я]+\s*[-–→]\s*[А-Я][а-я]+', text):
            context['structure_type'] = 'route_list'
        else:
            context['structure_type'] = 'free_text'
        
        return context
    
    def _extract_structured_data(self, text: str, context: Dict) -> Dict[str, Any]:
        """Извлекает структурированные данные с учетом контекста."""
        routes = []
        
        # Выбираем стратегию извлечения в зависимости от структуры
        if context['structure_type'] == 'tabular':
            routes = self._extract_from_table(text, context)
        elif context['structure_type'] == 'numbered_list':
            routes = self._extract_from_numbered_list(text, context)
        elif context['structure_type'] == 'route_list':
            routes = self._extract_from_route_list(text, context)
        else:
            routes = self._extract_from_free_text(text, context)
        
        # Извлекаем дополнительную информацию
        basis = self._extract_basis(text)
        additional_costs = self._extract_additional_costs(text)
        
        return {
            'routes': routes,
            'transport_type': context['transport_type'],
            'basis': basis,
            'additional_costs': additional_costs,
            'context': context
        }
    
    def _extract_from_table(self, text: str, context: Dict) -> List[ExtractedRoute]:
        """Извлекает данные из табличной структуры."""
        routes = []
        lines = text.split('\n')
        
        for line in lines:
            if '|' not in line or len(line.strip()) < 5:
                continue
            
            # Разбиваем строку по разделителям
            parts = [part.strip() for part in line.split('|')]
            
            if len(parts) < 2:
                continue
            
            # Ищем города в первых двух колонках
            origin_city = self._extract_city_from_text(parts[0])
            destination_city = self._extract_city_from_text(parts[1])
            
            if origin_city and destination_city:
                # Извлекаем цены из остальных колонок
                prices = self._extract_prices_from_parts(parts[2:])
                
                route = ExtractedRoute(
                    origin_city=origin_city,
                    origin_country=self._get_country_by_city(origin_city),
                    destination_city=destination_city,
                    destination_country=self._get_country_by_city(destination_city),
                    transport_type=context['transport_type'],
                    price_usd=prices.get('usd'),
                    price_cny=prices.get('cny'),
                    price_rub=prices.get('rub'),
                    transit_time=self._extract_transit_time_from_text(line),
                    basis='EXW',
                    vehicle_type='Тент 20т 82м3'
                )
                
                routes.append(route)
        
        return routes
    
    def _extract_from_numbered_list(self, text: str, context: Dict) -> List[ExtractedRoute]:
        """Извлекает данные из нумерованного списка."""
        routes = []
        
        # Паттерн для нумерованных списков
        pattern = r'\d+\.\s*([^:]+):\s*([^:]+):\s*(\d+(?:[\.,]\d+)?)\s*(USD|CNY|RMB|RUB)'
        matches = re.finditer(pattern, text, re.IGNORECASE)
        
        for match in matches:
            origin_city = self._clean_city_name(match.group(1))
            destination_city = self._clean_city_name(match.group(2))
            
            if origin_city and destination_city:
                try:
                    price_value = float(match.group(3).replace(',', '.'))
                    currency = match.group(4).upper()
                    
                    price_usd = price_value if currency in ['USD'] else None
                    price_cny = price_value if currency in ['CNY', 'RMB'] else None
                    price_rub = price_value if currency in ['RUB'] else None
                    
                    route = ExtractedRoute(
                        origin_city=origin_city,
                        origin_country=self._get_country_by_city(origin_city),
                        destination_city=destination_city,
                        destination_country=self._get_country_by_city(destination_city),
                        transport_type=context['transport_type'],
                        price_usd=price_usd,
                        price_cny=price_cny,
                        price_rub=price_rub,
                        transit_time=self._extract_transit_time_from_text(match.group(0)),
                        basis='EXW',
                        vehicle_type='Тент 20т 82м3'
                    )
                    
                    routes.append(route)
                except ValueError:
                    continue
        
        return routes
    
    def _extract_from_route_list(self, text: str, context: Dict) -> List[ExtractedRoute]:
        """Извлекает данные из списка маршрутов."""
        routes = []
        
        # Паттерн для списков маршрутов
        pattern = r'([А-Я][а-я]+(?:\s*[А-Я][а-я]+)*)\s*[-–→]\s*([А-Я][а-я]+(?:\s*[А-Я][а-я]+)*)'
        matches = re.finditer(pattern, text, re.IGNORECASE)
        
        for match in matches:
            origin_city = self._clean_city_name(match.group(1))
            destination_city = self._clean_city_name(match.group(2))
            
            if origin_city and destination_city:
                # Ищем цены рядом с маршрутом
                prices = self._extract_prices_near_text(text, match.start(), match.end())
                
                route = ExtractedRoute(
                    origin_city=origin_city,
                    origin_country=self._get_country_by_city(origin_city),
                    destination_city=destination_city,
                    destination_country=self._get_country_by_city(destination_city),
                    transport_type=context['transport_type'],
                    price_usd=prices.get('usd'),
                    price_cny=prices.get('cny'),
                    price_rub=prices.get('rub'),
                    transit_time=self._extract_transit_time_near_text(text, match.start(), match.end()),
                    basis='EXW',
                    vehicle_type='Тент 20т 82м3'
                )
                
                routes.append(route)
        
        return routes
    
    def _extract_from_free_text(self, text: str, context: Dict) -> List[ExtractedRoute]:
        """Извлекает данные из свободного текста с улучшенной логикой."""
        routes = []
        text_lower = text.lower()
        
        # Улучшенные паттерны для авто файлов
        auto_patterns = [
            # Паттерн: EXW Город/Город - Город - $Цена per truck
            r'EXW\s+([^/]+)/([^-]+)\s*-\s*([^-]+)\s*-\s*\$(\d+(?:[\.,]\d+)?)\s*per\s*truck',
            # Паттерн: Город -> Город: Цена
            r'([А-Я][а-я]+(?:\s*[А-Я][а-я]+)*)\s*[-–→]\s*([А-Я][а-я]+(?:\s*[А-Я][а-я]+)*)\s*[:=]\s*(\d+(?:[\.,]\d+)?)\s*(USD|CNY|RMB|RUB)',
            # Паттерн: Город (Китай) -> Город (Россия)
            r'([А-Я][а-я]+(?:\s*[А-Я][а-я]+)*)\s*\([Кк]итай\)\s*[-–→]\s*([А-Я][а-я]+(?:\s*[А-Я][а-я]+)*)\s*\([Рр]оссия\)',
            # Паттерн: Город - Город
            r'([А-Я][a-я]+(?:\s*[А-Я][а-я]+)*)\s*[-–]\s*([А-Я][а-я]+(?:\s*[А-Я][а-я]+)*)',
            # Паттерн: Город → Город
            r'([А-Я][а-я]+(?:\s*[А-Я][а-я]+)*)\s*→\s*([А-Я][а-я]+(?:\s*[А-Я][а-я]+)*)',
        ]
        
        # Ищем маршруты по паттернам
        for pattern in auto_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                # Обрабатываем разные форматы паттернов
                if 'EXW' in pattern:
                    # Паттерн EXW: origin1/origin2 - destination - $price
                    origin1 = match.group(1).strip()
                    origin2 = match.group(2).strip()
                    destination = match.group(3).strip()
                    price_value = float(match.group(4).replace(',', '.'))
                    
                    # Создаем маршруты для каждого города отправления
                    for origin in [origin1, origin2]:
                        origin_city = self._clean_city_name(origin)
                        destination_city = self._clean_city_name(destination)
                        
                        if self._is_valid_city(origin_city) and self._is_valid_city(destination_city):
                            route = ExtractedRoute(
                                origin_city=origin_city,
                                origin_country=self._get_country_by_city(origin_city),
                                destination_city=destination_city,
                                destination_country=self._get_country_by_city(destination_city),
                                transport_type=context['transport_type'],
                                price_usd=price_value,
                                transit_time=self._extract_transit_time_from_text(text),
                                basis='EXW',
                                vehicle_type='Тент 20т 82м3'
                            )
                            routes.append(route)
                else:
                    # Обычные паттерны
                    origin_city = match.group(1).strip()
                    destination_city = match.group(2).strip()
                    
                    # Очищаем названия городов
                    origin_city = self._clean_city_name(origin_city)
                    destination_city = self._clean_city_name(destination_city)
                    
                    # Пропускаем невалидные города
                    if not self._is_valid_city(origin_city) or not self._is_valid_city(destination_city):
                        continue
                    
                    # Определяем страны
                    origin_country = self._get_country_by_city(origin_city)
                    destination_country = self._get_country_by_city(destination_city)
                    
                    # Извлекаем цену из группы 3 (если есть)
                    price_usd = None
                    price_cny = None
                    price_rub = None
                    
                    if len(match.groups()) >= 3 and match.group(3):
                        try:
                            price_value = float(match.group(3).replace(',', '.'))
                            currency = match.group(4) if len(match.groups()) >= 4 else 'USD'
                            
                            if currency.upper() in ['USD', '$']:
                                price_usd = price_value
                            elif currency.upper() in ['CNY', 'RMB', '¥']:
                                price_cny = price_value
                            elif currency.upper() in ['RUB', '₽']:
                                price_rub = price_value
                        except (ValueError, IndexError):
                            pass
                    
                    # Если цена не найдена в паттерне, ищем рядом
                    if not any([price_usd, price_cny, price_rub]):
                        prices = self._extract_prices_near_text(text, match.start(), match.end())
                        price_usd = prices.get('usd')
                        price_cny = prices.get('cny')
                        price_rub = prices.get('rub')
                    
                    # Извлекаем время в пути
                    transit_time = self._extract_transit_time_near_text(text, match.start(), match.end())
                    
                    route = ExtractedRoute(
                        origin_city=origin_city,
                        origin_country=origin_country,
                        destination_city=destination_city,
                        destination_country=destination_country,
                        transport_type=context['transport_type'],
                        price_usd=price_usd,
                        price_cny=price_cny,
                        price_rub=price_rub,
                        transit_time=transit_time,
                        basis='EXW',
                        vehicle_type='Тент 20т 82м3'
                    )
                    
                    routes.append(route)
        
        # Если паттерны не сработали, используем поиск по ключевым словам
        if not routes:
            routes = self._extract_by_keywords(text, context)
        
        # Убираем дубликаты
        unique_routes = []
        seen = set()
        for route in routes:
            key = (route.origin_city, route.destination_city)
            if key not in seen:
                seen.add(key)
                unique_routes.append(route)
        
        return unique_routes
    
    def _clean_city_name(self, city: str) -> str:
        """Очищает название города от лишних символов."""
        if not city:
            return ""
        
        # Удаляем технические термины
        skip_words = [
            'factory', 'destination', 'without', 'reloading', 'please', 'recheck', 
            'case', 'above', 'quotation', 'assumed', 'carriage', 'costs', 'overweight',
            'tarpaulin', 'truck', 'ce', 'pol', 'pod', 'fcl', 'ltl', 'ftl', 'sea', 'air',
            'rail', 'auto', 'морской', 'авиа', 'жд', 'авто', 'port', 'terminal', '05', 'com'
        ]
        
        city_lower = city.lower()
        for word in skip_words:
            if word in city_lower:
                return ""
        
        # Удаляем лишние символы
        city = re.sub(r'[^\w\s\-\.]', '', city)
        city = re.sub(r'\s+', ' ', city).strip()
        
        # Пропускаем слишком короткие или длинные названия
        if len(city) < 2 or len(city) > 50:
            return ""
        
        return city
    
    def _is_valid_city(self, city: str) -> bool:
        """Проверяет, является ли строка валидным названием города."""
        if not city or len(city) < 2:
            return False
        
        # Пропускаем числа
        if city.isdigit():
            return False
        
        # Пропускаем технические термины
        invalid_terms = [
            'factory', 'destination', 'without', 'reloading', 'please', 'recheck',
            'case', 'above', 'quotation', 'assumed', 'carriage', 'costs', 'overweight',
            'tarpaulin', 'truck', 'ce', 'pol', 'pod', 'fcl', 'ltl', 'ftl', 'sea', 'air',
            'rail', 'auto', 'морской', 'авиа', 'жд', 'авто', 'port', 'terminal', '05', 'com'
        ]
        
        city_lower = city.lower()
        for term in invalid_terms:
            if term in city_lower:
                return False
        
        return True
    
    def _extract_prices_near_text(self, text: str, start_pos: int, end_pos: int) -> Dict[str, float]:
        """Извлекает цены рядом с найденным текстом."""
        prices = {}
        
        # Ищем в радиусе 200 символов
        search_start = max(0, start_pos - 200)
        search_end = min(len(text), end_pos + 200)
        search_text = text[search_start:search_end]
        
        for currency, patterns in self.currency_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, search_text, re.IGNORECASE)
                for match in matches:
                    try:
                        price = float(match.group(1).replace(',', '.'))
                        if currency == 'usd':
                            prices['usd'] = price
                        elif currency == 'cny':
                            prices['cny'] = price
                        elif currency == 'rub':
                            prices['rub'] = price
                    except ValueError:
                        continue
        
        return prices
    
    def _extract_transit_time_near_text(self, text: str, start_pos: int, end_pos: int) -> Optional[int]:
        """Извлекает время в пути рядом с найденным текстом."""
        search_start = max(0, start_pos - 200)
        search_end = min(len(text), end_pos + 200)
        search_text = text[search_start:search_end]
        
        for pattern in self.time_patterns:
            match = re.search(pattern, search_text, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue
        
        return None
    
    def _extract_by_keywords(self, text: str, context: Dict) -> List[ExtractedRoute]:
        """Извлекает маршруты по ключевым словам."""
        routes = []
        
        # Китайские города
        chinese_cities = [
            'гуанчжоу', 'guangzhou', 'шанхай', 'shanghai', 'пекин', 'beijing',
            'шенчжень', 'shenzhen', 'тяньцзинь', 'tianjin', 'далянь', 'dalian',
            'циндао', 'qingdao', 'нинбо', 'ningbo', 'сиань', 'xian', 'чунцин', 'chongqing',
            'ханчжоу', 'hangzhou', 'ухань', 'wuhan', 'нанкин', 'nanjing', 'сямэнь', 'xiamen',
            'иу', 'yiwu', 'гонконг', 'hong kong', 'макао', 'macau'
        ]
        
        # Российские города
        russian_cities = [
            'москва', 'moscow', 'санкт-петербург', 'st. petersburg', 'владивосток', 'vladivostok',
            'краснодар', 'krasnodar', 'ростов-на-дону', 'rostov', 'екатеринбург', 'yekaterinburg',
            'новосибирск', 'novosibirsk', 'красноярск', 'krasnoyarsk', 'уфа', 'казань', 'kazan'
        ]
        
        # Белорусские города
        belarus_cities = [
            'минск', 'minsk'
        ]
        
        text_lower = text.lower()
        
        # Ищем китайские города
        found_chinese = []
        for city in chinese_cities:
            if city in text_lower:
                found_chinese.append(city)
        
        # Ищем российские города
        found_russian = []
        for city in russian_cities:
            if city in text_lower:
                found_russian.append(city)
        
        # Ищем белорусские города
        found_belarus = []
        for city in belarus_cities:
            if city in text_lower:
                found_belarus.append(city)
        
        # Ограничиваем количество городов для избежания слишком многих маршрутов
        found_chinese = found_chinese[:2]  # Максимум 2 китайских города
        found_russian = found_russian[:2]  # Максимум 2 российских города
        found_belarus = found_belarus[:2]  # Максимум 2 белорусских города
        
        # Создаем маршруты только если найдены города
        if found_chinese and (found_russian or found_belarus):
            # Извлекаем цены из текста
            prices = self._extract_prices_from_text(text)
            transit_time = self._extract_transit_time_from_text(text)
            
            # Создаем маршруты с первыми найденными городами
            chinese_city = found_chinese[0]
            
            # Создаем маршруты для российских городов
            for russian_city in found_russian:
                # Очищаем названия городов
                clean_chinese = self._clean_city_name(chinese_city)
                clean_russian = self._clean_city_name(russian_city)
                
                if clean_chinese and clean_russian:
                    route = ExtractedRoute(
                        origin_city=clean_chinese,
                        origin_country='Китай',
                        destination_city=clean_russian,
                        destination_country='Россия',
                        transport_type=context['transport_type'],
                        price_usd=prices.get('usd'),
                        price_cny=prices.get('cny'),
                        price_rub=prices.get('rub'),
                        transit_time=transit_time,
                        basis='EXW',
                        vehicle_type='Тент 20т 82м3'
                    )
                    
                    routes.append(route)
            
            # Создаем маршруты для белорусских городов
            for belarus_city in found_belarus:
                # Очищаем названия городов
                clean_chinese = self._clean_city_name(chinese_city)
                clean_belarus = self._clean_city_name(belarus_city)
                
                if clean_chinese and clean_belarus:
                    route = ExtractedRoute(
                        origin_city=clean_chinese,
                        origin_country='Китай',
                        destination_city=clean_belarus,
                        destination_country='Беларусь',
                        transport_type=context['transport_type'],
                        price_usd=prices.get('usd'),
                        price_cny=prices.get('cny'),
                        price_rub=prices.get('rub'),
                        transit_time=transit_time,
                        basis='EXW',
                        vehicle_type='Тент 20т 82м3'
                    )
                    
                    routes.append(route)
        
        return routes
    
    def _extract_prices_from_text(self, text: str) -> Dict[str, float]:
        """Извлекает все цены из текста."""
        prices = {}
        
        for currency, patterns in self.currency_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    try:
                        price = float(match.group(1).replace(',', '.'))
                        # Берем самую большую цену для каждой валюты
                        if currency == 'usd':
                            if 'usd' not in prices or price > prices['usd']:
                                prices['usd'] = price
                        elif currency == 'cny':
                            if 'cny' not in prices or price > prices['cny']:
                                prices['cny'] = price
                        elif currency == 'rub':
                            if 'rub' not in prices or price > prices['rub']:
                                prices['rub'] = price
                    except ValueError:
                        continue
        
        return prices
    
    def _extract_transit_time_from_text(self, text: str) -> Optional[int]:
        """Извлекает время в пути из текста."""
        for pattern in self.time_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue
        
        return None
    
    def _extract_city_info(self, text: str) -> Optional[Dict[str, str]]:
        """Извлекает информацию о городе из текста."""
        if not text or len(text.strip()) < 2:
            return None
        
        text = text.strip().lower()
        
        # Удаляем лишние символы и слова
        text = re.sub(r'[^\w\s\-\.]', ' ', text)
        text = re.sub(r'\b(truck|transportation|from|to|port|terminal|station)\b', '', text)
        text = ' '.join(text.split())
        
        if len(text) < 2:
            return None
        
        # Ищем в базе данных городов
        for city_key, city_data in self.city_database.items():
            if (city_key in text or 
                city_data['ru'].lower() in text or 
                city_data['en'].lower() in text or
                any(code.lower() in text for code in city_data['codes'])):
                return {
                    'city': city_data['ru'],
                    'country': city_data['country']
                }
        
        # Если не нашли в базе, возвращаем как есть
        if len(text) > 2 and not text.isdigit():
            return {
                'city': text.title(),
                'country': 'Неизвестно'
            }
        
        return None
    
    def _extract_basis(self, text: str) -> str:
        """Извлекает базис поставки."""
        basis_patterns = {
            'EXW': r'\bEXW\b',
            'FOB': r'\bFOB\b',
            'CIF': r'\bCIF\b',
            'DAP': r'\bDAP\b',
            'DDP': r'\bDDP\b'
        }
        
        text_upper = text.upper()
        for basis, pattern in basis_patterns.items():
            if re.search(pattern, text_upper):
                return basis
        
        return 'EXW'  # По умолчанию
    
    def _extract_additional_costs(self, text: str) -> Dict[str, Optional[float]]:
        """Извлекает дополнительные расходы."""
        costs = {}
        
        cost_patterns = {
            'parking': r'(?:parking|стоянка|парковка)[:\s]*(\d+(?:[\.,]\d+)?)',
            'handling': r'(?:handling|обработка|перегрузка)[:\s]*(\d+(?:[\.,]\d+)?)',
            'declaration': r'(?:declaration|декларирование|таможня)[:\s]*(\d+(?:[\.,]\d+)?)',
            'registration': r'(?:registration|регистрация|оформление)[:\s]*(\d+(?:[\.,]\d+)?)'
        }
        
        for cost_type, pattern in cost_patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    cost = float(match.group(1).replace(',', '.'))
                    costs[cost_type] = cost
                except ValueError:
                    continue
        
        return costs
    
    def _validate_and_clean_data(self, data: Dict, context: Dict) -> Dict[str, Any]:
        """Валидирует и очищает извлеченные данные."""
        validated_routes = []
        
        for route in data.get('routes', []):
            # Пропускаем маршруты с одинаковыми городами
            if route.origin_city == route.destination_city:
                continue
            
            # Пропускаем маршруты с недостоверными данными
            if (len(route.origin_city) < 2 or len(route.destination_city) < 2 or
                route.origin_city.isdigit() or route.destination_city.isdigit()):
                continue
            
            # Пропускаем технические термины и мусор
            skip_terms = [
                'pol', 'pod', '20gp', '40gp', 'kg', 'min', 'usd', 'bl', 'fee', 'set', 'pick',
                'gate', 'handling', 'declaration', 'registration', 'parking', 'cases', 'shpt',
                'price', 'case', 'by', 'car', 'sd', 'if', 'nee', 'occurs', 'igkong', 'hongkon'
            ]
            
            origin_lower = route.origin_city.lower()
            dest_lower = route.destination_city.lower()
            
            # Если название города содержит много технических терминов, пропускаем
            origin_terms = sum(1 for term in skip_terms if term in origin_lower)
            dest_terms = sum(1 for term in skip_terms if term in dest_lower)
            
            if origin_terms > 2 or dest_terms > 2:
                continue
            
            # Пропускаем слишком длинные "города" (вероятно, это текст)
            if len(route.origin_city) > 50 or len(route.destination_city) > 50:
                continue
            
            # Конвертируем в словарь для API
            validated_route = {
                'origin_city': route.origin_city,
                'origin_country': route.origin_country,
                'destination_city': route.destination_city,
                'destination_country': route.destination_country,
                'transport_type': route.transport_type,
                'basis': route.basis,
                'price_usd': route.price_usd,
                'price_cny': route.price_cny,
                'price_rub': route.price_rub,
                'transit_time': route.transit_time,
                'vehicle_type': route.vehicle_type,
                'container_type': route.container_type,
                'weight_limit': route.weight_limit
            }
            
            validated_routes.append(validated_route)
        
        return {
            'routes': validated_routes,
            'transport_type': data['transport_type'],
            'basis': data['basis'],
            'additional_costs': data.get('additional_costs', {}),
            'context_confidence': context.get('confidence', 0.0),
            'structure_type': context.get('structure_type', 'unknown')
        }
    
    def _fallback_analysis(self, text: str) -> Dict[str, Any]:
        """Резервный анализ в случае ошибки."""
        return {
            'routes': [],
            'transport_type': 'auto',
            'basis': 'EXW',
            'additional_costs': {},
            'context_confidence': 0.0,
            'structure_type': 'unknown',
            'error': 'Fallback analysis used'
        }

    def _get_country_by_city(self, city: str) -> str:
        """Определяет страну по названию города."""
        if not city:
            return "Неизвестно"
        
        city_lower = city.lower()
        
        # Китайские города
        chinese_cities = [
            'гуанчжоу', 'guangzhou', 'шанхай', 'shanghai', 'пекин', 'beijing',
            'шенчжень', 'shenzhen', 'тяньцзинь', 'tianjin', 'далянь', 'dalian',
            'циндао', 'qingdao', 'нинбо', 'ningbo', 'сиань', 'xian', 'чунцин', 'chongqing',
            'ханчжоу', 'hangzhou', 'ухань', 'wuhan', 'нанкин', 'nanjing', 'сямэнь', 'xiamen',
            'иу', 'yiwu', 'гонконг', 'hong kong', 'макао', 'macau'
        ]
        
        # Российские города
        russian_cities = [
            'москва', 'moscow', 'санкт-петербург', 'st. petersburg', 'владивосток', 'vladivostok',
            'краснодар', 'krasnodar', 'ростов-на-дону', 'rostov', 'екатеринбург', 'yekaterinburg',
            'новосибирск', 'novosibirsk', 'красноярск', 'krasnoyarsk', 'уфа', 'казань', 'kazan'
        ]
        
        # Белорусские города
        belarus_cities = [
            'минск', 'minsk'
        ]
        
        if city_lower in chinese_cities:
            return "Китай"
        elif city_lower in russian_cities:
            return "Россия"
        elif city_lower in belarus_cities:
            return "Беларусь"
        else:
            return "Неизвестно"
    
    def _extract_city_from_text(self, text: str) -> Optional[str]:
        """Извлекает название города из текста."""
        if not text:
            return None
        
        # Очищаем текст от лишних символов
        text = re.sub(r'[^\w\s\-\.]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Проверяем, является ли это валидным городом
        if self._is_valid_city(text):
            return text
        
        return None
    
    def _extract_prices_from_parts(self, parts: List[str]) -> Dict[str, float]:
        """Извлекает цены из частей текста."""
        prices = {}
        
        for part in parts:
            for currency, patterns in self.currency_patterns.items():
                for pattern in patterns:
                    match = re.search(pattern, part, re.IGNORECASE)
                    if match:
                        try:
                            price = float(match.group(1).replace(',', '.'))
                            if currency == 'usd':
                                prices['usd'] = price
                            elif currency == 'cny':
                                prices['cny'] = price
                            elif currency == 'rub':
                                prices['rub'] = price
                        except ValueError:
                            continue
        
        return prices

def analyze_with_context(text: str, file_path: str = '') -> Dict[str, Any]:
    """Основная функция для анализа с контекстом."""
    analyzer = ContextAnalyzer()
    return analyzer.analyze_with_context(text, file_path)
