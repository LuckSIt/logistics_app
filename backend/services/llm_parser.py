from typing import List, Dict, Any
import logging
from .base_parser import BaseParser
from backend.parser import LLMParser

logger = logging.getLogger(__name__)


class LLMTariffParser(BaseParser):
    """
    Парсер тарифов на основе LLM (Ollama)
    """
    
    def __init__(self, model: str = "mistral"):
        self.llm_parser = LLMParser(model)
    
    def parse_tariff_data(self, file_path: str, supplier_id: int) -> List[Dict[str, Any]]:
        """
        Парсинг файла с помощью LLM
        """
        logger.info(f"Начинаем LLM парсинг файла: {file_path}")
        
        try:
            # Определяем тип транспорта по имени файла или содержимому
            transport_type = self._detect_transport_type(file_path)
            
            # Парсим файл через LLM
            results = self.llm_parser.parse_file(file_path, transport_type)
            
            # Добавляем supplier_id к каждой записи
            for result in results:
                result["supplier_id"] = supplier_id
            
            logger.info(f"LLM парсинг завершен. Извлечено {len(results)} записей")
            return results
            
        except Exception as e:
            logger.error(f"Ошибка LLM парсинга файла {file_path}: {e}")
            return []
    
    def _detect_transport_type(self, file_path: str) -> str:
        """
        Определение типа транспорта по имени файла
        """
        filename = file_path.lower()
        
        # Проверяем ключевые слова в имени файла
        if any(word in filename for word in ['air', 'авиа', 'воздушн']):
            return 'air'
        elif any(word in filename for word in ['sea', 'море', 'морск', 'fcl', 'lcl']):
            return 'sea'
        elif any(word in filename for word in ['rail', 'жд', 'железнодорожн', 'railway']):
            return 'rail'
        elif any(word in filename for word in ['multimodal', 'мульти', 'комбинированн']):
            return 'multimodal'
        else:
            return 'auto'  # По умолчанию
    
    def get_supported_formats(self) -> List[str]:
        """
        Возвращает список поддерживаемых форматов файлов
        """
        return ['.pdf', '.docx', '.xlsx', '.xls', '.png', '.jpg', '.jpeg']
    
    def get_transport_type(self) -> str:
        """
        Возвращает тип транспорта, который обрабатывает этот парсер
        """
        return 'auto'  # Универсальный парсер
