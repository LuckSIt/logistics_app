#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Специализированный парсер для железнодорожных тарифов
"""

import re
import logging
from typing import List, Dict, Any, Optional
from base_parser import BaseParser
from railway_analyzer import RailwayAnalyzer

logger = logging.getLogger(__name__)

class RailwayParser(BaseParser):
    """Специализированный парсер для железнодорожных тарифов."""
    
    def __init__(self):
        super().__init__()
        self.analyzer = RailwayAnalyzer()
        self.transport_type = "rail"
        
    def parse_tariff_data(self, file_path: str, supplier_id: int) -> List[Dict[str, Any]]:
        """
        Парсинг железнодорожных тарифов из файла.
        
        Args:
            file_path: Путь к файлу для парсинга
            supplier_id: ID поставщика
            
        Returns:
            Список словарей с данными тарифов
        """
        logger.info(f"Начинаем парсинг железнодорожных тарифов из файла: {file_path}")
        
        # Извлекаем текст из файла
        text = self.extract_text_from_file(file_path)
        if not text:
            logger.warning(f"Не удалось извлечь текст из файла: {file_path}")
            return []
            
        # Анализируем текст с помощью специализированного анализатора
        parsed_data = self.analyzer.extract_railway_routes(text)
        
        # Преобразуем данные в стандартный формат
        tariffs = []
        for data in parsed_data:
            tariff = self._convert_to_standard_format(data, supplier_id, file_path)
            if tariff and self.validate_parsed_data(tariff):
                tariffs.append(tariff)
                
        logger.info(f"Извлечено {len(tariffs)} железнодорожных тарифов")
        return tariffs
    
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
            
            # Определяем базис (по умолчанию EXW для ЖД)
            basis = data.get('basis', 'EXW')
            
            # Извлекаем тип вагона/контейнера
            vehicle_type = data.get('vehicle_type', '')
            if not vehicle_type:
                # Пытаемся определить по контексту
                if any(keyword in data.get('description', '').lower() for keyword in ['20', '40', 'контейнер']):
                    vehicle_type = '20DC' if '20' in data.get('description', '') else '40HC'
                else:
                    vehicle_type = 'вагон'
            
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
                # Специфичные для ЖД поля
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
            logger.error(f"Ошибка преобразования данных ЖД тарифа: {e}")
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
            r'(\d+)\s*дней?\s*в\s*пути'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except (ValueError, IndexError):
                    continue
                    
        return None
    
    def detect_railway_keywords(self, text: str) -> bool:
        """
        Определяет, содержит ли текст ключевые слова железнодорожного транспорта.
        
        Args:
            text: Текст для анализа
            
        Returns:
            True если текст содержит ЖД ключевые слова
        """
        railway_keywords = [
            'железнодорожн', 'жд', 'railway', 'rail', 'train', 'вагон', 'контейнер',
            'станция', 'station', '20dc', '40hc', '20gp', '40gp', 'экспресс', 'express',
            'электричка', 'локомотив', 'поезд', 'рельс', 'путь', 'перегон'
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in railway_keywords)

    def detect_rail_keywords(self, text: str) -> bool:
        """
        Определяет, содержит ли текст ключевые слова железнодорожного транспорта.
        
        Args:
            text: Текст для анализа
            
        Returns:
            True если текст содержит ЖД ключевые слова
        """
        railway_keywords = [
            'железнодорожн', 'жд', 'railway', 'rail', 'train', 'вагон', 'контейнер',
            'станция', 'station', '20dc', '40hc', '20gp', '40gp', 'экспресс', 'express',
            'электричка', 'локомотив', 'поезд', 'рельс', 'путь', 'перегон'
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in railway_keywords)
