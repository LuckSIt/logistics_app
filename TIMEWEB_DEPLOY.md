# 🚀 Развертывание на Timeweb VDS

Инструкция по развертыванию проекта Верес-Тариф на VDS Timeweb вместе с существующим приложением.

---

## 📋 ПРЕДВАРИТЕЛЬНЫЕ ТРЕБОВАНИЯ

- ✅ VDS на Timeweb (уже есть)
- ✅ Два домена (для фронта и бека) - уже куплены
- ✅ Docker и Docker Compose установлены
- ✅ Nginx установлен на сервере
- ✅ SSH доступ к серверу

---

## 🔧 ШАГ 1: ПОДГОТОВКА ДОМЕНОВ

### 1.1. Настройка DNS записей

В панели управления доменами (обычно это панель Timeweb) создайте A-записи:

```
ваш-домен-фронта.ru  →  IP вашего VDS
ваш-домен-бека.ru    →  IP вашего VDS
```

**Пример:**
```
veres.yourdomain.ru      →  12.34.56.78
api.veres.yourdomain.ru  →  12.34.56.78
```

⏱️ DNS может обновляться до 24 часов, но обычно это занимает 15-30 минут.

---

## 🛠️ ШАГ 2: ПОДКЛЮЧЕНИЕ К СЕРВЕРУ

```bash
# Подключитесь к вашему VDS
ssh root@ваш-ip-адрес

# Или если используете ключ
ssh -i ~/.ssh/your_key root@ваш-ip-адрес
```

---

## 📦 ШАГ 3: ЗАГРУЗКА ПРОЕКТА НА СЕРВЕР

### Вариант A: Через Git (рекомендуется)

```bash
# Перейдите в директорию для проектов
cd /var/www

# Клонируйте репозиторий
git clone https://ваш-репозиторий.git veres-tariff
cd veres-tariff
```

### Вариант B: Через SCP/SFTP

```bash
# На вашем локальном компьютере
scp -r C:\Users\Vladimir\PycharmProjects\logistics_app root@ваш-ip:/var/www/veres-tariff
```

---

## ⚙️ ШАГ 4: НАСТРОЙКА КОНФИГУРАЦИИ

### 4.1. Обновите docker-compose.timeweb.yml

```bash
cd /var/www/veres-tariff

# Отредактируйте файл
nano docker-compose.timeweb.yml
```

**Замените:**
- `ваш-домен-бека.ru` на ваш реальный домен бэкенда
- `ваш-домен-фронта.ru` на ваш реальный домен фронтенда

**Пример:**
```yaml
environment:
  - BACKEND_URL=https://api.veres.yourdomain.ru
  - FRONTEND_URL=https://veres.yourdomain.ru
```

### 4.2. Проверьте порты

Убедитесь, что порты **8001** и **8002** свободны:

```bash
# Проверка занятых портов
netstat -tulpn | grep -E '8001|8002'

# Если порты заняты, измените их в docker-compose.timeweb.yml
```

---

## 🔐 ШАГ 5: НАСТРОЙКА SSL СЕРТИФИКАТОВ

### 5.1. Установка Certbot (если не установлен)

```bash
# Для Ubuntu/Debian
apt update
apt install certbot python3-certbot-nginx -y
```

### 5.2. Получение сертификатов

```bash
# Для бэкенда
certbot certonly --nginx -d ваш-домен-бека.ru

# Для фронтенда
certbot certonly --nginx -d ваш-домен-фронта.ru
```

**Важно:** Сертификаты будут храниться в `/etc/letsencrypt/live/`

### 5.3. Автообновление сертификатов

```bash
# Проверьте автообновление
certbot renew --dry-run

# Certbot автоматически добавит задачу в cron
```

---

## 🌐 ШАГ 6: НАСТРОЙКА NGINX

### 6.1. Копирование конфигураций

```bash
cd /var/www/veres-tariff

# Скопируйте конфиги nginx
cp nginx-veres-backend.conf /etc/nginx/sites-available/
cp nginx-veres-frontend.conf /etc/nginx/sites-available/
```

### 6.2. Обновите домены в конфигах

```bash
# Бэкенд
nano /etc/nginx/sites-available/nginx-veres-backend.conf
# Замените все "ваш-домен-бека.ru" на ваш реальный домен

# Фронтенд
nano /etc/nginx/sites-available/nginx-veres-frontend.conf
# Замените все "ваш-домен-фронта.ru" на ваш реальный домен
```

### 6.3. Активация конфигураций

```bash
# Создайте симлинки
ln -s /etc/nginx/sites-available/nginx-veres-backend.conf /etc/nginx/sites-enabled/
ln -s /etc/nginx/sites-available/nginx-veres-frontend.conf /etc/nginx/sites-enabled/

# Проверьте конфигурацию nginx
nginx -t

# Если всё ОК, перезагрузите nginx
systemctl reload nginx
```

---

## 🐳 ШАГ 7: ЗАПУСК DOCKER КОНТЕЙНЕРОВ

### 7.1. Создание необходимых директорий

```bash
cd /var/www/veres-tariff

mkdir -p data uploaded_files generated_docs models_cache
chmod -R 755 data uploaded_files generated_docs models_cache
```

### 7.2. Сборка и запуск

```bash
# Остановите старые контейнеры (если есть)
docker-compose -f docker-compose.timeweb.yml down

# Соберите образы
docker-compose -f docker-compose.timeweb.yml build --no-cache

# Запустите контейнеры
docker-compose -f docker-compose.timeweb.yml up -d

# Проверьте статус
docker-compose -f docker-compose.timeweb.yml ps
```

### 7.3. Проверка логов

```bash
# Все логи
docker-compose -f docker-compose.timeweb.yml logs -f

# Только backend
docker-compose -f docker-compose.timeweb.yml logs -f veres-backend

# Только frontend
docker-compose -f docker-compose.timeweb.yml logs -f veres-frontend
```

---

## ✅ ШАГ 8: ПРОВЕРКА РАБОТОСПОСОБНОСТИ

### 8.1. Проверьте контейнеры

```bash
# Должны быть в статусе "Up"
docker ps | grep veres
```

### 8.2. Проверьте порты

```bash
# Проверьте, что приложения слушают порты
curl http://localhost:8001/health  # Backend
curl http://localhost:8002/        # Frontend
```

### 8.3. Проверьте через браузер

Откройте в браузере:
- Frontend: `https://ваш-домен-фронта.ru`
- Backend API: `https://ваш-домен-бека.ru/docs`

### 8.4. Проверьте логины

Попробуйте войти:
- admin / admin123
- employee1 / employee123
- forwarder1 / forwarder123
- client1 / client123

---

## 🔄 ШАГ 9: АВТОЗАПУСК ПРИ ПЕРЕЗАГРУЗКЕ

```bash
# Создайте systemd service
nano /etc/systemd/system/veres-tariff.service
```

**Содержимое файла:**
```ini
[Unit]
Description=Veres Tariff Docker Compose
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/var/www/veres-tariff
ExecStart=/usr/bin/docker-compose -f docker-compose.timeweb.yml up -d
ExecStop=/usr/bin/docker-compose -f docker-compose.timeweb.yml down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

**Активация:**
```bash
systemctl daemon-reload
systemctl enable veres-tariff.service
systemctl start veres-tariff.service

# Проверка статуса
systemctl status veres-tariff.service
```

---

## 📊 МОНИТОРИНГ И УПРАВЛЕНИЕ

### Полезные команды:

```bash
# Просмотр логов
docker-compose -f docker-compose.timeweb.yml logs -f

# Перезапуск сервисов
docker-compose -f docker-compose.timeweb.yml restart

# Остановка
docker-compose -f docker-compose.timeweb.yml down

# Обновление (при изменении кода)
cd /var/www/veres-tariff
git pull  # если используете Git
docker-compose -f docker-compose.timeweb.yml down
docker-compose -f docker-compose.timeweb.yml build --no-cache
docker-compose -f docker-compose.timeweb.yml up -d

# Просмотр использования ресурсов
docker stats
```

### Проверка использования места на диске:

```bash
# Размер Docker образов
docker system df

# Очистка неиспользуемых образов
docker system prune -a
```

---

## 🔧 TROUBLESHOOTING

### Проблема: Порты заняты

```bash
# Найдите процесс, использующий порт
lsof -i :8001
lsof -i :8002

# Измените порты в docker-compose.timeweb.yml
# Например: 8003:8000 и 8004:80
```

### Проблема: Nginx выдает 502 Bad Gateway

```bash
# Проверьте, запущены ли контейнеры
docker ps | grep veres

# Проверьте логи nginx
tail -f /var/log/nginx/veres-*-error.log

# Проверьте, доступны ли порты изнутри
curl http://localhost:8001
curl http://localhost:8002
```

### Проблема: SSL сертификаты не работают

```bash
# Проверьте пути к сертификатам
ls -la /etc/letsencrypt/live/ваш-домен/

# Переполучите сертификат
certbot delete --cert-name ваш-домен
certbot certonly --nginx -d ваш-домен
```

### Проблема: Контейнеры не запускаются

```bash
# Просмотрите логи
docker-compose -f docker-compose.timeweb.yml logs

# Проверьте права на директории
chmod -R 755 data uploaded_files generated_docs

# Пересоберите образы
docker-compose -f docker-compose.timeweb.yml build --no-cache
```

---

## 📈 ОПТИМИЗАЦИЯ

### Настройка ограничений ресурсов (опционально)

В `docker-compose.timeweb.yml` добавьте:

```yaml
services:
  veres-backend:
    # ... остальные настройки ...
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 1G
```

### Логирование

Для сохранения логов добавьте в `docker-compose.timeweb.yml`:

```yaml
services:
  veres-backend:
    # ... остальные настройки ...
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

---

## 🎯 ИТОГОВАЯ СТРУКТУРА НА СЕРВЕРЕ

```
/var/www/
├── ваше-первое-приложение/    # Существующее приложение
│   └── docker-compose.yml     # Порты: 80, 8000
│
└── veres-tariff/              # Новое приложение
    ├── backend/
    ├── frontend/
    ├── data/                  # База данных
    ├── uploaded_files/        # Загруженные файлы
    ├── generated_docs/        # Сгенерированные КП
    └── docker-compose.timeweb.yml  # Порты: 8001, 8002

/etc/nginx/sites-enabled/
├── ваше-первое-приложение.conf
├── nginx-veres-backend.conf
└── nginx-veres-frontend.conf
```

---

## 📞 ФИНАЛЬНАЯ ПРОВЕРКА

Чеклист перед запуском в продакшен:

- [ ] DNS записи настроены и активны
- [ ] SSL сертификаты получены для обоих доменов
- [ ] Порты 8001 и 8002 свободны
- [ ] Nginx конфигурации активированы
- [ ] Docker контейнеры запущены и работают
- [ ] Frontend открывается по https://ваш-домен-фронта.ru
- [ ] Backend API доступен по https://ваш-домен-бека.ru/docs
- [ ] Можно войти под всеми учетными записями
- [ ] Автозапуск настроен через systemd
- [ ] Логи пишутся корректно

---

## 🎉 ГОТОВО!

Ваше приложение теперь работает на Timeweb VDS вместе с существующим приложением!

**Полезные ссылки:**
- Frontend: https://ваш-домен-фронта.ru
- Backend API Docs: https://ваш-домен-бека.ru/docs
- Логи: `docker-compose -f docker-compose.timeweb.yml logs -f`

**Для обновления приложения:**
```bash
cd /var/www/veres-tariff
git pull
docker-compose -f docker-compose.timeweb.yml down
docker-compose -f docker-compose.timeweb.yml build --no-cache
docker-compose -f docker-compose.timeweb.yml up -d
```

Удачи! 🚀

