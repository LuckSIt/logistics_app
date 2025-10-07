# 🐳 Быстрый старт с Docker

## 📦 Предварительные требования

1. **Установите Docker Desktop:**
   - Windows/Mac: [https://www.docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop)
   - Linux: [https://docs.docker.com/engine/install/](https://docs.docker.com/engine/install/)

2. **Убедитесь, что Docker запущен:**
   ```bash
   docker --version
   docker-compose --version
   ```

---

## 🚀 Запуск приложения

### Windows

Просто запустите `start.bat`:
```cmd
start.bat
```

Или вручную:
```cmd
docker-compose up -d --build
```

### Linux / Mac

Сделайте скрипт исполняемым и запустите:
```bash
chmod +x start.sh
./start.sh
```

Или вручную:
```bash
docker-compose up -d --build
```

---

## 🌐 Доступ к приложению

После запуска приложение будет доступно по адресам:

- **Frontend (веб-интерфейс):** http://localhost
- **Backend API:** http://localhost:8000
- **API Документация:** http://localhost:8000/docs
- **Альтернативная документация:** http://localhost:8000/redoc

---

## 📊 Управление контейнерами

### Просмотр статуса
```bash
docker-compose ps
```

### Просмотр логов
```bash
# Все сервисы
docker-compose logs -f

# Только backend
docker-compose logs -f backend

# Только frontend
docker-compose logs -f frontend
```

### Остановка приложения
```bash
docker-compose down
```

### Остановка с удалением данных
```bash
docker-compose down -v
```

### Перезапуск сервиса
```bash
# Перезапустить backend
docker-compose restart backend

# Перезапустить frontend
docker-compose restart frontend
```

---

## 🔧 Разработка

### Пересборка после изменений в коде

```bash
# Пересобрать все
docker-compose up -d --build

# Пересобрать только backend
docker-compose up -d --build backend

# Пересобрать только frontend
docker-compose up -d --build frontend
```

### Выполнение команд внутри контейнера

```bash
# Подключиться к backend
docker exec -it veres-backend bash

# Выполнить команду в backend
docker exec -it veres-backend python init_db.py

# Подключиться к frontend
docker exec -it veres-frontend sh
```

### Просмотр использования ресурсов

```bash
docker stats veres-backend veres-frontend
```

---

## 🐛 Устранение неполадок

### Проблема: Порты заняты

Если порты 80 или 8000 уже используются, измените их в `docker-compose.yml`:

```yaml
services:
  backend:
    ports:
      - "8001:8000"  # Изменить на 8001
  
  frontend:
    ports:
      - "3000:80"    # Изменить на 3000
```

### Проблема: Контейнер не запускается

```bash
# Просмотрите логи
docker-compose logs backend
docker-compose logs frontend

# Полная очистка и перезапуск
docker-compose down -v
docker system prune -f
docker-compose up -d --build
```

### Проблема: База данных не создается

```bash
# Войдите в контейнер backend
docker exec -it veres-backend bash

# Вручную инициализируйте БД
python init_db.py
```

### Проблема: Frontend не подключается к Backend

Проверьте, что оба сервиса запущены:
```bash
docker-compose ps
```

Проверьте health check:
```bash
curl http://localhost:8000/health
```

---

## 📈 Продакшн развертывание

Для продакшн используйте отдельный конфиг:

```bash
# Запуск в продакшн режиме
docker-compose -f docker-compose.prod.yml up -d --build

# Остановка
docker-compose -f docker-compose.prod.yml down
```

Перед запуском создайте файл `.env`:
```bash
SECRET_KEY=your-super-secret-key-change-this
BACKEND_URL=https://your-backend-url.com
```

---

## 🧹 Очистка

### Удалить все контейнеры проекта
```bash
docker-compose down -v
```

### Удалить неиспользуемые образы
```bash
docker image prune -a
```

### Полная очистка Docker
```bash
docker system prune -a --volumes
```
⚠️ **Внимание:** Это удалит ВСЕ неиспользуемые контейнеры, образы и тома!

---

## 💾 Резервное копирование данных

### Backup базы данных
```bash
# Копировать БД из контейнера
docker cp veres-backend:/app/data/veres.db ./backup_veres.db
```

### Восстановление базы данных
```bash
# Копировать БД в контейнер
docker cp ./backup_veres.db veres-backend:/app/data/veres.db

# Перезапустить backend
docker-compose restart backend
```

---

## 📚 Полезные команды

```bash
# Версия Docker
docker --version
docker-compose --version

# Список всех контейнеров
docker ps -a

# Список образов
docker images

# Использование диска
docker system df

# Информация о контейнере
docker inspect veres-backend

# Экспорт логов в файл
docker-compose logs > logs.txt
```

---

## 🔗 Следующие шаги

- [📖 Полная документация](README.md)
- [☁️ Развертывание на Render](RENDER_DEPLOYMENT_GUIDE.md)
- [🐛 Отчет о проблемах](https://github.com/your-repo/issues)

---

## ℹ️ Справка

Если возникли проблемы:

1. Проверьте логи: `docker-compose logs -f`
2. Убедитесь, что Docker Desktop запущен
3. Попробуйте полную очистку и перезапуск
4. Создайте issue на GitHub

Удачи! 🚀

