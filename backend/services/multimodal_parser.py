#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Специализированный парсер для мультимодальных тарифов
"""

import re
import logging
from typing import List, Dict, Any, Optional
from base_parser import BaseParser
from adaptive_analyzer import AdaptiveTariffAnalyzer

logger = logging.getLogger(__name__)

class MultimodalParser(BaseParser):
    """Специализированный парсер для мультимодальных тарифов."""
    
    def __init__(self):
        super().__init__()
        self.analyzer = AdaptiveTariffAnalyzer()
        self.transport_type = "multimodal"
        
    def parse_tariff_data(self, file_path: str, supplier_id: int) -> List[Dict[str, Any]]:
        """
        Парсинг мультимодальных тарифов из файла.
        
        Args:
            file_path: Путь к файлу для парсинга
            supplier_id: ID поставщика
            
        Returns:
            Список словарей с данными тарифов
        """
        logger.info(f"Начинаем парсинг мультимодальных тарифов из файла: {file_path}")
        
        # Извлекаем текст из файла
        text = self.extract_text_from_file(file_path)
        if not text:
            logger.warning(f"Не удалось извлечь текст из файла: {file_path}")
            return []
            
        # Анализируем текст с помощью адаптивного анализатора
        parsed_data = self.analyzer.analyze_tariff_text_adaptive(text)
        
        # Фильтруем только мультимодальные данные
        multimodal_data = self._filter_multimodal_data(parsed_data)
        
        # Преобразуем данные в стандартный формат
        tariffs = []
        for data in multimodal_data:
            tariff = self._convert_to_standard_format(data, supplier_id, file_path)
            if tariff and self.validate_parsed_data(tariff):
                tariffs.append(tariff)
                
        logger.info(f"Извлечено {len(tariffs)} мультимодальных тарифов")
        return tariffs
    
    def _filter_multimodal_data(self, parsed_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Фильтрует данные, оставляя только мультимодальные тарифы.
        
        Args:
            parsed_data: Список всех распарсенных данных
            
        Returns:
            Список мультимодальных данных
        """
        multimodal_data = []
        
        for data in parsed_data:
            # Проверяем, содержит ли данные признаки мультимодальности
            if self._is_multimodal_tariff(data):
                multimodal_data.append(data)
                
        return multimodal_data
    
    def _is_multimodal_tariff(self, data: Dict[str, Any]) -> bool:
        """
        Определяет, является ли тариф мультимодальным.
        
        Args:
            data: Данные тарифа
            
        Returns:
            True если тариф мультимодальный
        """
        description = data.get('description', '').lower()
        
        # Ключевые слова мультимодальности
        multimodal_keywords = [
            'мультимодал', 'multimodal', 'комбинирован', 'combined', 'смешанн',
            'mixed', 'железнодорожн', 'railway', 'морск', 'sea', 'автомобил',
            'auto', 'контейнер', 'container', 'перевалк', 'transshipment'
        ]
        
        # Проверяем наличие ключевых слов
        if any(keyword in description for keyword in multimodal_keywords):
            return True
            
        # Проверяем наличие нескольких типов транспорта
        transport_types = []
        if any(word in description for word in ['авто', 'auto', 'грузовик', 'truck']):
            transport_types.append('auto')
        if any(word in description for word in ['жд', 'rail', 'train', 'вагон']):
            transport_types.append('rail')
        if any(word in description for word in ['море', 'sea', 'ship', 'порт']):
            transport_types.append('sea')
        if any(word in description for word in ['авиа', 'air', 'flight']):
            transport_types.append('air')
            
        # Если найдено более одного типа транспорта, считаем мультимодальным
        return len(transport_types) > 1
    
    def _convert_to_standard_format(self, data: Dict[str, Any], supplier_id: int, source_file: str) -> Optional[Dict[str, Any]]:
        """
        Преобразует данные анализатора в стандартный формат тарифа.
        
        Args:
            data: Данные от анализатора
            supplier_id: ID поставщика
            source_file: Исходный файл
            
        Returns:
            Словарь с данными тарифа в стандартном формате
        """
        try:
            # Извлекаем основные данные
            origin_city = data.get('origin_city', '')
            destination_city = data.get('destination_city', '')
            price = data.get('price', 0.0)
            currency = data.get('currency', 'USD')
            
            # Определяем базис (по умолчанию EXW для мультимодальных)
            basis = data.get('basis', 'EXW')
            
            # Извлекаем тип контейнера/услуги
            vehicle_type = data.get('vehicle_type', '')
            if not vehicle_type:
                # Пытаемся определить по контексту
                if any(keyword in data.get('description', '').lower() for keyword in ['20', '40', 'контейнер']):
                    vehicle_type = '20DC' if '20' in data.get('description', '') else '40HC'
                else:
                    vehicle_type = 'multimodal'
            
            # Извлекаем время в пути
            transit_time = self.extract_transit_time(data.get('description', ''))
            
            # Создаем стандартный тариф
            tariff = {
                'supplier_id': supplier_id,
                'transport_type': self.transport_type,
                'basis': basis,
                'origin_city': origin_city,
                'destination_city': destination_city,
                'vehicle_type': vehicle_type,
                'price_usd': price if currency.upper() == 'USD' else None,
                'price_rub': price if currency.upper() == 'RUB' else None,
                'transit_time_days': transit_time,
                'source_file': source_file,
                # Специфичные для мультимодальных поля
                'transit_port': data.get('transit_port', ''),
                'departure_station': data.get('departure_station', ''),
                'arrival_station': data.get('arrival_station', ''),
                'rail_tariff_rub': data.get('rail_tariff_rub'),
                'cbx_cost': data.get('cbx_cost'),
                'terminal_handling_cost': data.get('terminal_handling_cost'),
                'auto_pickup_cost': data.get('auto_pickup_cost'),
                'security_cost': data.get('security_cost'),
                'precarriage_cost': data.get('precarriage_cost')
            }
            
            return tariff
            
        except Exception as e:
            logger.error(f"Ошибка преобразования данных мультимодального тарифа: {e}")
            return None
    
    def extract_transit_time(self, text: str) -> Optional[int]:
        """
        Извлекает время в пути из текста.
        
        Args:
            text: Текст для анализа
            
        Returns:
            Время в пути в днях или None
        """
        if not text:
            return None
            
        # Паттерны для поиска времени в пути
        patterns = [
            r'(\d+)\s*дней?',
            r'(\d+)\s*days?',
            r'(\d+)\s*суток?',
            r'(\d+)\s*дн',
            r'(\d+)\s*сут',
            r'время\s*в\s*пути[:\s]*(\d+)',
            r'transit\s*time[:\s]*(\d+)',
            r'(\d+)\s*дней?\s*в\s*пути',
            r'ETA[:\s]*(\d+)',
            r'время\s*доставки[:\s]*(\d+)',
            r'total\s*time[:\s]*(\d+)',
            r'общее\s*время[:\s]*(\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except (ValueError, IndexError):
                    continue
                    
        return None
    
    def detect_multimodal_keywords(self, text: str) -> bool:
        """
        Определяет, содержит ли текст ключевые слова мультимодального транспорта.
        
        Args:
            text: Текст для анализа
            
        Returns:
            True если текст содержит мультимодальные ключевые слова
        """
        multimodal_keywords = [
            'мультимодал', 'multimodal', 'комбинирован', 'combined', 'смешанн',
            'mixed', 'перевалк', 'transshipment', 'intermodal', 'интермодал',
            'контейнер', 'container', 'комплексн', 'comprehensive'
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in multimodal_keywords)

