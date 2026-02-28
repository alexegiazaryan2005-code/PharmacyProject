"""
Файл: app/routes.py
Назначение: HTTP-маршруты Flask для интерфейса и API аптечной системы.
Роль в архитектуре: presentation/controller layer — принимает запросы, валидирует вход,
вызывает операции через ORM-модели и возвращает HTML/JSON-ответ.

Импорты:
- flask.*: роутинг, шаблоны, редиректы, flash-сообщения, JSON-ответы.
- sqlalchemy.*: агрегирующие функции и SQL-условия.
- app.extensions.db: сессия и SQL-функции ORM.
- app.models.*: доменные сущности (товары, аптеки, остатки, продажи и т.д.).
- random: генерация простых служебных номеров операций.

Связи:
- Шаблоны из app/templates/*.html.
- Модели из app/models.py.
- Регистрируется в app/__init__.py как Blueprint `main`.

Почему выбран Blueprint:
- Позволяет держать маршруты в модуле, а не смешивать их с кодом сборки приложения.
- Альтернатива: class-based views или REST-фреймворк (например, Flask-RESTX),
  предпочтительны при росте API и необходимости автодокументации.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from sqlalchemy import and_, func
from sqlalchemy.exc import IntegrityError
from app.extensions import db
from app.models import Product, Category, Recept, Manufacturer, Pharmacy, Stock, Supply, Sale, Transfer  # Stock должен быть здесь
import random
# Blueprint создается ТОЛЬКО ЗДЕСЬ
main = Blueprint('main', __name__)

# Все маршруты идут после этого...
# ... (весь остальной код маршрутов)

@main.route('/')
def index():
    """
    Отрисовывает главную страницу с агрегированной статистикой.

    Параметры:
        Нет.

    Возвращает:
        Response: HTML-страница `index.html`.

    Исключения:
        Явно не обрабатываются; ошибки БД могут быть проброшены Flask.

    Примеры:
        GET /
    """
    products_count = Product.query.count()
    categories_count = Category.query.count()
    pharmacies_count = Pharmacy.query.count()

    # Общее количество товаров на всех аптеках
    total_stock_quantity = db.session.query(db.func.sum(Stock.quantity)).scalar() or 0

    # [БЛОК: поиск аптек с критическим остатком]
    # Выбран явный цикл для наглядности бизнес-логики студентам.
    # Альтернатива: один SQL-запрос с JOIN/GROUP BY — быстрее на больших данных,
    # но сложнее для первичного изучения ORM.
    low_stock_pharmacies = []
    for pharmacy in Pharmacy.query.filter_by(is_active=True).all():
        low_stock_count = Stock.query.filter(
            Stock.pharmacy_id == pharmacy.id,
            Stock.quantity < Stock.min_quantity
        ).count()
        if low_stock_count > 0:
            low_stock_pharmacies.append({
                'pharmacy': pharmacy,
                'count': low_stock_count
            })

    return render_template('index.html',
                           products_count=products_count,
                           categories_count=categories_count,
                           pharmacies_count=pharmacies_count,
                           total_stock_quantity=total_stock_quantity,
                           low_stock_pharmacies=low_stock_pharmacies)


@main.route('/products')
def products():
    """
    Возвращает страницу списка товаров с поддержкой фильтрации.

    Параметры:
        category_id (int, optional): ID категории, берётся из query string.
        manufacturer_id (int, optional): ID производителя.
        recept_id (int, optional): ID типа рецептурности.
        pharmacy_id (int, optional): ID аптеки (в текущей версии не используется в фильтре).
        low_stock (bool, optional): флаг низкого остатка (в текущей версии не используется).

    Возвращает:
        Response: HTML `products.html`.

    Примеры:
        GET /products
        GET /products?category_id=3&manufacturer_id=2
    """
    # Получаем параметры фильтрации из запроса
    category_id = request.args.get('category_id', type=int)
    manufacturer_id = request.args.get('manufacturer_id', type=int)
    recept_id = request.args.get('recept_id', type=int)
    pharmacy_id = request.args.get('pharmacy_id', type=int)
    low_stock = request.args.get('low_stock', type=bool)

    # [БЛОК: сборка запроса по шагам]
    # Подход с поэтапным query = query.filter(...) удобен, когда фильтры опциональны.
    # Альтернатива: заранее собрать список условий и передать их в filter(*conditions).
    query = Product.query

    # Применяем фильтры
    if category_id:
        query = query.filter(Product.categories.any(id=category_id))
    if manufacturer_id:
        query = query.filter_by(manufacturer_id=manufacturer_id)
    if recept_id:
        query = query.filter_by(recept_id=recept_id)

    # Получаем отфильтрованный список товаров
    products_list = query.all()

    # Данные для фильтров
    categories = Category.query.all()
    recepts = Recept.query.all()
    manufacturers = Manufacturer.query.all()
    pharmacies = Pharmacy.query.filter_by(is_active=True).all()

    return render_template(
        'products.html',
        products=products_list,
        categories=categories,
        recepts=recepts,
        manufacturers=manufacturers,
        pharmacies=pharmacies
    )
@main.route('/categories')
def categories():
    """
    Возвращает страницу со списком категорий товаров.

    Параметры:
        Нет.

    Возвращает:
        Response: HTML `categories.html`.

    Исключения:
        Явно не перехватываются; ошибки БД, если возникнут, будут обработаны Flask.

    Примеры:
        GET /categories
    """
    categories_list = Category.query.all()
    return render_template('categories.html', categories=categories_list)


@main.route('/api/products')
def api_products():
    """
    Возвращает JSON-список товаров с агрегированным количеством и категориями.

    Возвращает:
        Response(JSON): массив объектов товаров.

    Почему JSON вручную:
        Явное формирование словаря помогает контролировать контракт API.
        Альтернатива: схемы сериализации (Marshmallow/Pydantic) — лучше для крупных API.
    """
    products_list = Product.query.all()

    result = []
    for product in products_list:
        # [БЛОК: подсчёт остатка по товару]
        # sum(...).scalar() может вернуть None для пустого набора, поэтому `or 0`.
        total_quantity = db.session.query(db.func.sum(Stock.quantity)) \
                             .filter(Stock.product_id == product.id).scalar() or 0

        # Получаем названия категорий
        categories = [c.name for c in product.categories]

        result.append({
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'total_quantity': total_quantity,
            'categories': categories,
            'manufacturer': product.product_manufacturer.name if product.product_manufacturer else None
        })

    return jsonify(result)


@main.route('/api/manufacturers', methods=['GET', 'POST'])
def api_manufacturers():
    """
    Возвращает JSON-список производителей.

    Параметры:
        HTTP method: GET/POST (в текущей версии фактически реализована логика GET).

    Возвращает:
        Response(JSON): массив производителей с полями id/name/country/description.
    """

    # В GET запросе должно быть:
    manufacturers = Manufacturer.query.all()
    result = [{
        'id': m.id,
        'name': m.name,
        'country': m.country,
        'description': m.description
    } for m in manufacturers]

    return jsonify(result)


@main.route('/api/manufacturers/search')
def search_manufacturers():
    """
    Выполняет поиск производителей по подстроке в названии.

    Параметры:
        q (str, optional): поисковая строка из query string.

    Возвращает:
        Response(JSON): массив объектов Select2-формата (`id`, `text`).

    Примеры:
        GET /api/manufacturers/search?q=phar
    """
    search_term = request.args.get('q', '')

    if not search_term or len(search_term) < 2:
        return jsonify([])

    manufacturers = Manufacturer.query.filter(
        Manufacturer.name.ilike(f'%{search_term}%')
    ).limit(10).all()

    result = [{'id': m.id, 'text': m.name} for m in manufacturers]
    return jsonify(result)


@main.route('/add_product', methods=['GET', 'POST'])
def add_product():
    """
    Обрабатывает создание нового товара и стартовых остатков по аптекам.

    Параметры (POST form):
        name (str, required): название товара.
        price (float, required): цена.
        category_ids (list[int], optional): категории товара.
        manufacturer_id (int, optional): производитель.
        recept_id (int, required): тип рецептурности.
        barcode (str, optional): штрихкод.
        stock_<pharmacy_id> (int, optional): начальный остаток для каждой аптеки.

    Возвращает:
        Response: редирект на список товаров при успехе или обратно на форму при ошибке.

    Исключения:
        Любые исключения БД/преобразования перехватываются в общем except c rollback.

    Примеры:
        GET /add_product
        POST /add_product
    """
    if request.method == 'POST':
        name = request.form.get('name')
        price = float(request.form.get('price'))
        category_ids = request.form.getlist('category_ids')
        category_ids = [int(cid) for cid in category_ids if cid]
        manufacturer_id = request.form.get('manufacturer_id')
        manufacturer_id = int(manufacturer_id) if manufacturer_id else None
        recept_id = int(request.form.get('recept_id'))
        barcode = request.form.get('barcode')

        # [БЛОК: извлечение динамических полей stock_*]
        # Выбран разбор request.form.items(), так как число аптек заранее неизвестно.
        # Альтернатива: JSON-структура в скрытом поле, но она сложнее для простых HTML-форм.
        pharmacy_stocks = {}
        for key, value in request.form.items():
            if key.startswith('stock_'):
                pharmacy_id = int(key.replace('stock_', ''))
                quantity = int(value) if value else 0
                pharmacy_stocks[pharmacy_id] = quantity

        try:
            # Создаем новый товар
            new_product = Product(
                name=name,
                price=price,
                manufacturer_id=manufacturer_id,
                recept_id=recept_id,
                barcode=barcode
            )

            # [БЛОК: привязка many-to-many категорий]
            # В цикле проверяем существование категории, чтобы избежать ошибки внешнего ключа.
            for cat_id in category_ids:
                category = Category.query.get(cat_id)
                if category:
                    new_product.categories.append(category)

            # Сохраняем товар сначала (чтобы получить ID)
            db.session.add(new_product)
            db.session.flush()

            # [БЛОК: upsert-логика остатков]
            # Почему такой подход: избегаем дублей благодаря проверке + уникальному ограничению в модели Stock.
            # Альтернатива: SQL UPSERT (INSERT ... ON CONFLICT), обычно быстрее, но менее переносим между СУБД.
            for pharmacy_id, quantity in pharmacy_stocks.items():
                existing_stock = Stock.query.filter_by(
                    pharmacy_id=pharmacy_id,
                    product_id=new_product.id
                ).first()

                if existing_stock:
                    # Если запись существует - обновляем количество
                    existing_stock.quantity += quantity
                else:
                    # Если записи нет - создаем новую
                    stock = Stock(
                        pharmacy_id=pharmacy_id,
                        product_id=new_product.id,
                        quantity=quantity,
                        min_quantity=5
                    )
                    db.session.add(stock)

            db.session.commit()
            flash('Товар успешно добавлен!', 'success')
            return redirect(url_for('main.products'))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Ошибка при добавлении товара: {str(e)}')
            flash(f'Ошибка при сохранении товара: {str(e)}', 'error')
            return redirect(url_for('main.add_product'))

    # GET запрос
    categories_list = Category.query.all()
    recepts_list = Recept.query.all()
    manufacturers_list = Manufacturer.query.all()
    pharmacies_list = Pharmacy.query.filter_by(is_active=True).all()

    return render_template('add_product.html',
                           categories=categories_list,
                           recepts=recepts_list,
                           manufacturers=manufacturers_list,
                           pharmacies=pharmacies_list)

@main.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    """
    Заготовка маршрута редактирования товара.

    Параметры:
        product_id (int, required): ID товара из URL.

    Возвращает:
        Response: временный редирект на список товаров.
    """
    product = Product.query.get_or_404(product_id)

    if request.method == 'POST':
        # ... существующий код POST ...
        pass

    # Временно перенаправляем на список товаров, если шаблон не создан
    flash('Функция редактирования временно недоступна', 'warning')
    return redirect(url_for('main.products'))
@main.route('/add_category', methods=['GET', 'POST'])
def add_category():
    """
    Создаёт новую категорию товара.

    Параметры (POST form):
        name (str, required): название категории.
        description (str, optional): описание.

    Возвращает:
        Response: редирект на список категорий или форму.

    Исключения:
        IntegrityError: при нарушении ограничений целостности (например, дубликат).
    """
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')

        if not name:
            flash('Название категории обязательно для заполнения!', 'error')
            return redirect(url_for('main.add_category'))

        # [БЛОК: защита от дубликатов на уровне приложения]
        # Это дружелюбнее, чем полагаться только на SQL-ошибку при commit.
        existing_category = Category.query.filter_by(name=name).first()
        if existing_category:
            flash('Категория с таким названием уже существует!', 'error')
            return redirect(url_for('main.categories'))

        try:
            new_category = Category(name=name, description=description)
            db.session.add(new_category)
            db.session.commit()
            flash('Категория успешно добавлена!', 'success')
            return redirect(url_for('main.categories'))

        except IntegrityError:
            db.session.rollback()
            flash('Произошла ошибка при добавлении категории. Возможно, такая категория уже существует.', 'error')
            return redirect(url_for('main.add_category'))

    return render_template('add_category.html')


@main.route('/pharmacies')
def pharmacies():
    """
    Показывает список аптек и число позиций с низким остатком в каждой аптеке.

    Возвращает:
        Response: HTML `pharmacies.html`.

    Почему отдельный агрегирующий запрос:
        Позволяет избежать N+1 подсчётов в шаблоне.
    """
    pharmacies_list = Pharmacy.query.order_by(Pharmacy.name).all()

    # [БЛОК: групповой подсчёт low stock]
    # Используем GROUP BY для подсчёта по каждой аптеке за один запрос.
    # Альтернатива: отдельный count() в цикле по аптекам (проще, но медленнее при росте данных).
    from sqlalchemy import func
    low_stock_counts = dict(
        db.session.query(
            Stock.pharmacy_id,
            func.count(Stock.id)
        ).filter(
            Stock.quantity < Stock.min_quantity
        ).group_by(Stock.pharmacy_id).all()
    )

    return render_template('pharmacies.html',
                           pharmacies=pharmacies_list,
                           low_stock_counts=low_stock_counts)

@main.route('/add_pharmacy', methods=['GET', 'POST'])
def add_pharmacy():
    """
    Создаёт новую аптеку сети с базовой валидацией формы.

    Параметры (POST form):
        name (str, required), address/phone/email/working_hours (str, optional).

    Возвращает:
        Response: редирект на список аптек при успехе, иначе обратно к форме.

    Исключения:
        IntegrityError: дубликат уникального названия.
    """
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        address = request.form.get('address', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        working_hours = request.form.get('working_hours', '').strip()

        # [БЛОК: минимальная валидация входа]
        # В текущем проекте применена простая ручная валидация.
        # Альтернатива: WTForms/Flask-WTF для декларативной и переиспользуемой валидации.
        if not name:
            flash('Название аптеки обязательно!', 'error')
            return redirect(url_for('main.add_pharmacy'))

        # Простая валидация email (если указан)
        if email and '@' not in email:
            flash('Пожалуйста, укажите корректный email адрес!', 'error')
            return redirect(url_for('main.add_pharmacy'))

        # Проверка на дубликаты
        existing = Pharmacy.query.filter_by(name=name).first()
        if existing:
            flash(f'Аптека с названием "{name}" уже существует!', 'error')
            return redirect(url_for('main.pharmacies'))

        try:
            new_pharmacy = Pharmacy(
                name=name,
                address=address or None,
                phone=phone or None,
                email=email or None,
                working_hours=working_hours or None,
                is_active=True
            )

            db.session.add(new_pharmacy)
            db.session.commit()

            flash(f'✅ Аптека "{name}" успешно добавлена!', 'success')
            return redirect(url_for('main.pharmacies'))

        except IntegrityError as e:
            db.session.rollback()
            if 'UNIQUE constraint failed' in str(e):
                flash(f'Аптека с названием "{name}" уже существует!', 'error')
            else:
                flash('Ошибка целостности данных при добавлении аптеки.', 'error')
            current_app.logger.error(f'IntegrityError adding pharmacy: {str(e)}')
            return redirect(url_for('main.add_pharmacy'))

        except Exception as e:
            db.session.rollback()
            flash('Произошла непредвиденная ошибка.', 'error')
            current_app.logger.error(f'Unexpected error adding pharmacy: {str(e)}')
            return redirect(url_for('main.add_pharmacy'))

    # GET запрос - отображаем форму
    return render_template('add_pharmacy.html')

@main.route('/edit_pharmacy/<int:pharmacy_id>', methods=['GET', 'POST'])
def edit_pharmacy(pharmacy_id):
    """
    Редактирует существующую аптеку.

    Параметры:
        pharmacy_id (int, required): ID аптеки из URL.

    Возвращает:
        Response: форма редактирования (GET) или редирект (POST).
    """
    pharmacy = Pharmacy.query.get_or_404(pharmacy_id)

    if request.method == 'POST':
        name = request.form.get('name', '').strip()

        if not name:
            flash('Название аптеки обязательно для заполнения!', 'error')
            return redirect(url_for('main.edit_pharmacy', pharmacy_id=pharmacy_id))

        pharmacy.name = name
        pharmacy.address = request.form.get('address', '').strip() or None
        pharmacy.phone = request.form.get('phone', '').strip() or None
        pharmacy.email = request.form.get('email', '').strip() or None
        pharmacy.working_hours = request.form.get('working_hours', '').strip() or None
        pharmacy.is_active = 'is_active' in request.form

        try:
            db.session.commit()
            flash(f'✅ Данные аптеки "{pharmacy.name}" обновлены!', 'success')
            return redirect(url_for('main.pharmacies'))
        except IntegrityError:
            db.session.rollback()
            flash('❌ Аптека с таким названием уже существует!', 'error')
            return redirect(url_for('main.edit_pharmacy', pharmacy_id=pharmacy_id))

    return render_template('edit_pharmacy.html', pharmacy=pharmacy)


@main.route('/pharmacy/<int:pharmacy_id>/low-stock')
def pharmacy_low_stock(pharmacy_id):
    """
    Показывает товары с остатком ниже минимального для конкретной аптеки.

    Параметры:
        pharmacy_id (int, required): ID аптеки.

    Возвращает:
        Response: HTML `pharmacy_low_stock.html`.
    """
    pharmacy = Pharmacy.query.get_or_404(pharmacy_id)

    # Получаем товары, где количество меньше минимального
    low_stock_items = Stock.query.filter(
        Stock.pharmacy_id == pharmacy_id,
        Stock.quantity < Stock.min_quantity
    ).all()

    # [БЛОК: enrichment данных для шаблона]
    # Формируем структуру, где сразу есть товар и величина дефицита (shortage).
    items_with_products = []
    for stock in low_stock_items:
        product = Product.query.get(stock.product_id)
        if product:
            items_with_products.append({
                'stock': stock,
                'product': product,
                'shortage': stock.min_quantity - stock.quantity
            })

    return render_template('pharmacy_low_stock.html',
                           pharmacy=pharmacy,
                           low_stock_items=items_with_products)

@main.route('/supply', methods=['GET', 'POST'])
def supply():
    """
    Оформляет поступление товара в аптеку и увеличивает остаток на складе.

    Параметры (POST form):
        supply_number, product_id, pharmacy_id, quantity, purchase_price,
        markup_percent, supplier_discount, selling_price, total_amount, notes.

    Возвращает:
        Response: форма (GET) или редирект после обработки (POST).

    Исключения:
        Общий except перехватывает ошибки преобразования и БД.
    """
    if request.method == 'POST':
        supply_number = request.form.get('supply_number')
        product_id = int(request.form.get('product_id'))
        pharmacy_id = int(request.form.get('pharmacy_id'))
        quantity = int(request.form.get('quantity'))
        purchase_price = float(request.form.get('purchase_price'))
        markup_percent = float(request.form.get('markup_percent'))
        supplier_discount = float(request.form.get('supplier_discount', 0))
        selling_price = float(request.form.get('selling_price'))
        total_amount = float(request.form.get('total_amount'))
        notes = request.form.get('notes')

        # [БЛОК: обработка файла накладной]
        # Текущая реализация минимальная: сохраняет по вычисленному пути.
        # Альтернатива (предпочтительна): `werkzeug.utils.secure_filename` + отдельная папка uploads.
        invoice_file = None
        if 'invoice_file' in request.files:
            file = request.files['invoice_file']
            if file.filename:
                # Здесь должна быть логика сохранения файла
                invoice_file = f"uploads/{supply_number}_{file.filename}"
                file.save(invoice_file)

        try:
            # Создаем запись о поступлении
            new_supply = Supply(
                supply_number=supply_number,
                product_id=product_id,
                pharmacy_id=pharmacy_id,
                quantity=quantity,
                purchase_price=purchase_price,
                selling_price=selling_price,
                markup_percent=markup_percent,
                discount_percent=supplier_discount,
                total_amount=total_amount,
                invoice_file=invoice_file,
                notes=notes
            )
            db.session.add(new_supply)

            # [БЛОК: обновление остатка (increase)]
            # Если запись остатка есть — увеличиваем quantity.
            # Если нет — создаём новую запись (инициализация товарного остатка в аптеке).
            stock = Stock.query.filter_by(
                pharmacy_id=pharmacy_id,
                product_id=product_id
            ).first()

            if stock:
                stock.quantity += quantity
            else:
                new_stock = Stock(
                    pharmacy_id=pharmacy_id,
                    product_id=product_id,
                    quantity=quantity,
                    min_quantity=5  # Значение по умолчанию
                )
                db.session.add(new_stock)

            db.session.commit()
            flash(f'✅ Поступление {supply_number} успешно оформлено!', 'success')
            return redirect(url_for('main.supplies_list'))

        except Exception as e:
            db.session.rollback()
            flash(f'❌ Ошибка при оформлении поступления: {str(e)}', 'error')
            return redirect(url_for('main.supply'))

    # GET запрос - ВНЕ блока POST
    supply_number = f"SUP-{random.randint(1000, 9999)}"
    products = Product.query.all()
    pharmacies = Pharmacy.query.filter_by(is_active=True).all()
    return render_template('supply.html',
                           products=products,
                           pharmacies=pharmacies,
                           supply_number=supply_number)


@main.route('/sale', methods=['GET', 'POST'])
def sale():
    """
    Оформляет продажу и уменьшает остаток товара в выбранной аптеке.

    Параметры (POST form):
        sale_number, product_id, pharmacy_id, quantity,
        customer_discount, promotion_discount, total_amount, use_fifo.

    Возвращает:
        Response: форма продажи (GET) либо редирект (POST).
    """
    if request.method == 'POST':
        sale_number = request.form.get('sale_number')
        product_id = int(request.form.get('product_id'))
        pharmacy_id = int(request.form.get('pharmacy_id'))
        quantity = int(request.form.get('quantity'))
        customer_discount = float(request.form.get('customer_discount', 0))
        promotion_discount = float(request.form.get('promotion_discount', 0))
        total_amount = float(request.form.get('total_amount'))
        use_fifo = 'use_fifo' in request.form

        try:
            # [БЛОК: проверка достаточности остатка]
            # Условие `not stock or stock.quantity < quantity` защищает от отрицательных остатков.
            stock = Stock.query.filter_by(
                pharmacy_id=pharmacy_id,
                product_id=product_id
            ).first()

            if not stock or stock.quantity < quantity:
                flash('❌ Недостаточно товара на складе!', 'error')
                return redirect(url_for('main.sale'))

            # Получаем цену товара
            product = Product.query.get(product_id)

            # Создаем запись о продаже
            new_sale = Sale(
                sale_number=sale_number,
                product_id=product_id,
                pharmacy_id=pharmacy_id,
                quantity=quantity,
                price_per_unit=product.price,
                customer_discount=customer_discount,
                promotion_discount=promotion_discount,
                total_amount=total_amount,
                is_fifo_applied=use_fifo
            )
            db.session.add(new_sale)

            # Уменьшаем остаток
            stock.quantity -= quantity

            db.session.commit()
            flash(f'✅ Продажа {sale_number} успешно оформлена!', 'success')
            return redirect(url_for('main.sales_list'))

        except Exception as e:
            db.session.rollback()
            flash(f'❌ Ошибка при оформлении продажи: {str(e)}', 'error')
            return redirect(url_for('main.sale'))

    # GET запрос
    sale_number = f"SALE-{random.randint(1000, 9999)}"
    pharmacies = Pharmacy.query.filter_by(is_active=True).all()
    return render_template('sale.html',
                           pharmacies=pharmacies,
                           sale_number=sale_number)


# 👇 НОВЫЙ МАРШРУТ - добавьте после функции sale()
@main.route('/sales/create/', methods=['GET', 'POST'])
@main.route('/sales/create', methods=['GET', 'POST'])
def sales_create():
    """Совместимый URL для создания продажи; перенаправляет на основной маршрут `/sale`."""
    return redirect(url_for('main.sale'))


@main.route('/transfer', methods=['GET', 'POST'])
def transfer():
    """
    Заготовка операции перемещения между аптеками.

    Возвращает:
        Response: форма `transfer.html`.

    Примечание:
        Ветка POST пока содержит `pass`, то есть бизнес-логика перемещения ещё не реализована.
    """
    # ... существующий код функции transfer ...
    if request.method == 'POST':
        # ... код обработки POST ...
        pass

    transfer_number = f"TR-{random.randint(1000, 9999)}"
    products = Product.query.all()
    pharmacies = Pharmacy.query.filter_by(is_active=True).all()
    return render_template('transfer.html',
                           products=products,
                           pharmacies=pharmacies,
                           transfer_number=transfer_number)


# ДОБАВЬТЕ ЭТОТ НОВЫЙ МАРШРУТ:
@main.route('/transfers/create/', methods=['GET', 'POST'])
@main.route('/transfers/create', methods=['GET', 'POST'])
def create_transfer():
    """Альтернативный URL создания перемещения; повторно использует функцию transfer()."""
    return transfer()  # Перенаправляем на существующую функцию


@main.route('/api/pharmacy/<int:pharmacy_id>/products')
def api_pharmacy_products(pharmacy_id):
    """
    Возвращает JSON-список товаров, доступных в конкретной аптеке, вместе с остатком.

    Параметры:
        pharmacy_id (int, required): ID аптеки.

    Возвращает:
        Response(JSON): массив товаров с `stock_quantity`.
    """
    stocks = Stock.query.filter_by(pharmacy_id=pharmacy_id).all()
    result = []

    for stock in stocks:
        product = Product.query.get(stock.product_id)
        if product:  # Проверка существования товара
            result.append({
                'id': product.id,
                'name': product.name,
                'price': product.price,
                'stock_quantity': stock.quantity,
                'barcode': product.barcode
            })

    return jsonify(result)


@main.route('/api/stock/<int:pharmacy_id>/<int:product_id>')
def api_get_stock(pharmacy_id, product_id):
    """
    Возвращает детали остатка по паре (аптека, товар).

    Параметры:
        pharmacy_id (int, required): ID аптеки.
        product_id (int, required): ID товара.

    Возвращает:
        Response(JSON): quantity/min/max/shelf_location или quantity=0, если записи нет.
    """
    stock = Stock.query.filter_by(
        pharmacy_id=pharmacy_id,
        product_id=product_id
    ).first()

    if stock:
        return jsonify({
            'quantity': stock.quantity,
            'min_quantity': stock.min_quantity,
            'max_quantity': stock.max_quantity,
            'shelf_location': stock.shelf_location
        })
    else:
        return jsonify({'quantity': 0})


@main.route('/supplies')
def supplies_list():
    """
    Показывает список поступлений, отсортированный по дате по убыванию.

    Параметры:
        Нет.

    Возвращает:
        Response: HTML `supplies_list.html`.

    Примеры:
        GET /supplies
    """
    supplies = Supply.query.order_by(Supply.supply_date.desc()).all()
    return render_template('supplies_list.html', supplies=supplies)


@main.route('/sales')
def sales_list():
    """
    Отображает список продаж.

    Примечание:
        В коде добавляется `DummyCustomer` для временной совместимости шаблона,
        ожидающего поле `sale.customer.name`.

    Возвращает:
        Response: HTML `sales_list.html`.

    Примеры:
        GET /sales
    """
    sales = Sale.query.order_by(Sale.sale_date.desc()).all()

    # [БЛОК: временная адаптация данных под шаблон]
    # Альтернатива (правильнее): добавить реальную модель Customer и связь в Sale.
    for sale in sales:
        # Создаем временный объект с атрибутом name
        class DummyCustomer:
            name = "Тестовый покупатель"

        sale.customer = DummyCustomer()

    return render_template('sales_list.html', sales=sales)


@main.route('/transfers')
def transfers_list():
    """
    Возвращает страницу со списком перемещений между аптеками.

    Параметры:
        Нет.

    Возвращает:
        Response: HTML `transfers_list.html`.
    """
    transfers = Transfer.query.order_by(Transfer.transfer_date.desc()).all()
    return render_template('transfers_list.html', transfers=transfers)


@main.route('/transfers/<int:transfer_id>')
def view_transfer(transfer_id):
    """
    Показывает детали одного перемещения по его ID.

    Параметры:
        transfer_id (int, required): идентификатор записи перемещения.

    Возвращает:
        Response: HTML `view_transfer.html`.

    Исключения:
        404 Not Found: если запись не существует (через get_or_404).
    """
    transfer = Transfer.query.get_or_404(transfer_id)
    return render_template('view_transfer.html', transfer=transfer)


@main.route('/transfers/<int:transfer_id>/edit', methods=['GET', 'POST'])
def edit_transfer(transfer_id):
    """
    Редактирует статус и примечание перемещения.

    Параметры:
        transfer_id (int, required): ID перемещения.

    Возвращает:
        Response: форма редактирования (GET) или редирект на список (POST).

    Исключения:
        404 Not Found: если перемещение не найдено.
    """
    transfer = Transfer.query.get_or_404(transfer_id)

    if request.method == 'POST':
        # Обновляем статус и другие поля
        transfer.status = request.form.get('status', transfer.status)
        transfer.notes = request.form.get('notes', transfer.notes)

        try:
            db.session.commit()
            flash(f'✅ Перемещение {transfer.transfer_number} обновлено!', 'success')
            return redirect(url_for('main.transfers_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'❌ Ошибка при обновлении: {str(e)}', 'error')

    return render_template('edit_transfer.html', transfer=transfer)


@main.route('/transfers/<int:transfer_id>/delete', methods=['POST'])
def delete_transfer(transfer_id):
    """
    Удаляет запись перемещения и при необходимости корректирует остатки.

    Параметры:
        transfer_id (int, required): ID перемещения.

    Почему проверяется status == 'completed':
        Только выполненное перемещение реально влияло на остатки.
    """
    transfer = Transfer.query.get_or_404(transfer_id)

    try:
        # Если перемещение было выполнено, нужно вернуть товары обратно?
        if transfer.status == 'completed':
            # Возвращаем товар в аптеку-источник
            from_stock = Stock.query.filter_by(
                pharmacy_id=transfer.from_pharmacy_id,
                product_id=transfer.product_id
            ).first()
            if from_stock:
                from_stock.quantity += transfer.quantity

            # Удаляем из аптеки-получателя
            to_stock = Stock.query.filter_by(
                pharmacy_id=transfer.to_pharmacy_id,
                product_id=transfer.product_id
            ).first()
            if to_stock:
                to_stock.quantity -= transfer.quantity

        db.session.delete(transfer)
        db.session.commit()
        flash(f'✅ Перемещение {transfer.transfer_number} удалено!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'❌ Ошибка при удалении: {str(e)}', 'error')

    return redirect(url_for('main.transfers_list'))

@main.route('/debug/check')
def debug_check():
    """
    Отладочный endpoint: возвращает агрегированную диагностику по БД в JSON.

    Параметры:
        Нет.

    Возвращает:
        Response(JSON): счётчики сущностей и список атрибутов sample-товара.
    """
    result = {
        'products_count': Product.query.count(),
        'categories_count': Category.query.count(),
        'manufacturers_count': Manufacturer.query.count(),
        'pharmacies_count': Pharmacy.query.count(),
        'stocks_count': Stock.query.count(),
        'recepts_count': Recept.query.count(),
    }

    # Проверяем структуру Product
    if result['products_count'] > 0:
        sample_product = Product.query.first()
        result['sample_product_attributes'] = [attr for attr in dir(sample_product)
                                               if not attr.startswith('_')]

    return jsonify(result)


@main.route('/debug/routes')
def debug_routes():
    """
    Отладочный endpoint: выводит список доступных маршрутов приложения.

    Возвращает:
        str: HTML-строка с переносами `<br>` между маршрутами.

    Почему строка, а не JSON:
        Быстро читается в браузере без форматтера.
        Альтернатива: jsonify(sorted(links)) для машинной обработки.
    """
    import urllib
    from flask import url_for, current_app

    links = []
    for rule in current_app.url_map.iter_rules():
        # Исключаем служебные и статические маршруты
        if not str(rule).startswith('/static') and not str(rule).startswith('/debug'):
            url = url_for(rule.endpoint, **(rule.defaults or {}))
            links.append(f'{url} -> {rule.endpoint}')

    return '<br>'.join(sorted(links))

@main.route('/test-transfers')
def test_transfers():
    """
    Тестовый маршрут: быстро показывает количество перемещений в базе.

    Возвращает:
        str: короткое текстовое сообщение с числом записей.
    """
    from app.models import Transfer
    transfers = Transfer.query.all()
    return f"Найдено перемещений: {len(transfers)}"


@main.route('/all-low-stock')
def all_low_stock():
    """
    Показывает объединённый список дефицитных позиций по всем аптекам.

    Возвращает:
        Response: HTML `all_low_stock.html`.
    """
    low_stock_items = []
    pharmacies = Pharmacy.query.all()

    # [БЛОК: двойной цикл аптека -> остатки]
    # Плюс: код читаемый для обучения.
    # Минус: может быть медленно на больших объёмах (N+1 запросы).
    # Альтернатива: один JOIN-запрос с фильтрацией по условию low stock.
    for pharmacy in pharmacies:
        stocks = Stock.query.filter_by(pharmacy_id=pharmacy.id).all()
        for stock in stocks:
            if stock.quantity < stock.product.min_stock:
                shortage = stock.product.min_stock - stock.quantity
                low_stock_items.append({
                    'pharmacy': f"Аптека: {pharmacy.name}",
                    'product': f"Товар: {stock.product.name} - {stock.product.price} руб.",
                    'stock': f"Остаток: Аптека {pharmacy.id}, Товар {stock.product_id}: {stock.quantity} шт.",
                    'shortage': shortage,
                    'quantity': stock.quantity,  # Правильно добавлено
                    'product_id': stock.product_id,
                    'pharmacy_id': pharmacy.id
                })

    return render_template('all_low_stock.html', low_stock_items=low_stock_items)