import sqlite3
import os
from app import create_app
from app.extensions import db
from app.models import Product

"""
Файл: update_db.py
Назначение: Добавляет колонку min_stock в таблицу products и заполняет её дефолтами.
Роль в проекте: точечная ручная миграция для SQLite.
"""


def update_database():
    """
    Выполняет безопасную (идемпотентную) проверку/добавление поля `min_stock`.

    Параметры:
        Нет.

    Возвращает:
        None.

    Исключения:
        Явно не перехватываются; ошибки файловой системы и SQL могут прервать выполнение.

    Примеры:
        update_database()
        # Проверит структуру и обновит БД при необходимости
    """

    # Путь к базе данных
    db_path = 'instance/pharmacy.db'

    # [БЛОК: проверка существования БД]
    if not os.path.exists(db_path):
        print(f"База данных не найдена по пути: {db_path}")
        print("Создаем новую базу данных...")
        app = create_app()
        with app.app_context():
            db.create_all()
        print("База данных создана")

    # Подключаемся к БД
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # [БЛОК: introspection структуры]
    # PRAGMA table_info удобен для SQLite; для других СУБД аналог будет отличаться.
    cursor.execute("PRAGMA table_info(products)")
    columns = cursor.fetchall()
    column_names = [column[1] for column in columns]

    # [БЛОК: ветвление по наличию колонки]
    # Условие выхода: если `min_stock` уже есть, ALTER TABLE не выполняется.
    if 'min_stock' not in column_names:
        print("Добавление колонки min_stock в таблицу products...")
        cursor.execute("ALTER TABLE products ADD COLUMN min_stock INTEGER DEFAULT 5")
        conn.commit()
        print("Колонка min_stock успешно добавлена!")

        # [БЛОК: backfill существующих строк]
        # После добавления колонки обновляем уже существующие записи единым UPDATE.
        app = create_app()
        with app.app_context():
            Product.query.update({Product.min_stock: 5})
            db.session.commit()
            print("Значения по умолчанию (5) установлены для всех товаров")
    else:
        print("Колонка min_stock уже существует в таблице products")

    # Проверяем структуру таблицы
    cursor.execute("PRAGMA table_info(products)")
    print("\nТекущая структура таблицы products:")
    for col in cursor.fetchall():
        print(f"  - {col[1]} ({col[2]})")

    conn.close()
    print("\nОбновление базы данных завершено")


if __name__ == '__main__':
    update_database()