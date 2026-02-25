# В скрипте init_db.py или отдельно
from app import create_app, db
from app.models import Product, Category

app = create_app()

with app.app_context():
    # Создайте таблицы
    db.create_all()

    # Добавьте тестовую категорию
    category1 = Category(name='Лекарства', description='Лекарственные препараты')
    db.session.add(category1)

    # Добавьте тестовый продукт
    product1 = Product(
        name='Аспирин',
        description='Обезболивающее средство',
        price=150.0,
        quantity=100,
        barcode='123456789',
        manufacturer='Bayer',
        requires_prescription=False,
        category_id=1
    )
    db.session.add(product1)

    db.session.commit()
    print("Тестовые данные добавлены!")