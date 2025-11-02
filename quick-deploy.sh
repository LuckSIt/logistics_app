#!/bin/bash

# 🚀 Скрипт автоматического деплоя Верес-Тариф на Timeweb
# Домены: app-kindplate.ru (frontend) и api-kindplate.ru (backend)
# IP: 45.132.50.45

set -e  # Остановка при ошибке

echo "============================================="
echo "🚀 Деплой Верес-Тариф на Timeweb"
echo "============================================="
echo ""

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Функция для вывода с цветом
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# Проверка, что скрипт запущен от root
if [ "$EUID" -ne 0 ]; then 
    print_error "Запустите скрипт от root: sudo bash quick-deploy.sh"
    exit 1
fi

# Переход в директорию проекта
PROJECT_DIR="/var/www/veres-tariff"
if [ ! -d "$PROJECT_DIR" ]; then
    print_error "Директория $PROJECT_DIR не найдена!"
    print_info "Создайте директорию и загрузите туда проект"
    exit 1
fi

cd $PROJECT_DIR
print_success "Перешли в директорию проекта: $PROJECT_DIR"

# Создание необходимых директорий
print_info "Создание необходимых директорий..."
mkdir -p data uploaded_files generated_docs models_cache
chmod -R 755 data uploaded_files generated_docs models_cache
print_success "Директории созданы"

# Проверка наличия docker-compose.timeweb.yml
if [ ! -f "docker-compose.timeweb.yml" ]; then
    print_error "Файл docker-compose.timeweb.yml не найден!"
    exit 1
fi

# Остановка старых контейнеров
print_info "Остановка старых контейнеров (если есть)..."
docker-compose -f docker-compose.timeweb.yml down 2>/dev/null || true
print_success "Старые контейнеры остановлены"

# Сборка образов
print_info "Сборка Docker образов (это может занять 5-10 минут)..."
docker-compose -f docker-compose.timeweb.yml build --no-cache
print_success "Образы собраны"

# Запуск контейнеров
print_info "Запуск контейнеров..."
docker-compose -f docker-compose.timeweb.yml up -d
print_success "Контейнеры запущены"

# Ожидание запуска
print_info "Ожидание запуска сервисов (30 секунд)..."
sleep 30

# Проверка статуса контейнеров
echo ""
print_info "Статус контейнеров:"
docker-compose -f docker-compose.timeweb.yml ps

# Проверка health endpoints
echo ""
print_info "Проверка здоровья сервисов..."

if curl -s -f http://localhost:8001/health > /dev/null 2>&1; then
    print_success "Backend работает (http://localhost:8001)"
else
    print_error "Backend не отвечает на http://localhost:8001/health"
fi

if curl -s -f http://localhost:8002/ > /dev/null 2>&1; then
    print_success "Frontend работает (http://localhost:8002)"
else
    print_error "Frontend не отвечает на http://localhost:8002"
fi

# Итоговая информация
echo ""
echo "============================================="
print_success "Деплой завершен!"
echo "============================================="
echo ""
echo "📊 Доступ к приложению:"
echo "   Frontend: https://app-kindplate.ru"
echo "   Backend:  https://api-kindplate.ru/docs"
echo ""
echo "👤 Данные для входа:"
echo "   Администратор: admin / admin123"
echo "   Сотрудник:     employee1 / employee123"
echo "   Экспедитор:    forwarder1 / forwarder123"
echo "   Клиент:        client1 / client123"
echo ""
echo "📝 Полезные команды:"
echo "   Логи:      docker-compose -f docker-compose.timeweb.yml logs -f"
echo "   Рестарт:   docker-compose -f docker-compose.timeweb.yml restart"
echo "   Остановка: docker-compose -f docker-compose.timeweb.yml down"
echo "   Статус:    docker-compose -f docker-compose.timeweb.yml ps"
echo ""

# Проверка nginx
if systemctl is-active --quiet nginx; then
    print_success "Nginx запущен"
    echo ""
    echo "⚠️  ВАЖНО: Убедитесь, что настроены:"
    echo "   1. SSL сертификаты для app-kindplate.ru и api-kindplate.ru"
    echo "   2. Nginx конфигурации в /etc/nginx/sites-enabled/"
    echo ""
    echo "   Подробнее в файле: DEPLOY_KINDPLATE.md"
else
    print_error "Nginx не запущен! Запустите: systemctl start nginx"
fi

echo ""
print_success "Готово! 🎉"

