@echo off
REM Скрипт автоматической настройки Верес-Тариф для Windows

echo 🚀 Настройка системы Верес-Тариф
echo ==================================

REM Проверяем наличие Docker
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker не установлен. Пожалуйста, установите Docker Desktop:
    echo    https://docs.docker.com/desktop/windows/install/
    pause
    exit /b 1
)

docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker Compose не установлен. Пожалуйста, установите Docker Compose:
    echo    https://docs.docker.com/compose/install/
    pause
    exit /b 1
)

echo ✅ Docker и Docker Compose найдены

REM Создаем необходимые директории
echo 📁 Создание директорий...
if not exist "data" mkdir data
if not exist "uploaded_files" mkdir uploaded_files
if not exist "generated_docs" mkdir generated_docs

REM Собираем и запускаем контейнеры
echo 🔨 Сборка и запуск контейнеров...
docker-compose up -d --build

REM Ждем запуска сервисов
echo ⏳ Ожидание запуска сервисов...
timeout /t 10 /nobreak >nul

REM Проверяем статус
echo 🔍 Проверка статуса сервисов...
docker-compose ps

echo.
echo 🎉 Установка завершена!
echo.
echo 📱 Приложение доступно по адресам:
echo    Frontend: http://localhost:3000
echo    Backend:  http://localhost:8000
echo.
echo 👤 Данные для входа:
echo    Администратор: admin / admin123
echo    Сотрудник:     employee1 / employee123
echo    Экспедитор:    forwarder1 / forwarder123
echo    Клиент:        client1 / client123
echo.
echo 📋 Полезные команды:
echo    Просмотр логов:    docker-compose logs -f
echo    Остановка:         docker-compose down
echo    Перезапуск:        docker-compose restart
echo    Обновление:        docker-compose pull ^&^& docker-compose up -d
echo.
echo 💡 Рекомендуется изменить пароли после первого входа!
echo.
pause
