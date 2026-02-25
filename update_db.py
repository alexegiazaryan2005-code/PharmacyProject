import sqlite3
import os
from app import create_app
from app.extensions import db
from app.models import Product


def update_database():
    """Добавление колонки min_stock в таблицу products"""

    # Путь к базе данных
    db_path = 'instance/pharmacy.db'

    # Проверяем существование файла БД
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

    # Проверяем наличие колонки min_stock
    cursor.execute("PRAGMA table_info(products)")
    columns = cursor.fetchall()
    column_names = [column[1] for column in columns]

    if 'min_stock' not in column_names:
        print("Добавление колонки min_stock в таблицу products...")
        cursor.execute("ALTER TABLE products ADD COLUMN min_stock INTEGER DEFAULT 5")
        conn.commit()
        print("Колонка min_stock успешно добавлена!")

        # Обновляем существующие записи
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