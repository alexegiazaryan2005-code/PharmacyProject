"""
Файл: update_products.py
Назначение: Массово обновляет тип рецептурности товаров по имени и категории.
Роль в проекте: data-cleanup утилита после изменения справочников.
"""

from app import create_app, db
from app.models import Product, Recept

app = create_app()

with app.app_context():
    # [БЛОК: контекст приложения Flask]
    # app_context обязателен для корректной работы ORM вне HTTP-запроса.
    # Альтернатива: использовать flask CLI-команды, где контекст создаётся автоматически.

    # [БЛОК: поиск опорных записей справочника]
    # Дальнейшая логика зависит от этих двух значений, поэтому проверяем их заранее.
    # Найдем рецептурные типы
    bez_recepta = Recept.query.filter_by(name="Без рецепта").first()
    po_receptu = Recept.query.filter_by(name="По рецепту").first()

    if not bez_recepta or not po_receptu:
        print("Ошибка: не найдены типы рецептурности")
        exit()

    # [БЛОК: обновление по паттерну названия]
    # ilike используется для регистронезависимого поиска (поведение может зависеть от СУБД).
    # Альтернатива: полнотекстовый поиск или отдельный классификатор товаров.
    # Антибиотики -> рецептурные
    products_to_update = Product.query.filter(
        Product.name.ilike('%амоксициллин%') |
        Product.name.ilike('%антибиот%')
    ).all()

    # Цикл for завершается после обхода всех найденных товаров;
    # условие выхода обеспечивается конечной длиной списка `.all()`.
    for product in products_to_update:
        product.recept_id = po_receptu.id
        print(f"Обновлен: {product.name} -> рецептурный")

    # [БЛОК: дополнительное правило по категории]
    # Это демонстрация того, как комбинировать несколько бизнес-правил в одном скрипте.
    # Альтернатива: выносить правила в отдельные функции и покрывать тестами.
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