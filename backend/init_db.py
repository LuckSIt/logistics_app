#!/usr/bin/env python3
"""
Скрипт инициализации базы данных для Docker
"""

import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

# Добавляем текущую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import Base, engine
import models

# Создаем контекст для хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_tables():
    """Создает все таблицы в базе данных"""
    print("🔨 Создание таблиц базы данных...")
    Base.metadata.create_all(bind=engine)
    print("✅ Таблицы созданы")

def create_admin_user():
    """Создает администратора по умолчанию"""
    print("👤 Создание администратора...")
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Проверяем, есть ли уже администратор
        admin = db.query(models.User).filter(models.User.username == "admin").first()
        if admin:
            print("✅ Администратор уже существует")
            return
        
        # Создаем администратора
        admin_user = models.User(
            username="admin",
            full_name="Администратор системы",
            email="admin@veres-tariff.ru",
            password_hash=pwd_context.hash("admin123"),
            role=models.UserRole.admin,
            is_active=True,
            company_name="Верес-Тариф"
        )
        
        db.add(admin_user)
        db.commit()
        print("✅ Администратор создан: admin / admin123")
        
    except Exception as e:
        print(f"❌ Ошибка создания администратора: {e}")
        db.rollback()
    finally:
        db.close()

def create_demo_users():
    """Создает демо-пользователей"""
    print("👥 Создание демо-пользователей...")
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        demo_users = [
            {
                "username": "employee1",
                "full_name": "Иван Петров",
                "email": "employee@veres-tariff.ru",
                "password": "employee123",
                "role": models.UserRole.employee,
                "company_name": "Верес-Тариф"
            },
            {
                "username": "forwarder1", 
                "full_name": "Мария Сидорова",
                "email": "forwarder@veres-tariff.ru",
                "password": "forwarder123",
                "role": models.UserRole.forwarder,
                "company_name": "Транспортная компания"
            },
            {
                "username": "client1",
                "full_name": "Алексей Козлов", 
                "email": "client@veres-tariff.ru",
                "password": "client123",
                "role": models.UserRole.client,
                "company_name": "ООО Клиент"
            }
        ]
        
        for user_data in demo_users:
            # Проверяем, есть ли уже такой пользователь
            existing = db.query(models.User).filter(models.User.username == user_data["username"]).first()
            if existing:
                print(f"✅ {user_data['username']} уже существует")
                continue
                
            user = models.User(
                username=user_data["username"],
                full_name=user_data["full_name"],
                email=user_data["email"],
                password_hash=pwd_context.hash(user_data["password"]),
                role=user_data["role"],
                is_active=True,
                company_name=user_data["company_name"]
            )
            
            db.add(user)
            print(f"✅ Создан пользователь: {user_data['username']} / {user_data['password']}")
        
        db.commit()
        print("✅ Все демо-пользователи созданы")
        
    except Exception as e:
        print(f"❌ Ошибка создания демо-пользователей: {e}")
        db.rollback()
    finally:
        db.close()

def main():
    """Основная функция инициализации"""
    print("🚀 Инициализация базы данных Верес-Тариф")
    print("=" * 50)
    
    try:
        # Создаем таблицы
        create_tables()
        
        # Создаем администратора
        create_admin_user()
        
        # Создаем демо-пользователей
        create_demo_users()
        
        print("\n🎉 Инициализация завершена успешно!")
        print("\n👤 Данные для входа:")
        print("   Администратор: admin / admin123")
        print("   Сотрудник:     employee1 / employee123") 
        print("   Экспедитор:    forwarder1 / forwarder123")
        print("   Клиент:        client1 / client123")
        
    except Exception as e:
        print(f"❌ Ошибка инициализации: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
