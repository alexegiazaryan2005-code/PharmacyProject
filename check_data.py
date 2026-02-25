from app import create_app, db
from app.models import Product, Recept

app = create_app()

with app.app_context():
    print("Проверка данных в базе:")
    print("\nВсе типы рецептурности:")
    for recept in Recept.query.all():
        print(f"  {recept.id}: {recept.name}")

    print("\nТовары и их рецептурность:")
    for product in Product.query.all():
        print(f"  {product.id}. {product.name}: {product.recept.name if product.recept else 'Нет данных'}")