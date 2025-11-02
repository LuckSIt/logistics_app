# 🚀 ДЕПЛОЙ ЧЕРЕЗ GIT (САМЫЙ ПРОСТОЙ СПОСОБ)

## 📋 ШАГ 1: ПОДГОТОВКА НА ЛОКАЛЬНОМ КОМПЬЮТЕРЕ

### 1.1. Инициализация Git (если еще не сделано)

```bash
cd C:\Users\Vladimir\PycharmProjects\logistics_app

# Инициализация
git init

# Добавление всех файлов
git add .

# Первый коммит
git commit -m "Initial commit: Veres-Tariff logistics app"
```

### 1.2. Создание репозитория на GitHub

1. Перейди на https://github.com
2. Нажми **"New repository"**
3. Название: `veres-tariff` или `logistics_app`
4. Описание: `Логистическая система Верес-Тариф`
5. **НЕ создавай** README, .gitignore (уже есть)
6. Нажми **"Create repository"**

### 1.3. Подключение к GitHub

```bash
# Добавь remote (замени YOUR_USERNAME на свой GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/veres-tariff.git

# Или через SSH (если настроен SSH ключ)
git remote add origin git@github.com:YOUR_USERNAME/veres-tariff.git

# Отправь код на GitHub
git branch -M main
git push -u origin main
```

---

## 🖥️ ШАГ 2: ДЕПЛОЙ НА СЕРВЕР TIMEWEB

### 2.1. Подключись к серверу

```bash
ssh root@45.132.50.45
```

### 2.2. Установка Git (если не установлен)

```bash
# Проверка
git --version

# Если не установлен
apt update && apt install git -y
```

### 2.3. Клонирование репозитория

```bash
# Создание директории
mkdir -p /var/www
cd /var/www

# Клонирование (замени YOUR_USERNAME на свой)
git clone https://github.com/YOUR_USERNAME/veres-tariff.git veres-tariff

# Переход в директорию
cd veres-tariff
```

### 2.4. Создание необходимых директорий

```bash
mkdir -p data uploaded_files generated_docs models_cache
chmod -R 755 data uploaded_files generated_docs models_cache
```

### 2.5. Установка SSL сертификатов

```bash
# Установка certbot
apt update && apt install certbot python3-certbot-nginx -y

# Остановка nginx (если работает)
systemctl stop nginx

# Получение сертификатов
certbot certonly --standalone -d api-kindplate.ru --email your@email.com --agree-tos --non-interactive
certbot certonly --standalone -d app-kindplate.ru --email your@email.com --agree-tos --non-interactive

# Запуск nginx
systemctl start nginx
```

### 2.6. Настройка Nginx

```bash
cd /var/www/veres-tariff

# Копирование конфигов
cp nginx-veres-backend.conf /etc/nginx/sites-available/veres-backend
cp nginx-veres-frontend.conf /etc/nginx/sites-available/veres-frontend

# Создание симлинков
ln -s /etc/nginx/sites-available/veres-backend /etc/nginx/sites-enabled/
ln -s /etc/nginx/sites-available/veres-frontend /etc/nginx/sites-enabled/

# Проверка и перезагрузка
nginx -t && systemctl reload nginx
```

### 2.7. Запуск приложения

```bash
cd /var/www/veres-tariff

# Автоматический деплой
chmod +x quick-deploy.sh
bash quick-deploy.sh

# ИЛИ вручную
docker-compose -f docker-compose.timeweb.yml build --no-cache
docker-compose -f docker-compose.timeweb.yml up -d
```

---

## 🔄 ШАГ 3: ОБНОВЛЕНИЕ ПРИЛОЖЕНИЯ

Когда нужно обновить код на сервере:

### 3.1. На локальном компьютере (Windows)

```bash
cd C:\Users\Vladimir\PycharmProjects\logistics_app

# Добавить изменения
git add .
git commit -m "Описание изменений"
git push
```

### 3.2. На сервере

```bash
ssh root@45.132.50.45
cd /var/www/veres-tariff

# Получить обновления
git pull

# Перезапустить контейнеры
docker-compose -f docker-compose.timeweb.yml down
docker-compose -f docker-compose.timeweb.yml build --no-cache
docker-compose -f docker-compose.timeweb.yml up -d
```

---

## 📝 БЫСТРАЯ ШПАРГАЛКА

### На Windows (обновление кода):
```bash
git add .
git commit -m "Update"
git push
```

### На сервере (применение обновлений):
```bash
cd /var/www/veres-tariff
git pull
docker-compose -f docker-compose.timeweb.yml restart
```

---

## 🔐 РАБОТА С ПРИВАТНЫМ РЕПОЗИТОРИЕМ

Если репозиторий приватный, на сервере при клонировании:

```bash
# Вариант 1: HTTPS с токеном
git clone https://YOUR_TOKEN@github.com/YOUR_USERNAME/veres-tariff.git

# Вариант 2: SSH ключ
ssh-keygen -t ed25519 -C "your@email.com"
cat ~/.ssh/id_ed25519.pub
# Добавь этот ключ на GitHub: Settings -> SSH Keys -> New SSH key
git clone git@github.com:YOUR_USERNAME/veres-tariff.git veres-tariff
```

---

## ✅ ПРЕИМУЩЕСТВА ЭТОГО СПОСОБА

✅ Легко обновлять код  
✅ История всех изменений  
✅ Можно откатиться к предыдущей версии  
✅ Не нужно каждый раз загружать все файлы  
✅ Работает с любого компьютера  

---

## 🎯 ПОЛНАЯ ПОСЛЕДОВАТЕЛЬНОСТЬ (КОПИРУЙ И ВСТАВЛЯЙ)

### На Windows:

```bash
cd C:\Users\Vladimir\PycharmProjects\logistics_app

git init
git add .
git commit -m "Initial commit: Veres-Tariff"
git remote add origin https://github.com/YOUR_USERNAME/veres-tariff.git
git branch -M main
git push -u origin main
```

### На сервере:

```bash
ssh root@45.132.50.45

cd /var/www
git clone https://github.com/YOUR_USERNAME/veres-tariff.git veres-tariff
cd veres-tariff

mkdir -p data uploaded_files generated_docs models_cache
chmod -R 755 data uploaded_files generated_docs models_cache

apt update && apt install certbot python3-certbot-nginx -y
systemctl stop nginx
certbot certonly --standalone -d api-kindplate.ru --email your@email.com --agree-tos --non-interactive
certbot certonly --standalone -d app-kindplate.ru --email your@email.com --agree-tos --non-interactive

cp nginx-veres-backend.conf /etc/nginx/sites-available/veres-backend
cp nginx-veres-frontend.conf /etc/nginx/sites-available/veres-frontend
ln -s /etc/nginx/sites-available/veres-backend /etc/nginx/sites-enabled/
ln -s /etc/nginx/sites-available/veres-frontend /etc/nginx/sites-enabled/
nginx -t && systemctl start nginx && systemctl reload nginx

chmod +x quick-deploy.sh
bash quick-deploy.sh
```

**Готово!** 🎉

Приложение будет доступно:
- Frontend: https://app-kindplate.ru
- Backend: https://api-kindplate.ru/docs

---

## 📞 ПРОВЕРКА

```bash
# Статус контейнеров
docker ps

# Логи
docker-compose -f docker-compose.timeweb.yml logs -f

# Проверка в браузере
curl https://api-kindplate.ru/health
```

---

Удачи! 🚀

