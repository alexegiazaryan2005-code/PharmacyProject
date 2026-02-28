"""
Файл: update_database.py
Назначение: Исторический скрипт обновления схемы под поле manufacturer_id.
Роль в проекте: аварийная миграция при рассинхронизации старой и новой структуры Product.

Важный риск:
- Скрипт использует `drop_all()` и `create_all()`, что удаляет данные.
- Применять только в тестовой среде или при наличии резервной копии.
"""

from app import create_app, db
from app.models import Product, Category, Manufacturer, Recept

app = create_app()

with app.app_context():
    # [БЛОК: проверка совместимости схемы]
    # Пробный SELECT используется как быстрый smoke-test наличия требуемой колонки.
    # Альтернатива: inspector/PRAGMA для точной проверки структуры без выполнения ORM-запроса.
    # Проверяем, существует ли колонка manufacturer_id
    try:
        # Пробуем выполнить запрос с manufacturer_id
        test = Product.query.first()
        print("Колонка manufacturer_id уже существует")
    except Exception as e:
        if "no such column: product.manufacturer_id" in str(e):
            print("Добавляем колонку manufacturer_id...")

            # Создаем новую таблицу с правильной структурой.
            # **Почему это спорный подход**: он прост, но разрушителен для данных.
            # Предпочтительная альтернатива: миграция ALTER TABLE через Alembic.
            db.drop_all()
            db.create_all()

            print("База данных успешно обновлена!")
        else:
            print(f"Другая ошибка: {e}")