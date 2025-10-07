#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Специализированный анализатор для автомобильных тарифов
"""

import re
from typing import Dict, List, Optional, Any
from services.adaptive_analyzer import analyze_tariff_text_adaptive

class AutoAnalyzer:
    """Специализированный анализатор для автомобильных тарифов."""
    
    def __init__(self):
        # Специфичные для авто паттерны
        self.auto_patterns = {
            'routes': [
                r'([А-Я][а-я]+)\s*[-→]\s*([А-Я][а-я]+)',  # Москва-Пекин
                r'([А-Я][а-я]+)\s*TO\s*([А-Я][а-я]+)',    # Москва TO Пекин
                r'([A-Z][a-z]+)\s*[-→]\s*([A-Z][a-z]+)',  # Beijing-Moscow
                r'([A-Z][a-z]+)\s*TO\s*([A-Z][a-z]+)',    # Beijing TO Moscow
                r'([A-Z][a-z]+)\s*-\s*([A-Z][a-z]+)',     # Beijing-Moscow
                r'([A-Z]{3})\s*[-→]\s*([A-Z]{3})',        # PEK-MOS
                r'([A-Z]{3})\s*TO\s*([A-Z]{3})',          # PEK TO MOS
            ],
            'prices': [
                r'(\d+(?:\.\d+)?)\s*USD',
                r'USD\s*(\d+(?:\.\d+)?)',
                r'(\d+(?:\.\d+)?)\s*CNY',
                r'(\d+(?:\.\d+)?)\s*RMB',
                r'(\d+(?:\.\d+)?)\s*RUB',
                r'(\d+(?:\.\d+)?)\s*₽',
                r'(\d+(?:\.\d+)?)\s*USD/cbm',
                r'(\d+(?:\.\d+)?)\s*USD/m3',
                r'(\d+(?:\.\d+)?)\s*CNY/cbm',
                r'(\d+(?:\.\d+)?)\s*CNY/m3',
            ],
            'vehicles': [
                r'FTL',
                r'LTL',
                r'грузовик',
                r'truck',
                r'фура',
                r'13m\s*truck',
                r'16m\s*truck',
                r'20m\s*truck',
                r'40m\s*truck',
                r'80cbm',
                r'90cbm',
                r'120cbm',
                r'cbm',
                r'm3',
            ],
            'borders': [
                r'граница',
                r'border',
                r'погранпереход',
                r'crossing',
                r'таможня',
                r'customs',
            ]
        }
        
        # Автомобильные маршруты и города
        self.auto_routes = {
            # Китайские города
            'PEK': 'Пекин',
            'Beijing': 'Пекин',
            'CAN': 'Гуанчжоу',
            'Guangzhou': 'Гуанчжоу',
            'SHA': 'Шанхай',
            'Shanghai': 'Шанхай',
            'SZX': 'Шэньчжэнь',
            'Shenzhen': 'Шэньчжэнь',
            'CTU': 'Чэнду',
            'Chengdu': 'Чэнду',
            'XIY': 'Сиань',
            'Xian': 'Сиань',
            'CKG': 'Чунцин',
            'Chongqing': 'Чунцин',
            'HGH': 'Ханчжоу',
            'Hangzhou': 'Ханчжоу',
            'NGB': 'Нинбо',
            'Ningbo': 'Нинбо',
            'TAO': 'Циндао',
            'Qingdao': 'Циндао',
            'DLC': 'Далянь',
            'Dalian': 'Далянь',
            'TSN': 'Тяньцзинь',
            'Tianjin': 'Тяньцзинь',
            'XMN': 'Сямэнь',
            'Xiamen': 'Сямэнь',
            'WUH': 'Ухань',
            'Wuhan': 'Ухань',
            'NKG': 'Нанкин',
            'Nanjing': 'Нанкин',
            'HKG': 'Гонконг',
            'Hong Kong': 'Гонконг',
            'MFM': 'Макао',
            'Macau': 'Макао',
            'YIW': 'Иу',
            'Yiwu': 'Иу',
            
            # Российские города
            'MOS': 'Москва',
            'Moscow': 'Москва',
            'SPB': 'Санкт-Петербург',
            'St. Petersburg': 'Санкт-Петербург',
            'VVO': 'Владивосток',
            'Vladivostok': 'Владивосток',
            'KRR': 'Краснодар',
            'Krasnodar': 'Краснодар',
            'ROV': 'Ростов-на-Дону',
            'Rostov': 'Ростов-на-Дону',
            'SVX': 'Екатеринбург',
            'Yekaterinburg': 'Екатеринбург',
            'OVB': 'Новосибирск',
            'Novosibirsk': 'Новосибирск',
            'KJA': 'Красноярск',
            'Krasnoyarsk': 'Красноярск',
            'UFA': 'Уфа',
            'KZN': 'Казань',
            'Kazan': 'Казань',
            'GOJ': 'Нижний Новгород',
            'Nizhny Novgorod': 'Нижний Новгород',
            'ASF': 'Астрахань',
            'Astrakhan': 'Астрахань',
            'STW': 'Ставрополь',
            'Stavropol': 'Ставрополь',
            
            # Казахстанские города
            'ALA': 'Алматы',
            'Almaty': 'Алматы',
            'AST': 'Астана',
            'Astana': 'Астана',
            'KZ': 'Казахстан',
            'Kazakhstan': 'Казахстан',
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
            'Иу': 'YIW',
            'Yiwu': 'YIW',
            'Москва': 'MOS',
            'Moscow': 'MOS',
            'Санкт-Петербург': 'SPB',
            'St. Petersburg': 'SPB',
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
            'Алматы': 'ALA',
            'Almaty': 'ALA',
            'Астана': 'AST',
            'Astana': 'AST',
            'Казахстан': 'KZ',
            'Kazakhstan': 'KZ',
        }
    
    def extract_auto_routes(self, text: str) -> List[Dict]:
        """Извлекает автомобильные маршруты."""
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
                        
                        # Извлекаем время в пути
                        transit_time = self._extract_transit_time(line)
                        
                        route = {
                            'origin_city': origin,
                            'origin_country': self._get_country_by_city(origin),
                            'destination_city': destination,
                            'destination_country': self._get_country_by_city(destination),
                            'transport_type': 'auto',
                            'price_usd': prices.get('usd'),
                            'price_cny': prices.get('cny'),
                            'price_rub': prices.get('rub'),
                            'transit_time': transit_time,
                            'vehicle_type': self._extract_vehicle_type(line)
                        }
                        routes.append(route)
        
        # Обрабатываем текстовые маршруты
        for pattern in self.auto_patterns['routes']:
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
                            'transport_type': 'auto',
                            'price_usd': None,
                            'price_cny': None,
                            'price_rub': None,
                            'vehicle_type': None
                        }
                        routes.append(route)
        
        return routes[:10]  # Ограничиваем количество
    
    def _normalize_city_name(self, city: str) -> Optional[str]:
        """Нормализует название города."""
        if not city or city.strip() == '':
            return None
        
        city = city.strip()
        
        # Проверяем коды городов
        if city.upper() in self.auto_routes:
            return self.auto_routes[city.upper()]
        
        # Проверяем города
        for normalized_city, code in self.city_codes.items():
            if city.lower() == normalized_city.lower() or city.lower() == code.lower():
                return normalized_city
        
        # Если не нашли, возвращаем как есть (если это похоже на город)
        if len(city) > 2 and not city.isdigit() and not city.lower() in ['from', 'to', 'via', 'through', 'route', 'road', 'highway']:
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
        
        # Проверяем коды городов
        for code, city in self.auto_routes.items():
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
            
            # Ищем USD (различные форматы)
            usd_patterns = [
                r'USD(\d+(?:\.\d+)?)',  # USD9600
                r'(\d+(?:\.\d+)?)\s*USD',  # 9600 USD
                r'USD\s*(\d+(?:\.\d+)?)',  # USD 9600
                r'(\d+(?:\.\d+)?)\s*\$',   # 9600 $
                r'\$(\d+(?:\.\d+)?)',      # $9600
            ]
            
            for pattern in usd_patterns:
                usd_match = re.search(pattern, part, re.IGNORECASE)
                if usd_match:
                    try:
                        prices['usd'] = float(usd_match.group(1))
                        break
                    except ValueError:
                        continue
            
            # Ищем CNY/RMB
            cny_patterns = [
                r'CNY(\d+(?:\.\d+)?)',
                r'(\d+(?:\.\d+)?)\s*CNY',
                r'RMB(\d+(?:\.\d+)?)',
                r'(\d+(?:\.\d+)?)\s*RMB',
            ]
            
            for pattern in cny_patterns:
                cny_match = re.search(pattern, part, re.IGNORECASE)
                if cny_match:
                    try:
                        prices['cny'] = float(cny_match.group(1))
                        break
                    except ValueError:
                        continue
            
            # Ищем RUB
            rub_patterns = [
                r'RUB(\d+(?:\.\d+)?)',
                r'(\d+(?:\.\d+)?)\s*RUB',
                r'(\d+(?:\.\d+)?)\s*₽',
                r'₽(\d+(?:\.\d+)?)',
            ]
            
            for pattern in rub_patterns:
                rub_match = re.search(pattern, part, re.IGNORECASE)
                if rub_match:
                    try:
                        prices['rub'] = float(rub_match.group(1))
                        break
                    except ValueError:
                        continue
        
        return prices
    
    def _extract_transit_time(self, text: str) -> Optional[int]:
        """Извлекает время в пути из текста."""
        # Ищем паттерны времени
        time_patterns = [
            r'(\d+)\s*days?',  # 25 days
            r'(\d+)\s*дней?',   # 25 дней
            r'(\d+)\s*дня?',    # 25 дня
            r'(\d+)\s*day',     # 25 day
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue
        
        return None
    
    def _extract_vehicle_type(self, text: str) -> Optional[str]:
        """Извлекает тип транспортного средства."""
        for pattern in self.auto_patterns['vehicles']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0).strip()
        return None
    
    def _get_country_by_city(self, city: str) -> str:
        """Определяет страну по городу."""
        if not city:
            return 'Неизвестно'
        
        # Китайские города
        chinese_cities = ['Пекин', 'Beijing', 'Гуанчжоу', 'Guangzhou', 'Шанхай', 'Shanghai', 'Шэньчжэнь', 'Shenzhen', 'Чэнду', 'Chengdu', 'Сиань', 'Xian', 'Чунцин', 'Chongqing', 'Ханчжоу', 'Hangzhou', 'Нинбо', 'Ningbo', 'Циндао', 'Qingdao', 'Далянь', 'Dalian', 'Тяньцзинь', 'Tianjin', 'Сямэнь', 'Xiamen', 'Ухань', 'Wuhan', 'Нанкин', 'Nanjing', 'Гонконг', 'Hong Kong', 'Макао', 'Macau', 'Иу', 'Yiwu']
        if city in chinese_cities:
            return 'Китай'
        
        # Российские города
        russian_cities = ['Москва', 'Moscow', 'Санкт-Петербург', 'St. Petersburg', 'Владивосток', 'Vladivostok', 'Краснодар', 'Krasnodar', 'Ростов-на-Дону', 'Rostov', 'Екатеринбург', 'Yekaterinburg', 'Новосибирск', 'Novosibirsk', 'Красноярск', 'Krasnoyarsk', 'Уфа', 'Казань', 'Kazan', 'Нижний Новгород', 'Nizhny Novgorod', 'Астрахань', 'Astrakhan', 'Ставрополь', 'Stavropol']
        if city in russian_cities:
            return 'Россия'
        
        # Казахстанские города
        kazakh_cities = ['Алматы', 'Almaty', 'Астана', 'Astana', 'Казахстан', 'Kazakhstan']
        if city in kazakh_cities:
            return 'Казахстан'
        
        return 'Неизвестно'
    
    def analyze_auto_file(self, text: str, file_path: str) -> Dict[str, Any]:
        """Анализирует автомобильный файл."""
        
        # Сначала используем стандартный анализатор
        base_result = analyze_tariff_text_adaptive(text)
        
        # Принудительно устанавливаем тип транспорта
        base_result['transport_type'] = 'auto'
        base_result['basis'] = 'EXW'  # По умолчанию для авто
        
        # Извлекаем автомобильные маршруты
        auto_routes = self.extract_auto_routes(text)
        
        # Объединяем результаты
        if auto_routes:
            base_result['routes'] = auto_routes
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
            
            # Очищаем названия городов
            origin = self._clean_city_name(origin)
            destination = self._clean_city_name(destination)
            
            # Пропускаем если после очистки города стали пустыми
            if not origin or not destination:
                continue
            
            # Пропускаем служебные слова
            skip_words = ['factory', 'destination', 'without', 'reloading', 'please', 'recheck', 'case', 'above', 'quotation', 'assumed', 'carriage', 'costs', 'overweight', 'tarpaulin', 'truck', 'ce']
            if any(word in origin.lower() or word in destination.lower() for word in skip_words):
                continue
            
            # Пропускаем даты и числа
            if re.match(r'^\d+/\d+\.?$', origin) or re.match(r'^\d+/\d+\.?$', destination):
                continue
            
            # Обновляем очищенные названия
            route['origin_city'] = origin
            route['destination_city'] = destination
            
            cleaned.append(route)
        
        return cleaned[:10]
    
    def _clean_city_name(self, city: str) -> str:
        """Очищает название города от лишних символов."""
        if not city:
            return ''
        
        # Убираем лишние символы
        city = city.strip()
        city = re.sub(r'[|]{2,}', ' ', city)  # Убираем множественные |
        city = re.sub(r'\s+', ' ', city)  # Убираем множественные пробелы
        city = re.sub(r'[^\w\s\-\.]', ' ', city)  # Оставляем только буквы, цифры, пробелы, дефисы и точки
        
        # Убираем служебные части
        parts_to_remove = [
            'truck transportation from', 'truck transportation', 'transportation from',
            'moscow,russia:', 'moscow,russia', 'russia:', 'russia',
            'usd', 'rub', 'days', 'day', 'please', 'recheck', 'case', 'by',
            'above', 'quotation', 'assumed', 'carriage', 'costs', 'overweight',
            'tarpaulin', 'truck', 'ce', 'me', 'te'
        ]
        
        for part in parts_to_remove:
            city = re.sub(rf'\b{part}\b', '', city, flags=re.IGNORECASE)
        
        # Очищаем от лишних пробелов
        city = ' '.join(city.split())
        
        # Если после очистки осталось меньше 2 символов, возвращаем пустую строку
        if len(city) < 2:
            return ''
        
        return city

def analyze_auto_file(text: str, file_path: str) -> Dict[str, Any]:
    """Универсальная функция анализа автомобильного файла."""
    analyzer = AutoAnalyzer()
    return analyzer.analyze_auto_file(text, file_path)

