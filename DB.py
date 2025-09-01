from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, Date, DateTime, Numeric, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
# from sqlalchemy.orm import declarative_base
# from sqlalchemy.orm import relationship
from datetime import datetime

def connect_db():
    host = "localhost"
    user = "postgres"  # You might want to change this to 'postgres' or your PostgreSQL username
    password = "$pwd=Mysql5"
    db = "hardwarepos"
    port = 5432  # Default PostgreSQL port

    engine = create_engine(f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}")
    conn = engine.connect()
    return conn, engine
# connect_db()

Base = declarative_base()


class Tax(Base):
    __tablename__ = 'taxes'

    id = Column(Integer, primary_key=True, autoincrement=True)
    tax_type = Column(String(25))
    percentage = Column(Numeric(5, 2))

    def __repr__(self):
        return f"<Tax(id={self.id}, type={self.tax_type}, percent={self.percentage})>"


class Category(Base):
    __tablename__ = 'category'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100))

    subcategories = relationship("SubCategory", back_populates="category")

    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}')>"


class SubCategory(Base):
    __tablename__ = 'subcategory'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50))
    category_id = Column(Integer, ForeignKey('category.id'))

    category = relationship("Category", back_populates="subcategories")
    products = relationship("Product", back_populates="subcategory")

    def __repr__(self):
        return f"<SubCategory(id={self.id}, name='{self.name}')>"


class Unit(Base):
    __tablename__ = 'units'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(20))
    unit = Column(String(10))

    products = relationship("Product", back_populates="unit")

    def __repr__(self):
        return f"<Unit(id={self.id}, name='{self.name}', unit='{self.unit}')>"


class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(100))
    note = Column(Text)
    unit_id = Column(Integer, ForeignKey('units.id'))
    sub_category_id = Column(Integer, ForeignKey('subcategory.id'))
    code = Column(String(10))
    barcode = Column(String(30))
    has_expire = Column(Boolean)
    image = Column(String(100))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    unit = relationship("Unit", back_populates="products")
    subcategory = relationship("SubCategory", back_populates="products")
    stocks = relationship("Stock", back_populates="product")

    def __repr__(self):
        return f"<Product(id={self.id}, title='{self.title}')>"


class Stock(Base):
    __tablename__ = 'stocks'

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_in = Column(Numeric(10, 2), default=0)
    stock_out = Column(Numeric(10, 2), default=0)
    current_stock = Column(Numeric(10, 2), default=0)
    return_stock = Column(Numeric(10, 2), default=0)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    actual_price = Column(Numeric(10, 2), nullable=False)
    min_selling_price = Column(Numeric(10, 2), nullable=False)
    selling_price = Column(Numeric(10, 2), nullable=False)
    expire_date = Column(Date, nullable=True)
    status = Column(String(10), default='active')
    batch_number = Column(String(20))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    product = relationship("Product", back_populates="stocks")
    invoice_items = relationship("InvoiceHasStock", back_populates="stock")
    movements = relationship("StockMovement", back_populates="stock")

    def __repr__(self):
        return f"<Stock(id={self.id}, product_id={self.product_id}, current={self.current_stock})>"


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(100), nullable=False)
    email = Column(String(100))
    phone = Column(String(15))
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime)
    created_on = Column(DateTime, default=datetime.now)
    last_modified_on = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    role = Column(String(20), nullable=False)

    invoices = relationship("Invoice", back_populates="user")
    grns = relationship("GRN", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"


class Customer(Base):
    __tablename__ = 'customers'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100))
    mobile = Column(String(15), unique=True)
    company = Column(String(100))
    street_address = Column(String(100))
    city = Column(String(100))
    credit = Column(Numeric(10, 2), default=0)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    invoices = relationship("Invoice", back_populates="customer" , cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Customer(id={self.id}, name='{self.name}')>"


class Invoice(Base):
    __tablename__ = 'invoices'

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_on = Column(DateTime, default=datetime.now)
    total = Column(Numeric(10, 2), nullable=False)
    discount_amount = Column(Numeric(10, 2), default=0)
    tax_amount = Column(Numeric(10, 2), default=0)
    paid_amount = Column(Numeric(10, 2), default=0)
    status = Column(String(10), default='pending')
    customer_id = Column(Integer, ForeignKey('customers.id'))
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    notes = Column(Text)

    customer = relationship("Customer", back_populates="invoices")
    user = relationship("User", back_populates="invoices")
    items = relationship("InvoiceHasStock", back_populates="invoice")
    transactions = relationship("InvoiceTransaction", back_populates="invoice")
    credit = relationship("InvoiceCredit", uselist=False, back_populates="invoice")

    def __repr__(self):
        return f"<Invoice(id={self.id}, total={self.total}, status='{self.status}')>"


class InvoiceCredit(Base):
    __tablename__ = 'invoice_credits'

    id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_id = Column(Integer, ForeignKey('invoices.id'), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    invoice = relationship("Invoice", back_populates="credit")

    def __repr__(self):
        return f"<InvoiceCredit(id={self.id}, invoice_id={self.invoice_id}, amount={self.amount})>"


class InvoiceHasStock(Base):
    __tablename__ = 'invoice_has_stock'

    id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_id = Column(Integer, ForeignKey('invoices.id', ondelete='CASCADE'), nullable=False)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    discount_amount = Column(Numeric(10, 2), default=0)

    invoice = relationship("Invoice", back_populates="items")
    stock = relationship("Stock", back_populates="invoice_items")

    def __repr__(self):
        return f"<InvoiceHasStock(id={self.id}, invoice={self.invoice_id}, stock={self.stock_id})>"


class Account(Base):
    __tablename__ = 'accounts'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    account_number = Column(String(20))
    bank_name = Column(String(50))
    balance = Column(Numeric(10, 2), default=0)
    is_available = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.now)

    invoice_transactions = relationship("InvoiceTransaction", back_populates="account")
    grn_transactions = relationship("GRNTransaction", back_populates="account")

    def __repr__(self):
        return f"<Account(id={self.id}, name='{self.name}', balance={self.balance})>"


class InvoiceTransaction(Base):
    __tablename__ = 'invoice_transactions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    amount = Column(Numeric(10, 2), nullable=False)
    date = Column(DateTime, default=datetime.now)
    invoice_id = Column(Integer, ForeignKey('invoices.id'), nullable=False)
    account_id = Column(Integer, ForeignKey('accounts.id'), nullable=False)
    transaction_type = Column(String(10), nullable=False)
    cheque_number = Column(String(25))
    card_transaction_id = Column(String(25))
    reference = Column(String(50))
    notes = Column(Text)

    invoice = relationship("Invoice", back_populates="transactions")
    account = relationship("Account", back_populates="invoice_transactions")

    def __repr__(self):
        return f"<InvoiceTransaction(id={self.id}, amount={self.amount}, type='{self.transaction_type}')>"


class Supplier(Base):
    __tablename__ = 'suppliers'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50))
    company_name = Column(String(50), nullable=False)
    code = Column(String(50))
    phone_number = Column(String(15))
    land_line = Column(String(15))
    email = Column(String(100))
    address = Column(Text)
    credit = Column(Numeric(10, 2), default=0)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    grns = relationship("GRN", back_populates="supplier")

    def __repr__(self):
        return f"<Supplier(id={self.id}, company='{self.company_name}')>"


class GRN(Base):
    __tablename__ = 'grn'

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_on = Column(DateTime, default=datetime.now)
    updated_on = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    total_amount = Column(Numeric(10, 2), nullable=False)
    discount_amount = Column(Numeric(10, 2), default=0)
    tax_amount = Column(Numeric(10, 2), default=0)
    paid_amount = Column(Numeric(10, 2), default=0)
    status = Column(String(20), default='pending')
    supplier_id = Column(Integer, ForeignKey('suppliers.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    notes = Column(Text)

    supplier = relationship("Supplier", back_populates="grns")
    user = relationship("User", back_populates="grns")
    transactions = relationship("GRNTransaction", back_populates="grn")

    def __repr__(self):
        return f"<GRN(id={self.id}, total={self.total_amount}, status='{self.status}')>"


class GRNTransaction(Base):
    __tablename__ = 'grn_transactions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    amount = Column(Numeric(10, 2), nullable=False)
    date = Column(DateTime, default=datetime.now)
    grn_id = Column(Integer, ForeignKey('grn.id', ondelete='CASCADE'))
    account_id = Column(Integer, ForeignKey('accounts.id'))
    transaction_type = Column(String(10), nullable=False)
    cheque_number = Column(String(25))
    card_transaction_id = Column(String(25))
    reference = Column(String(50))
    notes = Column(Text)

    grn = relationship("GRN", back_populates="transactions")
    account = relationship("Account", back_populates="grn_transactions")

    def __repr__(self):
        return f"<GRNTransaction(id={self.id}, amount={self.amount}, type='{self.transaction_type}')>"


class Cheque(Base):
    __tablename__ = 'cheques'

    id = Column(Integer, primary_key=True, autoincrement=True)
    cheque_number = Column(String(20), nullable=False)
    cheque_date = Column(Date, nullable=False)
    customer_id = Column(Integer, ForeignKey('customers.id'))
    supplier_id = Column(Integer, ForeignKey('suppliers.id'))
    invoice_id = Column(Integer, ForeignKey('invoices.id'))
    grn_id = Column(Integer, ForeignKey('grn.id'))
    amount = Column(Numeric(10, 2), nullable=False)
    status = Column(String(20), nullable=False)
    created_date = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f"<Cheque(id={self.id}, cheque_number='{self.cheque_number}')>"


class StockMovement(Base):
    __tablename__ = 'stock_movement'

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(Integer, ForeignKey('stocks.id', ondelete='CASCADE'), nullable=False)
    movement_type = Column(String(10), nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False)
    reference_id = Column(Integer)
    reference_type = Column(String(10))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.now)

    stock = relationship("Stock", back_populates="movements")

    def __repr__(self):
        return f"<StockMovement(id={self.id}, stock={self.stock_id}, type='{self.movement_type}')>"


class Variables(Base):
    __tablename__ = 'variables'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    value = Column(String(100), nullable=False)


class ExpenseTracker(Base):
    __tablename__ = 'expenseTracker'

    id = Column(Integer, primary_key=True, autoincrement=True)
    description = Column(Text, nullable=False)
    income = Column(Numeric(10, 2), default=0)
    outcome = Column(Numeric(10, 2), default=0)
    date = Column(DateTime, default=datetime.now)


# Create engine and tables
def create_database():
    conn, engine = connect_db()
    Base.metadata.create_all(engine)
    print("Database tables created successfully!")
    return conn, engine


if __name__ == '__main__':
    create_database()