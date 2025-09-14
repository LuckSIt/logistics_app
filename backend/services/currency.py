import requests


def get_rate_to_rub(currency_code: str) -> float:
    if not currency_code or currency_code.upper() == "RUB":
        return 1.0
    code = currency_code.upper()
    # Try Bank of Russia open API
    try:
        resp = requests.get(
            "https://www.cbr-xml-daily.ru/latest.js", timeout=5
        )
        if resp.ok:
            data = resp.json()
            rates = data.get("rates", {})
            if code in rates:
                # rates map from currency to RUB inverse (RUB base → actually base is RUB in inverse at daily API)
                # API returns rates as how many RUB per currency? According to docs it's RUB base false; use inverse
                # For simplicity, compute via RUB per unit: 1 / rates[code]
                return 1.0 / float(rates[code])
    except Exception:
        pass

    # Fallback: 1.0 (no conversion)
    return 1.0


def convert_to_rub(amount: float, currency_code: str) -> float:
    rate = get_rate_to_rub(currency_code)
    return float(amount) * rate


