# migrations.py
from app import create_app, db
from app.models import Product, Category, Recept, Manufacturer, ProductCategory

app = create_app()

with app.app_context():
    # 1. Создаем таблицу Manufacturer
    db.create_all()

    # 2. Переносим существующих производителей из строк в таблицу Manufacturer
    products = Product.query.all()
    manufacturer_names = set()

    for product in products:
        if product.manufacturer:
            manufacturer_names.add(product.manufacturer.strip())

    # Создаем записи производителей
    manufacturer_map = {}
    for name in manufacturer_names:
        if name:
            manufacturer = Manufacturer.query.filter_by(name=name).first()
            if not manufacturer:
                manufacturer = Manufacturer(name=name)
                db.session.add(manufacturer)
                db.session.commit()
            manufacturer_map[name] = manufacturer.id

    # 3. Обновляем товары с новыми manufacturer_id
    for product in products:
        if product.manufacturer and product.manufacturer in manufacturer_map:
            product.manufacturer_id = manufacturer_map[product.manufacturer]

    # 4. Переносим старые category_id в промежуточную таблицу
    for product in products:
        if product.category_id:
            # Проверяем, не существует ли уже такая связь
            existing = ProductCategory.query.filter_by(
                product_id=product.id,
                category_id=product.category_id
            ).first()

            if not existing:
                product_category = ProductCategory(
                    product_id=product.id,
                    category_id=product.category_id
                )
                db.session.add(product_category)

    db.session.commit()
    print("Миграция завершена успешно!")