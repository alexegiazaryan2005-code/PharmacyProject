"""
Файл: app/models.py
Назначение: Описание доменных сущностей аптечной системы в виде ORM-моделей SQLAlchemy.
Роль в архитектуре: слой данных (data/model layer), на который опираются маршруты и скрипты миграций.

Импорты:
- app.extensions.db: объект Flask-SQLAlchemy для объявления таблиц и колонок.
- sqlalchemy.Table/Column/...: низкоуровневые конструкции для промежуточной таблицы many-to-many.
- sqlalchemy.orm.relationship: декларация связей между моделями.

Связи:
- Используется в app/routes.py для CRUD-операций.
- Используется в скриптах миграций в корне проекта.
"""

from app.extensions import db
from sqlalchemy import Table, Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship

# Метаданные (metadata) хранят информацию обо всех таблицах.
metadata = db.metadata

# Промежуточная таблица для связи many-to-many между товарами и категориями.
# **Почему Table, а не отдельный класс-модель**:
# - здесь нет дополнительных полей связи (даты, приоритета и т.д.),
# - поэтому «чистая» таблица проще и эффективнее.
# Альтернатива: отдельная ORM-модель ProductCategory — нужна, если у связи появятся собственные атрибуты.
product_category = Table('product_category', metadata,
    Column('product_id', Integer, ForeignKey('products.id'), primary_key=True),
    Column('category_id', Integer, ForeignKey('categories.id'), primary_key=True)
)


class Recept(db.Model):
    """
    Модель типа рецептурности (например, «без рецепта», «по рецепту»).

    ООП:
        - **Инкапсуляция**: данные и связи собраны в одном классе.
        - Наследуется от `db.Model`, чтобы получить ORM-поведение SQLAlchemy.

    Магические методы:
        - __repr__: человекочитаемое представление для отладки.
    """
    __tablename__ = 'recepts'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    description = db.Column(db.String)

    products = relationship("Product", back_populates="recept")

    def __repr__(self):
        """
        Возвращает текстовое представление типа рецептурности.

        Возвращает:
            str: строка для логов/отладки.
        """
        return f'Тип рецептурности: {self.name}'


class Category(db.Model):
    """Модель товарной категории (например, «Антибиотики», «Витамины»)."""
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    description = db.Column(db.String)

    products = relationship("Product", secondary=product_category, back_populates="categories")

    def __repr__(self):
        """Возвращает краткое строковое представление категории."""
        return f'Категория: {self.name}'


class Manufacturer(db.Model):
    """Модель производителя лекарственных средств."""
    __tablename__ = 'manufacturers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.String)
    country = db.Column(db.String)

    products = relationship("Product", back_populates="manufacturer")

    def __repr__(self):
        """Возвращает строку для отладки с названием производителя."""
        return f'Производитель: {self.name}'


class Product(db.Model):
    """
    Модель товара (лекарства/медицинского изделия).

    Почему выбраны такие поля:
    - `barcode` уникален, так как это естественный бизнес-идентификатор товара.
    - `min_stock` хранится в товаре как дефолт для контроля минимального остатка.

    Альтернатива:
    - хранить минимальный остаток только в `Stock` (по каждой аптеке индивидуально).
      Это гибче, если нормы по остаткам сильно различаются между филиалами.
    """
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    description = db.Column(db.String)
    price = db.Column(db.Float)
    barcode = db.Column(db.String(50), unique=True)
    manufacturer_id = db.Column(db.Integer, db.ForeignKey('manufacturers.id'))
    recept_id = db.Column(db.Integer, db.ForeignKey('recepts.id'))
    min_stock = db.Column(db.Integer, default=5)

    manufacturer = relationship("Manufacturer", back_populates="products")
    recept = relationship("Recept", back_populates="products")
    categories = relationship("Category", secondary=product_category, back_populates="products")
    stocks = db.relationship('Stock', backref='product', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        """Возвращает отладочное представление товара с ценой."""
        return f'Товар: {self.name} - {self.price} руб.'


class Pharmacy(db.Model):
    """Модель филиала аптеки в сети."""
    __tablename__ = 'pharmacy'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    address = db.Column(db.String(300))
    phone = db.Column(db.String(50))
    email = db.Column(db.String(100))
    working_hours = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    stocks = db.relationship('Stock', backref='pharmacy', lazy='dynamic', cascade='all, delete-orphan')

    def get_default_min_quantity(self):
        """
        Возвращает дефолтный минимальный остаток для аптеки.

        Логика:
            Берётся `min_quantity` первой найденной записи stock.
            Если остатков ещё нет, используется значение по умолчанию 5.

        Возвращает:
            int: минимально допустимый остаток.

        Почему так:
            Это практичный компромисс при отсутствии отдельной таблицы настроек аптеки.
            Альтернатива: хранить настройки в отдельной сущности `PharmacySettings`.
        """
        first_stock = self.stocks.first()
        return first_stock.min_quantity if first_stock else 5

    def __repr__(self):
        """Возвращает строковое представление аптеки."""
        return f'Аптека: {self.name}'


class Stock(db.Model):
    """
    Модель складского остатка товара в конкретной аптеке.

    Ключевая идея:
        Один товар в одной аптеке должен иметь ровно одну запись остатка.
        Это обеспечивается уникальным ограничением `unique_pharmacy_product`.
    """
    __tablename__ = 'stock'
    __table_args__ = (
        db.UniqueConstraint('pharmacy_id', 'product_id', name='unique_pharmacy_product'),
    )
    id = db.Column(db.Integer, primary_key=True)
    pharmacy_id = db.Column(db.Integer, db.ForeignKey('pharmacy.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, default=0, nullable=False)
    min_quantity = db.Column(db.Integer, default=5, nullable=False)
    max_quantity = db.Column(db.Integer)
    shelf_location = db.Column(db.String(50))
    last_updated = db.Column(db.DateTime, default=db.func.current_timestamp(),
                             onupdate=db.func.current_timestamp())

    def __repr__(self):
        """Возвращает отладочную строку по текущему остатку."""
        return f'Остаток: Аптека {self.pharmacy_id}, Товар {self.product_id}: {self.quantity} шт.'


class Supply(db.Model):
    """Модель поступления товара (приходная операция)."""
    __tablename__ = 'supply'

    id = db.Column(db.Integer, primary_key=True)
    supply_number = db.Column(db.String(50), unique=True, nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    pharmacy_id = db.Column(db.Integer, db.ForeignKey('pharmacy.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    purchase_price = db.Column(db.Float, nullable=False)
    selling_price = db.Column(db.Float, nullable=False)
    markup_percent = db.Column(db.Float, nullable=False)
    discount_percent = db.Column(db.Float, default=0)
    total_amount = db.Column(db.Float, nullable=False)
    supply_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    invoice_file = db.Column(db.String(500))
    notes = db.Column(db.Text)

    product = db.relationship('Product', backref='supplies')
    pharmacy = db.relationship('Pharmacy', backref='supplies')

    def __repr__(self):
        """Возвращает строку с номером поступления."""
        return f'<Supply {self.supply_number}>'


class Sale(db.Model):
    """Модель продажи товара покупателю."""
    __tablename__ = 'sale'

    id = db.Column(db.Integer, primary_key=True)
    sale_number = db.Column(db.String(50), unique=True, nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    pharmacy_id = db.Column(db.Integer, db.ForeignKey('pharmacy.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price_per_unit = db.Column(db.Float, nullable=False)
    customer_discount = db.Column(db.Float, default=0)
    promotion_discount = db.Column(db.Float, default=0)
    total_amount = db.Column(db.Float, nullable=False)
    sale_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    is_fifo_applied = db.Column(db.Boolean, default=True)

    product = db.relationship('Product', backref='sales')
    pharmacy = db.relationship('Pharmacy', backref='sales')

    def __repr__(self):
        """Возвращает строку с номером продажи."""
        return f'<Sale {self.sale_number}>'


class Transfer(db.Model):
    """
    Модель межаптечного перемещения.

    Особенность:
        Есть две связи на одну и ту же таблицу `pharmacy` (`from_pharmacy_id` и `to_pharmacy_id`).
        Поэтому в relationship явно указан `foreign_keys`, иначе ORM не сможет однозначно определить связь.
    """
    __tablename__ = 'transfer'

    id = db.Column(db.Integer, primary_key=True)
    transfer_number = db.Column(db.String(50), unique=True, nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    from_pharmacy_id = db.Column(db.Integer, db.ForeignKey('pharmacy.id'), nullable=False)
    to_pharmacy_id = db.Column(db.Integer, db.ForeignKey('pharmacy.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    transfer_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    status = db.Column(db.String(20), default='pending')
    notes = db.Column(db.Text)
    completed_date = db.Column(db.DateTime)

    product = db.relationship('Product', backref='transfers')
    from_pharmacy = db.relationship('Pharmacy', foreign_keys=[from_pharmacy_id], backref='transfers_out')
    to_pharmacy = db.relationship('Pharmacy', foreign_keys=[to_pharmacy_id], backref='transfers_in')

    def __repr__(self):
        """Возвращает строку с номером перемещения."""
        return f'<Transfer {self.transfer_number}>'