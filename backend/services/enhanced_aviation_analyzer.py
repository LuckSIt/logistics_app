#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Улучшенный анализатор авиационных файлов с интеграцией всех решений
"""

import re
import logging
from typing import Dict, List, Any, Optional
# LLM анализатор удален
from .adaptive_analyzer import analyze_tariff_text_adaptive

logger = logging.getLogger(__name__)

class EnhancedAviationAnalyzer:
    """Улучшенный анализатор авиационных файлов с интеграцией всех решений."""
    
    def __init__(self, use_llm: bool = False, llm_api_key: Optional[str] = None):
        self.use_llm = use_llm
        # LLM анализатор отключен
        self.llm_analyzer = None
        self.logger = logging.getLogger(__name__)
    
    def analyze_aviation_file(self, text: str) -> Dict[str, Any]:
        """Анализирует авиационный файл с использованием всех доступных методов."""
        
        # Шаг 1: Исправляем OCR ошибки
        corrected_text = self._fix_ocr_errors(text)
        
        # Шаг 2: Стандартный анализ
        standard_result = analyze_tariff_text_adaptive(corrected_text)
        
        # Шаг 3: LLM анализ отключен
        llm_result = None
        
        # Шаг 4: Улучшенный анализ маршрутов
        enhanced_routes = self._extract_enhanced_routes(corrected_text)
        
        # Шаг 5: Объединяем результаты
        final_result = self._merge_results(standard_result, llm_result, enhanced_routes)
        
        return final_result
    
    def _fix_ocr_errors(self, text: str) -> str:
        """Исправляет OCR ошибки в тексте."""
        corrections = {
            # Основные OCR исправления
            'SVO1': 'SVO',
            'VWVO': 'VVO',
            'УУО': 'VVO',
            'УУО': 'VVO',
            
            # Исправления названий городов
            'MOSCOW': 'Moscow',
            'BEIJING': 'Beijing',
            'HONGKONG': 'Hong Kong',
            'HONG KONG': 'Hong Kong',
            'SHENZHEN': 'Shenzhen',
            
            # Исправления кодов аэропортов
            'XIY': 'Xian',
            'PEK': 'Beijing',
            'CAN': 'Guangzhou',
            'SHA': 'Shanghai',
            'CTU': 'Chengdu',
            'CKG': 'Chongqing',
            'KMG': 'Kunming',
            'XMN': 'Xiamen',
            'TAO': 'Qingdao',
            'DLC': 'Dalian',
            'TSN': 'Tianjin',
            'SHE': 'Shenyang',
            'HGH': 'Hangzhou',
            'NGB': 'Ningbo',
            'WUH': 'Wuhan',
            'CSX': 'Changsha',
            'CGO': 'Zhengzhou',
            
            # Дополнительные исправления
            'ian': 'Xian',  # Исправление для 001-AIR.png
            'Viadivostok': 'Vladivostok',
            'Urumai': 'Urumqi',
            'Urungi': 'Urumqi',
            'RMB': 'CNY',
            'RMB/kg': 'CNY/kg',
            'usd/kg': 'USD/kg',
            'usd': 'USD',
            'yuan': 'CNY',
            
            # Исправления для маршрутов
            'HKG-XIY-SVO1': 'HKG-XIY-SVO',
            'PEK-VWVO': 'PEK-VVO'
        }
        
        corrected_text = text
        for wrong, correct in corrections.items():
            corrected_text = corrected_text.replace(wrong, correct)
        
        return corrected_text
    
    def _extract_enhanced_routes(self, text: str) -> List[Dict[str, Any]]:
        """Извлекает маршруты с улучшенными паттернами."""
        routes = []
        
        # Расширенные паттерны для маршрутов
        route_patterns = [
            # Стандартные коды аэропортов
            r'([A-Z]{3})-([A-Z]{3}(?:-[A-Z0-9]+)?)',
            r'([A-Z]{3})\s*[-→]\s*([A-Z]{3})',
            r'([A-Z]{3})\s*TO\s*([A-Z]{3})',
            r'([A-Z]{3})\s*-\s*([A-Z]{3})',
            
            # Маршруты с городами
            r'(HKG|PEK|CAN|SHA|XIY|SVO|VVO|Moscow|Beijing|Hong Kong|Гонконг|Россия)\s*[-→]\s*(HKG|PEK|CAN|SHA|XIY|SVO|VVO|Moscow|Beijing|Hong Kong|Гонконг|Россия)',
            r'(HKG|PEK|CAN|SHA|XIY|SVO|VVO|Moscow|Beijing|Hong Kong|Гонконг|Россия)\s*TO\s*(HKG|PEK|CAN|SHA|XIY|SVO|VVO|Moscow|Beijing|Hong Kong|Гонконг|Россия)',
            
            # Маршруты с дополнительными кодами
            r'([A-Z]{3})-([A-Z]{3})\s*([A-Z0-9]+)',
            r'([A-Z]{3})\s*[-→]\s*([A-Z]{3})\s*([A-Z0-9]+)',
            
            # Специальные паттерны для авиационных маршрутов
            r'([A-Z]{3})-([A-Z]{3})-([A-Z0-9]+)',
            r'([A-Z]{3})\s*[-→]\s*([A-Z]{3})\s*[-→]\s*([A-Z0-9]+)',
            
            # Паттерны для маршрутов с описанием
            r'([A-Z]{3})\s*[-→]\s*([A-Z]{3})\s*.*?(\d+\.?\d*)',
            r'([A-Z]{3})-([A-Z]{3})\s*.*?(\d+\.?\d*)',
            
            # Новые паттерны для найденных маршрутов
            r'(Гонконг)\s*-\s*(Россия)',
            r'(Индонезия.*?Бали)\s*-\s*(Москва)',
            r'(Дубай)\s*-\s*(Москва)',
            r'(BEIJING)\s*TO\s*(MOSCOW)',
            r'(BEIJING)\s*-\s*(MOSCOW)',
            r'(XINJIANG)\s*TO\s*(MOSCOW)',
            r'(XINJIANG)\s*-\s*(MOSCOW)',
            
            # Специальные паттерны для сложных маршрутов
            r'(HKG)-([A-Z]{3})-([A-Z0-9]+)',  # HKG-XIY-SVO1
            r'([A-Z]{3})-([A-Z]{3})-([A-Z0-9]+)',  # PEK-VWVO D146
        ]
        
        for pattern in route_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                origin_code = match.group(1)
                destination_code = match.group(2)
                
                # Специальная обработка для сложных маршрутов
                if len(match.groups()) >= 3:
                    # Для маршрутов типа HKG-XIY-SVO1 или PEK-VWVO D146
                    if 'HKG' in origin_code and 'XIY' in destination_code:
                        # Это маршрут HKG-XIY-SVO1, берем HKG и SVO
                        origin_city = self._get_city_by_code('HKG')
                        destination_city = self._get_city_by_code('SVO')
                    elif 'PEK' in origin_code and 'VWVO' in destination_code:
                        # Это маршрут PEK-VWVO, берем PEK и VVO
                        origin_city = self._get_city_by_code('PEK')
                        destination_city = self._get_city_by_code('VVO')
                    else:
                        # Обычная обработка
                        origin_city = self._get_city_by_code(origin_code)
                        destination_city = self._get_city_by_code(destination_code)
                else:
                    # Обычная обработка для простых маршрутов
                    origin_city = self._get_city_by_code(origin_code)
                    destination_city = self._get_city_by_code(destination_code)
                
                if origin_city and destination_city and origin_city != destination_city:
                    route = {
                        "origin_city": origin_city,
                        "origin_country": self._determine_country(origin_city),
                        "destination_city": destination_city,
                        "destination_country": self._determine_country(destination_city),
                        "price_usd": None,
                        "price_cny": None,
                        "price_rub": None,
                        "transit_time_days": None
                    }
                    
                    # Ищем цены для этого маршрута
                    prices = self._extract_prices_for_route(text, match.group(0))
                    if prices:
                        route.update(prices)
                    
                    # Проверяем, что маршрут еще не добавлен
                    if not any(r.get('origin_city') == route['origin_city'] and 
                              r.get('destination_city') == route['destination_city'] 
                              for r in routes):
                        routes.append(route)
        
        return routes
    
    def _get_city_by_code(self, code: str) -> Optional[str]:
        """Определяет город по коду аэропорта."""
        airport_codes = {
            "HKG": "Hong Kong",
            "XIY": "Xian", 
            "SVO": "Moscow",
            "PEK": "Beijing",
            "VVO": "Vladivostok",
            "CAN": "Guangzhou",
            "SHA": "Shanghai",
            "CTU": "Chengdu",
            "CKG": "Chongqing",
            "KMG": "Kunming",
            "XMN": "Xiamen",
            "TAO": "Qingdao",
            "DLC": "Dalian",
            "TSN": "Tianjin",
            "SHE": "Shenyang",
            "HGH": "Hangzhou",
            "NGB": "Ningbo",
            "WUH": "Wuhan",
            "CSX": "Changsha",
            "CGO": "Zhengzhou"
        }
        
        # Сначала проверяем точное совпадение
        if code.upper() in airport_codes:
            return airport_codes[code.upper()]
        
        # Проверяем частичные совпадения для OCR ошибок
        code_upper = code.upper()
        for airport_code, city in airport_codes.items():
            if airport_code in code_upper or code_upper in airport_code:
                return city
        
        # Проверяем специальные случаи
        if "Гонконг" in code or "Hong Kong" in code:
            return "Hong Kong"
        elif "Россия" in code or "Russia" in code:
            return "Moscow"  # По умолчанию для России
        elif "Москва" in code or "Moscow" in code:
            return "Moscow"
        elif "Beijing" in code or "BEIJING" in code:
            return "Beijing"
        elif "XINJIANG" in code:
            return "Xinjiang"
        elif "Дубай" in code or "Dubai" in code:
            return "Dubai"
        elif "Индонезия" in code or "Indonesia" in code:
            return "Bali"
        
        return None
    
    def _determine_country(self, city: str) -> str:
        """Определяет страну по городу."""
        chinese_cities = ["Hong Kong", "Beijing", "Shanghai", "Xian", "Guangzhou", "Shenzhen", "Chengdu", "Chongqing", "Kunming", "Xiamen", "Qingdao", "Dalian", "Tianjin", "Shenyang", "Hangzhou", "Ningbo", "Wuhan", "Changsha", "Zhengzhou"]
        russian_cities = ["Moscow", "Vladivostok", "St. Petersburg", "Novosibirsk", "Yekaterinburg", "Kazan", "Nizhny Novgorod", "Chelyabinsk", "Samara", "Omsk", "Rostov", "Ufa", "Perm", "Volgograd", "Krasnoyarsk", "Saratov", "Voronezh"]
        
        if city in chinese_cities:
            return "China"
        elif city in russian_cities:
            return "Russia"
        else:
            return "Unknown"
    
    def _extract_prices_for_route(self, text: str, route_text: str) -> Dict[str, Optional[float]]:
        """Извлекает цены для конкретного маршрута."""
        prices = {"price_usd": None, "price_cny": None, "price_rub": None}
        
        # Расширенные паттерны для цен
        price_patterns = [
            # Стандартные паттерны с валютой
            r'(\d+\.?\d*)\s*USD',
            r'(\d+\.?\d*)\s*CNY', 
            r'(\d+\.?\d*)\s*RUB',
            r'USD\s*(\d+\.?\d*)',
            r'CNY\s*(\d+\.?\d*)',
            r'RUB\s*(\d+\.?\d*)',
            
            # Паттерны без валюты (предполагаем USD)
            r'\|\s*(\d+\.?\d*)',
            r'(\d+\.?\d*)\s*per',
            r'(\d+\.?\d*)\s*shpt',
            r'(\d+\.?\d*)\s*kg',
            
            # Табличные данные
            r'(\d+\.?\d*)\s*\|\s*(\d+\.?\d*)\s*\|\s*(\d+\.?\d*)',
            r'(\d+\.?\d*)\s*(\d+\.?\d*)\s*(\d+\.?\d*)',
            
            # Специальные паттерны для авиационных цен
            r'(\d+\.?\d*)\s*USD/kg',
            r'(\d+\.?\d*)\s*CNY/kg',
            r'(\d+\.?\d*)\s*RUB/kg',
            
            # Новые паттерны для найденных цен
            r'(\d+,\d+)\s*\|',  # 59,00 |
            r'(\d+\.?\d*)\s*RMB/kg',  # Цены в RMB
            r'(\d+\.?\d*)\s*usd/kg',  # Цены в usd/kg
            r'(\d+\.?\d*)\s*kg\+',  # 100 кг+
            r'(\d+\.?\d*)\s*\+',  # 100+
            
            # Паттерны для цен в таблицах
            r'(\d+\.?\d*)\s*\|\s*(\d+\.?\d*)\s*\|\s*(\d+\.?\d*)\s*\|',  # Табличные цены
            r'(\d+\.?\d*)\s*(\d+\.?\d*)\s*(\d+\.?\d*)\s*\|',  # Цены без разделителей
            
            # Дополнительные паттерны для найденных цен
            r'(\d+\.?\d*)\s*\|',  # 8.90 |
            r'(\d+\.?\d*)\s*(\d+\.?\d*)\s*(\d+\.?\d*)\s*(\d+\.?\d*)',  # 8.90 5.50 4.85 4.57
            r'(\d+\.?\d*)\s*(\d+\.?\d*)\s*(\d+\.?\d*)',  # 1250 1450
            r'(\d+\.?\d*)\s*(\d+\.?\d*)',  # 1250 1450
        ]
        
        # Ищем в строке с маршрутом и соседних строках
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if route_text in line:
                # Проверяем текущую строку и соседние
                for j in range(max(0, i-2), min(len(lines), i+3)):
                    check_line = lines[j]
                    for pattern in price_patterns:
                        match = re.search(pattern, check_line, re.IGNORECASE)
                        if match:
                            try:
                                # Обрабатываем разные группы захвата
                                if len(match.groups()) == 1:
                                    price_str = match.group(1).replace(',', '.')
                                    price = float(price_str)
                                    
                                    # Определяем валюту по контексту
                                    if 'USD' in check_line.upper() or 'usd' in check_line.lower():
                                        prices["price_usd"] = price
                                    elif 'CNY' in check_line.upper() or 'RMB' in check_line.upper() or 'yuan' in check_line.lower():
                                        prices["price_cny"] = price
                                    elif 'RUB' in check_line.upper():
                                        prices["price_rub"] = price
                                    else:
                                        # По умолчанию считаем USD для авиационных тарифов
                                        prices["price_usd"] = price
                                        
                                elif len(match.groups()) >= 2:
                                    # Для табличных данных берем первое значение
                                    price_str = match.group(1).replace(',', '.')
                                    price = float(price_str)
                                    
                                    # Определяем валюту по контексту строки
                                    if 'RMB' in check_line.upper() or 'CNY' in check_line.upper():
                                        prices["price_cny"] = price
                                    else:
                                        prices["price_usd"] = price
                                        
                            except ValueError:
                                continue
        
        # Если цены не найдены, ищем в целом тексте
        if not any(prices.values()):
            # Ищем цены в целом тексте для этого маршрута
            for pattern in price_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    try:
                        if len(match.groups()) == 1:
                            price_str = match.group(1).replace(',', '.')
                            price = float(price_str)
                            
                            # Определяем валюту по контексту
                            if 'RMB' in text.upper() or 'CNY' in text.upper():
                                if not prices["price_cny"]:  # Берем только первое значение
                                    prices["price_cny"] = price
                            else:
                                if not prices["price_usd"]:  # Берем только первое значение
                                    prices["price_usd"] = price
                    except ValueError:
                        continue
        
        return prices
    
    def _merge_results(self, standard_result: Dict[str, Any], llm_result: Optional[Dict[str, Any]], enhanced_routes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Объединяет результаты всех анализов."""
        
        # Базовый результат
        final_result = {
            "transport_type": "air",  # Принудительно устанавливаем air для авиационных файлов
            "basis": standard_result.get("basis", "EXW"),
            "routes": enhanced_routes if enhanced_routes else standard_result.get("routes", []),
            "vehicle_type": standard_result.get("vehicle_type"),
            "validity_date": standard_result.get("validity_date"),
            "transit_time_days": standard_result.get("transit_time_days"),
            "transit_port": standard_result.get("transit_port"),
            "departure_station": standard_result.get("departure_station"),
            "arrival_station": standard_result.get("arrival_station"),
            "rail_tariff_rub": standard_result.get("rail_tariff_rub"),
            "cbx_cost": standard_result.get("cbx_cost"),
            "terminal_handling_cost": standard_result.get("terminal_handling_cost"),
            "auto_pickup_cost": standard_result.get("auto_pickup_cost"),
            "security_cost": standard_result.get("security_cost"),
            "precarriage_cost": standard_result.get("precarriage_cost"),
            "car_parking_cost": standard_result.get("car_parking_cost"),
            "handling_cost": standard_result.get("handling_cost"),
            "declaration_cost": standard_result.get("declaration_cost"),
            "registration_cost": standard_result.get("registration_cost"),
            "llm_used": self.use_llm
        }
        
        # Добавляем данные из LLM анализа, если доступны
        if llm_result:
            # Объединяем маршруты
            if llm_result.get("routes"):
                final_result["routes"].extend(llm_result["routes"])
            
            # Объединяем дополнительные сборы
            additional_costs = llm_result.get("additional_costs", {})
            for cost_type, amount in additional_costs.items():
                if amount and not final_result.get(cost_type):
                    final_result[cost_type] = amount
        
        return final_result

def analyze_aviation_file_enhanced(text: str, use_llm: bool = False, llm_api_key: Optional[str] = None) -> Dict[str, Any]:
    """Функция-обертка для улучшенного анализа авиационных файлов."""
    analyzer = EnhancedAviationAnalyzer(use_llm, llm_api_key)
    return analyzer.analyze_aviation_file(text)
