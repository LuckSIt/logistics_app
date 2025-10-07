#!/usr/bin/env python3
import requests
import json

# Тестовые данные разных типов
test_cases = [
    {
        'name': 'Автоперевозки',
        'text': 'Тариф автоперевозок: Москва - Санкт-Петербург, цена 15000 рублей, срок 3 дня, базис EXW',
        'transport_type': 'auto'
    },
    {
        'name': 'Авиаперевозки',
        'text': 'Air freight: Shanghai - Moscow, rate 8.50 USD/kg, transit time 7 days, FOB',
        'transport_type': 'air'
    },
    {
        'name': 'Морские перевозки',
        'text': 'Sea freight: Shenzhen - St. Petersburg, 20ft container 3500 USD, transit 25 days, CIF',
        'transport_type': 'sea'
    },
    {
        'name': 'ЖД перевозки',
        'text': 'Rail tariff: Almaty - Moscow, 40ft container 2800 USD, transit 14 days, FCA',
        'transport_type': 'rail'
    },
    {
        'name': 'Смешанные данные',
        'text': 'TIR Tianjin Qingdao Shanghai Ningbo Guangzhou Shenzhen Manzhouli Moscow 11500 11500 11850 11850 12550 12550',
        'transport_type': 'auto'
    }
]

# Логинимся
login_data = {'username': 'admin', 'password': 'admin123'}
login_response = requests.post('http://127.0.0.1:8000/auth/login', data=login_data)
token = login_response.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

print("🚀 Тестируем разные типы тарифов\n")

for i, test_case in enumerate(test_cases, 1):
    print(f"{'='*50}")
    print(f"Тест {i}: {test_case['name']}")
    print(f"{'='*50}")

    try:
        response = requests.post('http://127.0.0.1:8000/huggingface-llm/parse-text',
                               json=test_case, headers=headers)

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

    print()

print("🎯 Тестирование завершено")

