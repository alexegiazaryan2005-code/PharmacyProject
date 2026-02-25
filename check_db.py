# check_db.py
import os
from app import create_app, db
from app.models import *

app = create_app()

with app.app_context():
    print(f"📁 Путь к БД: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print(f"📊 Таблицы в БД: {db.engine.table_names()}")

    # Проверим существующие таблицы
    inspector = db.inspect(db.engine)
    tables = inspector.get_table_names()
    print(f"\n📋 Существующие таблицы: {tables}")

    # Проверим структуру таблиц
    for table in tables:
        columns = inspector.get_columns(table)
        print(f"\nТаблица {table}:")
        for col in columns:
            print(f"  - {col['name']}: {col['type']}")