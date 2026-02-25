from app import create_app, db
from app.models import Product, Recept

app = create_app()

with app.app_context():
    # Найдем рецептурные типы
    bez_recepta = Recept.query.filter_by(name="Без рецепта").first()
    po_receptu = Recept.query.filter_by(name="По рецепту").first()

    if not bez_recepta or not po_receptu:
        print("Ошибка: не найдены типы рецептурности")
        exit()

    # Обновляем товары по правилам:
    # Антибиотики -> рецептурные
    products_to_update = Product.query.filter(
        Product.name.ilike('%амоксициллин%') |
        Product.name.ilike('%антибиот%')
    ).all()

    for product in products_to_update:
        product.recept_id = po_receptu.id
        print(f"Обновлен: {product.name} -> рецептурный")

    # Также можно обновить по категории "Антибиотики"
    from app.models import Category

    antibiotiki_category = Category.query.filter_by(name="Антибиотики").first()
    if antibiotiki_category:
        antibiotiki_products = Product.query.filter_by(category_id=antibiotiki_category.id).all()
        for product in antibiotiki_products:
            if product.recept_id == bez_recepta.id:
                product.recept_id = po_receptu.id
                print(f"Обновлен по категории: {product.name} -> рецептурный")

    db.session.commit()
    print("Обновление завершено!")