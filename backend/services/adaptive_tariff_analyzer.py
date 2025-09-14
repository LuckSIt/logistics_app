#!/usr/bin/env python3
"""
Адаптивный анализатор тарифов - автоматически определяет формат файла и применяет соответствующие стратегии парсинга.
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

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
                        r'\b(?:HKG|XIY|SVO|PEK|CAN|SHA|CTU|CKG|KMG|XMN|TAO|DLC|TSN|SHE|HGH|NGB|WUH|CSX|CGO|ZRH|FRA|CDG|LHR|JFK|LAX|ORD|DFW|SFO|MIA|ATL|IAH|DEN|LAS|PHX|MCO|BOS|DTW|MSP|CLT|EWR|BWI|IAD|SLC|PDX|AUS|BNA|RDU|CLE|IND|CVG|PIT|MCI|STL|BUF|RNO|TUS|ABQ|BOI|GEG|MSO|BZN|JAC|IDA|PIH|SUN|BOI|GJT|ASE|EGE|HDN|MTJ|GUC|TEX|LWS|PSC|ALW|EAT|GEG|MSO|BZN|JAC|IDA|PIH|SUN|BOI|GJT|ASE|EGE|HDN|MTJ|GUC|TEX|LWS|PSC|ALW|EAT)\b'
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
                        r'\b(?:Shenzhen|Guangzhou|Shanghai|Beijing|Tianjin|Qingdao|Dalian|Ningbo|Xiamen|Fuzhou|Wenzhou|Yiwu|Hangzhou|Suzhou|Nanjing|Wuxi|Changzhou|Zhenjiang|Yangzhou|Nantong|Taizhou|Lianyungang|Huai'an|Suqian|Xuzhou|Lianyungang|Yancheng|Nantong|Taizhou|Lianyungang|Huai'an|Suqian|Xuzhou|Lianyungang|Yancheng)\b'
                    ],
                    "price_patterns": [
                        r'\$\s*(\d+(?:[.,]\d+)?)\s*(?:per\s*truck|за\s*машину)',
                        r'(\d+(?:[.,]\d+)?)\s*(?:USD|usd|\$)\s*(?:per\s*truck|за\s*машину)',
                        r'EXW\s+[^-]+-([^-]+)-\s*\$(\d+(?:[.,]\d+)?)'
                    ],
                    "route_patterns": [
                        r'EXW\s+([^-]+)-([^-]+)-\s*\$',
                        r'([^-]+)\s*[-→]\s*([^-]+)\s*[-→]\s*\$'
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
    
    def analyze_text(self, text: str) -> Dict[str, Any]:
        """Анализирует текст с автоматическим определением формата."""
        self.logger.info("Начинаем адаптивный анализ текста")
        
        # Определяем лучшую стратегию
        best_strategy = self._detect_format(text)
        self.logger.info(f"Выбрана стратегия: {best_strategy.name} (уверенность: {best_strategy.confidence:.2f})")
        
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

def analyze_tariff_text_adaptive(text: str) -> Dict[str, Any]:
    """Адаптивный анализ текста тарифа."""
    analyzer = AdaptiveTariffAnalyzer()
    return analyzer.analyze_text(text)
