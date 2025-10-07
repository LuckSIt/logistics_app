#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Универсальный анализатор для всех типов файлов
"""

import re
import os
from typing import Dict, List, Optional, Any
from services.enhanced_aviation_analyzer import analyze_aviation_file_enhanced
from adaptive_analyzer import analyze_tariff_text_adaptive
from services.railway_analyzer import analyze_railway_file
from services.air_analyzer import analyze_air_file
from services.sea_analyzer import analyze_sea_file
from services.auto_analyzer import analyze_auto_file
from services.ltl_analyzer import analyze_ltl_file

class UniversalAnalyzer:
    """Универсальный анализатор для всех типов файлов."""
    
    def __init__(self):
        self.transport_keywords = {
            'air': ['авиа', 'aviation', 'air', 'flight', 'airport', 'hkg', 'pek', 'can', 'sha', 'xiy', 'svo', 'vvo'],
            'sea': ['море', 'sea', 'fcl', 'морской', 'контейнер', 'container', 'порт', 'port', 'vessel', 'ship'],
            'rail': ['жд', 'rail', 'железнодорожный', 'поезд', 'train', 'станция', 'station'],
            'auto': ['авто', 'auto', 'ftl', 'грузовик', 'truck', 'автомобильный'],
            'multimodal': ['мульти', 'multimodal', 'mmp', 'комбинированный', 'combined'],
            'ltl': ['сборка', 'ltl', 'частичная', 'partial', 'сборный']
        }
        
        self.basis_keywords = {
            'EXW': ['exw', 'ex works', 'франко завод'],
            'FCA': ['fca', 'free carrier'],
            'CPT': ['cpt', 'carriage paid to'],
            'CIP': ['cip', 'carriage and insurance paid to'],
            'DAP': ['dap', 'delivered at place'],
            'DPU': ['dpu', 'delivered at place unloaded'],
            'DDP': ['ddp', 'delivered duty paid'],
            'FAS': ['fas', 'free alongside ship'],
            'FOB': ['fob', 'free on board'],
            'CFR': ['cfr', 'cost and freight'],
            'CIF': ['cif', 'cost insurance and freight']
        }
    
    def determine_transport_type(self, text: str, file_path: str) -> str:
        """Определяет тип транспорта по содержимому и пути файла."""
        text_lower = text.lower()
        file_lower = file_path.lower()
        
        # Сначала проверяем по пути файла
        if 'авиа' in file_lower:
            return 'air'
        elif 'авто' in file_lower or 'ftl' in file_lower:
            return 'auto'
        elif 'жд' in file_lower or 'rail' in file_lower:
            return 'rail'
        elif 'море' in file_lower or 'fcl' in file_lower:
            return 'sea'
        elif 'сборка' in file_lower or 'ltl' in file_lower:
            return 'ltl'
        elif 'мульти' in file_lower or 'mmp' in file_lower:
            return 'multimodal'
        
        # Затем проверяем по содержимому
        scores = {transport: 0 for transport in self.transport_keywords}
        
        for transport, keywords in self.transport_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    scores[transport] += 1
        
        # Возвращаем тип с наибольшим количеством совпадений
        if max(scores.values()) > 0:
            return max(scores, key=scores.get)
        
        return 'auto'  # По умолчанию
    
    def determine_basis(self, text: str) -> str:
        """Определяет базис поставки."""
        text_lower = text.lower()
        
        for basis, keywords in self.basis_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return basis
        
        return 'EXW'  # По умолчанию
    
    def clean_routes(self, routes: List[Dict]) -> List[Dict]:
        """Очищает и фильтрует маршруты от ложных срабатываний."""
        cleaned_routes = []
        
        for route in routes:
            origin = route.get('origin_city', '')
            destination = route.get('destination_city', '')
            
            # Пропускаем маршруты с пустыми городами
            if not origin or not destination:
                continue
            
            # Очищаем названия городов
            origin = self._clean_city_name(origin)
            destination = self._clean_city_name(destination)
            
            # Пропускаем если после очистки города стали пустыми
            if not origin or not destination:
                continue
            
            # Пропускаем маршруты с одинаковыми городами
            if origin == destination:
                continue
            
            # Пропускаем маршруты с "Неизвестно"
            if 'Неизвестно' in origin or 'Неизвестно' in destination:
                continue
            
            # Пропускаем слишком короткие названия городов
            if len(origin) < 2 or len(destination) < 2:
                continue
            
            # Пропускаем числовые значения
            if origin.replace('.', '').replace(',', '').isdigit() or destination.replace('.', '').replace(',', '').isdigit():
                continue
            
            # Пропускаем служебные слова
            skip_words = ['pol', 'pod', 'fcl', 'ltl', 'ftl', 'sea', 'air', 'rail', 'auto', 'морской', 'авиа', 'жд', 'авто', 'port', 'terminal', '05', 'com']
            if any(word.lower() == origin.lower() or word.lower() == destination.lower() for word in skip_words):
                continue
            
            # Обновляем очищенные названия
            route['origin_city'] = origin
            route['destination_city'] = destination
            
            cleaned_routes.append(route)
        
        return cleaned_routes[:10]  # Ограничиваем количество маршрутов
    
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
            'china to', 'to china', 'vvo', 'vyp', 'com', 'port', 'terminal',
            'station', 'border', 'customs', 'gate', 'checkpoint', 'vladvistok'
        ]
        
        for part in parts_to_remove:
            city = re.sub(rf'\b{part}\b', '', city, flags=re.IGNORECASE)
        
        # Проверяем на точное совпадение со служебными словами
        skip_words = ['sea', 'air', 'rail', 'auto', '05', 'com', 'pol', 'pod', 'fcl', 'ltl', 'ftl']
        if city.lower() in [word.lower() for word in skip_words]:
            return ''
        
        # Очищаем от лишних пробелов
        city = ' '.join(city.split())
        
        # Если после очистки осталось меньше 2 символов, возвращаем пустую строку
        if len(city) < 2:
            return ''
        
        return city
    
    def analyze_file(self, text: str, file_path: str, use_llm: bool = False) -> Dict[str, Any]:
        """Анализирует файл с универсальным подходом."""
        
        # Определяем тип транспорта
        transport_type = self.determine_transport_type(text, file_path)
        basis = self.determine_basis(text)
        
        # Выбираем подходящий анализатор
        if transport_type == 'air':
            result = analyze_air_file(text, file_path)
        elif transport_type == 'rail':
            result = analyze_railway_file(text, file_path)
        elif transport_type == 'sea':
            result = analyze_sea_file(text, file_path)
        elif transport_type == 'auto':
            result = analyze_auto_file(text, file_path)
        elif transport_type == 'ltl':
            result = analyze_ltl_file(text, file_path)
        else:
            result = analyze_tariff_text_adaptive(text)
        
        # Принудительно устанавливаем правильный тип транспорта
        result['transport_type'] = transport_type
        result['basis'] = basis
        
        # Очищаем маршруты
        if 'routes' in result:
            result['routes'] = self.clean_routes(result['routes'])
        
        return result

def analyze_file_universal(text: str, file_path: str, use_llm: bool = False) -> Dict[str, Any]:
    """Универсальная функция анализа файла."""
    analyzer = UniversalAnalyzer()
    return analyzer.analyze_file(text, file_path, use_llm)
