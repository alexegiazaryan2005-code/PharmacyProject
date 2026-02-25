from app import create_app, db
from app.models import Product, Pharmacy, Stock


def migrate_data():
    """Миграция данных из старой структуры в новую сетевую"""
    app = create_app()
    with app.app_context():
        # Создаем таблицы, если их нет
        db.create_all()

        # Проверяем, есть ли уже аптеки
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

            # Переносим остатки из старой системы
            # ВАЖНО: У вас больше нет product.quantity!
            # Нужно либо создать Stock записи с quantity=0
            # либо если были данные, их нужно перенести
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