# 🚀 БЫСТРЫЙ ДЕПЛОЙ НА TIMEWEB (api-kindplate.ru)

**IP сервера:** 45.132.50.45  
**Backend:** api-kindplate.ru  
**Frontend:** app-kindplate.ru

---

## ⚡ ПОШАГОВАЯ ИНСТРУКЦИЯ

### ШАГ 1: Подключение к серверу

```bash
ssh root@45.132.50.45
```

---

### ШАГ 2: Установка зависимостей (если еще не установлены)

```bash
# Проверка Docker
docker --version

# Если Docker не установлен:
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
systemctl start docker
systemctl enable docker

# Установка Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Проверка
docker-compose --version
```

---

### ШАГ 3: Создание директории и загрузка проекта

```bash
# Создание директории
mkdir -p /var/www/veres-tariff
cd /var/www/veres-tariff

# ВАРИАНТ A: Через Git (если проект в репозитории)
git clone https://ваш-репозиторий.git .

# ВАРИАНТ B: Через SCP с локального компьютера
# На вашем компьютере выполните:
# scp -r C:\Users\Vladimir\PycharmProjects\logistics_app root@45.132.50.45:/var/www/veres-tariff
```

---

### ШАГ 4: Создание необходимых директорий

```bash
cd /var/www/veres-tariff

mkdir -p data uploaded_files generated_docs models_cache
chmod -R 755 data uploaded_files generated_docs models_cache
```

---

### ШАГ 5: Настройка DNS (ПРОВЕРКА)

Убедитесь, что A-записи для доменов настроены:

```
A-запись: app-kindplate.ru  →  45.132.50.45
A-запись: api-kindplate.ru  →  45.132.50.45
```

**Проверка DNS:**
```bash
# Проверьте разрешение доменов
nslookup app-kindplate.ru
nslookup api-kindplate.ru

# Или через ping
ping -c 3 app-kindplate.ru
ping -c 3 api-kindplate.ru
```

---

### ШАГ 6: Получение SSL сертификатов

```bash
# Установка Certbot
apt update
apt install certbot python3-certbot-nginx -y

# Получение сертификата для бэкенда
certbot certonly --standalone -d api-kindplate.ru --email ваш-email@example.com --agree-tos --non-interactive

# Получение сертификата для фронтенда
certbot certonly --standalone -d app-kindplate.ru --email ваш-email@example.com --agree-tos --non-interactive

# Проверка сертификатов
ls -la /etc/letsencrypt/live/api-kindplate.ru/
ls -la /etc/letsencrypt/live/app-kindplate.ru/
```

**Важно:** Если порт 80 занят, временно остановите nginx:
```bash
systemctl stop nginx
# Затем получите сертификаты
# После получения запустите nginx обратно:
systemctl start nginx
```

---

### ШАГ 7: Настройка Nginx

```bash
cd /var/www/veres-tariff

# Копируем конфигурации
cp nginx-veres-backend.conf /etc/nginx/sites-available/veres-backend
cp nginx-veres-frontend.conf /etc/nginx/sites-available/veres-frontend

# Создаем симлинки
ln -s /etc/nginx/sites-available/veres-backend /etc/nginx/sites-enabled/
ln -s /etc/nginx/sites-available/veres-frontend /etc/nginx/sites-enabled/

# Проверяем конфигурацию
nginx -t

# Если OK, перезагружаем nginx
systemctl reload nginx
```

---

### ШАГ 8: Запуск Docker контейнеров

```bash
cd /var/www/veres-tariff

# Остановка старых контейнеров (если были)
docker-compose -f docker-compose.timeweb.yml down

# Сборка образов
docker-compose -f docker-compose.timeweb.yml build --no-cache

# Запуск контейнеров в фоновом режиме
docker-compose -f docker-compose.timeweb.yml up -d

# Проверка статуса
docker-compose -f docker-compose.timeweb.yml ps
```

---

### ШАГ 9: Проверка работоспособности

```bash
# Проверка контейнеров
docker ps | grep veres

# Проверка логов
docker-compose -f docker-compose.timeweb.yml logs -f

# Проверка локальных портов
curl http://localhost:8001/health  # Backend
curl http://localhost:8002/        # Frontend

# Проверка через домены (изнутри сервера)
curl https://api-kindplate.ru/health
curl https://app-kindplate.ru/
```

---

### ШАГ 10: Открыть в браузере

Откройте в браузере:
- **Frontend:** https://app-kindplate.ru
- **Backend API Docs:** https://api-kindplate.ru/docs

---

## 🎯 ПОЛНЫЙ СКРИПТ АВТОМАТИЧЕСКОГО ДЕПЛОЯ

Создайте файл `quick-deploy.sh` на сервере:

```bash
cat > /var/www/veres-tariff/quick-deploy.sh << 'EOF'
#!/bin/bash

echo "🚀 Начало деплоя Верес-Тариф на Timeweb"
echo "============================================="

# Переход в директорию проекта
cd /var/www/veres-tariff || exit

# Создание необходимых директорий
echo "📁 Создание директорий..."
mkdir -p data uploaded_files generated_docs models_cache
chmod -R 755 data uploaded_files generated_docs models_cache

# Остановка старых контейнеров
echo "🛑 Остановка старых контейнеров..."
docker-compose -f docker-compose.timeweb.yml down

# Сборка образов
echo "🔨 Сборка Docker образов..."
docker-compose -f docker-compose.timeweb.yml build --no-cache

# Запуск контейнеров
echo "▶️  Запуск контейнеров..."
docker-compose -f docker-compose.timeweb.yml up -d

# Ожидание запуска
echo "⏳ Ожидание запуска сервисов (30 сек)..."
sleep 30

# Проверка статуса
echo "✅ Проверка статуса..."
docker-compose -f docker-compose.timeweb.yml ps

# Проверка health endpoints
echo "🏥 Проверка здоровья сервисов..."
curl -s http://localhost:8001/health || echo "⚠️  Backend не отвечает"
curl -s http://localhost:8002/ > /dev/null || echo "⚠️  Frontend не отвечает"

echo ""
echo "============================================="
echo "✅ Деплой завершен!"
echo ""
echo "📊 Доступ к приложению:"
echo "   Frontend: https://app-kindplate.ru"
echo "   Backend:  https://api-kindplate.ru/docs"
echo ""
echo "📝 Полезные команды:"
echo "   Логи:      docker-compose -f docker-compose.timeweb.yml logs -f"
echo "   Рестарт:   docker-compose -f docker-compose.timeweb.yml restart"
echo "   Остановка: docker-compose -f docker-compose.timeweb.yml down"
echo ""
EOF

# Сделать скрипт исполняемым
chmod +x /var/www/veres-tariff/quick-deploy.sh
```

**Использование скрипта:**
```bash
/var/www/veres-tariff/quick-deploy.sh
```

---

## 🔄 НАСТРОЙКА АВТОЗАПУСКА

```bash
# Создание systemd service
cat > /etc/systemd/system/veres-tariff.service << 'EOF'
[Unit]
Description=Veres Tariff Docker Compose
Requires=docker.service
After=docker.service network-online.target
Wants=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/var/www/veres-tariff
ExecStart=/usr/local/bin/docker-compose -f docker-compose.timeweb.yml up -d
ExecStop=/usr/local/bin/docker-compose -f docker-compose.timeweb.yml down
TimeoutStartSec=300

[Install]
WantedBy=multi-user.target
EOF

# Активация автозапуска
systemctl daemon-reload
systemctl enable veres-tariff.service
systemctl start veres-tariff.service

# Проверка статуса
systemctl status veres-tariff.service
```

---

## 📊 ПРОВЕРКА ИСПОЛЬЗУЕМЫХ ПОРТОВ

```bash
# Проверка, какие порты заняты
netstat -tulpn | grep -E ':80|:443|:8001|:8002'

# Если порты 8001 или 8002 заняты, измените их в docker-compose.timeweb.yml
# Например: 8003:8000 и 8004:80
```

---

## 🔧 УПРАВЛЕНИЕ ПРИЛОЖЕНИЕМ

### Основные команды:

```bash
# Перейти в директорию проекта
cd /var/www/veres-tariff

# Просмотр логов (все сервисы)
docker-compose -f docker-compose.timeweb.yml logs -f

# Просмотр логов (только backend)
docker-compose -f docker-compose.timeweb.yml logs -f veres-backend

# Просмотр логов (только frontend)
docker-compose -f docker-compose.timeweb.yml logs -f veres-frontend

# Рестарт сервисов
docker-compose -f docker-compose.timeweb.yml restart

# Остановка
docker-compose -f docker-compose.timeweb.yml down

# Обновление (при изменении кода)
git pull  # если используете Git
docker-compose -f docker-compose.timeweb.yml down
docker-compose -f docker-compose.timeweb.yml build --no-cache
docker-compose -f docker-compose.timeweb.yml up -d

# Просмотр статуса контейнеров
docker-compose -f docker-compose.timeweb.yml ps

# Просмотр использования ресурсов
docker stats
```

---

## 🎯 УЧЕТНЫЕ ДАННЫЕ ДЛЯ ВХОДА

После успешного запуска используйте:

| Роль | Логин | Пароль |
|------|-------|--------|
| Администратор | `admin` | `admin123` |
| Сотрудник | `employee1` | `employee123` |
| Экспедитор | `forwarder1` | `forwarder123` |
| Клиент | `client1` | `client123` |

---

## ✅ ФИНАЛЬНЫЙ ЧЕКЛИСТ

- [ ] SSH подключение к серверу работает
- [ ] Docker и Docker Compose установлены
- [ ] Проект загружен в /var/www/veres-tariff
- [ ] DNS записи A настроены и работают
- [ ] SSL сертификаты получены для обоих доменов
- [ ] Nginx конфигурации установлены
- [ ] Docker контейнеры запущены
- [ ] https://app-kindplate.ru открывается
- [ ] https://api-kindplate.ru/docs открывается
- [ ] Можно войти под любой учетной записью
- [ ] Автозапуск настроен

---

## 🆘 TROUBLESHOOTING

### Проблема: DNS не резолвится

```bash
# Проверка DNS
dig app-kindplate.ru
dig api-kindplate.ru

# Подождите 15-30 минут после настройки A-записей
```

### Проблема: SSL сертификаты не получаются

```bash
# Убедитесь, что порт 80 свободен
systemctl stop nginx
lsof -i :80

# Попробуйте снова
certbot certonly --standalone -d api-kindplate.ru
certbot certonly --standalone -d app-kindplate.ru

# Запустите nginx обратно
systemctl start nginx
```

### Проблема: Nginx выдает 502 Bad Gateway

```bash
# Проверьте контейнеры
docker ps | grep veres

# Проверьте логи
docker-compose -f docker-compose.timeweb.yml logs

# Проверьте порты изнутри
curl http://localhost:8001
curl http://localhost:8002
```

### Проблема: Контейнеры не запускаются

```bash
# Просмотр логов
docker-compose -f docker-compose.timeweb.yml logs

# Проверка прав
ls -la data uploaded_files generated_docs

# Пересборка
docker-compose -f docker-compose.timeweb.yml down
docker-compose -f docker-compose.timeweb.yml build --no-cache
docker-compose -f docker-compose.timeweb.yml up -d
```

---

## 🎉 ВСЁ ГОТОВО!

После выполнения всех шагов ваше приложение будет доступно по адресам:

- **Frontend:** https://app-kindplate.ru
- **Backend API:** https://api-kindplate.ru/docs

**Для мониторинга:**
```bash
# Статус контейнеров
docker ps

# Использование ресурсов
docker stats

# Логи в реальном времени
docker-compose -f docker-compose.timeweb.yml logs -f
```

Удачи! 🚀

