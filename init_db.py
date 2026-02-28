"""
Файл: init_db.py
Назначение: Минимальный пример инициализации БД и добавления тестовых записей.
Роль в проекте: учебный/проверочный скрипт для первого запуска.

Примечание:
- Скрипт отражает раннюю версию модели Product; оставлен как пример рабочей последовательности
    «создать схему -> добавить данные -> commit».
"""

from app import create_app, db
from app.models import Product, Category

app = create_app()

with app.app_context():
    # [БЛОК: создание схемы]
    db.create_all()

    # [БЛОК: подготовка тестовых сущностей]
    # Явное поэтапное добавление помогает студентам увидеть жизненный цикл ORM-объекта.
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

    # commit фиксирует транзакцию; без него изменения останутся только в памяти сессии.
    db.session.commit()
    print("Тестовые данные добавлены!")