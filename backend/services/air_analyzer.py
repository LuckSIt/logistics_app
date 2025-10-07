#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Специализированный анализатор для авиационных тарифов
"""

import re
from typing import Dict, List, Optional, Any
from services.adaptive_analyzer import analyze_tariff_text_adaptive

class AirAnalyzer:
    """Специализированный анализатор для авиационных тарифов."""
    
    def __init__(self):
        # Специфичные для авиа паттерны
        self.air_patterns = {
            'routes': [
                r'([A-Z]{3})\s*[-→]\s*([A-Z]{3})',  # HKG-PEK
                r'([A-Z]{3})\s*TO\s*([A-Z]{3})',    # HKG TO PEK
                r'([A-Z]{3})\s*-\s*([A-Z]{3})',     # HKG-PEK
                r'([А-Я][а-я]+)\s*[-→]\s*([А-Я][а-я]+)',  # Москва-Пекин
                r'([А-Я][а-я]+)\s*TO\s*([А-Я][а-я]+)',    # Москва TO Пекин
                r'([A-Z][a-z]+)\s*[-→]\s*([A-Z][a-z]+)',  # Beijing-Moscow
                r'([A-Z][a-z]+)\s*TO\s*([A-Z][a-z]+)',    # Beijing TO Moscow
                r'([A-Z][a-z]+)\s*-\s*([A-Z][a-z]+)',     # Beijing-Moscow
            ],
            'prices': [
                r'(\d+(?:\.\d+)?)\s*USD/kg',
                r'(\d+(?:\.\d+)?)\s*USD\s*per\s*kg',
                r'(\d+(?:\.\d+)?)\s*USD',
                r'USD\s*(\d+(?:\.\d+)?)',
                r'(\d+(?:\.\d+)?)\s*CNY/kg',
                r'(\d+(?:\.\d+)?)\s*RMB/kg',
                r'(\d+(?:\.\d+)?)\s*CNY',
                r'(\d+(?:\.\d+)?)\s*RUB/kg',
                r'(\d+(?:\.\d+)?)\s*RUB',
                r'(\d+(?:\.\d+)?)\s*₽/kg',
                r'(\d+(?:\.\d+)?)\s*₽',
            ],
            'airports': [
                r'([A-Z]{3})\s*Airport',
                r'Airport\s*([A-Z]{3})',
                r'([A-Z]{3})\s*International',
                r'International\s*([A-Z]{3})',
            ],
            'weights': [
                r'(\d+(?:\.\d+)?)\s*kg',
                r'(\d+(?:\.\d+)?)\s*KG',
                r'(\d+(?:\.\d+)?)\s*kilograms',
                r'(\d+(?:\.\d+)?)\s*tons',
                r'(\d+(?:\.\d+)?)\s*tonnes',
            ]
        }
        
        # Авиационные коды и города
        self.air_codes = {
            # Китайские аэропорты
            'PEK': 'Пекин',
            'CAN': 'Гуанчжоу', 
            'SHA': 'Шанхай',
            'SZX': 'Шэньчжэнь',
            'CTU': 'Чэнду',
            'XIY': 'Сиань',
            'CKG': 'Чунцин',
            'HGH': 'Ханчжоу',
            'NGB': 'Нинбо',
            'TAO': 'Циндао',
            'DLC': 'Далянь',
            'TSN': 'Тяньцзинь',
            'XMN': 'Сямэнь',
            'WUH': 'Ухань',
            'NKG': 'Нанкин',
            'HKG': 'Гонконг',
            'MFM': 'Макао',
            
            # Российские аэропорты
            'SVO': 'Москва',
            'DME': 'Москва',
            'VKO': 'Москва',
            'LED': 'Санкт-Петербург',
            'VVO': 'Владивосток',
            'KRR': 'Краснодар',
            'ROV': 'Ростов-на-Дону',
            'SVX': 'Екатеринбург',
            'OVB': 'Новосибирск',
            'KJA': 'Красноярск',
            'UFA': 'Уфа',
            'KZN': 'Казань',
            'GOJ': 'Нижний Новгород',
            'ASF': 'Астрахань',
            'STW': 'Ставрополь',
            
            # Международные аэропорты
            'DXB': 'Дубай',
            'IST': 'Стамбул',
            'AMS': 'Амстердам',
            'FRA': 'Франкфурт',
            'CDG': 'Париж',
            'LHR': 'Лондон',
            'JFK': 'Нью-Йорк',
            'LAX': 'Лос-Анджелес',
            'NRT': 'Токио',
            'ICN': 'Сеул',
            'SIN': 'Сингапур',
            'BKK': 'Бангкок',
            'DEL': 'Дели',
            'BOM': 'Мумбаи',
        }
        
        # Города и их коды
        self.city_codes = {
            'Пекин': 'PEK',
            'Beijing': 'PEK',
            'Гуанчжоу': 'CAN',
            'Guangzhou': 'CAN',
            'Шанхай': 'SHA',
            'Shanghai': 'SHA',
            'Шэньчжэнь': 'SZX',
            'Shenzhen': 'SZX',
            'Чэнду': 'CTU',
            'Chengdu': 'CTU',
            'Сиань': 'XIY',
            'Xian': 'XIY',
            'Чунцин': 'CKG',
            'Chongqing': 'CKG',
            'Ханчжоу': 'HGH',
            'Hangzhou': 'HGH',
            'Нинбо': 'NGB',
            'Ningbo': 'NGB',
            'Циндао': 'TAO',
            'Qingdao': 'TAO',
            'Далянь': 'DLC',
            'Dalian': 'DLC',
            'Тяньцзинь': 'TSN',
            'Tianjin': 'TSN',
            'Сямэнь': 'XMN',
            'Xiamen': 'XMN',
            'Ухань': 'WUH',
            'Wuhan': 'WUH',
            'Нанкин': 'NKG',
            'Nanjing': 'NKG',
            'Гонконг': 'HKG',
            'Hong Kong': 'HKG',
            'Макао': 'MFM',
            'Macau': 'MFM',
            'Москва': 'SVO',
            'Moscow': 'SVO',
            'Санкт-Петербург': 'LED',
            'St. Petersburg': 'LED',
            'Владивосток': 'VVO',
            'Vladivostok': 'VVO',
            'Краснодар': 'KRR',
            'Krasnodar': 'KRR',
            'Ростов-на-Дону': 'ROV',
            'Rostov': 'ROV',
            'Екатеринбург': 'SVX',
            'Yekaterinburg': 'SVX',
            'Новосибирск': 'OVB',
            'Novosibirsk': 'OVB',
            'Красноярск': 'KJA',
            'Krasnoyarsk': 'KJA',
            'Уфа': 'UFA',
            'Казань': 'KZN',
            'Kazan': 'KZN',
            'Нижний Новгород': 'GOJ',
            'Nizhny Novgorod': 'GOJ',
            'Астрахань': 'ASF',
            'Astrakhan': 'ASF',
            'Ставрополь': 'STW',
            'Stavropol': 'STW',
            'Дубай': 'DXB',
            'Dubai': 'DXB',
            'Стамбул': 'IST',
            'Istanbul': 'IST',
            'Амстердам': 'AMS',
            'Amsterdam': 'AMS',
            'Франкфурт': 'FRA',
            'Frankfurt': 'FRA',
            'Париж': 'CDG',
            'Paris': 'CDG',
            'Лондон': 'LHR',
            'London': 'LHR',
            'Нью-Йорк': 'JFK',
            'New York': 'JFK',
            'Лос-Анджелес': 'LAX',
            'Los Angeles': 'LAX',
            'Токио': 'NRT',
            'Tokyo': 'NRT',
            'Сеул': 'ICN',
            'Seoul': 'ICN',
            'Сингапур': 'SIN',
            'Singapore': 'SIN',
            'Бангкок': 'BKK',
            'Bangkok': 'BKK',
            'Дели': 'DEL',
            'Delhi': 'DEL',
            'Мумбаи': 'BOM',
            'Mumbai': 'BOM',
        }
    
    def extract_air_routes(self, text: str) -> List[Dict]:
        """Извлекает авиационные маршруты."""
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
                            'transport_type': 'air',
                            'price_usd': prices.get('usd'),
                            'price_cny': prices.get('cny'),
                            'price_rub': prices.get('rub'),
                            'weight_unit': self._extract_weight_unit(line)
                        }
                        routes.append(route)
        
        # Обрабатываем текстовые маршруты
        for pattern in self.air_patterns['routes']:
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
                            'transport_type': 'air',
                            'price_usd': None,
                            'price_cny': None,
                            'price_rub': None,
                            'weight_unit': None
                        }
                        routes.append(route)
        
        return routes[:10]  # Ограничиваем количество
    
    def _normalize_city_name(self, city: str) -> Optional[str]:
        """Нормализует название города."""
        if not city or city.strip() == '':
            return None
        
        city = city.strip()
        
        # Проверяем авиационные коды
        if city.upper() in self.air_codes:
            return self.air_codes[city.upper()]
        
        # Проверяем города
        for normalized_city, code in self.city_codes.items():
            if city.lower() == normalized_city.lower() or city.lower() == code.lower():
                return normalized_city
        
        # Если не нашли, возвращаем как есть (если это похоже на город)
        if len(city) > 2 and not city.isdigit() and not city.lower() in ['from', 'to', 'via', 'through', 'route', 'flight', 'airport']:
            return city
        
        return None
    
    def _extract_city_from_text(self, text: str) -> Optional[str]:
        """Извлекает название города из текста."""
        if not text or text.strip() == '':
            return None
        
        text = text.strip()
        
        # Проверяем известные города
        for city in self.city_codes.keys():
            if city.lower() in text.lower():
                return city
        
        # Проверяем коды аэропортов
        for code, city in self.air_codes.items():
            if code.lower() in text.lower():
                return city
        
        # Если не нашли, возвращаем как есть (если это похоже на город)
        if len(text) > 2 and not text.isdigit():
            return text
        
        return None
    
    def _extract_prices_from_parts(self, parts: List[str]) -> Dict:
        """Извлекает цены из частей строки."""
        prices = {'usd': None, 'cny': None, 'rub': None}
        
        for part in parts:
            part = part.strip()
            if not part:
                continue
            
            # Ищем USD
            usd_match = re.search(r'(\d+(?:\.\d+)?)\s*USD', part, re.IGNORECASE)
            if usd_match:
                prices['usd'] = float(usd_match.group(1))
            
            # Ищем CNY/RMB
            cny_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:CNY|RMB)', part, re.IGNORECASE)
            if cny_match:
                prices['cny'] = float(cny_match.group(1))
            
            # Ищем RUB
            rub_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:RUB|₽)', part, re.IGNORECASE)
            if rub_match:
                prices['rub'] = float(rub_match.group(1))
        
        return prices
    
    def _extract_weight_unit(self, text: str) -> Optional[str]:
        """Извлекает единицу веса."""
        for pattern in self.air_patterns['weights']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0).strip()
        return None
    
    def _get_country_by_city(self, city: str) -> str:
        """Определяет страну по городу."""
        if not city:
            return 'Неизвестно'
        
        # Китайские города
        chinese_cities = ['Пекин', 'Beijing', 'Гуанчжоу', 'Guangzhou', 'Шанхай', 'Shanghai', 'Шэньчжэнь', 'Shenzhen', 'Чэнду', 'Chengdu', 'Сиань', 'Xian', 'Чунцин', 'Chongqing', 'Ханчжоу', 'Hangzhou', 'Нинбо', 'Ningbo', 'Циндао', 'Qingdao', 'Далянь', 'Dalian', 'Тяньцзинь', 'Tianjin', 'Сямэнь', 'Xiamen', 'Ухань', 'Wuhan', 'Нанкин', 'Nanjing', 'Гонконг', 'Hong Kong', 'Макао', 'Macau']
        if city in chinese_cities:
            return 'Китай'
        
        # Российские города
        russian_cities = ['Москва', 'Moscow', 'Санкт-Петербург', 'St. Petersburg', 'Владивосток', 'Vladivostok', 'Краснодар', 'Krasnodar', 'Ростов-на-Дону', 'Rostov', 'Екатеринбург', 'Yekaterinburg', 'Новосибирск', 'Novosibirsk', 'Красноярск', 'Krasnoyarsk', 'Уфа', 'Казань', 'Kazan', 'Нижний Новгород', 'Nizhny Novgorod', 'Астрахань', 'Astrakhan', 'Ставрополь', 'Stavropol']
        if city in russian_cities:
            return 'Россия'
        
        # Другие страны
        if city in ['Дубай', 'Dubai']:
            return 'ОАЭ'
        elif city in ['Стамбул', 'Istanbul']:
            return 'Турция'
        elif city in ['Амстердам', 'Amsterdam']:
            return 'Нидерланды'
        elif city in ['Франкфурт', 'Frankfurt']:
            return 'Германия'
        elif city in ['Париж', 'Paris']:
            return 'Франция'
        elif city in ['Лондон', 'London']:
            return 'Великобритания'
        elif city in ['Нью-Йорк', 'New York', 'Лос-Анджелес', 'Los Angeles']:
            return 'США'
        elif city in ['Токио', 'Tokyo']:
            return 'Япония'
        elif city in ['Сеул', 'Seoul']:
            return 'Южная Корея'
        elif city in ['Сингапур', 'Singapore']:
            return 'Сингапур'
        elif city in ['Бангкок', 'Bangkok']:
            return 'Таиланд'
        elif city in ['Дели', 'Delhi', 'Мумбаи', 'Mumbai']:
            return 'Индия'
        
        return 'Неизвестно'
    
    def analyze_air_file(self, text: str, file_path: str) -> Dict[str, Any]:
        """Анализирует авиационный файл."""
        
        # Сначала используем стандартный анализатор
        base_result = analyze_tariff_text_adaptive(text)
        
        # Принудительно устанавливаем тип транспорта
        base_result['transport_type'] = 'air'
        base_result['basis'] = 'EXW'  # По умолчанию для авиа
        
        # Извлекаем авиационные маршруты
        air_routes = self.extract_air_routes(text)
        
        # Объединяем результаты
        if air_routes:
            base_result['routes'] = air_routes
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
            
            # Пропускаем числовые значения (цены, даты и т.д.)
            if origin.replace('.', '').replace(',', '').isdigit() or destination.replace('.', '').replace(',', '').isdigit():
                continue
            
            # Пропускаем служебные слова
            skip_words = ['кг', 'kg', 'дата', 'date', 'вылета', 'departure', 'авиакомпания', 'airline', 'volga', 'днепр']
            if any(word in origin.lower() or word in destination.lower() for word in skip_words):
                continue
            
            # Пропускаем слишком короткие коды (если это не авиационные коды)
            if len(origin) <= 2 and origin.upper() not in self.air_codes:
                continue
            if len(destination) <= 2 and destination.upper() not in self.air_codes:
                continue
            
            cleaned.append(route)
        
        return cleaned[:10]

def analyze_air_file(text: str, file_path: str) -> Dict[str, Any]:
    """Универсальная функция анализа авиационного файла."""
    analyzer = AirAnalyzer()
    return analyzer.analyze_air_file(text, file_path)

