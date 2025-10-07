#!/usr/bin/env python3
import requests
import json

# Логинимся
login_data = {'username': 'admin', 'password': 'admin123'}
login_response = requests.post('http://127.0.0.1:8000/auth/login', data=login_data)
token = login_response.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

print("🔍 Проверяем статус гибридного парсера...")

# Проверяем статус
try:
    response = requests.get('http://127.0.0.1:8000/huggingface-llm/status', headers=headers)
    print("Статус сервиса:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
except Exception as e:
    print(f"Ошибка получения статуса: {e}")

# Тестируем парсинг
test_cases = [
    ("Автоперевозки", "Тариф автоперевозок: Москва - Санкт-Петербург, цена 15000 рублей, срок 3 дня, базис EXW", "auto"),
    ("Авиаперевозки", "AIRLINE: MU D1357+D2, ROUTE: HKG-XIY-SVO1, Rate: 8.90 USD/kg MIN Q45, Transit: 7 days, FOB", "air")
]

print("\n🧪 Тестируем парсинг...")

for name, text, transport_type in test_cases:
    print(f"\n--- {name} ---")

    try:
        response = requests.post('http://127.0.0.1:8000/huggingface-llm/parse-text',
                               json={'text': text, 'transport_type': transport_type, 'supplier_name': 'Тест'},
                               headers=headers)

        if response.status_code == 200:
            result = response.json()
            print("✅ Успешно")
            print(f"Сообщение: {result.get('message', 'Нет сообщения')}")
            print("Извлеченные данные:")
            for key, value in result.get('data', {}).items():
                print(f"  {key}: {value}")
        else:
            print(f"❌ Ошибка: {response.status_code}")
            print(response.text)

    except Exception as e:
        print(f"❌ Исключение: {e}")

print("\n🎯 Тестирование завершено")

