"""
Файл: migrate_to_network.py
Назначение: Мигрирует данные к сетевой модели аптек с отдельной таблицей остатков Stock.
Роль в проекте: переходный скрипт при изменении доменной модели хранения количества.
"""

from app import create_app, db
from app.models import Product, Pharmacy, Stock


def migrate_data():
    """
    Переносит данные из старой структуры в новую, где остатки хранятся отдельно по аптекам.

    Параметры:
        Нет.

    Возвращает:
        None.

    Исключения:
        Явно не перехватываются; ошибки БД будут проброшены вызывающей стороне.

    Примеры:
        migrate_data()
        # Создаст базовую аптеку и стартовые записи Stock при первом запуске
    """
    app = create_app()
    with app.app_context():
        # Создаем таблицы, если их нет
        db.create_all()

        # [БЛОК: защита от повторной миграции]
        # Если аптеки уже существуют, считаем, что базовый перенос выполнен,
        # и выходим без изменений — это делает скрипт идемпотентным по смыслу.
        if Pharmacy.query.count() == 0:
            # Создаем основную аптеку
            main_pharmacy = Pharmacy(
                name="Главная аптека",
                address="г. Москва, ул. Ленина, д. 1",
                phone="+7 (495) 123-45-67",
                working_hours="09:00 - 21:00",
                is_active=True
            )
            db.session.add(main_pharmacy)
            db.session.flush()

            # [БЛОК: создание стартовых записей Stock]
            # В данной версии quantity инициализируется нулём, потому что историческое поле quantity у товара удалено.
            # Альтернатива: загрузить реальные остатки из архивной таблицы/CSV, если она доступна.
            # ВАЖНО: У вас больше нет product.quantity!
            # Нужно либо создать Stock записи с quantity=0
            # либо если были данные, их нужно перенести
            # Цикл for завершится естественно после обхода всех товаров (условие выхода — конец итератора Query).
            for product in Product.query.all():
                stock = Stock(
                    pharmacy_id=main_pharmacy.id,
                    product_id=product.id,
                    quantity=0,  # Установите 0, т.к. поле quantity удалено
                    min_quantity=5,
                    shelf_location="A1"
                )
                db.session.add(stock)

            db.session.commit()
            print(f"Миграция завершена. Создана аптека: {main_pharmacy.name}")
        else:
            print("Аптеки уже существуют. Миграция не требуется.")


if __name__ == "__main__":
    migrate_data()