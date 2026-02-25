# init_migrations.py
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
    """Инициализация миграций"""
    with app.app_context():
        migrate = Migrate(app, db)

        # Проверяем, есть ли папка migrations
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