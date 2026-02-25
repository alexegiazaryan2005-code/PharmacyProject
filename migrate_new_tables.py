from app import create_app, db
import sqlite3
import os


def migrate_tables():
    """Создание новых таблиц в базе данных"""

    # Сначала создаем приложение для импорта моделей
    app = create_app()

    with app.app_context():
        print("🔄 Начинаем создание новых таблиц...")

        # Получаем путь к базе данных из конфигурации
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        print(f"📁 Путь к БД: {db_path}")

        # Подключаемся напрямую к SQLite
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # SQL для создания новых таблиц (с проверкой существования)
        create_tables = [
            """
            CREATE TABLE IF NOT EXISTS supply (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                supply_number VARCHAR(50) NOT NULL UNIQUE,
                product_id INTEGER NOT NULL,
                pharmacy_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                purchase_price FLOAT NOT NULL,
                selling_price FLOAT NOT NULL,
                markup_percent FLOAT NOT NULL,
                discount_percent FLOAT DEFAULT 0,
                total_amount FLOAT NOT NULL,
                supply_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                invoice_file VARCHAR(200),
                notes TEXT,
                FOREIGN KEY (product_id) REFERENCES product (id),
                FOREIGN KEY (pharmacy_id) REFERENCES pharmacy (id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS sale (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_number VARCHAR(50) NOT NULL UNIQUE,
                product_id INTEGER NOT NULL,
                pharmacy_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                price_per_unit FLOAT NOT NULL,
                customer_discount FLOAT DEFAULT 0,
                promotion_discount FLOAT DEFAULT 0,
                total_amount FLOAT NOT NULL,
                sale_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_fifo_applied BOOLEAN DEFAULT 1,
                FOREIGN KEY (product_id) REFERENCES product (id),
                FOREIGN KEY (pharmacy_id) REFERENCES pharmacy (id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS transfer (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transfer_number VARCHAR(50) NOT NULL UNIQUE,
                product_id INTEGER NOT NULL,
                from_pharmacy_id INTEGER NOT NULL,
                to_pharmacy_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                transfer_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR(20) DEFAULT 'pending',
                notes TEXT,
                completed_date DATETIME,
                FOREIGN KEY (product_id) REFERENCES product (id),
                FOREIGN KEY (from_pharmacy_id) REFERENCES pharmacy (id),
                FOREIGN KEY (to_pharmacy_id) REFERENCES pharmacy (id)
            )
            """
        ]

        # Создаем таблицы
        for sql in create_tables:
            try:
                cursor.execute(sql)
                print(f"✅ Таблица создана: {sql.split()[5]}")  # Выводим имя таблицы
            except Exception as e:
                print(f"❌ Ошибка: {e}")

        # Создаем индексы
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_supply_product ON supply(product_id);",
            "CREATE INDEX IF NOT EXISTS idx_supply_pharmacy ON supply(pharmacy_id);",
            "CREATE INDEX IF NOT EXISTS idx_sale_product ON sale(product_id);",
            "CREATE INDEX IF NOT EXISTS idx_sale_pharmacy ON sale(pharmacy_id);",
            "CREATE INDEX IF NOT EXISTS idx_transfer_product ON transfer(product_id);",
            "CREATE INDEX IF NOT EXISTS idx_transfer_from ON transfer(from_pharmacy_id);",
            "CREATE INDEX IF NOT EXISTS idx_transfer_to ON transfer(to_pharmacy_id);"
        ]

        for sql in indexes:
            try:
                cursor.execute(sql)
                print(f"✅ Индекс создан")
            except Exception as e:
                print(f"❌ Ошибка создания индекса: {e}")

        # Сохраняем изменения
        conn.commit()

        # Проверяем созданные таблицы
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("\n📋 Все таблицы в базе данных:")
        for table in tables:
            print(f"   - {table[0]}")

        conn.close()
        print("\n✅ Миграция успешно завершена!")


if __name__ == '__main__':
    migrate_tables()