from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import random
from DB import *


def create_dummy_data(engine):
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Create Taxes
        taxes = [
            Tax(tax_type="VAT", percentage=18.00),
            Tax(tax_type="Service Tax", percentage=5.00),
            Tax(tax_type="Import Duty", percentage=10.00)
        ]
        session.add_all(taxes)
        session.commit()
        print("✓ Taxes created")
    except Exception as e:
        session.rollback()
        print(f"Error creating taxes: {e}")

    try:
        # Create Categories
        categories = [
            Category(name="Tools & Equipment"),
            Category(name="Building Materials"),
            Category(name="Hardware & Fasteners"),
            Category(name="Electrical Supplies"),
            Category(name="Plumbing Supplies"),
            Category(name="Paint & Decorating"),
            Category(name="Garden & Outdoor")
        ]
        session.add_all(categories)
        session.commit()
        print("✓ Categories created")
    except Exception as e:
        session.rollback()
        print(f"Error creating categories: {e}")

    try:
        # Create SubCategories
        subcategories = [
            # Tools & Equipment subcategories
            SubCategory(name="Power Tools", category_id=1),
            SubCategory(name="Hand Tools", category_id=1),
            SubCategory(name="Measuring Tools", category_id=1),
            SubCategory(name="Tool Storage", category_id=1),

            # Building Materials subcategories
            SubCategory(name="Lumber", category_id=2),
            SubCategory(name="Plywood & Boards", category_id=2),
            SubCategory(name="Cement & Concrete", category_id=2),
            SubCategory(name="Roofing", category_id=2),

            # Hardware & Fasteners subcategories
            SubCategory(name="Nails & Screws", category_id=3),
            SubCategory(name="Bolts & Nuts", category_id=3),
            SubCategory(name="Hinges & Latches", category_id=3),
            SubCategory(name="Chains & Ropes", category_id=3),

            # Electrical Supplies subcategories
            SubCategory(name="Wires & Cables", category_id=4),
            SubCategory(name="Switches & Sockets", category_id=4),
            SubCategory(name="Lighting", category_id=4),
            SubCategory(name="Circuit Breakers", category_id=4),

            # Plumbing Supplies subcategories
            SubCategory(name="Pipes & Fittings", category_id=5),
            SubCategory(name="Faucets & Taps", category_id=5),
            SubCategory(name="Toilets & Basins", category_id=5),
            SubCategory(name="Water Heaters", category_id=5),

            # Paint & Decorating subcategories
            SubCategory(name="Paints", category_id=6),
            SubCategory(name="Brushes & Rollers", category_id=6),
            SubCategory(name="Wallpaper", category_id=6),
            SubCategory(name="Adhesives", category_id=6),

            # Garden & Outdoor subcategories
            SubCategory(name="Gardening Tools", category_id=7),
            SubCategory(name="Plants & Seeds", category_id=7),
            SubCategory(name="Outdoor Lighting", category_id=7),
            SubCategory(name="BBQ & Outdoor Cooking", category_id=7)
        ]
        session.add_all(subcategories)
        session.commit()
        print("✓ Subcategories created")
    except Exception as e:
        session.rollback()
        print(f"Error creating subcategories: {e}")

    try:
        # Create Units
        units = [
            Unit(name="Piece", unit="pcs"),
            Unit(name="Kilogram", unit="kg"),
            Unit(name="Meter", unit="m"),
            Unit(name="Liter", unit="L"),
            Unit(name="Box", unit="box"),
            Unit(name="Pack", unit="pack"),
            Unit(name="Roll", unit="roll")
        ]
        session.add_all(units)
        session.commit()
        print("✓ Units created")
    except Exception as e:
        session.rollback()
        print(f"Error creating units: {e}")

    try:
        # Create Products
        products = [
            # Power Tools
            Product(title="Cordless Drill 18V", note="Lithium-ion battery, variable speed", unit_id=1,
                    sub_category_id=1, code="PT001", barcode="1234567890123", has_expire=False),
            Product(title="Circular Saw 7-1/4\"", note="15 Amp motor, electric brake", unit_id=1, sub_category_id=1,
                    code="PT002", barcode="1234567890124", has_expire=False),
            Product(title="Angle Grinder 4-1/2\"", note="10 Amp motor, side handle", unit_id=1, sub_category_id=1,
                    code="PT003", barcode="1234567890125", has_expire=False),

            # Hand Tools
            Product(title="Claw Hammer 16oz", note="Fiberglass handle, magnetic nail starter", unit_id=1,
                    sub_category_id=2, code="HT001", barcode="1234567890126", has_expire=False),
            Product(title="Screwdriver Set 6-Piece", note="Phillips and flat head, cushioned grip", unit_id=5,
                    sub_category_id=2, code="HT002", barcode="1234567890127", has_expire=False),
            Product(title="Adjustable Wrench 10\"", note="Chrome vanadium steel, smooth adjustment", unit_id=1,
                    sub_category_id=2, code="HT003", barcode="1234567890128", has_expire=False),

            # Lumber
            Product(title="Pine Board 2x4x8'", note="Premium grade, kiln dried", unit_id=3, sub_category_id=5,
                    code="BM001", barcode="1234567890129", has_expire=False),
            Product(title="Plywood 4x8' 1/2\"", note="BC grade, sanded both sides", unit_id=1, sub_category_id=6,
                    code="BM002", barcode="1234567890130", has_expire=False),

            # Nails & Screws
            Product(title="Common Nails 3\" 5lb", note="Bright finish, smooth shank", unit_id=2, sub_category_id=9,
                    code="HF001", barcode="1234567890131", has_expire=False),
            Product(title="Wood Screws #8 2-1/2\" 1lb", note="Phillips head, zinc plated", unit_id=2, sub_category_id=9,
                    code="HF002", barcode="1234567890132", has_expire=False),

            # Electrical
            Product(title="Romex Wire 12/2 250ft", note="With ground, yellow jacket", unit_id=3, sub_category_id=13,
                    code="ES001", barcode="1234567890133", has_expire=False),
            Product(title="LED Bulb 60W Equivalent", note="Soft white, 800 lumens", unit_id=1, sub_category_id=15,
                    code="ES002", barcode="1234567890134", has_expire=False),

            # Plumbing
            Product(title="PVC Pipe 1/2\" x 10ft", note="Schedule 40, white", unit_id=3, sub_category_id=17,
                    code="PS001", barcode="1234567890135", has_expire=False),
            Product(title="Ball Valve 1/2\" Brass", note="Full port, chrome plated", unit_id=1, sub_category_id=17,
                    code="PS002", barcode="1234567890136", has_expire=False),

            # Paint
            Product(title="Interior Latex Paint White 1Gal", note="Semi-gloss, one coat coverage", unit_id=4,
                    sub_category_id=21, code="PD001", barcode="1234567890137", has_expire=True),
            Product(title="Paint Brush 3\" Synthetic", note="Angled tip, wooden handle", unit_id=1, sub_category_id=22,
                    code="PD002", barcode="1234567890138", has_expire=False),

            # Garden
            Product(title="Shovel Round Point", note="Fiberglass handle, steel head", unit_id=1, sub_category_id=25,
                    code="GO001", barcode="1234567890139", has_expire=False),
            Product(title="Potting Soil 20L", note="Enriched with nutrients, for all plants", unit_id=4,
                    sub_category_id=26, code="GO002", barcode="1234567890140", has_expire=False)
        ]
        session.add_all(products)
        session.commit()
        print("✓ Products created")
    except Exception as e:
        session.rollback()
        print(f"Error creating products: {e}")

    try:
        # Create Stocks with different batches and prices
        stocks = []
        for product in products:
            # Create 1-3 stock entries per product with different prices
            for i in range(random.randint(1, 3)):
                expire_date = None
                if product.has_expire:
                    expire_date = datetime.now().date() + timedelta(days=random.randint(180, 720))

                actual_price = round(random.uniform(5, 200), 2)
                min_selling_price = round(actual_price * 1.2, 2)
                selling_price = round(actual_price * random.uniform(1.3, 1.8), 2)

                stock = Stock(
                    product_id=product.id,
                    stock_in=random.randint(50, 200),
                    current_stock=random.randint(20, 100),
                    actual_price=actual_price,
                    min_selling_price=min_selling_price,
                    selling_price=selling_price,
                    expire_date=expire_date,
                    batch_number=f"BATCH{product.id:03d}{i + 1}",
                    status="active"
                )
                stocks.append(stock)

        session.add_all(stocks)
        session.commit()
        print("✓ Stocks created")
    except Exception as e:
        session.rollback()
        print(f"Error creating stocks: {e}")

    try:
        # Create Users
        users = [
            User(name="John Smith", username="john", password="password123", email="john@hardwarestore.com",
                 phone="555-0101", role="admin", is_active=True),
            User(name="Sarah Johnson", username="sarah", password="password123", email="sarah@hardwarestore.com",
                 phone="555-0102", role="cashier", is_active=True),
            User(name="Mike Wilson", username="mike", password="password123", email="mike@hardwarestore.com",
                 phone="555-0103", role="manager", is_active=True),
            User(name="Lisa Brown", username="lisa", password="password123", email="lisa@hardwarestore.com",
                 phone="555-0104", role="cashier", is_active=True)
        ]
        session.add_all(users)
        session.commit()
        print("✓ Users created")
    except Exception as e:
        session.rollback()
        print(f"Error creating users: {e}")

    try:
        # Create Customers
        customers = [
            Customer(name="Robert Davis", mobile="555-0201", company="Davis Construction", street_address="123 Main St",
                     city="Springfield", credit=0),
            Customer(name="Jennifer Miller", mobile="555-0202", company="Miller Renovations",
                     street_address="456 Oak Ave", city="Springfield", credit=500.00),
            Customer(name="Thomas Wilson", mobile="555-0203", company="Wilson Contracting",
                     street_address="789 Pine Rd", city="Springfield", credit=1000.00),
            Customer(name="Maria Garcia", mobile="555-0204", company=None, street_address="321 Elm St",
                     city="Springfield", credit=0),
            Customer(name="James Johnson", mobile="555-0205", company="JJ Handyman", street_address="654 Maple Dr",
                     city="Springfield", credit=250.00)
        ]
        session.add_all(customers)
        session.commit()
        print("✓ Customers created")
    except Exception as e:
        session.rollback()
        print(f"Error creating customers: {e}")

    try:
        # Create Accounts
        accounts = [
            Account(name="Main Cash Account", account_number="CASH001", bank_name="Cash", balance=5000.00),
            Account(name="Business Checking", account_number="CHK12345", bank_name="Springfield Bank",
                    balance=25000.00),
            Account(name="Business Savings", account_number="SAV67890", bank_name="Springfield Bank", balance=15000.00),
            Account(name="Credit Card Terminal", account_number="CC001", bank_name="Payment Processing", balance=0.00)
        ]
        session.add_all(accounts)
        session.commit()
        print("✓ Accounts created")
    except Exception as e:
        session.rollback()
        print(f"Error creating accounts: {e}")

    try:
        # Create Suppliers
        suppliers = [
            Supplier(name="David Thompson", company_name="Thompson Tools Inc.", code="THMP01", phone_number="555-0301",
                     land_line="555-0302", email="david@thompsontools.com", address="100 Industrial Park, Springfield",
                     credit=0),
            Supplier(name="Susan Lee", company_name="Lee Building Supplies", code="LEE01", phone_number="555-0303",
                     land_line="555-0304", email="susan@leebuildingsupplies.com",
                     address="200 Commerce Ave, Springfield", credit=0),
            Supplier(name="Mark Roberts", company_name="Roberts Electrical Wholesale", code="ROBR01",
                     phone_number="555-0305", land_line="555-0306", email="mark@robertselectrical.com",
                     address="300 Technology Dr, Springfield", credit=0),
            Supplier(name="Amanda White", company_name="White Paint & Decor", code="WHIT01", phone_number="555-0307",
                     land_line="555-0308", email="amanda@whitepaint.com", address="400 Artisan St, Springfield",
                     credit=0)
        ]
        session.add_all(suppliers)
        session.commit()
        print("✓ Suppliers created")
    except Exception as e:
        session.rollback()
        print(f"Error creating suppliers: {e}")

    try:
        # Create Invoices
        invoices = []
        for i in range(20):  # Create 20 sample invoices
            customer = random.choice(customers)
            user = random.choice(users)

            # Create invoice date in the last 30 days
            invoice_date = datetime.now() - timedelta(days=random.randint(1, 30))

            invoice = Invoice(
                created_on=invoice_date,
                total=0,  # Will be calculated after adding items
                customer_id=customer.id,
                user_id=user.id,
                status=random.choice(['paid', 'pending', 'paid']),  # Mostly paid
                notes=random.choice([None, "Urgent delivery", "Customer will pick up", "Include invoice in email"])
            )
            invoices.append(invoice)

        session.add_all(invoices)
        session.commit()
        print("✓ Invoices created")
    except Exception as e:
        session.rollback()
        print(f"Error creating invoices: {e}")

    try:
        # Create Invoice Items and calculate totals
        for invoice in invoices:
            total = 0
            tax_amount = 0
            discount_amount = 0

            # Add 1-5 items to each invoice
            for _ in range(random.randint(1, 5)):
                stock = random.choice(stocks)
                quantity = random.randint(1, 10)
                unit_price = stock.selling_price
                line_total = quantity * unit_price

                # Apply random discount sometimes
                discount = round(random.uniform(0, 0.15) * line_total, 2) if random.random() < 0.3 else 0
                line_total -= discount

                item = InvoiceHasStock(
                    invoice_id=invoice.id,
                    stock_id=stock.id,
                    quantity=quantity,
                    unit_price=unit_price,
                    discount_amount=discount
                )
                session.add(item)

                total += line_total
                discount_amount += discount

            # Add tax (around 10% of total)
            tax_amount = round(total * 0.1, 2)
            total += tax_amount

            invoice.total = total
            invoice.tax_amount = tax_amount
            invoice.discount_amount = discount_amount

            # If status is paid, set paid amount
            if invoice.status == 'paid':
                invoice.paid_amount = total

        session.commit()
        print("✓ Invoice items created")
    except Exception as e:
        session.rollback()
        print(f"Error creating invoice items: {e}")

    try:
        # Create Invoice Transactions for paid invoices
        for invoice in invoices:
            if invoice.status == 'paid':
                transaction = InvoiceTransaction(
                    amount=invoice.paid_amount,
                    date=invoice.created_on + timedelta(hours=1),  # Payment shortly after invoice
                    invoice_id=invoice.id,
                    account_id=random.choice(accounts).id,
                    transaction_type=random.choice(['cash', 'card', 'check']),
                    notes=f"Payment for invoice #{invoice.id}"
                )
                session.add(transaction)

        session.commit()
        print("✓ Invoice transactions created")
    except Exception as e:
        session.rollback()
        print(f"Error creating invoice transactions: {e}")

    try:
        # Create GRNs (Goods Received Notes)
        grns = []
        for i in range(10):  # Create 10 sample GRNs
            supplier = random.choice(suppliers)
            user = random.choice(users)

            # Create GRN date in the last 60 days
            grn_date = datetime.now() - timedelta(days=random.randint(1, 60))

            grn = GRN(
                created_on=grn_date,
                total_amount=round(random.uniform(500, 5000), 2),  # Random total amount
                supplier_id=supplier.id,
                user_id=user.id,
                status=random.choice(['received', 'pending']),
                notes=random.choice([None, "Check quality upon arrival", "Store in main warehouse"])
            )
            grns.append(grn)

        session.add_all(grns)
        session.commit()
        print("✓ GRNs created")
    except Exception as e:
        session.rollback()
        print(f"Error creating GRNs: {e}")

    try:
        # Create GRN Transactions
        for grn in grns:
            if grn.status == 'received':
                transaction = GRNTransaction(
                    amount=grn.total_amount,
                    date=grn.created_on + timedelta(days=random.randint(1, 7)),  # Payment days after receipt
                    grn_id=grn.id,
                    account_id=random.choice(accounts).id,
                    transaction_type=random.choice(['cash', 'transfer', 'check']),
                    notes=f"Payment for GRN #{grn.id}"
                )
                session.add(transaction)

        session.commit()
        print("✓ GRN transactions created")
    except Exception as e:
        session.rollback()
        print(f"Error creating GRN transactions: {e}")

    try:
        # Create Cheques
        cheques = []
        for i in range(5):
            cheque = Cheque(
                cheque_number=f"CHQ{1000 + i}",
                cheque_date=datetime.now().date() + timedelta(days=random.randint(10, 30)),
                customer_id=random.choice(customers).id if random.random() < 0.5 else None,
                supplier_id=random.choice(suppliers).id if random.random() < 0.5 else None,
                amount=round(random.uniform(100, 2000), 2),
                status=random.choice(['pending', 'cleared', 'bounced'])
            )
            cheques.append(cheque)

        session.add_all(cheques)
        session.commit()
        print("✓ Cheques created")
    except Exception as e:
        session.rollback()
        print(f"Error creating cheques: {e}")

    try:
        # Create Stock Movements
        stock_movements = []
        for stock in stocks:
            # Create initial stock in movement
            movement = StockMovement(
                stock_id=stock.id,
                movement_type="in",
                quantity=stock.stock_in,
                reference_type="grn",
                reference_id=random.randint(1, 10),
                notes="Initial stock receipt"
            )
            stock_movements.append(movement)

            # Create some stock out movements (sales)
            for _ in range(random.randint(3, 8)):
                movement = StockMovement(
                    stock_id=stock.id,
                    movement_type="out",
                    quantity=random.randint(1, 10),
                    reference_type="invoice",
                    reference_id=random.randint(1, 20),
                    notes="Sale to customer"
                )
                stock_movements.append(movement)

        session.add_all(stock_movements)
        session.commit()
        print("✓ Stock movements created")
    except Exception as e:
        session.rollback()
        print(f"Error creating stock movements: {e}")

    try:
        # Create Variables
        variables = [
            Variables(name="store_name", value="Springfield Hardware"),
            Variables(name="store_address", value="123 Main Street, Springfield"),
            Variables(name="store_phone", value="555-1000"),
            Variables(name="store_email", value="info@springfieldhardware.com"),
            Variables(name="tax_rate", value="10.0"),
            Variables(name="currency", value="USD")
        ]
        session.add_all(variables)
        session.commit()
        print("✓ Variables created")
    except Exception as e:
        session.rollback()
        print(f"Error creating variables: {e}")

    try:
        # Create ExpenseTracker entries
        expenses = []
        for i in range(30):  # Last 30 days of expenses
            date = datetime.now() - timedelta(days=i)

            # Some days have both income and expenses, some just one
            if random.random() < 0.7:  # 70% chance of income
                income = round(random.uniform(500, 3000), 2)
            else:
                income = 0

            if random.random() < 0.8:  # 80% chance of expenses
                outcome = round(random.uniform(100, 1000), 2)
            else:
                outcome = 0

            expense = ExpenseTracker(
                description=random.choice([
                    "Daily sales", "Supplier payment", "Utility bills",
                    "Employee wages", "Rent payment", "Maintenance costs"
                ]),
                income=income,
                outcome=outcome,
                date=date
            )
            expenses.append(expense)

        session.add_all(expenses)
        session.commit()
        print("✓ Expenses created")
    except Exception as e:
        session.rollback()
        print(f"Error creating expenses: {e}")

    print("\nDummy data creation completed!")
    print("Summary:")
    print(f"- {len(taxes)} taxes")
    print(f"- {len(categories)} categories")
    print(f"- {len(subcategories)} subcategories")
    print(f"- {len(products)} products")
    print(f"- {len(stocks)} stock entries")
    print(f"- {len(users)} users")
    print(f"- {len(customers)} customers")
    print(f"- {len(accounts)} accounts")
    print(f"- {len(suppliers)} suppliers")
    print(f"- {len(invoices)} invoices")
    print(f"- {len(grns)} GRNs")
    print(f"- {len(cheques)} cheques")
    print(f"- {len(stock_movements)} stock movements")
    print(f"- {len(variables)} variables")
    print(f"- {len(expenses)} expense entries")


# Add this to your main execution block
if __name__ == '__main__':
    conn, engine = connect_db()
    create_database()  # This creates the tables
    create_dummy_data(engine)  # This populates with dummy data