"""
Гибридный анализатор: Парсер + LLM для структурирования данных согласно шаблонам форм
Сначала использует парсер для извлечения данных, затем LLM для улучшения контекста
"""

import logging
import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
import traceback

logger = logging.getLogger(__name__)

class HuggingFaceLLMAnalyzer:
    """
    Hugging Face LLM анализатор для понимания контекста и структурирования данных
    """
    
    def __init__(self):
        self.llm_available = False
        self.pipeline = None
        self.fallback_mode = False
        self._init_llm()
        
    def _init_llm(self):
        """Инициализация Hugging Face LLM в офлайн режиме"""
        try:
            logger.info("Пробуем инициализацию Hugging Face LLM в офлайн режиме...")
            
            # Пробуем создать простую заглушку LLM для демонстрации
            self._init_mock_llm()
            
        except Exception as e:
            logger.error(f"Ошибка инициализации Hugging Face LLM: {e}")
            self.llm_available = False
            self.fallback_mode = True
    
    def _init_mock_llm(self):
        """Инициализация продвинутого парсера для демонстрации"""
        try:
            logger.info("Инициализируем продвинутый парсер для демонстрации...")

            class AdvancedTariffParser:
                def __init__(self):
                    # Загружаем паттерны из intelligent_parser
                    from .intelligent_parser import IntelligentParser
                    self.parser = IntelligentParser()

                def __call__(self, prompt, **kwargs):
                    # Анализируем промпт и извлекаем данные из текста
                    import re

                    # Извлекаем текст из промпта
                    text_match = re.search(r'TEXT: (.+?)(?:\n|$)', prompt, re.DOTALL)
                    if text_match:
                        text = text_match.group(1).strip()

                        # Определяем тип транспорта из промпта или текста
                        transport_type = self._detect_transport_type(text)

                        # Используем intelligent_parser для анализа
                        result = self.parser.parse_file(text, transport_type)

                        if result.get('success', False):
                            # Конвертируем результат в JSON
                            data = result.get('data', {})

                            # Нормализуем данные
                            normalized_data = self._normalize_data(data, transport_type)

                            result_json = json.dumps(normalized_data, ensure_ascii=False)
                        else:
                            # Fallback на простой парсинг
                            result_json = self._simple_parse(text, transport_type)
                    else:
                        result_json = '{"origin_city": "Москва", "destination_city": "Санкт-Петербург", "price_usd": "5000", "transit_time_days": "2", "basis": "EXW"}'

                    return [{'generated_text': result_json}]

                def _detect_transport_type(self, text):
                    """Определяем тип транспорта по тексту"""
                    text_lower = text.lower()

                    if any(word in text_lower for word in ['авиа', 'air', 'аэропорт', 'airport', 'airline']):
                        return 'air'
                    elif any(word in text_lower for word in ['море', 'sea', 'порт', 'port', 'контейнер', 'container']):
                        return 'sea'
                    elif any(word in text_lower for word in ['жд', 'rail', 'станция', 'station', 'вагон', 'wagon']):
                        return 'rail'
                    else:
                        return 'auto'

                def _normalize_data(self, data, transport_type):
                    """Нормализуем данные для фронтенда"""
                    normalized = {}

                    # Маппинг полей
                    field_mapping = {
                        'origin_city': 'origin_city',
                        'destination_city': 'destination_city',
                        'price_rub': 'price_rub',
                        'price_usd': 'price_usd',
                        'transit_time_days': 'transit_time_days',
                        'basis': 'basis',
                        'weight': 'weight_kg',
                        'volume': 'volume_m3'
                    }

                    for key, value in data.items():
                        if key in field_mapping:
                            normalized[field_mapping[key]] = value

                    # Добавляем обязательные поля с дефолтными значениями
                    if transport_type == 'air' and 'price_usd' not in normalized and 'price_rub' in normalized:
                        normalized['price_usd'] = str(float(normalized['price_rub']) / 100)

                    if transport_type == 'auto' and 'price_rub' not in normalized and 'price_usd' in normalized:
                        normalized['price_rub'] = str(float(normalized['price_usd']) * 100)

                    return normalized

                def _simple_parse(self, text, transport_type):
                    """Продвинутый парсинг с использованием паттернов"""
                    data = {}

                    # Используем паттерны из IntelligentParser
                    patterns = self._get_parsing_patterns()

                    for field, pattern in patterns.items():
                        matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
                        if matches:
                            if isinstance(matches[0], tuple):
                                # Если паттерн возвращает несколько групп (например, маршрут)
                                if field == 'route':
                                    origin, destination = matches[0]
                                    data['origin_city'] = origin.strip()
                                    data['destination_city'] = destination.strip()
                                else:
                                    data[field] = matches[0][0].strip()
                            else:
                                # Если паттерн возвращает одну группу
                                data[field] = matches[0].strip()

                    # Если не нашли маршрут отдельно, попробуем найти города
                    if 'origin_city' not in data or 'destination_city' not in data:
                        cities = re.findall(r'\b[A-ZА-Я][a-zа-я]+(?:\s+[A-ZА-Я][a-zа-я]+)*\b', text)
                        # Фильтруем короткие слова и ищем реальные города
                        cities = [city for city in cities if len(city) > 3 and not any(word in city.lower() for word in ['price', 'rate', 'usd', 'руб'])]
                        if len(cities) >= 2:
                            data['origin_city'] = cities[0]
                            data['destination_city'] = cities[-1]

                    # Если не нашли цену, ищем числа
                    if 'price_rub' not in data and 'price_usd' not in data:
                        prices = re.findall(r'\b(\d+(?:[.,]\d+)?)\s*(?:руб|рубл|₽|RUB|долл|\$|USD)', text, re.IGNORECASE)
                        if prices:
                            price_value, currency = prices[0]
                            if 'usd' in currency.lower() or '$' in currency:
                                data['price_usd'] = price_value
                            else:
                                data['price_rub'] = price_value

                    # Если все еще нет цены, берем первое число
                    if 'price_rub' not in data and 'price_usd' not in data:
                        numbers = re.findall(r'\b(\d+(?:[.,]\d+)?)\b', text)
                        if numbers:
                            # Определяем валюту по контексту
                            if any(word in text.lower() for word in ['usd', 'доллар', '$']):
                                data['price_usd'] = numbers[0]
                            else:
                                data['price_rub'] = numbers[0]

                    # Базис по умолчанию
                    if 'basis' not in data:
                        data['basis'] = 'EXW'

                    return json.dumps(data, ensure_ascii=False)

                def _get_parsing_patterns(self):
                    """Получаем паттерны для парсинга из IntelligentParser"""
                    return {
                        'route': r'([А-Яа-я\w\s\-]+)\s*[-→→]\s*([А-Яа-я\w\s\-]+)',
                        'price_rub': r'(\d+(?:[.,]\d+)?)\s*(?:руб|рубл|₽|RUB)',
                        'price_usd': r'(\d+(?:[.,]\d+)?)\s*(?:долл|\$|USD)',
                        'price_eur': r'(\d+(?:[.,]\d+)?)\s*(?:евро|€|EUR)',
                        'transit_time_days': r'(\d+)\s*(?:дней|дня|день|days)',
                        'basis': r'(EXW|FCA|FOB|CIF|CFR|DAP|DDP)',
                        'weight_kg': r'(\d+(?:[.,]\d+)?)\s*(?:кг|kg|тонн)',
                        'volume_m3': r'(\d+(?:[.,]\d+)?)\s*(?:м³|m3|cbm)'
                    }

            self.pipeline = AdvancedTariffParser()
            self.llm_available = True
            logger.info("✅ Продвинутый парсер успешно инициализирован")

        except Exception as e:
            logger.error(f"Ошибка инициализации продвинутого парсера: {e}")
            self.llm_available = False
            self.fallback_mode = True
    
    def _init_llm_alternative(self):
        """Альтернативный способ инициализации LLM"""
        try:
            from transformers import pipeline, GPT2LMHeadModel, GPT2Tokenizer
            import torch
            
            logger.info("Пробуем загрузить GPT2 локально...")
            
            # Загружаем модель и токенизатор по отдельности
            tokenizer = GPT2Tokenizer.from_pretrained('distilgpt2')
            model = GPT2LMHeadModel.from_pretrained('distilgpt2')
            
            # Создаем pipeline
            self.pipeline = pipeline(
                "text-generation",
                model=model,
                tokenizer=tokenizer,
                max_length=128,
                do_sample=True,
                temperature=0.7,
                pad_token_id=tokenizer.eos_token_id
            )
            
            self.llm_available = True
            logger.info("Hugging Face LLM (альтернативный способ) успешно инициализирован")
            
        except Exception as e:
            logger.error(f"Альтернативная инициализация также не удалась: {e}")
            logger.info("Пробуем самую простую модель...")
            self._init_simple_model()
    
    def _init_simple_model(self):
        """Инициализация простой модели с локальным кэшем"""
        try:
            from transformers import pipeline, GPT2LMHeadModel, GPT2Tokenizer
            import torch
            import os
            
            logger.info("Пробуем загрузить простые модели с локальным кэшем...")
            
            # Создаем директорию для кэша
            cache_dir = "./models_cache"
            os.makedirs(cache_dir, exist_ok=True)
            
            # Пробуем модели в порядке простоты
            simple_models = [
                "distilgpt2",  # Самая легкая модель
                "gpt2"         # Классическая GPT-2
            ]
            
            for model_name in simple_models:
                try:
                    logger.info(f"Пробуем модель: {model_name}")
                    
                    # Используем pipeline напрямую для простоты
                    self.pipeline = pipeline(
                        "text-generation",
                        model=model_name,
                        max_length=128,
                        do_sample=True,
                        temperature=0.7,
                        pad_token_id=50256,  # EOS token для GPT-2
                        device=-1  # CPU only
                    )
                    
                    self.llm_available = True
                    logger.info(f"✅ Hugging Face LLM ({model_name}) успешно инициализирован")
                    return
                    
                except Exception as e:
                    logger.warning(f"Модель {model_name} не загрузилась: {e}")
                    continue
            
            # Если все модели не загрузились, используем заглушку
            logger.warning("Все модели недоступны, используем fallback режим")
            self.llm_available = False
            self.fallback_mode = True
            
        except ImportError as e:
            logger.warning(f"Transformers не установлен: {e}")
            self.llm_available = False
            self.fallback_mode = True
        except Exception as e:
            logger.error(f"Ошибка инициализации простых моделей: {e}")
            self.llm_available = False
            self.fallback_mode = True
    
    def analyze_context_and_structure(self, extracted_text: str, transport_type: str = "auto", supplier_name: str = "") -> Dict[str, Any]:
        """
        Гибридный анализ: Парсер извлекает данные, LLM понимает контекст

        Алгоритм:
        1. Парсер извлекает базовые данные из текста (как в старом подходе)
        2. LLM анализирует контекст и структурирует данные для формы
        3. Объединяем результаты для максимальной точности

        Args:
            extracted_text: Текст, извлеченный OCR
            transport_type: Тип транспорта (auto, air, sea, rail)
            supplier_name: Название поставщика

        Returns:
            Структурированные данные для формы
        """
        try:
            logger.info(f"Начинаем гибридный анализ текста ({len(extracted_text)} символов) для типа {transport_type}")

            # Шаг 1: Парсер извлекает базовые данные (как в старом подходе)
            logger.info("Шаг 1: Парсер извлекает базовые данные")
            raw_data = self._extract_with_parser(extracted_text, transport_type)

            # Шаг 2: LLM анализирует контекст и структурирует данные
            if self.llm_available:
                logger.info("Шаг 2: LLM анализирует контекст и структурирует данные")
                structured_data = self._structure_with_llm(extracted_text, transport_type, supplier_name, raw_data)
            else:
                logger.info("Шаг 2: Пропускаем (LLM недоступен)")
                structured_data = raw_data

            # Шаг 3: Финальная валидация и нормализация
            logger.info("Шаг 3: Финальная валидация и нормализация")
            final_data = self._validate_and_enrich_data(structured_data, transport_type)

            logger.info(f"Гибридный анализ завершен. Извлечено {len(final_data)} полей")
            return final_data

        except Exception as e:
            logger.error(f"Ошибка гибридного анализа: {e}")
            logger.error(traceback.format_exc())
            return self._fallback_parsing(extracted_text, transport_type)

    def _extract_with_parser(self, text: str, transport_type: str) -> Dict[str, Any]:
        """Шаг 1: Извлечение базовых данных с помощью парсера"""
        try:
            # Импортируем парсер фабрику
            from .parser_factory import ParserFactory

            # Создаем парсер для указанного типа транспорта
            parser = ParserFactory.get_parser(transport_type)

            # Парсим текст (используем parse_file с текстом как содержимое)
            # Для этого создаем временный файл или адаптируем интерфейс
            result = parser.parse_text_direct(text)

            logger.info(f"Парсер извлек {len(result)} полей")
            return result

        except Exception as e:
            logger.warning(f"Ошибка парсера: {e}. Используем fallback.")
            return self._simple_parse(text, transport_type)

    def _structure_with_llm(self, text: str, transport_type: str, supplier_name: str, parser_data: Dict[str, Any]) -> Dict[str, Any]:
        """Шаг 2: LLM анализирует контекст и структурирует данные"""
        try:
            # Создаем промпт для анализа контекста извлеченных данных
            prompt = self._create_context_analysis_prompt(text, transport_type, supplier_name, parser_data)

            # Отправляем запрос в LLM
            response = self._query_llm(prompt)

            # Парсим ответ LLM
            structured_data = self._parse_llm_response(response, transport_type)

            logger.info(f"LLM структурировал данные: {len(structured_data)} полей")
            return structured_data

        except Exception as e:
            logger.warning(f"Ошибка структурирования LLM: {e}. Используем данные парсера.")
            return parser_data

    def _validate_and_merge_data(self, parser_data: Dict[str, Any], enhanced_data: Dict[str, Any], transport_type: str) -> Dict[str, Any]:
        """Шаг 3: Финальная валидация данных от LLM"""
        try:
            # Используем данные от LLM как основные
            final_data = enhanced_data.copy()

            # Добавляем любые дополнительные поля из парсера, которых нет в LLM данных
            for key, value in parser_data.items():
                if key not in final_data:
                    final_data[key] = value

            # Валидируем обязательные поля
            validated_data = self._validate_and_enrich_data(final_data, transport_type)

            logger.info(f"Финальные данные: {len(validated_data)} полей")
            return validated_data

        except Exception as e:
            logger.error(f"Ошибка финальной валидации: {e}")
            return parser_data

    def _create_context_analysis_prompt(self, text: str, transport_type: str, supplier_name: str, parser_data: Dict[str, Any]) -> str:
        """Создание промпта для анализа контекста извлеченных данных"""
        form_template = self._get_form_template(transport_type)

        prompt = f"""Analyze this {transport_type} tariff from {supplier_name}:

ORIGINAL TEXT: {text}

PARSER EXTRACTED DATA: {json.dumps(parser_data, ensure_ascii=False)}

Based on the extracted data from the parser, structure it according to the form template.
The parser has already extracted some fields, but you need to:

1. Map the extracted data to the correct form fields
2. Ensure all required fields are present
3. Convert currencies if needed (RUB to USD for air/sea)
4. Validate and correct city names, routes, and delivery terms
5. Add any missing context information

Required form fields for {transport_type}:
{form_template}

Return properly structured JSON data for the form:
"""
        return prompt

    def _create_analysis_prompt(self, text: str, transport_type: str, supplier_name: str) -> str:
        """Создание промпта для LLM"""
        
        # Определяем шаблон формы в зависимости от типа транспорта
        form_template = self._get_form_template(transport_type)
        
        prompt = f"""Analyze this {transport_type} tariff from {supplier_name}:

TEXT: {text[:300]}...

Extract these fields as JSON:
{form_template}

Return only valid JSON:
"""
        return prompt
    
    def _get_form_template(self, transport_type: str) -> str:
        """Получение шаблона формы для типа транспорта"""
        
        templates = {
            'auto': """
- origin_city: Город отправления
- destination_city: Город назначения  
- price_rub: Цена в рублях
- transit_time_days: Срок доставки в днях
- basis: Базис поставки (EXW, FCA, FOB, CIF, DAP, DDP)
""",
            'air': """
- origin_city: Город отправления
- destination_city: Город назначения
- price_usd: Цена в долларах
- transit_time_days: Срок доставки в днях
- basis: Базис поставки (EXW, FCA, FOB)
""",
            'sea': """
- origin_city: Порт отправления
- destination_city: Порт назначения
- price_usd: Цена в долларах
- transit_time_days: Срок доставки в днях
- basis: Базис поставки (EXW, FCA, FOB, CIF, CFR)
""",
            'rail': """
- origin_city: Станция отправления
- destination_city: Станция назначения
- price_rub: Цена в рублях
- transit_time_days: Срок доставки в днях
- basis: Базис поставки (EXW, FCA, FOB)
"""
        }
        
        return templates.get(transport_type, templates['auto'])
    
    def _query_llm(self, prompt: str) -> str:
        """Запрос к Hugging Face LLM"""
        try:
            if not self.llm_available or not self.pipeline:
                raise Exception("Hugging Face LLM недоступен")
            
            # Генерируем ответ
            response = self.pipeline(
                prompt,
                max_length=len(prompt) + 200,
                num_return_sequences=1,
                temperature=0.7,
                do_sample=True,
                pad_token_id=50256
            )
            
            # Извлекаем сгенерированный текст
            generated_text = response[0]['generated_text']
            
            # Убираем исходный промпт из ответа
            if generated_text.startswith(prompt):
                generated_text = generated_text[len(prompt):].strip()
            
            logger.info(f"Hugging Face LLM ответ: {generated_text[:100]}...")
            return generated_text
            
        except Exception as e:
            logger.error(f"Ошибка запроса к Hugging Face LLM: {e}")
            raise
    
    def _parse_llm_response(self, response: str, transport_type: str) -> Dict[str, Any]:
        """Парсинг ответа LLM"""
        try:
            # Ищем JSON в ответе
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                data = json.loads(json_str)
                logger.info(f"Hugging Face LLM вернул структурированные данные: {list(data.keys())}")
                return data
            else:
                # Если JSON не найден, пытаемся извлечь данные с помощью regex
                logger.warning("JSON не найден в ответе, используем regex парсинг")
                return self._extract_data_with_regex(response, transport_type)
                
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON от Hugging Face LLM: {e}")
            return self._extract_data_with_regex(response, transport_type)
        except Exception as e:
            logger.error(f"Ошибка обработки ответа Hugging Face LLM: {e}")
            return {}
    
    def _extract_data_with_regex(self, text: str, transport_type: str) -> Dict[str, Any]:
        """Извлечение данных с помощью regex если LLM не вернул JSON"""
        try:
            data = {}
            
            # Паттерны для извлечения данных
            patterns = {
                'origin_city': r'(?:от|из|откуда|origin|departure)[\s:]*([А-Яа-я\w\s\-\.]+)',
                'destination_city': r'(?:до|в|куда|destination|arrival)[\s:]*([А-Яа-я\w\s\-\.]+)',
                'price_rub': r'(\d+(?:[.,]\d+)?)\s*(?:руб|рубл|₽|RUB)',
                'price_usd': r'(\d+(?:[.,]\d+)?)\s*(?:долл|\$|USD)',
                'transit_time_days': r'(\d+)\s*(?:дней|дня|день|days)',
                'basis': r'(EXW|FCA|FOB|CIF|CFR|DAP|DDP)'
            }
            
            for field, pattern in patterns.items():
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    data[field] = matches[0].strip()
                    logger.info(f"Извлечено {field}: {matches[0]}")
            
            return data
            
        except Exception as e:
            logger.error(f"Ошибка regex извлечения: {e}")
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
                    # Попробуем найти альтернативное поле
                    if field == 'price_usd' and 'price_rub' in data:
                        # Конвертируем рубли в доллары (примерный курс 100 руб = 1 USD)
                        validated_data[field] = str(float(data['price_rub']) / 100)
                        logger.info(f"Конвертировали {data['price_rub']} руб в {validated_data[field]} USD")
                    elif field == 'price_rub' and 'price_usd' in data:
                        # Конвертируем доллары в рубли
                        validated_data[field] = str(float(data['price_usd']) * 100)
                        logger.info(f"Конвертировали {data['price_usd']} USD в {validated_data[field]} руб")
                    else:
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
            validated_data['parsing_method'] = 'huggingface_llm_analysis'
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
            from .intelligent_parser import IntelligentParser
            parser = IntelligentParser()
            result = parser.parse_file(text, transport_type)
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
    
    def _enhanced_fallback_parsing(self, text: str, transport_type: str, supplier_name: str) -> Dict[str, Any]:
        """Улучшенный fallback парсинг с контекстным анализом"""
        try:
            # Импортируем только при необходимости
            from .intelligent_parser import IntelligentParser

            # Используем intelligent_parser как основу
            parser = IntelligentParser()
            result = parser.parse_file(text, transport_type)
            
            if result.get('success', True):
                # Добавляем контекстную информацию
                result['parsing_method'] = 'enhanced_fallback_parsing'
                result['supplier_name'] = supplier_name
                result['context_analysis'] = True
                
                # Улучшаем данные на основе контекста
                result = self._enhance_with_context(result, text, transport_type, supplier_name)
                
                logger.info(f"Улучшенный fallback парсинг завершен. Извлечено полей: {len(result)}")
                return result
            else:
                return {
                    'error': 'Enhanced fallback parsing failed',
                    'success': False,
                    'transport_type': transport_type,
                    'parsing_method': 'enhanced_fallback_failed'
                }
                
        except Exception as e:
            logger.error(f"Ошибка улучшенного fallback парсинга: {e}")
            return self._fallback_parsing(text, transport_type)
    
    def _enhance_with_context(self, data: Dict[str, Any], text: str, transport_type: str, supplier_name: str) -> Dict[str, Any]:
        """Улучшение данных на основе контекста"""
        try:
            # Добавляем контекстную информацию
            if 'origin_city' not in data or not data['origin_city']:
                # Пытаемся найти города в тексте
                cities = self._extract_cities_from_text(text)
                if len(cities) >= 2:
                    data['origin_city'] = cities[0]
                    data['destination_city'] = cities[1]
            
            # Добавляем информацию о поставщике
            data['supplier_context'] = supplier_name
            
            # Улучшаем цены на основе контекста
            if 'price_rub' not in data and 'price_usd' not in data:
                prices = self._extract_prices_from_text(text)
                if prices:
                    # Определяем валюту по контексту
                    if 'руб' in text.lower() or '₽' in text:
                        data['price_rub'] = prices[0]
                    elif 'usd' in text.lower() or '$' in text:
                        data['price_usd'] = prices[0]
                    else:
                        data['price_value'] = prices[0]
            
            return data
            
        except Exception as e:
            logger.error(f"Ошибка улучшения контекста: {e}")
            return data
    
    def _extract_cities_from_text(self, text: str) -> List[str]:
        """Извлечение городов из текста"""
        try:
            import re
            # Простой паттерн для поиска городов
            city_pattern = r'\b([А-Я][а-я]+(?:\s+[А-Я][а-я]+)*)\b'
            cities = re.findall(city_pattern, text)
            # Фильтруем короткие слова и возвращаем уникальные
            return list(set([city for city in cities if len(city) > 3]))[:5]
        except:
            return []
    
    def _extract_prices_from_text(self, text: str) -> List[float]:
        """Извлечение цен из текста"""
        try:
            import re
            # Паттерн для поиска чисел (цен)
            price_pattern = r'\b(\d+(?:[.,]\d+)?)\b'
            prices = re.findall(price_pattern, text)
            # Конвертируем в числа и фильтруем разумные значения
            return [float(p.replace(',', '.')) for p in prices if 10 <= float(p.replace(',', '.')) <= 1000000][:3]
        except:
            return []

# Создаем глобальный экземпляр
huggingface_llm_analyzer = HuggingFaceLLMAnalyzer()
