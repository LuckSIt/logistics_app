#!/usr/bin/env python3
"""
Адаптивный анализатор тарифов - автоматически определяет формат файла и применяет соответствующие стратегии парсинга.
"""

import re
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# LLM анализатор удален
LLM_AVAILABLE = False

@dataclass
class ParsingStrategy:
    """Стратегия парсинга для определенного формата."""
    name: str
    confidence: float
    patterns: Dict[str, List[str]]
    priority: int

class AdaptiveTariffAnalyzer:
    """Адаптивный анализатор тарифов с автоматическим определением формата."""
    
    def __init__(self):
        self.strategies = self._initialize_strategies()
        self.logger = logging.getLogger(__name__)
    
    def _initialize_strategies(self) -> List[ParsingStrategy]:
        """Инициализирует все доступные стратегии парсинга."""
        return [
            # Стратегия 1: Авиационные тарифы (высокий приоритет)
            ParsingStrategy(
                name="air_tariff",
                confidence=0.0,
                priority=1,
                patterns={
                    "transport_indicators": [
                        r'\b(?:air|airline|AIR|MU|D\d+|flight|авиа|рейс)\b',
                        r'\b(?:HKG|XIY|SVO|PEK|CAN|SHA|CTU|CKG|KMG|XMN|TAO|DLC|TSN|SHE|HGH|NGB|WUH|CSX|CGO)\b'
                    ],
                    "price_patterns": [
                        r'\b(\d+\.?\d*)\s*(?:USD|usd|\$|доллар|долларов?)\b',
                        r'\b(\d+\.?\d*)\s*(?:RUB|руб|рублей?)\b',
                        r'\b(\d+\.?\d*)\s*(?:SD|sd)\b',
                        r'\|\s*(\d+\.?\d*)\s+(\d+\.?\s*\d*)\s+(\d+\.?\s*\d*)\s+(\d+\.?\d*)'
                    ],
                    "route_patterns": [
                        r'\b([A-Z]{3})-([A-Z]{3}(?:-[A-Z0-9]+)?)\b',
                        r'\b([A-Z]{3})\s*[-→]\s*([A-Z]{3})\b'
                    ],
                    "cost_patterns": [
                        r'(?:CAR\s*PARKING|GATE\s*FEE|PARKING)[:\s]*SD\s*(\d+(?:[.,]\d+)?)',
                        r'(?:HANDLING\s*FEE)[:\s]*SD\s*(\d+(?:[.,]\d+)?)',
                        r'(?:ECLARATION\s*FEE)[:\s]*SD\s*(\d+(?:[.,]\d+)?)',
                        r'(?:EGISTRATION\s*FEE)[:\s]*SD\s*(\d+(?:[.,]\d+)?)'
                    ]
                }
            ),
            
            # Стратегия 2: FTL тарифы
            ParsingStrategy(
                name="ftl_tariff",
                confidence=0.0,
                priority=2,
                patterns={
                    "transport_indicators": [
                        r'\b(?:FTL|truck|грузовик|авто|автомобиль|EXW|FCA|CPT|CIP|DAP|DDP)\b',
                        r'\b(?:Shenzhen|Guangzhou|Shanghai|Beijing|Tianjin|Qingdao|Dalian|Ningbo|Xiamen|Fuzhou|Wenzhou|Yiwu|Hangzhou|Suzhou|Nanjing|Wuxi|Changzhou|Zhenjiang|Yangzhou|Nantong|Taizhou|Lianyungang|Huai\'an|Suqian|Xuzhou|Lianyungang|Yancheng|Nantong|Taizhou|Lianyungang|Huai\'an|Suqian|Xuzhou|Lianyungang|Yancheng)\b',
                        r'\b(?:CNY|юань|tilt\s*tautliner|per\s*truck|за\s*машину)\b'
                    ],
                    "price_patterns": [
                        r'\$\s*(\d+(?:[.,]\d+)?)\s*(?:per\s*truck|за\s*машину)',
                        r'(\d+(?:[.,]\d+)?)\s*(?:USD|usd|\$)\s*(?:per\s*truck|за\s*машину)',
                        r'EXW\s+[^-]+-([^-]+)-\s*\$(\d+(?:[.,]\d+)?)',
                        r'(\d+(?:[.,]\d+)?)\s*(?:USD|usd|\$)\s*(?:per\s*truck|за\s*машину)',
                        r'(\d+(?:[.,]\d+)?)\s*(?:доллар|долларов?)\s*(?:за\s*машину|per\s*truck)',
                        # Добавляем китайские паттерны
                        r'(\d+(?:\s*\d+)?)\s*CNY',
                        r'EXW\s+[^:]+:\s*(\d+(?:\s*\d+)?)\s*CNY'
                    ],
                    "route_patterns": [
                        r'EXW\s+([^-]+)-([^-]+)-\s*\$',
                        r'([^-]+)\s*[-→]\s*([^-]+)\s*[-→]\s*\$',
                        r'EXW\s+([^-\n]+?)\s*-\s*([^-\n]+?)\s*-\s*\$?(\d+(?:,\d+)?)'
                    ],
                    "vehicle_patterns": [
                        r'\b(?:tilt\s*tautliner|тент|рефрижератор|контейнеровоз)\b',
                        r'\d+\.\d+\*\d+\.\d+\*\d+\.\d+M'
                    ]
                }
            ),
            
            # Стратегия 3: Морские тарифы
            ParsingStrategy(
                name="sea_tariff",
                confidence=0.0,
                priority=3,
                patterns={
                    "transport_indicators": [
                        r'\b(?:sea|ocean|морской|FCL|LCL|container|контейнер|ship|судно)\b',
                        r'\b(?:Shanghai|Ningbo|Qingdao|Tianjin|Dalian|Xiamen|Guangzhou|Shenzhen|Hong Kong|Singapore|Rotterdam|Hamburg|Antwerp|Le Havre|Los Angeles|Long Beach|New York|Savannah|Charleston|Miami|Houston|Seattle|Vancouver|Toronto|Montreal)\b'
                    ],
                    "price_patterns": [
                        r'\b(\d+(?:[.,]\d+)?)\s*(?:USD|usd|\$)\s*(?:per\s*container|за\s*контейнер)',
                        r'FCL\s*(\d+(?:[.,]\d+)?)\s*(?:USD|usd|\$)',
                        r'LCL\s*(\d+(?:[.,]\d+)?)\s*(?:USD|usd|\$)'
                    ],
                    "route_patterns": [
                        r'([^-]+)\s*[-→]\s*([^-]+)\s*(?:FCL|LCL)',
                        r'FCL\s+([^-]+)-([^-]+)'
                    ]
                }
            ),
            
            # Стратегия 4: Железнодорожные тарифы
            ParsingStrategy(
                name="rail_tariff",
                confidence=0.0,
                priority=4,
                patterns={
                    "transport_indicators": [
                        r'\b(?:rail|железная\s*дорога|поезд|RFCL|FCL|вагон|контейнер)\b',
                        r'\b(?:Moscow|St\.?\s*Petersburg|Novosibirsk|Yekaterinburg|Kazan|Nizhny Novgorod|Chelyabinsk|Samara|Omsk|Rostov|Ufa|Perm|Volgograd|Krasnoyarsk|Saratov|Voronezh|Tolyatti|Krasnodar|Ulyanovsk|Izhevsk|Yaroslavl|Barnaul|Vladivostok|Irkutsk|Khabarovsk|Kemerovo|Ryazan|Astrakhan|Naberezhnye Chelny|Penza|Lipetsk|Kirov|Cheboksary|Tula|Kaliningrad|Kurgan|Ulan-Ude|Stavropol|Sochi|Ivanovo|Bryansk|Tver|Belgorod|Arkhangelsk|Vladimir|Chita|Grozny|Kaluga|Smolensk|Volzhsky|Murmansk|Vladikavkaz|Saransk|Yakutsk|Cherepovets|Vologda|Orjol|Kurgan|Sterlitamak|Grozny|Ulan-Ude|Vladikavkaz|Saransk|Yakutsk|Cherepovets|Vologda|Orjol|Kurgan|Sterlitamak)\b'
                    ],
                    "price_patterns": [
                        r'\b(\d+(?:[.,]\d+)?)\s*(?:RUB|руб|рублей?)\s*(?:за\s*вагон|per\s*wagon)',
                        r'RFCL\s*(\d+(?:[.,]\d+)?)\s*(?:RUB|руб)',
                        r'FCL\s*(\d+(?:[.,]\d+)?)\s*(?:RUB|руб)'
                    ],
                    "route_patterns": [
                        r'([^-]+)\s*[-→]\s*([^-]+)\s*(?:RFCL|FCL)',
                        r'RFCL\s+([^-]+)-([^-]+)'
                    ]
                }
            ),
            
            # Стратегия 5: Универсальная (низкий приоритет)
            ParsingStrategy(
                name="universal",
                confidence=0.0,
                priority=5,
                patterns={
                    "transport_indicators": [
                        r'\b(?:тариф|tariff|цена|price|стоимость|cost)\b'
                    ],
                    "price_patterns": [
                        r'\b(\d+(?:[.,]\d+)?)\s*(?:USD|usd|\$|RUB|руб)\b',
                        r'\b(\d+(?:[.,]\d+)?)\s*(?:доллар|рубль|долларов?|рублей?)\b'
                    ],
                    "route_patterns": [
                        r'([^-]+)\s*[-→]\s*([^-]+)',
                        r'от\s+([^-]+)\s+до\s+([^-]+)',
                        r'from\s+([^-]+)\s+to\s+([^-]+)'
                    ]
                }
            )
        ]
    
    def analyze_text(self, text: str, use_llm: bool = False, llm_api_key: Optional[str] = None) -> Dict[str, Any]:
        """Анализирует текст с автоматическим определением формата."""
        self.logger.info("Начинаем адаптивный анализ текста")
        
        # Определяем лучшую стратегию
        best_strategy = self._detect_format(text)
        self.logger.info(f"Выбрана стратегия: {best_strategy.name} (уверенность: {best_strategy.confidence:.2f})")
        
        # Если это авиационный тариф и LLM доступен, используем его
        if use_llm and LLM_AVAILABLE and best_strategy.name == "air_tariff":
            self.logger.info("Используем LLM для анализа авиационного тарифа")
            try:
                # LLM анализ отключен
                llm_result = None
                # Объединяем результаты
                result = self._apply_strategy(text, best_strategy)
                result.update(llm_result)
                return result
            except Exception as e:
                self.logger.error(f"Ошибка LLM анализа, используем стандартный: {e}")
        
        # Применяем выбранную стратегию
        result = self._apply_strategy(text, best_strategy)
        
        return result
    
    def _detect_format(self, text: str) -> ParsingStrategy:
        """Определяет формат файла и выбирает лучшую стратегию."""
        text_lower = text.lower()
        
        for strategy in self.strategies:
            confidence = 0.0
            total_patterns = 0
            matched_patterns = 0
            
            # Проверяем индикаторы транспорта
            for pattern in strategy.patterns.get("transport_indicators", []):
                total_patterns += 1
                if re.search(pattern, text_lower, re.IGNORECASE):
                    matched_patterns += 1
            
            # Проверяем паттерны цен
            for pattern in strategy.patterns.get("price_patterns", []):
                total_patterns += 1
                if re.search(pattern, text, re.IGNORECASE):
                    matched_patterns += 1
            
            # Проверяем паттерны маршрутов
            for pattern in strategy.patterns.get("route_patterns", []):
                total_patterns += 1
                if re.search(pattern, text, re.IGNORECASE):
                    matched_patterns += 1
            
            # Вычисляем уверенность
            if total_patterns > 0:
                confidence = matched_patterns / total_patterns
            
            strategy.confidence = confidence
        
        # Выбираем стратегию с наивысшей уверенностью и приоритетом
        best_strategy = max(self.strategies, key=lambda s: (s.confidence, -s.priority))
        
        return best_strategy
    
    def _apply_strategy(self, text: str, strategy: ParsingStrategy) -> Dict[str, Any]:
        """Применяет выбранную стратегию для извлечения данных."""
        result = {
            "transport_type": None,
            "basis": "EXW",
            "routes": [],
            "vehicle_type": None,
            "price_rub": None,
            "price_usd": None,
            "validity_date": None,
            "transit_time_days": None,
            "transit_port": None,
            "departure_station": None,
            "arrival_station": None,
            "rail_tariff_rub": None,
            "cbx_cost": None,
            "terminal_handling_cost": None,
            "auto_pickup_cost": None,
            "security_cost": None,
            "precarriage_cost": None,
            "car_parking_cost": None,
            "handling_cost": None,
            "declaration_cost": None,
            "registration_cost": None
        }
        
        # Определяем тип транспорта на основе стратегии
        transport_mapping = {
            "air_tariff": "air",
            "ftl_tariff": "auto",
            "sea_tariff": "sea",
            "rail_tariff": "rail",
            "universal": "auto"
        }
        result["transport_type"] = transport_mapping.get(strategy.name, "auto")
        
        # Извлекаем маршруты
        result["routes"] = self._extract_routes(text, strategy)
        
        # Извлекаем цены
        prices = self._extract_prices(text, strategy)
        if prices:
            result["price_usd"] = prices.get("usd")
            result["price_rub"] = prices.get("rub")
        
        # Извлекаем дополнительные затраты
        costs = self._extract_costs(text, strategy)
        for cost_key, value in costs.items():
            if value is not None:
                result[cost_key] = value
        
        # Извлекаем тип ТС
        result["vehicle_type"] = self._extract_vehicle_type(text, strategy)
        
        return result
    
    def _extract_routes(self, text: str, strategy: ParsingStrategy) -> List[Dict[str, Any]]:
        """Извлекает маршруты из текста."""
        routes = []
        lines = text.split('\n')
        
        # Специальная обработка для авиационных тарифов
        if strategy.name == "air_tariff":
            routes = self._extract_air_routes(text, lines)
        elif strategy.name == "ftl_tariff":
            routes = self._extract_ftl_routes(text, lines)
        else:
            # Общая обработка для остальных типов
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Ищем маршруты с помощью паттернов стратегии
                for pattern in strategy.patterns.get("route_patterns", []):
                    matches = re.finditer(pattern, line, re.IGNORECASE)
                    for match in matches:
                        if len(match.groups()) >= 2:
                            origin = match.group(1).strip()
                            destination = match.group(2).strip()
                            
                            # Определяем страны
                            origin_country = self._determine_country(origin)
                            destination_country = self._determine_country(destination)
                            
                            # Ищем цены для этого маршрута
                            prices = self._extract_prices_for_route(line, strategy)
                            
                            route = {
                                "origin_country": origin_country,
                                "origin_city": origin,
                                "destination_country": destination_country,
                                "destination_city": destination,
                                "price_rub": prices.get("rub"),
                                "price_usd": prices.get("usd"),
                                "transit_time_days": None
                            }
                            
                            routes.append(route)
        
        return routes
    
    def _extract_air_routes(self, text: str, lines: List[str]) -> List[Dict[str, Any]]:
        """Специальная обработка авиационных маршрутов."""
        routes = []
        
        # Объединяем строки для лучшего поиска
        combined_text = ' '.join(lines)
        
        # Ищем авиационные маршруты с ценами
        air_patterns = [
            r'([A-Z]{3})-([A-Z]{3}(?:-[A-Z0-9]+)?)\s+(\d+/\w+)\s+(\d+\.?\d*)\s+(\d+\.?\d*)\s+(\d+\.?\d*)\s+(\d+\.?\d*)',
            r'([A-Z]{3})-([A-Z]{3}(?:-[A-Z0-9]+)?)\s+(\d+/\w+)\s*[|]\s*(\d+\.?\d*)\s+(\d+\.?\s*\d*)\s+(\d+\.?\s*\d*)\s+(\d+\.?\d*)',
            r'([A-Z]{3})-([A-Z]{3})\s+(\d+/\w+)\s+(\d+\.?\d*)\s+(\d+\.?\d*)\s+(\d+\.?\d*)\s+(\d+\.?\d*)'
        ]
        
        for pattern in air_patterns:
            matches = re.finditer(pattern, combined_text, re.IGNORECASE)
            for match in matches:
                origin_code = match.group(1)
                destination_code = match.group(2)
                
                # Определяем города по кодам
                origin_city = self._get_city_by_code(origin_code)
                destination_city = self._get_city_by_code(destination_code)
                
                if origin_city and destination_city:
                    # Извлекаем цены
                    prices = []
                    for i in range(4, 8):
                        try:
                            price = float(match.group(i).replace(',', '.'))
                            prices.append(price)
                        except (ValueError, IndexError):
                            prices.append(None)
                    
                    route = {
                        "origin_country": self._determine_country(origin_city),
                        "origin_city": origin_city,
                        "destination_country": self._determine_country(destination_city),
                        "destination_city": destination_city,
                        "price_rub": None,
                        "price_usd": prices[0] if prices[0] else None,  # Первая цена как основная
                        "transit_time_days": None
                    }
                    
                    routes.append(route)
        
        return routes
    
    def _extract_ftl_routes(self, text: str, lines: List[str]) -> List[Dict[str, Any]]:
        """Специальная обработка FTL маршрутов."""
        routes = []
        
        # Объединяем строки для лучшего поиска
        combined_text = ' '.join(lines)
        
        # Ищем EXW маршруты с ценами (поддерживаем USD и CNY)
        exw_patterns = [
            # Паттерны с USD - основной формат для FTL
            r'EXW\s+([^-]+?)\s*-\s*([^-]+?)\s*-\s*\$(\d+(?:,\d+)?)',
            r'EXW\s+([^-]+?)\s*-\s*([^-]+?)\s*-\s*\$(\d+(?:,\d+)?)\s*per\s*truck',
            r'EXW\s+([^-]+?)\s*-\s*([^-]+?)\s*-\s*([^-\n]+)',
            
            # Паттерны с CNY - для китайских тарифов
            # Специальный паттерн для Shanghai/Guangzhou-KZ-Moscow: 78 600 CNY
            r'EXW\s+([^-:]+?)-([^-:]+?)-([^:]+?):\s*(\d+(?:\s*\d+)?)\s*CNY',
            # Базовые паттерны с двоеточием
            r'EXW\s+([^:\n]+?):\s*(\d+(?:\s*\d+)?)\s*CNY',
            r'EXW\s+([^:\n]+?)-([^:\n]+?):\s*(\d+(?:\s*\d+)?)\s*CNY',
            r'EXW\s+([^:\n]+?)[/-]([^:\n]+?):\s*(\d+(?:\s*\d+)?)\s*CNY/FTL',
            r'EXW\s+([^:\n]+?)[/-]([^:\n]+?):\s*(\d+(?:\s*\d+)?)\s*CNY/(\d+)cbm',
            
            # Паттерны с переносами строк
            r'EXW\s+([^:\n]+?):\s*(\d+(?:\s*\d+)?)\s*\n\s*CNY',
            r'EXW\s+([^:\n]+?)[/-]([^:\n]+?):\s*(\d+(?:\s*\d+)?)\s*\n\s*CNY/FTL'
        ]
        
        for pattern in exw_patterns:
            matches = re.finditer(pattern, combined_text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                groups = match.groups()
                
                # Разные паттерны имеют разную структуру групп
                transit_text = None  # Инициализируем для всех случаев
                
                if len(groups) >= 4:
                    # Специальный паттерн для маршрутов типа Origin-Transit-Destination: Price CNY
                    origin_text = groups[0].strip()
                    transit_text = groups[1].strip()
                    destination_text = groups[2].strip()
                    price_text = groups[3].strip()
                    
                    # Извлекаем цену в CNY и конвертируем в USD
                    try:
                        price_cny = float(price_text.replace(' ', '').replace(',', '.'))
                        price_usd = price_cny * 0.14  # Конвертируем в USD
                    except ValueError:
                        price_usd = None
                        
                elif len(groups) >= 3:
                    # USD паттерны: (origin, destination, price)
                    origin_text = groups[0].strip()
                    destination_text = groups[1].strip()
                    price_text = groups[2].strip()
                    
                    # Определяем валюту и извлекаем цену
                    price_usd = None
                    if '$' in price_text or 'USD' in price_text.upper():
                        # USD цена
                        price_match = re.search(r'(\d+(?:,\d+)?)', price_text)
                        if price_match:
                            try:
                                price_usd = float(price_match.group(1).replace(',', ''))
                            except ValueError:
                                pass
                    elif 'CNY' in price_text.upper():
                        # CNY цена - конвертируем в USD
                        price_match = re.search(r'(\d+(?:\s*\d+)?)', price_text)
                        if price_match:
                            try:
                                price_cny = float(price_match.group(1).replace(' ', ''))
                                price_usd = price_cny * 0.14  # Примерный курс CNY к USD
                            except ValueError:
                                pass
                    else:
                        # Пытаемся извлечь числовое значение
                        price_match = re.search(r'(\d+(?:,\d+)?)', price_text)
                        if price_match:
                            try:
                                price_usd = float(price_match.group(1).replace(',', ''))
                            except ValueError:
                                pass
                    
                elif len(groups) >= 2:
                    # CNY паттерны: (route, price) или (origin-destination, price)
                    if '-' in groups[0]:
                        # Разбиваем маршрут на части
                        route_parts = groups[0].split('-', 1)
                        origin_text = route_parts[0].strip()
                        destination_text = route_parts[1].strip() if len(route_parts) > 1 else ""
                    else:
                        origin_text = groups[0].strip()
                        destination_text = groups[1].strip() if len(groups) > 1 else ""
                    
                    # Извлекаем цену в CNY
                    price_text = groups[-1]  # Последняя группа - цена
                    try:
                        price_cny = float(price_text.replace(' ', '').replace(',', '.'))
                        price_usd = price_cny * 0.14  # Конвертируем в USD
                    except (ValueError, IndexError):
                        price_usd = None
                else:
                    continue  # Пропускаем некорректные паттерны
                
                # Обрабатываем города с разделителями
                origin_cities = [city.strip() for city in origin_text.split('/') if city.strip()]
                destination_cities = [city.strip() for city in destination_text.split('/') if city.strip()] if destination_text else []
                
                # Специальная обработка для маршрутов с транзитом (4 группы)
                if len(groups) >= 4 and transit_text:
                    # Для случая Origin-Transit-Destination создаем прямой маршрут Origin -> Destination
                    # Игнорируем транзитную точку для простоты, так как это просто указание маршрута
                    
                    # Убираем переопределение destination_cities, используем уже извлеченные
                    destination_cities = [self._find_city_in_text(destination_text)]
                    destination_cities = [city for city in destination_cities if city]
                    
                    # Если destination_cities пуст, пытаемся использовать транзитную точку как назначение
                    if not destination_cities:
                        if transit_text.upper() == 'KZ':
                            destination_cities = ['Kazakhstan']
                        elif transit_text.upper() == 'MZL':
                            destination_cities = ['Moscow']
                        else:
                            transit_city = self._find_city_in_text(transit_text)
                            if transit_city:
                                destination_cities = [transit_city]
                
                # Если нет назначения, пытаемся найти его в origin_text
                elif not destination_cities and '-' in origin_text:
                    parts = origin_text.split('-')
                    if len(parts) >= 2:
                        origin_cities = [city.strip() for city in parts[0].split('/') if city.strip()]
                        destination_cities = [city.strip() for city in parts[-1].split('/') if city.strip()]
                
                # Создаем маршруты для всех комбинаций
                for origin_part in origin_cities:
                    for dest_part in destination_cities:
                        origin_city = self._find_city_in_text(origin_part)
                        destination_city = self._find_city_in_text(dest_part)
                        
                        if origin_city and destination_city:
                            route = {
                                "origin_country": self._determine_country(origin_city),
                                "origin_city": origin_city,
                                "destination_country": self._determine_country(destination_city),
                                "destination_city": destination_city,
                                "price_rub": None,
                                "price_usd": price_usd,
                                "transit_time_days": None
                            }
                            
                            # Проверяем, что такой маршрут еще не добавлен
                            if not any(r["origin_city"] == route["origin_city"] and 
                                      r["destination_city"] == route["destination_city"] 
                                      for r in routes):
                                routes.append(route)
        
        return routes
    
    def _get_city_by_code(self, code: str) -> str:
        """Определяет город по коду аэропорта."""
        airport_codes = {
            "HKG": "Hong Kong",
            "XIY": "Xian",
            "PEK": "Beijing",
            "PVG": "Shanghai",
            "CAN": "Guangzhou",
            "SZX": "Shenzhen",
            "NGB": "Ningbo",
            "TSN": "Tianjin",
            "TAO": "Qingdao",
            "MOW": "Moscow",
            "LED": "St. Petersburg",
            "MSQ": "Minsk"
        }
        
        return airport_codes.get(code.upper(), code)
    
    def _find_city_in_text(self, text: str) -> str:
        """Ищет город в тексте."""
        cities = [
            "Shenzhen", "Guangzhou", "Shanghai", "Beijing", "Tianjin", "Qingdao",
            "Dalian", "Ningbo", "Xiamen", "Fuzhou", "Wenzhou", "Yiwu", "Hangzhou",
            "Suzhou", "Nanjing", "Wuxi", "Changzhou", "Zhenjiang", "Yangzhou",
            "Nantong", "Taizhou", "Lianyungang", "Huai'an", "Suqian", "Xuzhou",
            "Yancheng", "Moscow", "St. Petersburg", "Novosibirsk", "Yekaterinburg",
            "Kazan", "Nizhny Novgorod", "Chelyabinsk", "Samara", "Omsk", "Rostov",
            "Ufa", "Perm", "Volgograd", "Krasnoyarsk", "Saratov", "Voronezh",
            "Tolyatti", "Krasnodar", "Ulyanovsk", "Izhevsk", "Yaroslavl", "Barnaul",
            "Vladivostok", "Irkutsk", "Khabarovsk", "Kemerovo", "Ryazan", "Astrakhan",
            "Naberezhnye Chelny", "Penza", "Lipetsk", "Kirov", "Cheboksary", "Tula",
            "Kaliningrad", "Kurgan", "Ulan-Ude", "Stavropol", "Sochi", "Ivanovo",
            "Bryansk", "Tver", "Belgorod", "Arkhangelsk", "Vladimir", "Chita",
            "Grozny", "Kaluga", "Smolensk", "Volzhsky", "Murmansk", "Vladikavkaz",
            "Saransk", "Yakutsk", "Cherepovets", "Vologda", "Orjol", "Sterlitamak"
        ]
        
        # Сначала ищем точное совпадение
        for city in cities:
            if re.search(rf'\b{re.escape(city)}\b', text, re.IGNORECASE):
                return city
        
        # Если не нашли, ищем частичные совпадения
        text_lower = text.lower()
        for city in cities:
            city_lower = city.lower()
            if city_lower in text_lower or text_lower in city_lower:
                return city
        
        # Специальная обработка для кодов стран
        country_codes = {
            "KZ": "Kazakhstan",
            "MZL": "Moscow"
        }
        
        for code, country in country_codes.items():
            if code.lower() in text_lower:
                return country
        
        return None
    
    def _extract_prices(self, text: str, strategy: ParsingStrategy) -> Dict[str, Optional[float]]:
        """Извлекает цены из текста."""
        prices = {"usd": None, "rub": None}
        
        for pattern in strategy.patterns.get("price_patterns", []):
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    price_text = match.group(1)
                    price = float(re.sub(r'[^\d.,]', '', price_text).replace(',', '.'))
                    
                    # Определяем валюту
                    if re.search(r'(?:USD|usd|\$|доллар)', match.group(0), re.IGNORECASE):
                        if prices["usd"] is None:
                            prices["usd"] = price
                    elif re.search(r'(?:RUB|руб|рублей?)', match.group(0), re.IGNORECASE):
                        if prices["rub"] is None:
                            prices["rub"] = price
                    else:
                        # По умолчанию считаем USD
                        if prices["usd"] is None:
                            prices["usd"] = price
                except (ValueError, IndexError):
                    continue
        
        return prices
    
    def _extract_prices_for_route(self, line: str, strategy: ParsingStrategy) -> Dict[str, Optional[float]]:
        """Извлекает цены для конкретного маршрута."""
        return self._extract_prices(line, strategy)
    
    def _extract_costs(self, text: str, strategy: ParsingStrategy) -> Dict[str, Optional[float]]:
        """Извлекает дополнительные затраты."""
        costs = {}
        
        # Паттерны для дополнительных затрат
        cost_patterns = {
            "car_parking_cost": [
                r'(?:CAR\s*PARKING|GATE\s*FEE|PARKING)[:\s]*SD\s*(\d+(?:[.,]\d+)?)',
                r'(?:CAR\s*PARKING|GATE\s*FEE|PARKING)[:\s]*USD?\s*(\d+(?:[.,]\d+)?)'
            ],
            "handling_cost": [
                r'(?:HANDLING\s*FEE|HANDLING)[:\s]*SD\s*(\d+(?:[.,]\d+)?)',
                r'(?:HANDLING\s*FEE|HANDLING)[:\s]*USD?\s*(\d+(?:[.,]\d+)?)'
            ],
            "declaration_cost": [
                r'(?:ECLARATION\s*FEE|DECLARATION)[:\s]*SD\s*(\d+(?:[.,]\d+)?)',
                r'(?:DECLARATION\s*FEE|DECLARATION)[:\s]*USD?\s*(\d+(?:[.,]\d+)?)'
            ],
            "registration_cost": [
                r'(?:EGISTRATION\s*FEE|REGISTRATION)[:\s]*SD\s*(\d+(?:[.,]\d+)?)',
                r'(?:REGISTRATION\s*FEE|REGISTRATION)[:\s]*USD?\s*(\d+(?:[.,]\d+)?)'
            ]
        }
        
        for cost_key, patterns in cost_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    try:
                        cost = float(match.group(1).replace(',', '.'))
                        costs[cost_key] = cost
                        break
                    except (ValueError, IndexError):
                        continue
        
        return costs
    
    def _extract_vehicle_type(self, text: str, strategy: ParsingStrategy) -> Optional[str]:
        """Извлекает тип транспортного средства."""
        if strategy.name == "air_tariff":
            # Для авиации ищем тип самолета или код
            match = re.search(r'(\d+/\w+)', text)
            if match:
                return match.group(1)
        
        elif strategy.name == "ftl_tariff":
            # Для FTL ищем тип грузовика
            vehicle_patterns = [
                r'\b(?:tilt\s*tautliner|тент|рефрижератор)\b',
                r'\d+\.\d+\*\d+\.\d+\*\d+\.\d+M'
            ]
            for pattern in vehicle_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    return match.group(0)
        
        return None
    
    def _determine_country(self, city: str) -> str:
        """Определяет страну по названию города."""
        city_lower = city.lower()
        
        # Китай
        chinese_cities = [
            'shenzhen', 'guangzhou', 'shanghai', 'beijing', 'tianjin', 'qingdao', 
            'dalian', 'ningbo', 'xiamen', 'fuzhou', 'wenzhou', 'yiwu', 'hangzhou',
            'suzhou', 'nanjing', 'wuxi', 'changzhou', 'zhenjiang', 'yangzhou',
            'nantong', 'taizhou', 'lianyungang', 'huai\'an', 'suqian', 'xuzhou',
            'yancheng', 'hkg', 'hong kong', 'xiy', 'xian', 'pek', 'can', 'sha',
            'ctu', 'ckg', 'kmg', 'xmn', 'tao', 'dlc', 'tsn', 'she', 'hgh', 'ngb',
            'wuh', 'csx', 'cgo'
        ]
        
        # Россия
        russian_cities = [
            'moscow', 'москва', 'st. petersburg', 'saint petersburg', 'санкт-петербург',
            'novosibirsk', 'новосибирск', 'yekaterinburg', 'екатеринбург', 'kazan',
            'казань', 'nizhny novgorod', 'нижний новгород', 'chelyabinsk', 'челябинск',
            'samara', 'самара', 'omsk', 'омск', 'rostov', 'ростов', 'ufa', 'уфа',
            'perm', 'пермь', 'volgograd', 'волгоград', 'krasnoyarsk', 'красноярск',
            'saratov', 'саратов', 'voronezh', 'воронеж', 'tolyatti', 'тольятти',
            'krasnodar', 'краснодар', 'ulyanovsk', 'ульяновск', 'izhevsk', 'ижевск',
            'yaroslavl', 'ярославль', 'barnaul', 'барнаул', 'vladivostok', 'владивосток',
            'irkutsk', 'иркутск', 'khabarovsk', 'хабаровск', 'kemerovo', 'кемерово',
            'ryazan', 'рязань', 'astrakhan', 'астрахань', 'naberezhnye chelny',
            'набережные челны', 'penza', 'пенза', 'lipetsk', 'липецк', 'kirov',
            'киров', 'cheboksary', 'чебоксары', 'tula', 'тула', 'kaliningrad',
            'калининград', 'kurgan', 'курган', 'ulan-ude', 'улан-удэ', 'stavropol',
            'ставрополь', 'sochi', 'сочи', 'ivanovo', 'иваново', 'bryansk', 'брянск',
            'tver', 'тверь', 'belgorod', 'белгород', 'arkhangelsk', 'архангельск',
            'vladimir', 'владимир', 'chita', 'чита', 'grozny', 'грозный', 'kaluga',
            'калуга', 'smolensk', 'смоленск', 'volzhsky', 'волжский', 'murmansk',
            'мурманск', 'vladikavkaz', 'владикавказ', 'saransk', 'саранск', 'yakutsk',
            'якутск', 'cherepovets', 'череповец', 'vologda', 'вологда', 'orjol',
            'орёл', 'sterlitamak', 'стерлитамак', 'svo', 'moscow', 'spb', 'peter'
        ]
        
        # Беларусь
        belarus_cities = [
            'minsk', 'минск', 'gomel', 'гомель', 'mogilev', 'могилёв', 'vitebsk',
            'витебск', 'grodno', 'гродно', 'brest', 'брест', 'bobruisk', 'бобруйск',
            'baranovichi', 'барановичи', 'borisov', 'борисов', 'pinsk', 'пинск',
            'orsha', 'орша', 'mozyr', 'мозырь', 'soligorsk', 'солигорск', 'novopolotsk',
            'новополоцк', 'lida', 'лида', 'molodechno', 'молодечно', 'polotsk',
            'полоцк', 'slutsk', 'слуцк', 'zhlobin', 'жлобин', 'slonim', 'слоним',
            'kobrin', 'кобрин', 'volkovysk', 'волковыск', 'kalinkovichi', 'калинковичи',
            'smarhon', 'сморгонь', 'rogachev', 'рогачёв', 'osipovichi', 'осиповичи',
            'berezino', 'березино', 'dzerzhinsk', 'дзержинск', 'ivye', 'ивье',
            'marina gorka', 'марина горка', 'fanipol', 'фаниполь', 'berezovka',
            'березовка', 'lyuban', 'любань', 'stolbtsy', 'столбцы', 'uzda', 'узда',
            'kopyl', 'копыль', 'kletsk', 'клецк', 'nesvizh', 'несвиж', 'cherven',
            'червень', 'smolevichi', 'смолевичи', 'logoysk', 'логиск', 'starye dorogi',
            'старые дороги', 'krupki', 'крупки', 'myadel', 'мядель', 'vileika',
            'вилейка', 'postavy', 'поставы', 'glubokoye', 'глубокое', 'sharkovshchina',
            'шарковщина', 'miory', 'миоры', 'braslav', 'браслав', 'verhnedvinsk',
            'верхнедвинск', 'rossony', 'россоны', 'dokshitsy', 'докшицы', 'lepel',
            'лепель', 'chashniki', 'чашники', 'belynichi', 'белыничи', 'kostyukovichi',
            'костюковичи', 'klimovichi', 'климовичи', 'krichev', 'кричев', 'cherikov',
            'чериков', 'slavgorod', 'славгород', 'bykhov', 'быхов', 'rogachev',
            'рогачёв', 'zhlobin', 'жлобин', 'rechitsa', 'речица', 'svetlogorsk',
            'светлогорск', 'kalinkovichi', 'калинковичи', 'mozyr', 'мозырь', 'petrikov',
            'петриков', 'el\'sk', 'ельск', 'narovlya', 'наровля', 'lelitchev',
            'лельчицы', 'zhitkovichi', 'житковичи', 'oktyabrsky', 'октябрьский',
            'luninets', 'лунинец', 'pinsk', 'пинск', 'ivanovo', 'иваново', 'drogichin',
            'дрогичин', 'berezovka', 'березовка', 'antopol', 'антополь', 'david-gorodok',
            'давид-городок', 'stolin', 'столин', 'mikashevichi', 'микашевичи',
            'luninets', 'лунинец', 'zhitkovichi', 'житковичи', 'oktyabrsky',
            'октябрьский', 'lelitchev', 'лельчицы', 'narovlya', 'наровля', 'el\'sk',
            'ельск', 'petrikov', 'петриков', 'mozyr', 'мозырь', 'kalinkovichi',
            'калинковичи', 'svetlogorsk', 'светлогорск', 'rechitsa', 'речица',
            'zhlobin', 'жлобин', 'rogachev', 'рогачёв', 'bykhov', 'быхов', 'slavgorod',
            'славгород', 'cherikov', 'чериков', 'krichev', 'кричев', 'klimovichi',
            'климовичи', 'kostyukovichi', 'костюковичи', 'belynichi', 'белыничи',
            'chashniki', 'чашники', 'lepel', 'лепель', 'dokshitsy', 'докшицы',
            'rossony', 'россоны', 'verhnedvinsk', 'верхнедвинск', 'braslav',
            'браслав', 'miory', 'миоры', 'sharkovshchina', 'шарковщина', 'glubokoye',
            'глубокое', 'postavy', 'поставы', 'vileika', 'вилейка', 'myadel',
            'мядель', 'krupki', 'крупки', 'starye dorogi', 'старые дороги',
            'logoysk', 'логиск', 'smolevichi', 'смолевичи', 'cherven', 'червень',
            'nesvizh', 'несвиж', 'kletsk', 'клецк', 'kopyl', 'копыль', 'uzda',
            'узда', 'stolbtsy', 'столбцы', 'lyuban', 'любань', 'berezovka',
            'березовка', 'fanipol', 'фаниполь', 'marina gorka', 'марина горка',
            'ivye', 'ивье', 'dzerzhinsk', 'дзержинск', 'berezino', 'березино',
            'osipovichi', 'осиповичи', 'rogachev', 'рогачёв', 'kalinkovichi',
            'калинковичи', 'volkovysk', 'волковыск', 'kobrin', 'кобрин', 'slonim',
            'слоним', 'zhlobin', 'жлобин', 'slutsk', 'слуцк', 'polotsk', 'полоцк',
            'molodechno', 'молодечно', 'lida', 'лида', 'novopolotsk', 'новополоцк',
            'soligorsk', 'солигорск', 'mozyr', 'мозырь', 'orsha', 'орша', 'pinsk',
            'пинск', 'borisov', 'борисов', 'baranovichi', 'барановичи', 'bobruisk',
            'бобруйск', 'brest', 'брест', 'grodno', 'гродно', 'vitebsk', 'витебск',
            'mogilev', 'могилёв', 'gomel', 'гомель', 'minsk', 'минск'
        ]
        
        if city_lower in chinese_cities:
            return "Китай"
        elif city_lower in russian_cities:
            return "Россия"
        elif city_lower in belarus_cities:
            return "Беларусь"
        else:
            return "Неизвестно"

def analyze_tariff_text_adaptive(text: str, use_llm: bool = False, llm_api_key: Optional[str] = None) -> Dict[str, Any]:
    """Адаптивный анализ текста тарифа."""
    analyzer = AdaptiveTariffAnalyzer()
    return analyzer.analyze_text(text, use_llm, llm_api_key)
