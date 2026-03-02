"""
Файл: check_db.py
Назначение: Диагностический скрипт для быстрой проверки структуры БД.
Роль в проекте: эксплуатационная утилита (operations tool) при отладке локальной среды.

Импорты:
- app.create_app/db: доступ к конфигурации и движку SQLAlchemy.
- app.models.*: регистрирует модели в metadata перед работой с БД.
"""

import os
from app import create_app, db
from app.models import *

app = create_app()

# Создаем контекст приложения Flask для работы вне HTTP-запроса
# Нужен для доступа к БД, конфигам, url_for и current_app
with app.app_context():
    # [БЛОК: базовая информация]
    # Вывод URI и таблиц помогает быстро убедиться, что приложение подключилось к ожидаемой БД.
    print(f"📁 Путь к БД: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print(f"📊 Таблицы в БД: {db.engine.table_names()}")

    # Проверим существующие таблицы
    # Получаем инспектор БД для просмотра структуры
    inspector = db.inspect(db.engine)
    tables = inspector.get_table_names()
    print(f"\n📋 Существующие таблицы: {tables}")

    # [БЛОК: обход всех таблиц и колонок]
    # Используем inspector, потому что это переносимый путь (работает для разных СУБД),
    # в отличие от SQLite-специфичных PRAGMA.
    for table in tables:
        columns = inspector.get_columns(table)
        print(f"\nТаблица {table}:")
        for col in columns:
            print(f"  - {col['name']}: {col['type']}")