from typing import List, Dict, Any, Optional
import pandas as pd
import re
from services.base_parser import BaseParser

class AutoParser(BaseParser):
    """
    Специализированный парсер для автомобильных перевозок
    """
    
    def __init__(self):
        super().__init__('auto')
    
    def parse_tariff_data(self, file_path: str, supplier_id: int) -> List[Dict[str, Any]]:
        """
        Парсинг тарифов автомобильных перевозок
        """
        self.logger.info(f"Начинаем парсинг автомобильных тарифов из файла: {file_path}")
        
        try:
            # Извлекаем текст из файла
            text = self.extract_text_from_file(file_path)
            if not text:
                self.logger.warning(f"Не удалось извлечь текст из файла: {file_path}")
                return []
            
            # Очищаем текст
            clean_text = self.clean_text(text)
            
            # Парсим данные в зависимости от формата файла
            if file_path.lower().endswith(('.xls', '.xlsx')):
                return self._parse_excel_auto(file_path, supplier_id)
            elif file_path.lower().endswith('.csv'):
                return self._parse_csv_auto(file_path, supplier_id)
            else:
                return self._parse_text_auto(clean_text, supplier_id)
                
        except Exception as e:
            self.logger.error(f"Ошибка парсинга автомобильных тарифов: {e}")
            return []
    
    def _parse_excel_auto(self, file_path: str, supplier_id: int) -> List[Dict[str, Any]]:
        """
        Парсинг Excel файлов с автомобильными тарифами
        """
        try:
            # Читаем Excel файл
            df = pd.read_excel(file_path)
            self.logger.info(f"Прочитан Excel файл с {len(df)} строками")
            
            results = []
            
            # Определяем колонки по заголовкам
            columns = self._identify_auto_columns(df.columns.tolist())
            
            for index, row in df.iterrows():
                try:
                    tariff_data = self._extract_auto_tariff_from_row(row, columns, supplier_id)
                    if tariff_data:
                        results.append(tariff_data)
                except Exception as e:
                    self.logger.warning(f"Ошибка обработки строки {index}: {e}")
                    continue
            
            # Валидируем данные
            validated_results = self.validate_parsed_data(results)
            self.log_parsing_results(file_path, validated_results)
            
            return validated_results
            
        except Exception as e:
            self.logger.error(f"Ошибка парсинга Excel файла: {e}")
            return []
    
    def _parse_csv_auto(self, file_path: str, supplier_id: int) -> List[Dict[str, Any]]:
        """
        Парсинг CSV файлов с автомобильными тарифами
        """
        try:
            # Читаем CSV файл
            df = pd.read_csv(file_path)
            self.logger.info(f"Прочитан CSV файл с {len(df)} строками")
            
            results = []
            
            # Определяем колонки по заголовкам
            columns = self._identify_auto_columns(df.columns.tolist())
            
            for index, row in df.iterrows():
                try:
                    tariff_data = self._extract_auto_tariff_from_row(row, columns, supplier_id)
                    if tariff_data:
                        results.append(tariff_data)
                except Exception as e:
                    self.logger.warning(f"Ошибка обработки строки {index}: {e}")
                    continue
            
            # Валидируем данные
            validated_results = self.validate_parsed_data(results)
            self.log_parsing_results(file_path, validated_results)
            
            return validated_results
            
        except Exception as e:
            self.logger.error(f"Ошибка парсинга CSV файла: {e}")
            return []
    
    def _parse_text_auto(self, text: str, supplier_id: int) -> List[Dict[str, Any]]:
        """
        Парсинг текстовых файлов с автомобильными тарифами
        """
        results = []
        
        # Разбиваем текст на строки
        lines = text.split('\n')
        
        for line in lines:
            if not line.strip():
                continue
            
            try:
                tariff_data = self._extract_auto_tariff_from_text(line, supplier_id)
                if tariff_data:
                    results.append(tariff_data)
            except Exception as e:
                self.logger.warning(f"Ошибка обработки строки: {e}")
                continue
        
        # Валидируем данные
        validated_results = self.validate_parsed_data(results)
        self.log_parsing_results("text_file", validated_results)
        
        return validated_results
    
    def _identify_auto_columns(self, columns: List[str]) -> Dict[str, Optional[str]]:
        """
        Определение колонок для автомобильных тарифов
        """
        column_mapping = {
            'origin': None,
            'destination': None,
            'price': None,
            'currency': None,
            'weight': None,
            'volume': None,
            'delivery_type': None,
            'loading_type': None,
            'transit_time': None
        }
        
        for col in columns:
            col_lower = col.lower().strip()
            
            # Маршрут
            if any(keyword in col_lower for keyword in ['откуда', 'отправление', 'origin', 'из']):
                column_mapping['origin'] = col
            elif any(keyword in col_lower for keyword in ['куда', 'назначение', 'destination', 'в']):
                column_mapping['destination'] = col
            
            # Цена
            elif any(keyword in col_lower for keyword in ['цена', 'стоимость', 'тариф', 'price', 'cost']):
                column_mapping['price'] = col
            
            # Валюта
            elif any(keyword in col_lower for keyword in ['валюта', 'currency', 'руб', 'долл', 'евро']):
                column_mapping['currency'] = col
            
            # Вес и объём
            elif any(keyword in col_lower for keyword in ['вес', 'масса', 'weight', 'кг', 'тонн']):
                column_mapping['weight'] = col
            elif any(keyword in col_lower for keyword in ['объем', 'объём', 'volume', 'м3', 'м³']):
                column_mapping['volume'] = col
            
            # Тип доставки
            elif any(keyword in col_lower for keyword in ['тип', 'доставка', 'delivery', 'ftl', 'ltl']):
                column_mapping['delivery_type'] = col
            
            # Время в пути
            elif any(keyword in col_lower for keyword in ['время', 'дни', 'срок', 'transit', 'days']):
                column_mapping['transit_time'] = col
        
        return column_mapping
    
    def _extract_auto_tariff_from_row(self, row: pd.Series, columns: Dict[str, Optional[str]], supplier_id: int) -> Optional[Dict[str, Any]]:
        """
        Извлечение данных автомобильного тарифа из строки таблицы
        """
        tariff_data = {
            'supplier_id': supplier_id,
            'transport_type': 'auto'
        }
        
        # Извлекаем маршрут
        if columns['origin'] and columns['origin'] in row:
            tariff_data['origin_city'] = str(row[columns['origin']]).strip()
        
        if columns['destination'] and columns['destination'] in row:
            tariff_data['destination_city'] = str(row[columns['destination']]).strip()
        
        # Извлекаем цену
        if columns['price'] and columns['price'] in row:
            price_value = row[columns['price']]
            if pd.notna(price_value):
                try:
                    price = float(str(price_value).replace(',', '.'))
                    tariff_data['price'] = price
                except ValueError:
                    pass
        
        # Извлекаем валюту
        if columns['currency'] and columns['currency'] in row:
            currency = str(row[columns['currency']]).strip()
            if currency:
                tariff_data['currency'] = self.extract_currency(currency)
        
        # Извлекаем вес и объём
        if columns['weight'] and columns['weight'] in row:
            weight_value = row[columns['weight']]
            if pd.notna(weight_value):
                try:
                    weight = float(str(weight_value).replace(',', '.'))
                    tariff_data['weight_kg'] = weight
                except ValueError:
                    pass
        
        if columns['volume'] and columns['volume'] in row:
            volume_value = row[columns['volume']]
            if pd.notna(volume_value):
                try:
                    volume = float(str(volume_value).replace(',', '.'))
                    tariff_data['volume_m3'] = volume
                except ValueError:
                    pass
        
        # Извлекаем тип доставки
        if columns['delivery_type'] and columns['delivery_type'] in row:
            delivery_type = str(row[columns['delivery_type']]).strip().lower()
            if 'ftl' in delivery_type or 'полная' in delivery_type:
                tariff_data['loading_type'] = 'full'
            elif 'ltl' in delivery_type or 'частичная' in delivery_type:
                tariff_data['loading_type'] = 'partial'
        
        # Извлекаем время в пути
        if columns['transit_time'] and columns['transit_time'] in row:
            transit_value = row[columns['transit_time']]
            if pd.notna(transit_value):
                try:
                    transit_time = int(str(transit_value))
                    tariff_data['transit_time_days'] = transit_time
                except ValueError:
                    pass
        
        # Проверяем, что есть обязательные поля
        if tariff_data.get('origin_city') and tariff_data.get('destination_city') and tariff_data.get('price'):
            return tariff_data
        
        return None
    
    def _extract_auto_tariff_from_text(self, text: str, supplier_id: int) -> Optional[Dict[str, Any]]:
        """
        Извлечение данных автомобильного тарифа из текста
        """
        tariff_data = {
            'supplier_id': supplier_id,
            'transport_type': 'auto'
        }
        
        # Извлекаем маршрут
        route = self.extract_route(text)
        if route['origin']:
            tariff_data['origin_city'] = route['origin']
        if route['destination']:
            tariff_data['destination_city'] = route['destination']
        
        # Извлекаем цену
        price = self.extract_price(text)
        if price:
            tariff_data['price'] = price
        
        # Извлекаем валюту
        currency = self.extract_currency(text)
        if currency:
            tariff_data['currency'] = currency
        
        # Извлекаем вес и объём
        weight_volume = self.extract_weight_volume(text)
        if weight_volume['weight']:
            tariff_data['weight_kg'] = weight_volume['weight']
        if weight_volume['volume']:
            tariff_data['volume_m3'] = weight_volume['volume']
        
        # Определяем тип загрузки
        text_lower = text.lower()
        if any(keyword in text_lower for keyword in ['ftl', 'полная загрузка', 'полный груз']):
            tariff_data['loading_type'] = 'full'
        elif any(keyword in text_lower for keyword in ['ltl', 'частичная загрузка', 'сборный груз']):
            tariff_data['loading_type'] = 'partial'
        
        # Извлекаем время в пути
        transit_patterns = [
            r'(\d+)\s*(дней|дня|день)',
            r'(\d+)\s*(суток|сутки)',
            r'время[:\s]*(\d+)',
            r'срок[:\s]*(\d+)'
        ]
        
        for pattern in transit_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    transit_time = int(match.group(1))
                    tariff_data['transit_time_days'] = transit_time
                    break
                except ValueError:
                    continue
        
        # Проверяем, что есть обязательные поля
        if tariff_data.get('origin_city') and tariff_data.get('destination_city') and tariff_data.get('price'):
            return tariff_data
        
        return None

    def detect_auto_keywords(self, text: str) -> bool:
        """
        Определяет, содержит ли текст ключевые слова автомобильного транспорта.
        
        Args:
            text: Текст для анализа
            
        Returns:
            True если текст содержит автомобильные ключевые слова
        """
        auto_keywords = [
            'автомобиль', 'авто', 'машина', 'грузовик', 'фура',
            'ftl', 'ltl', 'дверь-дверь', 'дверь до двери',
            'автовывоз', 'автодоставка', 'автоперевозка'
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in auto_keywords)
