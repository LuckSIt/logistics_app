from fastapi import APIRouter, Query
from datetime import date
from typing import Optional
from services.cbr import (
    get_latest_rates, 
    get_historical_rates, 
    convert_currency,
    get_usd_rate,
    get_eur_rate
)

router = APIRouter()


@router.get("/")
def get_currency_rates():
    """
    Получение актуальных курсов валют
    """
    return get_latest_rates()


@router.get("/history")
def get_currency_history(date_req: Optional[date] = Query(None, description="Дата в формате YYYY-MM-DD")):
    """
    Получение исторических курсов валют
    """
    return get_historical_rates(date_req)


@router.get("/convert")
def convert_currency_endpoint(
    amount: float = Query(..., description="Сумма для конвертации"),
    from_currency: str = Query(..., description="Исходная валюта (USD, EUR, CNY, RUB)"),
    to_currency: str = Query("RUB", description="Целевая валюта (по умолчанию RUB)")
):
    """
    Конвертация валют
    """
    result = convert_currency(amount, from_currency, to_currency)
    return {
        "amount": amount,
        "from_currency": from_currency,
        "to_currency": to_currency,
        "result": result
    }


@router.get("/usd")
def get_usd_rate_endpoint():
    """
    Получение курса USD к рублю
    """
    return {"USD": get_usd_rate()}


@router.get("/eur")
def get_eur_rate_endpoint():
    """
    Получение курса EUR к рублю
    """
    return {"EUR": get_eur_rate()}


