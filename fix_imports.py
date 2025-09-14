#!/usr/bin/env python3
"""
Скрипт для исправления импортов в backend файлах для Docker
"""

import os
import re

def fix_imports_in_file(file_path):
    """Исправляет импорты в одном файле"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Заменяем импорты backend.* на относительные
    replacements = [
        (r'from backend\.', 'from '),
        (r'import backend\.', 'import '),
        (r'from backend import', 'import'),
    ]
    
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Исправлен: {file_path}")

def main():
    """Основная функция"""
    backend_dir = "backend"
    
    # Список файлов для исправления
    files_to_fix = [
        "main.py",
        "models.py", 
        "schemas.py",
        "database.py",
    ]
    
    # Добавляем все файлы из routers/
    routers_dir = os.path.join(backend_dir, "routers")
    if os.path.exists(routers_dir):
        for file in os.listdir(routers_dir):
            if file.endswith('.py') and file != '__init__.py':
                files_to_fix.append(os.path.join("routers", file))
    
    # Добавляем все файлы из services/
    services_dir = os.path.join(backend_dir, "services")
    if os.path.exists(services_dir):
        for file in os.listdir(services_dir):
            if file.endswith('.py') and file != '__init__.py':
                files_to_fix.append(os.path.join("services", file))
    
    print("🔧 Исправление импортов для Docker...")
    
    for file in files_to_fix:
        file_path = os.path.join(backend_dir, file)
        if os.path.exists(file_path):
            fix_imports_in_file(file_path)
        else:
            print(f"⚠️ Файл не найден: {file_path}")
    
    print("✅ Все импорты исправлены!")

if __name__ == "__main__":
    main()
