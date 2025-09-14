#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM-анализатор для улучшенного извлечения данных из авиационных тарифов
"""

import json
import re
from typing import Dict, List, Any, Optional
import logging

try:
    import openai
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.warning("OpenAI не установлен. LLM функциональность недоступна.")

# Импортируем конфигурацию
try:
    from ..config.llm_config import LLMConfig
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False
    logging.warning("LLM конфигурация недоступна")

class LLMTariffAnalyzer:
    """Анализатор тарифов с использованием LLM для улучшенного понимания контекста."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or (LLMConfig.get_api_key() if CONFIG_AVAILABLE else None)
        self.client = None
        self.logger = logging.getLogger(__name__)
        
        if OPENAI_AVAILABLE and self.api_key:
            try:
                self.client = OpenAI(api_key=self.api_key)
                self.logger.info("LLM клиент инициализирован")
            except Exception as e:
                self.logger.error(f"Ошибка инициализации LLM клиента: {e}")
                self.client = None
        elif CONFIG_AVAILABLE and LLMConfig.is_available():
            try:
                self.client = OpenAI(api_key=LLMConfig.get_api_key())
                self.logger.info("LLM клиент инициализирован из конфигурации")
            except Exception as e:
                self.logger.error(f"Ошибка инициализации LLM клиента из конфигурации: {e}")
                self.client = None
    
    def analyze_aviation_tariff(self, text: str) -> Dict[str, Any]:
        """Анализирует авиационный тариф с помощью LLM."""
        if not self.client:
            return self._fallback_analysis(text)
        
        try:
            # Создаем промпт для LLM
            prompt = self._create_aviation_prompt(text)
            
            # Отправляем запрос к LLM
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "Ты эксперт по логистике и авиационным тарифам. Твоя задача - извлечь структурированные данные из текста авиационного тарифа."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=2000
            )
            
            # Парсим ответ
            result_text = response.choices[0].message.content
            return self._parse_llm_response(result_text)
            
        except Exception as e:
            self.logger.error(f"Ошибка LLM анализа: {e}")
            return self._fallback_analysis(text)
    
    def _create_aviation_prompt(self, text: str) -> str:
        """Создает промпт для анализа авиационного тарифа."""
        return f"""
Проанализируй следующий текст авиационного тарифа и извлеки структурированные данные в формате JSON:

ТЕКСТ:
{text}

ИНСТРУКЦИИ:
1. Определи тип транспорта (air/auto/sea/rail)
2. Найди все маршруты в формате "откуда-куда"
3. Извлеки цены в USD, CNY, RUB
4. Определи базис поставки (EXW, FOB, CIF, etc.)
5. Найди дополнительные сборы (handling, parking, declaration, etc.)
6. Исправь OCR ошибки в кодах аэропортов (например, SVO1 -> SVO, VWVO -> VVO)

ОТВЕТ ДОЛЖЕН БЫТЬ В ФОРМАТЕ JSON:
{{
    "transport_type": "air",
    "basis": "EXW",
    "routes": [
        {{
            "origin_city": "Hong Kong",
            "origin_country": "China", 
            "destination_city": "Moscow",
            "destination_country": "Russia",
            "price_usd": 8.90,
            "price_cny": null,
            "price_rub": null,
            "transit_time_days": null
        }}
    ],
    "additional_costs": {{
        "car_parking_cost": 25.0,
        "handling_cost": 100.0,
        "declaration_cost": 50.0,
        "registration_cost": 65.0
    }},
    "vehicle_type": "375/shpt",
    "validity_date": null,
    "transit_time_days": null
}}

Если не можешь извлечь какие-то данные, используй null. Будь максимально точным в исправлении OCR ошибок.
"""
    
    def _parse_llm_response(self, response_text: str) -> Dict[str, Any]:
        """Парсит ответ от LLM."""
        try:
            # Ищем JSON в ответе
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
            else:
                self.logger.warning("JSON не найден в ответе LLM")
                return self._fallback_analysis(response_text)
        except json.JSONDecodeError as e:
            self.logger.error(f"Ошибка парсинга JSON от LLM: {e}")
            return self._fallback_analysis(response_text)
    
    def _fallback_analysis(self, text: str) -> Dict[str, Any]:
        """Резервный анализ без LLM."""
        return {
            "transport_type": "air",
            "basis": "EXW", 
            "routes": [],
            "additional_costs": {},
            "vehicle_type": None,
            "validity_date": None,
            "transit_time_days": None
        }
    
    def fix_ocr_errors(self, text: str) -> str:
        """Исправляет типичные OCR ошибки в авиационных кодах."""
        corrections = {
            'SVO1': 'SVO',
            'VWVO': 'VVO', 
            'VWVO': 'VVO',
            'УУО': 'VVO',
            'УУО': 'VVO',
            'MOSCOW': 'Moscow',
            'BEIJING': 'Beijing',
            'HONGKONG': 'Hong Kong',
            'HONG KONG': 'Hong Kong',
            'SHENZHEN': 'Shenzhen',
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
            'CGO': 'Zhengzhou'
        }
        
        corrected_text = text
        for wrong, correct in corrections.items():
            corrected_text = corrected_text.replace(wrong, correct)
        
        return corrected_text
    
    def extract_structured_data(self, text: str) -> Dict[str, Any]:
        """Извлекает структурированные данные с исправлением OCR."""
        # Сначала исправляем OCR ошибки
        corrected_text = self.fix_ocr_errors(text)
        
        # Затем анализируем с LLM
        if self.client:
            return self.analyze_aviation_tariff(corrected_text)
        else:
            return self._extract_without_llm(corrected_text)
    
    def _extract_without_llm(self, text: str) -> Dict[str, Any]:
        """Извлечение данных без LLM с улучшенными паттернами."""
        result = {
            "transport_type": "air",
            "basis": "EXW",
            "routes": [],
            "additional_costs": {},
            "vehicle_type": None,
            "validity_date": None,
            "transit_time_days": None
        }
        
        # Ищем маршруты с исправленными кодами аэропортов
        route_patterns = [
            r'([A-Z]{3})-([A-Z]{3}(?:-[A-Z0-9]+)?)',
            r'([A-Z]{3})\s*[-→]\s*([A-Z]{3})',
            r'([A-Z]{3})\s*TO\s*([A-Z]{3})',
            r'([A-Z]{3})\s*-\s*([A-Z]{3})',
            # Добавляем паттерны для маршрутов с городами
            r'(HKG|PEK|CAN|SHA|XIY|SVO|VVO|Moscow|Beijing|Hong Kong)\s*[-→]\s*(HKG|PEK|CAN|SHA|XIY|SVO|VVO|Moscow|Beijing|Hong Kong)',
            r'(HKG|PEK|CAN|SHA|XIY|SVO|VVO|Moscow|Beijing|Hong Kong)\s*TO\s*(HKG|PEK|CAN|SHA|XIY|SVO|VVO|Moscow|Beijing|Hong Kong)',
            # Паттерны для маршрутов с дополнительными кодами
            r'([A-Z]{3})-([A-Z]{3})\s*([A-Z0-9]+)',
            r'([A-Z]{3})\s*[-→]\s*([A-Z]{3})\s*([A-Z0-9]+)'
        ]
        
        for pattern in route_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                origin_code = match.group(1)
                destination_code = match.group(2)
                
                # Определяем города по кодам
                origin_city = self._get_city_by_code(origin_code)
                destination_city = self._get_city_by_code(destination_code)
                
                if origin_city and destination_city:
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
                    
                    result["routes"].append(route)
        
        # Извлекаем дополнительные сборы
        result["additional_costs"] = self._extract_additional_costs(text)
        
        # Извлекаем тип ТС
        vehicle_match = re.search(r'(\d+/\w+)', text)
        if vehicle_match:
            result["vehicle_type"] = vehicle_match.group(1)
        
        return result
    
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
        
        return airport_codes.get(code.upper())
    
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
        
        # Ищем цены рядом с маршрутом
        price_patterns = [
            r'(\d+\.?\d*)\s*USD',
            r'(\d+\.?\d*)\s*CNY', 
            r'(\d+\.?\d*)\s*RUB',
            r'USD\s*(\d+\.?\d*)',
            r'CNY\s*(\d+\.?\d*)',
            r'RUB\s*(\d+\.?\d*)',
            # Добавляем паттерны для цен без валюты (предполагаем USD)
            r'\|\s*(\d+\.?\d*)',
            r'(\d+\.?\d*)\s*per',
            r'(\d+\.?\d*)\s*shpt',
            r'(\d+\.?\d*)\s*kg',
            # Паттерны для цен в таблицах
            r'(\d+\.?\d*)\s*\|\s*(\d+\.?\d*)\s*\|\s*(\d+\.?\d*)',
            r'(\d+\.?\d*)\s*(\d+\.?\d*)\s*(\d+\.?\d*)'
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
                                    price = float(match.group(1))
                                    # Определяем валюту по контексту
                                    if 'USD' in check_line.upper():
                                        prices["price_usd"] = price
                                    elif 'CNY' in check_line.upper():
                                        prices["price_cny"] = price
                                    elif 'RUB' in check_line.upper():
                                        prices["price_rub"] = price
                                    else:
                                        # По умолчанию считаем USD
                                        prices["price_usd"] = price
                                elif len(match.groups()) >= 3:
                                    # Для табличных данных берем первое значение
                                    price = float(match.group(1))
                                    prices["price_usd"] = price
                            except ValueError:
                                continue
        
        return prices
    
    def _extract_additional_costs(self, text: str) -> Dict[str, Optional[float]]:
        """Извлекает дополнительные сборы."""
        costs = {}
        
        cost_patterns = {
            "car_parking_cost": [
                r'CAR\s*PARKING.*?(\d+(?:\.\d+)?)',
                r'GATE\s*FEE.*?(\d+(?:\.\d+)?)',
                r'PARKING.*?(\d+(?:\.\d+)?)'
            ],
            "handling_cost": [
                r'HANDLING\s*FEE.*?(\d+(?:\.\d+)?)',
                r'HANDLING.*?(\d+(?:\.\d+)?)'
            ],
            "declaration_cost": [
                r'ECLARATION\s*FEE.*?(\d+(?:\.\d+)?)',
                r'DECLARATION.*?(\d+(?:\.\d+)?)'
            ],
            "registration_cost": [
                r'EGISTRATION\s*FEE.*?(\d+(?:\.\d+)?)',
                r'REGISTRATION.*?(\d+(?:\.\d+)?)'
            ]
        }
        
        for cost_type, patterns in cost_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    try:
                        costs[cost_type] = float(match.group(1))
                        break
                    except ValueError:
                        continue
        
        return costs

def analyze_tariff_with_llm(text: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """Функция-обертка для анализа тарифа с LLM."""
    analyzer = LLMTariffAnalyzer(api_key)
    return analyzer.extract_structured_data(text)
