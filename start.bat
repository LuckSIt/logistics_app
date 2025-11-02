@echo off
REM Скрипт быстрого запуска Верес-Тариф на Windows

echo ================================================
echo   Верес-Тариф - Система управления тарифами
echo ================================================
echo.

REM Проверка Docker
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker не установлен или не запущен!
    echo Установите Docker Desktop: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

echo [1/4] Проверка Docker... OK
echo.

REM Остановка предыдущих контейнеров
echo [2/4] Остановка старых контейнеров...
docker-compose down 2>nul
echo.

REM Сборка и запуск
echo [3/4] Сборка и запуск приложения...
echo Это может занять несколько минут при первом запуске...
echo.
docker-compose up -d --build

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Ошибка при запуске!
    echo Проверьте логи: docker-compose logs
    pause
    exit /b 1
)

echo.
echo [4/4] Ожидание готовности сервисов...
timeout /t 10 /nobreak >nul

echo.
echo ================================================
echo   Приложение успешно запущено!
echo ================================================
echo.
echo Frontend: http://localhost
echo Backend API: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.
echo Для просмотра логов: docker-compose logs -f
echo Для остановки: docker-compose down
echo.

REM Открываем браузер
start http://localhost

echo Нажмите любую клавишу для выхода...
pause >nul





