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
    """Главная страница"""
    products_count = Product.query.count()
    categories_count = Category.query.count()
    pharmacies_count = Pharmacy.query.count()

    # Общее количество товаров на всех аптеках
    total_stock_quantity = db.session.query(db.func.sum(Stock.quantity)).scalar() or 0

    # Аптеки с критическим остатком
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
    """Список товаров"""
    # Получаем параметры фильтрации из запроса
    category_id = request.args.get('category_id', type=int)
    manufacturer_id = request.args.get('manufacturer_id', type=int)
    recept_id = request.args.get('recept_id', type=int)
    pharmacy_id = request.args.get('pharmacy_id', type=int)
    low_stock = request.args.get('low_stock', type=bool)

    # Базовый запрос
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
    """Список категорий"""
    categories_list = Category.query.all()
    return render_template('categories.html', categories=categories_list)


@main.route('/api/products')
def api_products():
    """API для получения товаров (JSON)"""
    products_list = Product.query.all()

    result = []
    for product in products_list:
        # Получаем общее количество через связанные остатки
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
    # ... код ...

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
    """Поиск производителей по названию"""
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
    """Добавление нового товара"""
    if request.method == 'POST':
        name = request.form.get('name')
        price = float(request.form.get('price'))
        category_ids = request.form.getlist('category_ids')
        category_ids = [int(cid) for cid in category_ids if cid]
        manufacturer_id = request.form.get('manufacturer_id')
        manufacturer_id = int(manufacturer_id) if manufacturer_id else None
        recept_id = int(request.form.get('recept_id'))
        barcode = request.form.get('barcode')

        # Получаем начальные остатки по аптекам
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

            # Добавляем категории
            for cat_id in category_ids:
                category = Category.query.get(cat_id)
                if category:
                    new_product.categories.append(category)

            # Сохраняем товар сначала (чтобы получить ID)
            db.session.add(new_product)
            db.session.flush()

            # Добавляем остатки по аптекам с проверкой существования
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
    """Редактирование существующего товара"""
    product = Product.query.get_or_404(product_id)

    if request.method == 'POST':
        # ... существующий код POST ...
        pass

    # Временно перенаправляем на список товаров, если шаблон не создан
    flash('Функция редактирования временно недоступна', 'warning')
    return redirect(url_for('main.products'))
@main.route('/add_category', methods=['GET', 'POST'])
def add_category():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')

        if not name:
            flash('Название категории обязательно для заполнения!', 'error')
            return redirect(url_for('main.add_category'))

        # Проверяем существование категории
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
    """Список аптек сети"""
    pharmacies_list = Pharmacy.query.order_by(Pharmacy.name).all()

    # Оптимизированный запрос для получения всех low_stock_counts одним запросом
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
    """Добавление новой аптеки"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        address = request.form.get('address', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        working_hours = request.form.get('working_hours', '').strip()

        # Валидация
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
    """Просмотр товаров с низким остатком в конкретной аптеке"""
    pharmacy = Pharmacy.query.get_or_404(pharmacy_id)

    # Получаем товары, где количество меньше минимального
    low_stock_items = Stock.query.filter(
        Stock.pharmacy_id == pharmacy_id,
        Stock.quantity < Stock.min_quantity
    ).all()

    # Обогащаем данными о товарах
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
    """Поступление товаров"""
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

        # Сохраняем файл накладной
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

            # Обновляем остатки в аптеке
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
    """Реализация товаров"""
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
            # Проверяем наличие товара
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
    """Создание новой продажи - перенаправляет на основной маршрут /sale"""
    return redirect(url_for('main.sale'))


@main.route('/transfer', methods=['GET', 'POST'])
def transfer():
    """Перемещение товаров между аптеками"""
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
    """Создание нового перемещения (альтернативный URL)"""
    return transfer()  # Перенаправляем на существующую функцию


@main.route('/api/pharmacy/<int:pharmacy_id>/products')
def api_pharmacy_products(pharmacy_id):
    """API для получения товаров в конкретной аптеке с остатками"""
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
    """API для получения информации об остатках конкретного товара в аптеке"""
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
    """Список поступлений"""
    supplies = Supply.query.order_by(Supply.supply_date.desc()).all()
    return render_template('supplies_list.html', supplies=supplies)


@main.route('/sales')
def sales_list():
    """Список продаж"""
    sales = Sale.query.order_by(Sale.sale_date.desc()).all()

    # Добавляем фиктивного покупателя к каждой продаже для тестирования
    for sale in sales:
        # Создаем временный объект с атрибутом name
        class DummyCustomer:
            name = "Тестовый покупатель"

        sale.customer = DummyCustomer()

    return render_template('sales_list.html', sales=sales)


@main.route('/transfers')
def transfers_list():
    """Список перемещений"""
    transfers = Transfer.query.order_by(Transfer.transfer_date.desc()).all()
    return render_template('transfers_list.html', transfers=transfers)


@main.route('/transfers/<int:transfer_id>')
def view_transfer(transfer_id):
    """Просмотр деталей конкретного перемещения"""
    transfer = Transfer.query.get_or_404(transfer_id)
    return render_template('view_transfer.html', transfer=transfer)


@main.route('/transfers/<int:transfer_id>/edit', methods=['GET', 'POST'])
def edit_transfer(transfer_id):
    """Редактирование перемещения"""
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
    """Удаление перемещения"""
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
    """Диагностика состояния базы данных"""
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
    """Показать все доступные маршруты"""
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
    """Тестовый маршрут для проверки"""
    from app.models import Transfer
    transfers = Transfer.query.all()
    return f"Найдено перемещений: {len(transfers)}"


@main.route('/all-low-stock')
def all_low_stock():
    low_stock_items = []
    pharmacies = Pharmacy.query.all()

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