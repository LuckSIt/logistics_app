#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Конфигурация для LLM анализатора
"""

import os
from typing import Optional

class LLMConfig:
    """Конфигурация для LLM анализатора."""
    
    # OpenAI API ключ (устанавливается через переменную окружения OPENAI_API_KEY)
    OPENAI_API_KEY: Optional[str] = os.getenv('OPENAI_API_KEY')
    
    # Модель для использования
    DEFAULT_MODEL: str = "gpt-3.5-turbo"
    
    # Настройки запросов
    MAX_TOKENS: int = 2000
    TEMPERATURE: float = 0.1
    
    # Включить/выключить LLM анализ
    ENABLE_LLM: bool = bool(OPENAI_API_KEY)
    
    # Fallback настройки
    USE_FALLBACK: bool = True
    
    @classmethod
    def is_available(cls) -> bool:
        """Проверяет доступность LLM."""
        return cls.ENABLE_LLM and cls.OPENAI_API_KEY is not None
    
    @classmethod
    def get_api_key(cls) -> Optional[str]:
        """Возвращает API ключ."""
        return cls.OPENAI_API_KEY
