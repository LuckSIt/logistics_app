from typing import List, Dict, Any
import logging
from services.base_parser import BaseParser
from services.enhanced_ocr_service import enhanced_ocr_service
from intelligent_parser import intelligent_parser
# import ollama  # Отключено для стабильной версии

logger = logging.getLogger(__name__)


class LLMTariffParser(BaseParser):
    """
    Парсер тарифов на основе LLM (Ollama) с fallback на OCR
    """
    
    def __init__(self, model: str = "mistral"):
        self.model = model
        # self.client = ollama.Client()  # Отключено для стабильной версии
    
    def parse_tariff_data(self, file_path: str, supplier_id: int) -> List[Dict[str, Any]]:
        """
        Парсинг файла с помощью LLM с fallback на OCR
        """
        logger.info(f"Начинаем LLM парсинг файла: {file_path}")
        
        try:
            # Определяем тип транспорта по имени файла или содержимому
            transport_type = self._detect_transport_type(file_path)
            
            # LLM функционал отключен для стабильной версии
            # Используем fallback на OCR сервис
            logger.info("LLM отключен, используем OCR fallback")
            
            # Используем интеллектуальный парсер как fallback
            parsed_data = intelligent_parser.parse_file(file_path, transport_type, supplier_id)
            
            if parsed_data.get('success', False):
                # Преобразуем в формат, ожидаемый LLM парсером
                results = [parsed_data]
                logger.info(f"OCR fallback успешен. Извлечено {len(results)} записей")
                return results
            else:
                logger.warning("OCR fallback не смог извлечь данные")
                return []
            
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
    
    # LLM методы отключены для стабильной версии
