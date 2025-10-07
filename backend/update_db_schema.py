#!/usr/bin/env python3
"""
Скрипт для обновления схемы базы данных
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Добавляем текущую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from .database import DATABASE_URL, engine

def update_database_schema():
    """Обновляет схему базы данных"""
    print("🔧 Обновление схемы базы данных...")
    
    try:
        with engine.connect() as connection:
            # Проверяем, существует ли колонка is_active
            result = connection.execute(text("""
                PRAGMA table_info(users);
            """)).fetchall()
            
            columns = [row[1] for row in result]
            
            if 'is_active' not in columns:
                print("➕ Добавление колонки 'is_active' в таблицу 'users'...")
                connection.execute(text("""
                    ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT 1;
                """))
                connection.commit()
                print("✅ Колонка 'is_active' добавлена")
            else:
                print("✅ Колонка 'is_active' уже существует")
            
            # Проверяем, существует ли колонка created_by_user_id в tariffs
            result = connection.execute(text("""
                PRAGMA table_info(tariffs);
            """)).fetchall()
            
            columns = [row[1] for row in result]
            
            if 'created_by_user_id' not in columns:
                print("➕ Добавление колонки 'created_by_user_id' в таблицу 'tariffs'...")
                connection.execute(text("""
                    ALTER TABLE tariffs ADD COLUMN created_by_user_id INTEGER;
                """))
                connection.commit()
                print("✅ Колонка 'created_by_user_id' добавлена в 'tariffs'")
            else:
                print("✅ Колонка 'created_by_user_id' уже существует в 'tariffs'")
            
            # Проверяем, существует ли колонка created_by_user_id в tariff_archive
            result = connection.execute(text("""
                PRAGMA table_info(tariff_archive);
            """)).fetchall()
            
            columns = [row[1] for row in result]
            
            if 'created_by_user_id' not in columns:
                print("➕ Добавление колонки 'created_by_user_id' в таблицу 'tariff_archive'...")
                connection.execute(text("""
                    ALTER TABLE tariff_archive ADD COLUMN created_by_user_id INTEGER;
                """))
                connection.commit()
                print("✅ Колонка 'created_by_user_id' добавлена в 'tariff_archive'")
            else:
                print("✅ Колонка 'created_by_user_id' уже существует в 'tariff_archive'")
                
        print("✅ Схема базы данных обновлена успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка обновления схемы: {e}")
        return False
    
    return True

def main():
    """Основная функция"""
    print("🚀 Обновление схемы базы данных Верес-Тариф")
    print("=" * 50)
    
    if update_database_schema():
        print("\n🎉 Обновление завершено успешно!")
        print("Теперь можно запускать приложение.")
    else:
        print("\n❌ Ошибка обновления схемы!")
        sys.exit(1)

if __name__ == "__main__":
    main()
