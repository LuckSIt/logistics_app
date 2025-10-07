from typing import Dict, Type
from services.base_parser import BaseParser
from services.auto_parser import AutoParser
from services.railway_parser import RailwayParser
from services.sea_parser import SeaParser
from services.air_parser import AirParser
from services.multimodal_parser import MultimodalParser
from services.llm_parser import LLMTariffParser

class ParserFactory:
    """
    Фабрика для создания специализированных парсеров
    """
    
    _parsers: Dict[str, Type[BaseParser]] = {
        'auto': AutoParser,
        'rail': RailwayParser,
        'sea': SeaParser,
        'air': AirParser,
        'multimodal': MultimodalParser,
        'llm': LLMTariffParser,  # LLM парсер для универсальной обработки
    }
    
    @classmethod
    def get_parser(cls, transport_type: str) -> BaseParser:
        """
        Получение парсера для указанного типа транспорта
        """
        parser_class = cls._parsers.get(transport_type.lower())
        if not parser_class:
            raise ValueError(f"Парсер для типа транспорта '{transport_type}' не найден")
        
        return parser_class()
    
    @classmethod
    def get_available_transport_types(cls) -> list:
        """
        Получение списка доступных типов транспорта
        """
        return list(cls._parsers.keys())
    
    @classmethod
    def detect_transport_type(cls, file_path: str, content: str = None) -> str:
        """
        Автоматическое определение типа транспорта по содержимому файла
        """
        if not content:
            # Если контент не передан, пытаемся извлечь из файла
            try:
                from parsers import extract_text_from_file
                content = extract_text_from_file(file_path)
            except Exception:
                return 'auto'  # По умолчанию
        
        if not content:
            return 'auto'
        
        content_lower = content.lower()
        
        # Определяем тип транспорта по ключевым словам
        transport_indicators = {
            'auto': [
                'автомобиль', 'авто', 'машина', 'грузовик', 'фура',
                'ftl', 'ltl', 'дверь-дверь', 'дверь до двери',
                'автовывоз', 'автодоставка', 'автоперевозка'
            ],
            'rail': [
                'железнодорожный', 'жд', 'вагон', 'контейнер',
                'железная дорога', 'жд перевозка', 'ж/д',
                'контейнерный вагон', 'платформа', 'крытый вагон'
            ],
            'sea': [
                'морской', 'море', 'судно', 'корабль', 'контейнеровоз',
                'fcl', 'lcl', 'bulk', 'порт', 'причал', 'доки',
                'коносамент', 'фрахт', 'демередж'
            ],
            'air': [
                'авиа', 'самолет', 'воздушный', 'аэропорт',
                'авианакладная', 'авиаперевозка', 'авиадоставка',
                'express', 'charter', 'cargo'
            ],
            'multimodal': [
                'мультимодальный', 'мульти', 'комбинированный',
                'перегрузка', 'трансшипмент', 'интермодальный'
            ]
        }
        
        # Подсчитываем совпадения для каждого типа
        scores = {}
        for transport_type, indicators in transport_indicators.items():
            score = sum(1 for indicator in indicators if indicator in content_lower)
            scores[transport_type] = score
        
        # Возвращаем тип с наибольшим количеством совпадений
        if scores:
            best_type = max(scores, key=scores.get)
            if scores[best_type] > 0:
                return best_type
        
        # Если не удалось определить, возвращаем авто по умолчанию
        return 'auto'
    
    @classmethod
    def parse_with_auto_detection(cls, file_path: str, supplier_id: int) -> list:
        """
        Парсинг файла с автоматическим определением типа транспорта
        """
        # Определяем тип транспорта
        transport_type = cls.detect_transport_type(file_path)
        
        # Получаем соответствующий парсер
        parser = cls.get_parser(transport_type)
        
        # Парсим данные
        return parser.parse_tariff_data(file_path, supplier_id)
    
    @classmethod
    def register_parser(cls, transport_type: str, parser_class: Type[BaseParser]):
        """
        Регистрация нового парсера
        """
        cls._parsers[transport_type.lower()] = parser_class
