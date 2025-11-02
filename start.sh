#!/bin/bash
# Скрипт быстрого запуска Верес-Тариф на Linux/Mac

set -e

echo "================================================"
echo "  Верес-Тариф - Система управления тарифами"
echo "================================================"
echo ""

# Проверка Docker
if ! command -v docker &> /dev/null; then
    echo "[ERROR] Docker не установлен!"
    echo "Установите Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

echo "[1/4] Проверка Docker... OK"
echo ""

# Проверка Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "[ERROR] Docker Compose не установлен!"
    echo "Установите Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "[2/4] Остановка старых контейнеров..."
docker-compose down 2>/dev/null || true
echo ""

echo "[3/4] Сборка и запуск приложения..."
echo "Это может занять несколько минут при первом запуске..."
echo ""
docker-compose up -d --build

if [ $? -ne 0 ]; then
    echo ""
    echo "[ERROR] Ошибка при запуске!"
    echo "Проверьте логи: docker-compose logs"
    exit 1
fi

echo ""
echo "[4/4] Ожидание готовности сервисов..."
sleep 15

echo ""
echo "================================================"
echo "  Приложение успешно запущено!"
echo "================================================"
echo ""
echo "Frontend: http://localhost"
echo "Backend API: http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Для просмотра логов: docker-compose logs -f"
echo "Для остановки: docker-compose down"
echo ""

# Открываем браузер (если возможно)
if command -v xdg-open &> /dev/null; then
    xdg-open http://localhost &
elif command -v open &> /dev/null; then
    open http://localhost &
fi

echo "Готово!"





