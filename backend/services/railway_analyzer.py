#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Специализированный анализатор для железнодорожных тарифов
"""

import re
from typing import Dict, List, Optional, Any
from .adaptive_analyzer import analyze_tariff_text_adaptive

class RailwayAnalyzer:
    """Специализированный анализатор для железнодорожных тарифов."""
    
    def __init__(self):
        # Специфичные для ЖД паттерны
        self.railway_patterns = {
            'stations': [
                r'станция\s+([А-Я][а-я]+)',
                r'ст\.\s*([А-Я][а-я]+)',
                r'([А-Я][а-я]+)\s*станция',
                r'([А-Я][а-я]+)\s*ст\.',
            ],
            'routes': [
                r'([А-Я][а-я]+)\s*[-→]\s*([А-Я][а-я]+)',
                r'([А-Я][а-я]+)\s*TO\s*([А-Я][а-я]+)',
                r'([А-Я][а-я]+)\s*-\s*([А-Я][а-я]+)',
                r'([A-Z][a-z]+)\s*[-→]\s*([A-Z][a-z]+)',
                r'([A-Z][a-z]+)\s*TO\s*([A-Z][a-z]+)',
            ],
            'prices': [
                r'(\d+)\s*USD',
                r'(\d+)\s*RUB',
                r'(\d+)\s*₽',
                r'USD\s*(\d+)',
                r'RUB\s*(\d+)',
                r'₽\s*(\d+)',
                r'(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)',
                r'(\d+)\s*(\d+)\s*(\d+)',
            ],
            'containers': [
                r'20\s*DC',
                r'40\s*HC',
                r'20\s*фут',
                r'40\s*фут',
                r'20\s*GP',
                r'40\s*GP',
            ]
        }
        
        # Расширенная база городов и станций
        self.railway_stations = {
            'Москва': ['Электроугли', 'Купавна', 'Белый Раст', 'Люберцы', 'Селятино', 'Selyatino', 'Elektrougli', 'Bely Rast'],
            'Санкт-Петербург': ['Шушары', 'Ховрино', 'Заневский пост'],
            'Екатеринбург': ['Товарный', 'Звезда'],
            'Новосибирск': ['Клещиха', 'Иня', 'Чемской', 'Главный'],
            'Красноярск': ['Базаиха'],
            'Ростов': ['Товарный', 'Ростов-на-Дону'],
            'Владивосток': ['Коммерческий', 'Рыбный порт'],
            'Находка': ['Восточный порт'],
            'Шанхай': ['Shanghai', 'SHANGHAI'],
            'Гуанчжоу': ['Guangzhou', 'GUANGZHOU'],
            'Шэньчжэнь': ['Shenzhen', 'SHENZHEN'],
            'Нинбо': ['Ningbo', 'NINGBO'],
            'Тяньцзинь': ['Tianjin', 'TIANJIN'],
            'Циндао': ['Qingdao', 'QINGDAO'],
            'Далянь': ['Dalian', 'DALIAN'],
            'Пекин': ['Beijing', 'BEIJING'],
            'Чунцин': ['Chongqing', 'CHONGQING'],
            'Чэнду': ['Chengdu', 'CHENGDU'],
            'Сиань': ['Xian', 'XI\'AN', 'XIAN'],
            'Чжэнчжоу': ['Zhengzhou', 'ZHENGZHOU'],
            'Хэфэй': ['Hefei', 'HEFEI'],
            'Вэньчжоу': ['Wenzhou', 'WENZHOU'],
            'Вэйфан': ['Weifang', 'WEIFANG'],
            'Вэйхай': ['Weihai', 'WEIHAI'],
            'Сямэнь': ['Xiamen', 'XIAMEN'],
            'Сучжоу': ['Suzhou', 'SUZHOU'],
            'Шицзячжуан': ['Shijiazhuang', 'SHIJIAZHUANG'],
            'Датянь': ['Datian', 'DATIAN'],
            'Чанша': ['Changsha', 'CHANGSHA'],
            'Цзэнчэн': ['Zengcheng', 'ZENGCHENG', 'Zengchengxi'],
            'Шэньян': ['Shenyang', 'SHENYANG'],
            'Датун': ['Datong', 'DATONG'],
            'Цзяочжоу': ['Jiaozhou', 'JIAOZHOU'],
            'Цзинань': ['Jinan', 'JINAN'],
            'Цзыбо': ['Zibo', 'ZIBO'],
            'Дэцин': ['Deqing', 'DEQING'],
            'Уцзян': ['Wujiang', 'WUJIANG']
        }
        
        # Границы и переходы
        self.borders = {
            'Эрлянь': ['Erlian', 'ERLIAN', 'Eelian'],
            'Алашанькоу': ['Alashankou', 'ALASHANKOU'],
            'Хоргос': ['Khorgos', 'KHORGOS']
        }
    
    def extract_railway_routes(self, text: str) -> List[Dict]:
        """Извлекает железнодорожные маршруты."""
        routes = []
        
        # Обрабатываем табличные данные
        lines = text.split('\n')
        for line in lines:
            if '|' in line:
                # Табличная строка
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 3:
                    # Ищем города в первых колонках
                    origin = self._extract_city_from_text(parts[0])
                    destination = self._extract_city_from_text(parts[1])
                    
                    if origin and destination and origin != destination:
                        # Ищем цены в остальных колонках
                        prices = self._extract_prices_from_parts(parts[2:])
                        
                        route = {
                            'origin_city': origin,
                            'origin_country': self._get_country_by_city(origin),
                            'destination_city': destination,
                            'destination_country': self._get_country_by_city(destination),
                            'transport_type': 'rail',
                            'price_usd': prices.get('usd'),
                            'price_rub': prices.get('rub'),
                            'container_type': self._extract_container_type(line)
                        }
                        routes.append(route)
        
        # Обрабатываем текстовые маршруты
        for pattern in self.railway_patterns['routes']:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                origin = match.group(1).strip()
                destination = match.group(2).strip()
                
                if origin and destination and origin != destination:
                    # Нормализуем названия городов
                    origin = self._normalize_city_name(origin)
                    destination = self._normalize_city_name(destination)
                    
                    if origin and destination and origin != destination:
                        route = {
                            'origin_city': origin,
                            'origin_country': self._get_country_by_city(origin),
                            'destination_city': destination,
                            'destination_country': self._get_country_by_city(destination),
                            'transport_type': 'rail',
                            'price_usd': None,
                            'price_rub': None,
                            'container_type': None
                        }
                        routes.append(route)
        
        return routes[:10]  # Ограничиваем количество
    
    def _normalize_city_name(self, city: str) -> Optional[str]:
        """Нормализует название города."""
        if not city or city.strip() == '':
            return None
        
        city = city.strip()
        
        # Проверяем известные города
        for normalized_city, variants in self.railway_stations.items():
            if city.lower() in [v.lower() for v in variants] or city.lower() == normalized_city.lower():
                return normalized_city
        
        # Проверяем границы
        for border, variants in self.borders.items():
            if city.lower() in [v.lower() for v in variants] or city.lower() == border.lower():
                return border
        
        # Если не нашли, возвращаем как есть (если это похоже на город)
        if len(city) > 2 and not city.isdigit() and not city.lower() in ['loading', 'departure', 'destination', 'station', 'place', 'location', 'door', 'to', 'from', 'via', 'border']:
            return city
        
        return None
    
    def _extract_city_from_text(self, text: str) -> Optional[str]:
        """Извлекает название города из текста."""
        if not text or text.strip() == '':
            return None
        
        text = text.strip()
        
        # Проверяем известные города
        for city in self.railway_stations.keys():
            if city.lower() in text.lower():
                return city
        
        # Проверяем станции
        for city, stations in self.railway_stations.items():
            for station in stations:
                if station.lower() in text.lower():
                    return city
        
        # Если не нашли, возвращаем как есть (если это похоже на город)
        if len(text) > 2 and not text.isdigit():
            return text
        
        return None
    
    def _extract_prices_from_parts(self, parts: List[str]) -> Dict:
        """Извлекает цены из частей строки."""
        prices = {'usd': None, 'rub': None}
        
        for part in parts:
            part = part.strip()
            if not part:
                continue
            
            # Ищем USD
            usd_match = re.search(r'(\d+)\s*USD', part, re.IGNORECASE)
            if usd_match:
                prices['usd'] = float(usd_match.group(1))
            
            # Ищем RUB
            rub_match = re.search(r'(\d+)\s*RUB', part, re.IGNORECASE)
            if rub_match:
                prices['rub'] = float(rub_match.group(1))
            
            # Ищем ₽
            rub_symbol_match = re.search(r'(\d+)\s*₽', part)
            if rub_symbol_match:
                prices['rub'] = float(rub_symbol_match.group(1))
            
            # Если это просто число, предполагаем RUB
            if part.isdigit() and not prices['rub']:
                prices['rub'] = float(part)
        
        return prices
    
    def _extract_container_type(self, text: str) -> Optional[str]:
        """Извлекает тип контейнера."""
        for pattern in self.railway_patterns['containers']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0).strip()
        return None
    
    def _get_country_by_city(self, city: str) -> str:
        """Определяет страну по городу."""
        if not city:
            return 'Неизвестно'
        
        # Китайские города
        chinese_cities = ['Шанхай', 'Гуанчжоу', 'Шэньчжэнь', 'Нинбо', 'Тяньцзинь', 'Циндао', 'Далянь', 'Пекин', 'Чунцин', 'Чэнду', 'Сиань', 'Чжэнчжоу', 'Хэфэй', 'Вэньчжоу', 'Вэйфан', 'Вэйхай', 'Сямэнь', 'Сучжоу', 'Шицзячжуан', 'Датянь', 'Чанша', 'Цзэнчэн', 'Шэньян', 'Датун', 'Цзяочжоу', 'Цзинань', 'Цзыбо', 'Дэцин', 'Уцзян']
        if city in chinese_cities:
            return 'Китай'
        
        # Российские города
        russian_cities = ['Москва', 'Санкт-Петербург', 'Екатеринбург', 'Новосибирск', 'Красноярск', 'Ростов', 'Владивосток', 'Находка']
        if city in russian_cities:
            return 'Россия'
        
        # Казахстан
        if city in ['Алматы', 'Астана']:
            return 'Казахстан'
        
        # Границы
        if city in ['Эрлянь', 'Алашанькоу', 'Хоргос']:
            return 'Граница'
        
        return 'Неизвестно'
    
    def analyze_railway_file(self, text: str, file_path: str) -> Dict[str, Any]:
        """Анализирует железнодорожный файл."""
        
        # Сначала используем стандартный анализатор
        base_result = analyze_tariff_text_adaptive(text)
        
        # Принудительно устанавливаем тип транспорта
        base_result['transport_type'] = 'rail'
        base_result['basis'] = 'EXW'  # По умолчанию для ЖД
        
        # Извлекаем железнодорожные маршруты
        railway_routes = self.extract_railway_routes(text)
        
        # Объединяем результаты
        if railway_routes:
            base_result['routes'] = railway_routes
        else:
            # Очищаем стандартные маршруты от ложных срабатываний
            base_result['routes'] = self._clean_standard_routes(base_result.get('routes', []))
        
        return base_result
    
    def _clean_standard_routes(self, routes: List[Dict]) -> List[Dict]:
        """Очищает стандартные маршруты от ложных срабатываний."""
        cleaned = []
        
        for route in routes:
            origin = route.get('origin_city', '')
            destination = route.get('destination_city', '')
            
            # Пропускаем маршруты с пустыми городами
            if not origin or not destination:
                continue
            
            # Пропускаем маршруты с "Неизвестно"
            if 'Неизвестно' in origin or 'Неизвестно' in destination:
                continue
            
            # Пропускаем слишком короткие названия
            if len(origin) < 2 or len(destination) < 2:
                continue
            
            cleaned.append(route)
        
        return cleaned[:10]

def analyze_railway_file(text: str, file_path: str) -> Dict[str, Any]:
    """Универсальная функция анализа железнодорожного файла."""
    analyzer = RailwayAnalyzer()
    return analyzer.analyze_railway_file(text, file_path)
