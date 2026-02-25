from app import create_app, db
from app.models import Category, Product, Recept  # Добавляем импорт Recept

app = create_app()

with app.app_context():
    # Создаем таблицы
    db.create_all()
    print("Таблицы созданы!")

    # Проверяем, есть ли уже данные
    if Category.query.count() == 0:
        print("Создаем тестовые данные...")

        # Создаем категории рецептурности
        recepts_data = [
            ("Без рецепта", "Препараты, отпускаемые без рецепта врача"),
            ("По рецепту", "Рецептурные препараты"),
            ("Рецептурный строгий учет", "Препараты строгого учета, наркотические средства"),
        ]

        recepts = []
        for name, desc in recepts_data:
            recept = Recept(name=name, description=desc)
            recepts.append(recept)
            db.session.add(recept)

        db.session.commit()
        print(f"Создано {len(recepts)} типов рецептурности")

        # Создаем категории (остается без изменений)
        categories_data = [
            ("Обезболивающие", "Лекарства для снятия боли"),
            ("Антибиотики", "Антибактериальные препараты"),
            ("Витамины", "Витамины и БАДы"),
            ("Уход за кожей", "Косметические средства"),
            ("Медицинские изделия", "Бинты, пластыри и т.д.")
        ]

        categories = []
        for name, desc in categories_data:
            cat = Category(name=name, description=desc)
            categories.append(cat)
            db.session.add(cat)

        db.session.commit()
        print(f"Создано {len(categories)} категорий")

        # Создаем товары с указанием типа рецептурности
        products_data = [
            # name, price, quantity, category_id, manufacturer, barcode, recept_id
            ("Аспирин", 150.50, 100, 1, "Bayer", "123456789012", 1),
            ("Амоксициллин", 320.75, 50, 2, "Sandoz", "234567890123", 2),
            ("Витамин C", 450.00, 200, 3, "Solgar", "345678901234", 1),
            ("Крем для рук", 280.25, 150, 4, "Nivea", "456789012345", 1),
            ("Бинт стерильный", 120.00, 300, 5, "Hartmann", "567890123456", 1),
            ("Нурофен", 280.00, 80, 1, "Reckitt", "678901234567", 1),
            ("Цитрамон", 95.50, 120, 1, "Фармстандарт", "789012345678", 1),
        ]

        for name, price, quantity, cat_id, manufacturer, barcode, recept_id in products_data:
            product = Product(
                name=name,
                price=price,
                quantity=quantity,
                category_id=cat_id,
                manufacturer=manufacturer,
                barcode=barcode,
                recept_id=recept_id  # Добавляем тип рецептурности
            )
            db.session.add(product)

        db.session.commit()
        print(f"Создано {len(products_data)} товаров")

        print("Тестовые данные успешно добавлены!")
    else:
        print("В базе данных уже есть данные")

    # Выводим статистику
    print(f"\nСтатистика базы данных:")
    print(f"Типов рецептурности: {Recept.query.count()}")
    print(f"Категорий: {Category.query.count()}")
    print(f"Товаров: {Product.query.count()}")