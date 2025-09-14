#!/usr/bin/env python3
"""
Скрипт для создания первого администратора системы
"""

import os
import sys
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from backend.database import SessionLocal, engine
from backend.models import Base, User, UserRole
from backend.services.security import get_password_hash

def create_admin():
    """Создает первого администратора системы"""
    
    # Создаем таблицы если их нет
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Проверяем, есть ли уже администраторы
        existing_admin = db.query(User).filter(User.role == UserRole.admin).first()
        if existing_admin:
            print(f"Администратор уже существует: {existing_admin.username}")
            return
        
        # Создаем первого администратора
        admin = User(
            username="admin",
            password_hash=get_password_hash("admin123"),
            role=UserRole.admin,
            full_name="Системный администратор",
            email="admin@veres-tariff.ru",
            phone="+7 (000) 000-00-00",
            company_name="Верес-Тариф",
            responsible_person="Системный администратор"
        )
        
        db.add(admin)
        db.commit()
        db.refresh(admin)
        
        print("✅ Первый администратор создан успешно!")
        print(f"Логин: admin")
        print(f"Пароль: admin123")
        print(f"Роль: {admin.role.value}")
        print(f"ID: {admin.id}")
        
    except Exception as e:
        print(f"❌ Ошибка создания администратора: {e}")
        db.rollback()
    finally:
        db.close()

def create_demo_users():
    """Создает демо-пользователей для тестирования"""
    
    db = SessionLocal()
    try:
        # Создаем демо-пользователей
        demo_users = [
            {
                "username": "employee1",
                "password": "employee123",
                "role": UserRole.employee,
                "full_name": "Иван Петров",
                "email": "employee@veres-tariff.ru",
                "phone": "+7 (111) 111-11-11",
                "company_name": "Верес-Тариф",
                "responsible_person": "Иван Петров"
            },
            {
                "username": "forwarder1",
                "password": "forwarder123",
                "role": UserRole.forwarder,
                "full_name": "Мария Сидорова",
                "email": "forwarder@veres-tariff.ru",
                "phone": "+7 (222) 222-22-22",
                "company_name": "Логистическая компания",
                "responsible_person": "Мария Сидорова"
            },
            {
                "username": "client1",
                "password": "client123",
                "role": UserRole.client,
                "full_name": "Алексей Козлов",
                "email": "client@example.ru",
                "phone": "+7 (333) 333-33-33",
                "company_name": "ООО Клиент",
                "responsible_person": "Алексей Козлов"
            }
        ]
        
        for user_data in demo_users:
            # Проверяем, существует ли пользователь
            existing_user = db.query(User).filter(User.username == user_data["username"]).first()
            if existing_user:
                print(f"Пользователь {user_data['username']} уже существует")
                continue
            
            user = User(
                username=user_data["username"],
                password_hash=get_password_hash(user_data["password"]),
                role=user_data["role"],
                full_name=user_data["full_name"],
                email=user_data["email"],
                phone=user_data["phone"],
                company_name=user_data["company_name"],
                responsible_person=user_data["responsible_person"]
            )
            
            db.add(user)
            print(f"✅ Создан пользователь: {user_data['username']} ({user_data['role'].value})")
        
        db.commit()
        print("\n🎉 Все демо-пользователи созданы успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка создания демо-пользователей: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Создание пользователей системы Верес-Тариф")
    print("=" * 50)
    
    # Создаем администратора
    create_admin()
    
    print("\n" + "=" * 50)
    
    # Создаем демо-пользователей
    create_demo_users()
    
    print("\n" + "=" * 50)
    print("📋 Список созданных пользователей:")
    print("👑 Администратор: admin / admin123")
    print("👨‍💼 Сотрудник: employee1 / employee123")
    print("📦 Экспедитор: forwarder1 / forwarder123")
    print("👤 Клиент: client1 / client123")
    print("\n💡 Рекомендуется изменить пароли после первого входа!")
