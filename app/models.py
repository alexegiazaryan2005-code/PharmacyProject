from app.extensions import db
from sqlalchemy import Table, Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship

# Определяем metadata для Table
metadata = db.metadata

# Определение промежуточной таблицы для связи многие-ко-многим
product_category = Table('product_category', metadata,
    Column('product_id', Integer, ForeignKey('products.id'), primary_key=True),
    Column('category_id', Integer, ForeignKey('categories.id'), primary_key=True)
)

class Recept(db.Model):
    __tablename__ = 'recepts'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    description = db.Column(db.String)

    products = relationship("Product", back_populates="recept")

    def __repr__(self):
        return f'Тип рецептурности: {self.name}'

class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    description = db.Column(db.String)

    products = relationship("Product", secondary=product_category, back_populates="categories")

    def __repr__(self):
        return f'Категория: {self.name}'

class Manufacturer(db.Model):
    __tablename__ = 'manufacturers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.String)
    country = db.Column(db.String)

    products = relationship("Product", back_populates="manufacturer")

    def __repr__(self):
        return f'Производитель: {self.name}'

class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    description = db.Column(db.String)
    price = db.Column(db.Float)
    barcode = db.Column(db.String(50), unique=True)
    manufacturer_id = db.Column(db.Integer, db.ForeignKey('manufacturers.id'))
    recept_id = db.Column(db.Integer, db.ForeignKey('recepts.id'))
    min_stock = db.Column(db.Integer, default=5)  # ДОБАВЛЕНО: минимальный остаток для товара

    manufacturer = relationship("Manufacturer", back_populates="products")
    recept = relationship("Recept", back_populates="products")
    categories = relationship("Category", secondary=product_category, back_populates="products")
    stocks = db.relationship('Stock', backref='product', lazy='dynamic', cascade='all, delete-orphan')
    def __repr__(self):
        return f'Товар: {self.name} - {self.price} руб.'

class Pharmacy(db.Model):
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
        first_stock = self.stocks.first()
        return first_stock.min_quantity if first_stock else 5

    def __repr__(self):
        return f'Аптека: {self.name}'

class Stock(db.Model):
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
        return f'Остаток: Аптека {self.pharmacy_id}, Товар {self.product_id}: {self.quantity} шт.'

class Supply(db.Model):
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
        return f'<Supply {self.supply_number}>'

class Sale(db.Model):
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
    pharmacy = db.relationship('Pharmacy', backref='sales')  # ЭТО ДОЛЖНО БЫТЬ

    def __repr__(self):
        return f'<Sale {self.sale_number}>'

class Transfer(db.Model):
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
        return f'<Transfer {self.transfer_number}>'