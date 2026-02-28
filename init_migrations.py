"""
Файл: init_migrations.py
Назначение: Автоматизирует базовый цикл Flask-Migrate (init/migrate/upgrade).
Роль в проекте: служебный скрипт для подготовки и применения миграций.
"""

import os
import sys
from flask import Flask
from flask_migrate import Migrate, init, migrate, upgrade

# Добавляем путь к проекту
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app, db
from app.models import *

app = create_app()


def setup_migrations():
    """
    Инициализирует репозиторий миграций (при необходимости), генерирует и применяет миграцию.

    Параметры:
        Нет.

    Возвращает:
        None.

    Исключения:
        Явно не перехватываются; ошибки shell-команд или окружения приведут к завершению скрипта.

    Почему используется os.system:
        Это быстрый способ вызвать CLI-команды.
        Альтернатива (предпочтительнее в больших проектах): API Alembic/Flask-Migrate без shell-вызовов.

    Примеры:
        >>> setup_migrations()
        # Инициализирует `migrations/` (если её нет), затем выполнит migrate и upgrade
    """
    with app.app_context():
        migrate = Migrate(app, db)

        # [БЛОК: init только при первом запуске]
        # Условие выхода: если папка `migrations` уже существует, этап init пропускается.
        # Это защищает от случайного перезаписывания структуры миграций.
        if not os.path.exists('migrations'):
            print("📁 Инициализация миграций...")
            os.system('flask db init')

        print("📝 Создание миграции...")
        os.system('flask db migrate -m "Initial migration"')

        print("🔄 Применение миграции...")
        os.system('flask db upgrade')

        print("✅ Миграции завершены!")


if __name__ == '__main__':
    setup_migrations()