"""
Сервис для адаптивного анализа текста и извлечения данных тарифа.
"""

from adaptive_analyzer import analyze_tariff_text_adaptive

def analyze_tariff_text(text: str):
    """
    Адаптивный анализ текста и извлечение данных для создания тарифа.
    Автоматически определяет формат файла и применяет соответствующие стратегии парсинга.
    
    Args:
        text: Извлеченный текст из файла
        
    Returns:
        Словарь с данными для заполнения формы тарифа
    """
    return analyze_tariff_text_adaptive(text)
