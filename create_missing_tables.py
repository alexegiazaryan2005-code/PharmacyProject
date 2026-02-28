"""
Файл: create_missing_tables.py
Назначение: Проверяет, какие таблицы отсутствуют в БД, и создаёт их.
Роль в проекте: восстановление схемы после частичных миграций или ручных изменений.
"""

from app import create_app, db
from app.models import *
import sqlite3
import os


def create_missing_tables():
    """
    Создаёт недостающие таблицы и при необходимости добавляет стартовые типы рецептурности.

    Возвращает:
        None.

    Исключения:
        Явно не перехватываются на уровне функции; возможные ошибки БД будут проброшены.
    """
    app = create_app()

    with app.app_context():
        print(f"📁 База данных: {app.config['SQLALCHEMY_DATABASE_URI']}")

        # Получаем список существующих таблиц
        inspector = db.inspect(db.engine)
        existing_tables = inspector.get_table_names()
        print(f"📋 Существующие таблицы: {existing_tables}")

        # [БЛОК: ожидаемые таблицы]
        # Здесь указаны имена таблиц как их «видит» БД, а не имена Python-классов.
        all_models = [
            'recept',
            'category',
            'manufacturer',
            'product',
            'product_category',
            'pharmacy',
            'stock',
            'supply',
            'sale',
            'transfer'
        ]

        # Вычисляем разницу множеств (фактически в форме list comprehension).
        missing_tables = [t for t in all_models if t not in existing_tables]

        if missing_tables:
            print(f"⚠️ Отсутствуют таблицы: {missing_tables}")
            print("🔄 Создаем недостающие таблицы...")

            # create_all() безопасен для существующих таблиц: не удаляет и не переопределяет их.
            db.create_all()

            # Проверяем результат
            inspector = db.inspect(db.engine)
            new_tables = inspector.get_table_names()
            print(f"✅ Теперь есть таблицы: {new_tables}")

            # Добавляем начальные данные для recept, если таблица была создана
            if 'recept' not in existing_tables and Recept.query.count() == 0:
                print("📝 Добавляем начальные типы рецептурности...")
                recepts = [
                    Recept(name="Без рецепта", description="Безрецептурный препарат"),
                    Recept(name="Рецептурный", description="Отпускается по рецепту"),
                    Recept(name="Строгой отчетности", description="Рецептурный препарат строгого учета")
                ]
                for recept in recepts:
                    db.session.add(recept)
                db.session.commit()
                print("✅ Начальные типы рецептурности добавлены")
        else:
            print("✅ Все необходимые таблицы уже существуют!")


if __name__ == '__main__':
    create_missing_tables()