"""
Контекстный LLM анализатор для структурирования данных согласно шаблонам форм
Использует OCR для извлечения текста и LLM для понимания контекста
"""

import logging
import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
import traceback

logger = logging.getLogger(__name__)

class ContextLLMAnalyzer:
    """
    LLM анализатор для понимания контекста и структурирования данных
    """
    
    def __init__(self):
        self.llm_available = False
        self._init_llm()
        
    def _init_llm(self):
        """Инициализация LLM (Ollama)"""
        try:
            import ollama
            self.ollama = ollama
            self.llm_available = True
            logger.info("LLM (Ollama) успешно инициализирован")
        except ImportError:
            logger.warning("Ollama не установлен. LLM функции недоступны")
            self.llm_available = False
            self.ollama = None
        except Exception as e:
            logger.error(f"Ошибка инициализации LLM: {e}")
            self.llm_available = False
            self.ollama = None
    
    def analyze_context_and_structure(self, extracted_text: str, transport_type: str = "auto", supplier_name: str = "") -> Dict[str, Any]:
        """
        Анализ контекста и структурирование данных с помощью LLM
        
        Args:
            extracted_text: Текст, извлеченный OCR
            transport_type: Тип транспорта (auto, air, sea, rail)
            supplier_name: Название поставщика
            
        Returns:
            Структурированные данные для формы
        """
        try:
            if not self.llm_available:
                logger.warning("LLM недоступен, используем fallback парсинг")
                return self._fallback_parsing(extracted_text, transport_type)
            
            # Создаем промпт для LLM
            prompt = self._create_analysis_prompt(extracted_text, transport_type, supplier_name)
            
            # Отправляем запрос в LLM
            response = self._query_llm(prompt)
            
            # Парсим ответ LLM
            structured_data = self._parse_llm_response(response, transport_type)
            
            # Валидируем и дополняем данные
            validated_data = self._validate_and_enrich_data(structured_data, transport_type)
            
            logger.info(f"LLM анализ завершен. Извлечено полей: {len(validated_data)}")
            return validated_data
            
        except Exception as e:
            logger.error(f"Ошибка LLM анализа: {e}")
            logger.error(traceback.format_exc())
            return self._fallback_parsing(extracted_text, transport_type)
    
    def _create_analysis_prompt(self, text: str, transport_type: str, supplier_name: str) -> str:
        """Создание промпта для LLM"""
        
        # Определяем шаблон формы в зависимости от типа транспорта
        form_template = self._get_form_template(transport_type)
        
        prompt = f"""
Ты - эксперт по логистике и тарифам. Проанализируй следующий текст и извлеки структурированные данные для формы тарифа.

ТИП ТРАНСПОРТА: {transport_type.upper()}
ПОСТАВЩИК: {supplier_name}

ТЕКСТ ДЛЯ АНАЛИЗА:
{text}

ШАБЛОН ФОРМЫ:
{form_template}

ИНСТРУКЦИИ:
1. Внимательно проанализируй текст
2. Найди все релевантные данные для формы
3. Извлеки города отправления и назначения
4. Найди цены и валюты
5. Определи сроки доставки
6. Выдели дополнительные параметры
7. Верни результат в формате JSON

ВАЖНО:
- Если данные не найдены, используй null
- Города должны быть в формате "Город, Страна" (например: "Москва, Россия")
- Цены указывай как числа (без валюты)
- Даты в формате YYYY-MM-DD
- Будь точным и не выдумывай данные

Верни только JSON без дополнительных комментариев:
"""
        return prompt
    
    def _get_form_template(self, transport_type: str) -> str:
        """Получение шаблона формы для типа транспорта"""
        
        templates = {
            'auto': """
ОБЯЗАТЕЛЬНЫЕ ПОЛЯ:
- origin_city: Город отправления
- destination_city: Город назначения
- price_rub: Цена в рублях
- transit_time_days: Срок доставки в днях
- basis: Базис поставки (EXW, FCA, FOB, CIF, DAP, DDP)

ДОПОЛНИТЕЛЬНЫЕ ПОЛЯ:
- vehicle_type: Тип транспорта
- border_point: Пограничный пункт
- currency_conversion: Конвертация валюты (%)
- validity_date: Дата действия тарифа
- notes: Примечания
""",
            'air': """
ОБЯЗАТЕЛЬНЫЕ ПОЛЯ:
- origin_city: Город отправления
- destination_city: Город назначения
- price_usd: Цена в долларах
- transit_time_days: Срок доставки в днях
- basis: Базис поставки (EXW, FCA, FOB)

ДОПОЛНИТЕЛЬНЫЕ ПОЛЯ:
- weight_kg: Вес в кг
- volume_m3: Объем в м³
- volumetric_weight_kg: Объемный вес в кг
- departure_airport: Аэропорт отправления
- arrival_airport: Аэропорт назначения
- precarriage_cost: Стоимость прекерриджа
- terminal_handling_cost: Терминальная обработка
- validity_date: Дата действия тарифа
- notes: Примечания
""",
            'sea': """
ОБЯЗАТЕЛЬНЫЕ ПОЛЯ:
- origin_city: Порт отправления
- destination_city: Порт назначения
- price_usd: Цена в долларах
- transit_time_days: Срок доставки в днях
- basis: Базис поставки (EXW, FCA, FOB, CIF, CFR)

ДОПОЛНИТЕЛЬНЫЕ ПОЛЯ:
- container_type: Тип контейнера (20GP, 40GP, 40HC, 45HC)
- container_size: Размер контейнера в футах
- departure_port: Порт отправления
- arrival_port: Порт назначения
- transit_port: Транзитный порт
- validity_date: Дата действия тарифа
- notes: Примечания
""",
            'rail': """
ОБЯЗАТЕЛЬНЫЕ ПОЛЯ:
- origin_city: Станция отправления
- destination_city: Станция назначения
- price_rub: Цена в рублях
- transit_time_days: Срок доставки в днях
- basis: Базис поставки (EXW, FCA, FOB)

ДОПОЛНИТЕЛЬНЫЕ ПОЛЯ:
- container_type: Тип контейнера
- wagon_type: Тип вагона
- departure_station: Станция отправления
- arrival_station: Станция назначения
- cbx_cost: Стоимость СВХ
- validity_date: Дата действия тарифа
- notes: Примечания
"""
        }
        
        return templates.get(transport_type, templates['auto'])
    
    def _query_llm(self, prompt: str) -> str:
        """Запрос к LLM"""
        try:
            if not self.llm_available or not self.ollama:
                raise Exception("LLM недоступен")
                
            response = self.ollama.chat(
                model='mistral',
                messages=[
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ]
            )
            return response['message']['content']
        except Exception as e:
            logger.error(f"Ошибка запроса к LLM: {e}")
            raise
    
    def _parse_llm_response(self, response: str, transport_type: str) -> Dict[str, Any]:
        """Парсинг ответа LLM"""
        try:
            # Ищем JSON в ответе
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                data = json.loads(json_str)
                logger.info(f"LLM вернул структурированные данные: {list(data.keys())}")
                return data
            else:
                logger.warning("LLM не вернул JSON, используем fallback")
                return {}
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON от LLM: {e}")
            return {}
        except Exception as e:
            logger.error(f"Ошибка обработки ответа LLM: {e}")
            return {}
    
    def _validate_and_enrich_data(self, data: Dict[str, Any], transport_type: str) -> Dict[str, Any]:
        """Валидация и обогащение данных"""
        try:
            validated_data = {}
            
            # Обязательные поля для каждого типа транспорта
            required_fields = {
                'auto': ['origin_city', 'destination_city', 'price_rub', 'transit_time_days', 'basis'],
                'air': ['origin_city', 'destination_city', 'price_usd', 'transit_time_days', 'basis'],
                'sea': ['origin_city', 'destination_city', 'price_usd', 'transit_time_days', 'basis'],
                'rail': ['origin_city', 'destination_city', 'price_rub', 'transit_time_days', 'basis']
            }
            
            # Проверяем обязательные поля
            missing_fields = []
            for field in required_fields.get(transport_type, []):
                if field not in data or data[field] is None:
                    missing_fields.append(field)
                else:
                    validated_data[field] = data[field]
            
            # Добавляем дополнительные поля
            for key, value in data.items():
                if key not in validated_data and value is not None:
                    validated_data[key] = value
            
            # Добавляем метаданные
            validated_data['transport_type'] = transport_type
            validated_data['parsed_at'] = datetime.now().isoformat()
            validated_data['parsing_method'] = 'llm_context_analysis'
            validated_data['missing_required_fields'] = missing_fields
            
            if missing_fields:
                logger.warning(f"Отсутствуют обязательные поля: {missing_fields}")
            
            return validated_data
            
        except Exception as e:
            logger.error(f"Ошибка валидации данных: {e}")
            return data
    
    def _fallback_parsing(self, text: str, transport_type: str) -> Dict[str, Any]:
        """Fallback парсинг без LLM"""
        try:
            # Импортируем только при необходимости, чтобы избежать циклических импортов
            from .intelligent_parser import intelligent_parser
            result = intelligent_parser.parse_text(text, transport_type)
            if result.get('success', True):  # Если success не False, считаем успешным
                return result
            else:
                return {
                    'error': 'Intelligent parser failed',
                    'success': False,
                    'transport_type': transport_type,
                    'parsing_method': 'intelligent_parser_failed'
                }
        except ImportError as e:
            logger.error(f"Не удалось импортировать intelligent_parser: {e}")
            return {
                'error': f'Import error: {str(e)}',
                'success': False,
                'transport_type': transport_type,
                'parsing_method': 'import_failed'
            }
        except Exception as e:
            logger.error(f"Ошибка fallback парсинга: {e}")
            return {
                'error': str(e),
                'success': False,
                'transport_type': transport_type,
                'parsing_method': 'fallback_failed'
            }

# Создаем глобальный экземпляр
context_llm_analyzer = ContextLLMAnalyzer()
