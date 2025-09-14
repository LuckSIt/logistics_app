import time
import requests
from datetime import datetime, date
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

_cache = {"latest": (0, None), "history": (0, None)}
_ttl = 60 * 60  # 1 час кэширования


def get_latest_rates() -> Dict[str, Any]:
    """
    Получение актуальных курсов валют от ЦБ РФ
    Использует официальный API ЦБ РФ
    """
    ts, data = _cache["latest"]
    if time.time() - ts < _ttl and data is not None:
        return data
    
    try:
        # Официальный API ЦБ РФ
        url = "https://www.cbr.ru/scripts/XML_daily.asp"
        params = {
            "date_req": datetime.now().strftime("%d/%m/%Y")
        }
        
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        
        # Парсим XML ответ
        import xml.etree.ElementTree as ET
        root = ET.fromstring(resp.content)
        
        rates = {}
        for valute in root.findall(".//Valute"):
            char_code = valute.find("CharCode").text
            value = float(valute.find("Value").text.replace(",", "."))
            nominal = int(valute.find("Nominal").text)
            rates[char_code] = value / nominal  # Курс за 1 единицу валюты
        
        # Добавляем рубль
        rates["RUB"] = 1.0
        
        data = {
            "Date": datetime.now().strftime("%Y-%m-%d"),
            "Valute": rates
        }
        
        _cache["latest"] = (time.time(), data)
        return data
        
    except Exception as e:
        logger.error(f"Ошибка получения курсов валют: {e}")
        # Fallback на резервный источник
        try:
            resp = requests.get("https://www.cbr-xml-daily.ru/daily_json.js", timeout=10)
            resp.raise_for_status()
            data = resp.json()
            _cache["latest"] = (time.time(), data)
            return data
        except Exception as fallback_error:
            logger.error(f"Ошибка резервного источника курсов валют: {fallback_error}")
            # Возвращаем базовые курсы
            return {
                "Date": datetime.now().strftime("%Y-%m-%d"),
                "Valute": {
                    "USD": 95.0,
                    "EUR": 105.0,
                    "CNY": 13.0,
                    "RUB": 1.0
                }
            }


def get_historical_rates(date_req: Optional[date] = None) -> Dict[str, Any]:
    """
    Получение исторических курсов валют
    """
    if date_req is None:
        date_req = date.today()
    
    try:
        url = "https://www.cbr.ru/scripts/XML_daily.asp"
        params = {
            "date_req": date_req.strftime("%d/%m/%Y")
        }
        
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        
        import xml.etree.ElementTree as ET
        root = ET.fromstring(resp.content)
        
        rates = {}
        for valute in root.findall(".//Valute"):
            char_code = valute.find("CharCode").text
            value = float(valute.find("Value").text.replace(",", "."))
            nominal = int(valute.find("Nominal").text)
            rates[char_code] = value / nominal
        
        rates["RUB"] = 1.0
        
        return {
            "Date": date_req.strftime("%Y-%m-%d"),
            "Valute": rates
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения исторических курсов валют: {e}")
        return get_latest_rates()


def convert_currency(amount: float, from_currency: str, to_currency: str = "RUB") -> float:
    """
    Конвертация валют
    """
    if from_currency == to_currency:
        return amount
    
    rates = get_latest_rates()
    valutes = rates.get("Valute", {})
    
    if from_currency not in valutes or to_currency not in valutes:
        logger.warning(f"Курс валюты не найден: {from_currency} -> {to_currency}")
        return amount
    
    # Конвертируем через рубли
    if from_currency == "RUB":
        return amount * valutes[to_currency]
    elif to_currency == "RUB":
        return amount * valutes[from_currency]
    else:
        # Конвертируем через рубли
        rub_amount = amount * valutes[from_currency]
        return rub_amount * valutes[to_currency]


def get_usd_rate() -> float:
    """
    Получение курса USD к рублю
    """
    rates = get_latest_rates()
    return rates.get("Valute", {}).get("USD", 95.0)


def get_eur_rate() -> float:
    """
    Получение курса EUR к рублю
    """
    rates = get_latest_rates()
    return rates.get("Valute", {}).get("EUR", 105.0)


