#!/usr/bin/env python3
"""
Скрипт для обновления базы данных - добавление полей created_by_user_id
"""

import os
import sys
import sqlite3
from pathlib import Path

# Добавляем путь к модулям backend
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def update_database():
    """Обновляет базу данных, добавляя новые поля"""
    
    # Путь к базе данных
    db_path = Path(__file__).parent.parent / "veres.db"
    
    if not db_path.exists():
        print(f"База данных {db_path} не найдена!")
        return False
    
    try:
        # Подключаемся к базе данных
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        print("Обновление базы данных...")
        
        # Проверяем, существуют ли уже поля
        cursor.execute("PRAGMA table_info(tariffs)")
        tariffs_columns = [column[1] for column in cursor.fetchall()]
        
        cursor.execute("PRAGMA table_info(tariff_archive)")
        archive_columns = [column[1] for column in cursor.fetchall()]
        
        # Добавляем поле created_by_user_id в таблицу tariffs
        if 'created_by_user_id' not in tariffs_columns:
            print("Добавление поля created_by_user_id в таблицу tariffs...")
            cursor.execute("ALTER TABLE tariffs ADD COLUMN created_by_user_id INTEGER")
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_tariffs_created_by_user_id ON tariffs(created_by_user_id)")
            print("✓ Поле created_by_user_id добавлено в таблицу tariffs")
        else:
            print("✓ Поле created_by_user_id уже существует в таблице tariffs")
        
        # Добавляем поле created_by_user_id в таблицу tariff_archive
        if 'created_by_user_id' not in archive_columns:
            print("Добавление поля created_by_user_id в таблицу tariff_archive...")
            cursor.execute("ALTER TABLE tariff_archive ADD COLUMN created_by_user_id INTEGER")
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_tariff_archive_created_by_user_id ON tariff_archive(created_by_user_id)")
            print("✓ Поле created_by_user_id добавлено в таблицу tariff_archive")
        else:
            print("✓ Поле created_by_user_id уже существует в таблице tariff_archive")
        
        # Сохраняем изменения
        conn.commit()
        print("✓ База данных успешно обновлена!")
        
        return True
        
    except Exception as e:
        print(f"Ошибка при обновлении базы данных: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    success = update_database()
    if success:
        print("\n🎉 Обновление завершено успешно!")
    else:
        print("\n❌ Обновление завершилось с ошибками!")
        sys.exit(1)
