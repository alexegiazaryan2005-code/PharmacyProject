from app import create_app, db
from app.models import Product, Category, Manufacturer, Recept

app = create_app()

with app.app_context():
    # Проверяем, существует ли колонка manufacturer_id
    try:
        # Пробуем выполнить запрос с manufacturer_id
        test = Product.query.first()
        print("Колонка manufacturer_id уже существует")
    except Exception as e:
        if "no such column: product.manufacturer_id" in str(e):
            print("Добавляем колонку manufacturer_id...")

            # Создаем новую таблицу с правильной структурой
            db.drop_all()
            db.create_all()

            print("База данных успешно обновлена!")
        else:
            print(f"Другая ошибка: {e}")