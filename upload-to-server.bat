@echo off
REM Скрипт для загрузки проекта на Timeweb VDS
REM IP: 45.132.50.45

echo ============================================
echo   Загрузка проекта на Timeweb VDS
echo ============================================
echo.

REM Проверка наличия scp
where scp >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] SCP не найден!
    echo Установите OpenSSH Client в Windows:
    echo Settings -^> Apps -^> Optional Features -^> Add OpenSSH Client
    pause
    exit /b 1
)

echo [1/3] Проверка подключения к серверу...
ping -n 1 45.132.50.45 >nul
if %errorlevel% neq 0 (
    echo [ERROR] Сервер 45.132.50.45 недоступен!
    pause
    exit /b 1
)
echo [OK] Сервер доступен
echo.

echo [2/3] Загрузка файлов на сервер...
echo Это может занять несколько минут...
echo.

REM Загрузка всех файлов кроме ненужных
scp -r ^
    backend ^
    frontend ^
    data ^
    docker-compose.timeweb.yml ^
    Dockerfile.backend ^
    Dockerfile.frontend ^
    nginx-veres-backend.conf ^
    nginx-veres-frontend.conf ^
    quick-deploy.sh ^
    README.md ^
    DEPLOY_KINDPLATE.md ^
    "КРАТКАЯ_ИНСТРУКЦИЯ.md" ^
    "ШПАРГАЛКА_ДЛЯ_ДЕПЛОЯ.txt" ^
    root@45.132.50.45:/var/www/veres-tariff/

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Ошибка при загрузке файлов!
    echo Возможные причины:
    echo 1. Неверный пароль SSH
    echo 2. SSH ключ не настроен
    echo 3. Директория на сервере не создана
    echo.
    echo Попробуйте подключиться вручную:
    echo ssh root@45.132.50.45
    echo.
    pause
    exit /b 1
)

echo.
echo [OK] Файлы загружены
echo.

echo [3/3] Готово!
echo.
echo ============================================
echo   Файлы загружены на сервер
echo ============================================
echo.
echo Следующие шаги:
echo.
echo 1. Подключитесь к серверу:
echo    ssh root@45.132.50.45
echo.
echo 2. Запустите деплой:
echo    cd /var/www/veres-tariff
echo    bash quick-deploy.sh
echo.
echo 3. Или следуйте инструкциям в файле:
echo    КРАТКАЯ_ИНСТРУКЦИЯ.md
echo.
pause

