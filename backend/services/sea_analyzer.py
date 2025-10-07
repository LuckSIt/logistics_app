#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Специализированный анализатор для морских тарифов
"""

import re
from typing import Dict, List, Optional, Any
from adaptive_analyzer import analyze_tariff_text_adaptive

class SeaAnalyzer:
    """Специализированный анализатор для морских тарифов."""
    
    def __init__(self):
        # Специфичные для моря паттерны
        self.sea_patterns = {
            'routes': [
                r'([A-Z]{3,5})\s*[-→]\s*([A-Z]{3,5})',  # SHANGHAI-VVO
                r'([A-Z]{3,5})\s*TO\s*([A-Z]{3,5})',    # SHANGHAI TO VVO
                r'([A-Z]{3,5})\s*-\s*([A-Z]{3,5})',     # SHANGHAI-VVO
                r'([А-Я][а-я]+)\s*[-→]\s*([А-Я][а-я]+)',  # Шанхай-Владивосток
                r'([А-Я][а-я]+)\s*TO\s*([А-Я][а-я]+)',    # Шанхай TO Владивосток
                r'([A-Z][a-z]+)\s*[-→]\s*([A-Z][a-z]+)',  # Shanghai-Vladivostok
                r'([A-Z][a-z]+)\s*TO\s*([A-Z][a-z]+)',    # Shanghai TO Vladivostok
            ],
            'prices': [
                r'(\d+(?:\.\d+)?)\s*USD',
                r'USD\s*(\d+(?:\.\d+)?)',
                r'(\d+(?:\.\d+)?)\s*CNY',
                r'(\d+(?:\.\d+)?)\s*RMB',
                r'(\d+(?:\.\d+)?)\s*RUB',
                r'(\d+(?:\.\d+)?)\s*₽',
                r'(\d+(?:\.\d+)?)\s*USD/20',
                r'(\d+(?:\.\d+)?)\s*USD/40',
                r'(\d+(?:\.\d+)?)\s*USD/20DC',
                r'(\d+(?:\.\d+)?)\s*USD/40HC',
            ],
            'containers': [
                r'20\s*DC',
                r'40\s*HC',
                r'20\s*фут',
                r'40\s*фут',
                r'20\s*GP',
                r'40\s*GP',
                r'20\s*футовый',
                r'40\s*футовый',
            ],
            'ports': [
                r'Port\s+of\s+([A-Z][a-z]+)',
                r'([A-Z][a-z]+)\s+Port',
                r'([A-Z]{3,5})\s+Terminal',
                r'Terminal\s+([A-Z]{3,5})',
            ]
        }
        
        # Морские порты и города
        self.sea_ports = {
            # Китайские порты
            'SHANGHAI': 'Шанхай',
            'NINGBO': 'Нинбо',
            'QINGDAO': 'Циндао',
            'TIANJIN': 'Тяньцзинь',
            'DALIAN': 'Далянь',
            'XINGANG': 'Синган',
            'YANTIAN': 'Яньтянь',
            'SHEKOU': 'Шэкоу',
            'NANSHA': 'Наньша',
            'GUANGZHOU': 'Гуанчжоу',
            'SHENZHEN': 'Шэньчжэнь',
            'XIAMEN': 'Сямэнь',
            'FUZHOU': 'Фучжоу',
            'WENZHOU': 'Вэньчжоу',
            'NANTONG': 'Наньтун',
            'ZHANGJIAGANG': 'Чжанцзяган',
            'LIANYUNGANG': 'Ляньюньган',
            'YANTAI': 'Яньтай',
            'WEIHAI': 'Вэйхай',
            'QINHUANGDAO': 'Циньхуандао',
            
            # Российские порты
            'VVO': 'Владивосток',
            'Vladivostok': 'Владивосток',
            'VYP': 'Восточный',
            'Vostochny': 'Восточный',
            'NLE': 'Находка',
            'Nakhodka': 'Находка',
            'SPB': 'Санкт-Петербург',
            'St. Petersburg': 'Санкт-Петербург',
            'FCT': 'Санкт-Петербург',
            'PLP': 'Санкт-Петербург',
            'KALININGRAD': 'Калининград',
            'Kaliningrad': 'Калининград',
            'NOVOROSSIYSK': 'Новороссийск',
            'Novorossiysk': 'Новороссийск',
            'ROSTOV': 'Ростов-на-Дону',
            'Rostov': 'Ростов-на-Дону',
            'ASTRAKHAN': 'Астрахань',
            'Astrakhan': 'Астрахань',
            'MURMANSK': 'Мурманск',
            'Murmansk': 'Мурманск',
            'ARKHANGELSK': 'Архангельск',
            'Arkhangelsk': 'Архангельск',
            
            # Международные порты
            'BUSAN': 'Пусан',
            'Busan': 'Пусан',
            'SINGAPORE': 'Сингапур',
            'Singapore': 'Сингапур',
            'HONG KONG': 'Гонконг',
            'Hong Kong': 'Гонконг',
            'ROTTERDAM': 'Роттердам',
            'Rotterdam': 'Роттердам',
            'HAMBURG': 'Гамбург',
            'Hamburg': 'Гамбург',
            'ANTWERP': 'Антверпен',
            'Antwerp': 'Антверпен',
            'FELIXSTOWE': 'Феликстоу',
            'Felixstowe': 'Феликстоу',
            'LOS ANGELES': 'Лос-Анджелес',
            'Los Angeles': 'Лос-Анджелес',
            'LONG BEACH': 'Лонг-Бич',
            'Long Beach': 'Лонг-Бич',
            'NEW YORK': 'Нью-Йорк',
            'New York': 'Нью-Йорк',
            'SAVANNAH': 'Саванна',
            'Savannah': 'Саванна',
        }
        
        # Города и их порты
        self.city_ports = {
            'Шанхай': 'SHANGHAI',
            'Shanghai': 'SHANGHAI',
            'Нинбо': 'NINGBO',
            'Ningbo': 'NINGBO',
            'Циндао': 'QINGDAO',
            'Qingdao': 'QINGDAO',
            'Тяньцзинь': 'TIANJIN',
            'Tianjin': 'TIANJIN',
            'Далянь': 'DALIAN',
            'Dalian': 'DALIAN',
            'Синган': 'XINGANG',
            'Xingang': 'XINGANG',
            'Яньтянь': 'YANTIAN',
            'Yantian': 'YANTIAN',
            'Шэкоу': 'SHEKOU',
            'Shekou': 'SHEKOU',
            'Наньша': 'NANSHA',
            'Nansha': 'NANSHA',
            'Гуанчжоу': 'GUANGZHOU',
            'Guangzhou': 'GUANGZHOU',
            'Шэньчжэнь': 'SHENZHEN',
            'Shenzhen': 'SHENZHEN',
            'Сямэнь': 'XIAMEN',
            'Xiamen': 'XIAMEN',
            'Фучжоу': 'FUZHOU',
            'Fuzhou': 'FUZHOU',
            'Вэньчжоу': 'WENZHOU',
            'Wenzhou': 'WENZHOU',
            'Наньтун': 'NANTONG',
            'Nantong': 'NANTONG',
            'Чжанцзяган': 'ZHANGJIAGANG',
            'Zhangjiagang': 'ZHANGJIAGANG',
            'Ляньюньган': 'LIANYUNGANG',
            'Lianyungang': 'LIANYUNGANG',
            'Яньтай': 'YANTAI',
            'Yantai': 'YANTAI',
            'Вэйхай': 'WEIHAI',
            'Weihai': 'WEIHAI',
            'Циньхуандао': 'QINHUANGDAO',
            'Qinhuangdao': 'QINHUANGDAO',
            'Владивосток': 'VVO',
            'Vladivostok': 'VVO',
            'Восточный': 'VYP',
            'Vostochny': 'VYP',
            'Находка': 'NLE',
            'Nakhodka': 'NLE',
            'Санкт-Петербург': 'SPB',
            'St. Petersburg': 'SPB',
            'Калининград': 'KALININGRAD',
            'Kaliningrad': 'KALININGRAD',
            'Новороссийск': 'NOVOROSSIYSK',
            'Novorossiysk': 'NOVOROSSIYSK',
            'Ростов-на-Дону': 'ROSTOV',
            'Rostov': 'ROSTOV',
            'Астрахань': 'ASTRAKHAN',
            'Astrakhan': 'ASTRAKHAN',
            'Мурманск': 'MURMANSK',
            'Murmansk': 'MURMANSK',
            'Архангельск': 'ARKHANGELSK',
            'Arkhangelsk': 'ARKHANGELSK',
            'Пусан': 'BUSAN',
            'Busan': 'BUSAN',
            'Сингапур': 'SINGAPORE',
            'Singapore': 'SINGAPORE',
            'Гонконг': 'HONG KONG',
            'Hong Kong': 'HONG KONG',
            'Роттердам': 'ROTTERDAM',
            'Rotterdam': 'ROTTERDAM',
            'Гамбург': 'HAMBURG',
            'Hamburg': 'HAMBURG',
            'Антверпен': 'ANTWERP',
            'Antwerp': 'ANTWERP',
            'Феликстоу': 'FELIXSTOWE',
            'Felixstowe': 'FELIXSTOWE',
            'Лос-Анджелес': 'LOS ANGELES',
            'Los Angeles': 'LOS ANGELES',
            'Лонг-Бич': 'LONG BEACH',
            'Long Beach': 'LONG BEACH',
            'Нью-Йорк': 'NEW YORK',
            'New York': 'NEW YORK',
            'Саванна': 'SAVANNAH',
            'Savannah': 'SAVANNAH',
        }
    
    def extract_sea_routes(self, text: str) -> List[Dict]:
        """Извлекает морские маршруты."""
        routes = []
        
        # Обрабатываем табличные данные
        lines = text.split('\n')
        for line in lines:
            if '|' in line:
                # Табличная строка
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 3:
                    # Ищем порты в первых колонках
                    origin = self._extract_port_from_text(parts[0])
                    destination = self._extract_port_from_text(parts[1])
                    
                    if origin and destination and origin != destination:
                        # Ищем цены в остальных колонках
                        prices = self._extract_prices_from_parts(parts[2:])
                        
                        route = {
                            'origin_city': origin,
                            'origin_country': self._get_country_by_city(origin),
                            'destination_city': destination,
                            'destination_country': self._get_country_by_city(destination),
                            'transport_type': 'sea',
                            'price_usd': prices.get('usd'),
                            'price_cny': prices.get('cny'),
                            'price_rub': prices.get('rub'),
                            'container_type': self._extract_container_type(line)
                        }
                        routes.append(route)
        
        # Обрабатываем текстовые маршруты
        for pattern in self.sea_patterns['routes']:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                origin = match.group(1).strip()
                destination = match.group(2).strip()
                
                if origin and destination and origin != destination:
                    # Нормализуем названия портов
                    origin = self._normalize_port_name(origin)
                    destination = self._normalize_port_name(destination)
                    
                    if origin and destination and origin != destination:
                        route = {
                            'origin_city': origin,
                            'origin_country': self._get_country_by_city(origin),
                            'destination_city': destination,
                            'destination_country': self._get_country_by_city(destination),
                            'transport_type': 'sea',
                            'price_usd': None,
                            'price_cny': None,
                            'price_rub': None,
                            'container_type': None
                        }
                        routes.append(route)
        
        return routes[:10]  # Ограничиваем количество
    
    def _normalize_port_name(self, port: str) -> Optional[str]:
        """Нормализует название порта."""
        if not port or port.strip() == '':
            return None
        
        port = port.strip()
        
        # Проверяем коды портов
        if port.upper() in self.sea_ports:
            return self.sea_ports[port.upper()]
        
        # Проверяем города
        for normalized_city, code in self.city_ports.items():
            if port.lower() == normalized_city.lower() or port.lower() == code.lower():
                return normalized_city
        
        # Если не нашли, возвращаем как есть (если это похоже на порт)
        if len(port) > 2 and not port.isdigit() and not port.lower() in ['from', 'to', 'via', 'through', 'route', 'port', 'terminal']:
            return port
        
        return None
    
    def _extract_port_from_text(self, text: str) -> Optional[str]:
        """Извлекает название порта из текста."""
        if not text or text.strip() == '':
            return None
        
        text = text.strip()
        
        # Проверяем известные порты
        for port in self.city_ports.keys():
            if port.lower() in text.lower():
                return port
        
        # Проверяем коды портов
        for code, port in self.sea_ports.items():
            if code.lower() in text.lower():
                return port
        
        # Если не нашли, возвращаем как есть (если это похоже на порт)
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
    
    def _extract_container_type(self, text: str) -> Optional[str]:
        """Извлекает тип контейнера."""
        for pattern in self.sea_patterns['containers']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0).strip()
        return None
    
    def _get_country_by_city(self, city: str) -> str:
        """Определяет страну по городу."""
        if not city:
            return 'Неизвестно'
        
        # Китайские города
        chinese_cities = ['Шанхай', 'Shanghai', 'Нинбо', 'Ningbo', 'Циндао', 'Qingdao', 'Тяньцзинь', 'Tianjin', 'Далянь', 'Dalian', 'Синган', 'Xingang', 'Яньтянь', 'Yantian', 'Шэкоу', 'Shekou', 'Наньша', 'Nansha', 'Гуанчжоу', 'Guangzhou', 'Шэньчжэнь', 'Shenzhen', 'Сямэнь', 'Xiamen', 'Фучжоу', 'Fuzhou', 'Вэньчжоу', 'Wenzhou', 'Наньтун', 'Nantong', 'Чжанцзяган', 'Zhangjiagang', 'Ляньюньган', 'Lianyungang', 'Яньтай', 'Yantai', 'Вэйхай', 'Weihai', 'Циньхуандао', 'Qinhuangdao']
        if city in chinese_cities:
            return 'Китай'
        
        # Российские города
        russian_cities = ['Владивосток', 'Vladivostok', 'Восточный', 'Vostochny', 'Находка', 'Nakhodka', 'Санкт-Петербург', 'St. Petersburg', 'Калининград', 'Kaliningrad', 'Новороссийск', 'Novorossiysk', 'Ростов-на-Дону', 'Rostov', 'Астрахань', 'Astrakhan', 'Мурманск', 'Murmansk', 'Архангельск', 'Arkhangelsk']
        if city in russian_cities:
            return 'Россия'
        
        # Другие страны
        if city in ['Пусан', 'Busan']:
            return 'Южная Корея'
        elif city in ['Сингапур', 'Singapore']:
            return 'Сингапур'
        elif city in ['Гонконг', 'Hong Kong']:
            return 'Китай'
        elif city in ['Роттердам', 'Rotterdam']:
            return 'Нидерланды'
        elif city in ['Гамбург', 'Hamburg']:
            return 'Германия'
        elif city in ['Антверпен', 'Antwerp']:
            return 'Бельгия'
        elif city in ['Феликстоу', 'Felixstowe']:
            return 'Великобритания'
        elif city in ['Лос-Анджелес', 'Los Angeles', 'Лонг-Бич', 'Long Beach', 'Нью-Йорк', 'New York', 'Саванна', 'Savannah']:
            return 'США'
        
        return 'Неизвестно'
    
    def analyze_sea_file(self, text: str, file_path: str) -> Dict[str, Any]:
        """Анализирует морской файл."""
        
        # Сначала используем стандартный анализатор
        base_result = analyze_tariff_text_adaptive(text)
        
        # Принудительно устанавливаем тип транспорта
        base_result['transport_type'] = 'sea'
        base_result['basis'] = 'FOB'  # По умолчанию для моря
        
        # Извлекаем морские маршруты
        sea_routes = self.extract_sea_routes(text)
        
        # Объединяем результаты
        if sea_routes:
            base_result['routes'] = sea_routes
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

def analyze_sea_file(text: str, file_path: str) -> Dict[str, Any]:
    """Универсальная функция анализа морского файла."""
    analyzer = SeaAnalyzer()
    return analyzer.analyze_sea_file(text, file_path)

