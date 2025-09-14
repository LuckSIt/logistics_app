#!/bin/bash

# Скрипт автоматической настройки Верес-Тариф

echo "🚀 Настройка системы Верес-Тариф"
echo "=================================="

# Проверяем наличие Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен. Пожалуйста, установите Docker:"
    echo "   https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose не установлен. Пожалуйста, установите Docker Compose:"
    echo "   https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker и Docker Compose найдены"

# Создаем необходимые директории
echo "📁 Создание директорий..."
mkdir -p data uploaded_files generated_docs

# Собираем и запускаем контейнеры
echo "🔨 Сборка и запуск контейнеров..."
docker-compose up -d --build

# Ждем запуска сервисов
echo "⏳ Ожидание запуска сервисов..."
sleep 10

# Проверяем статус
echo "🔍 Проверка статуса сервисов..."
docker-compose ps

echo ""
echo "🎉 Установка завершена!"
echo ""
echo "📱 Приложение доступно по адресам:"
echo "   Frontend: http://localhost:3000"
echo "   Backend:  http://localhost:8000"
echo ""
echo "👤 Данные для входа:"
echo "   Администратор: admin / admin123"
echo "   Сотрудник:     employee1 / employee123"
echo "   Экспедитор:    forwarder1 / forwarder123"
echo "   Клиент:        client1 / client123"
echo ""
echo "📋 Полезные команды:"
echo "   Просмотр логов:    docker-compose logs -f"
echo "   Остановка:         docker-compose down"
echo "   Перезапуск:        docker-compose restart"
echo "   Обновление:        docker-compose pull && docker-compose up -d"
echo ""
echo "💡 Рекомендуется изменить пароли после первого входа!"
