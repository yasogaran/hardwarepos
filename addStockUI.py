import flet as ft
from datetime import datetime
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, update, select, or_, text

import DB

CONN: create_engine
SESSION: Session

products = ""

units = dict()

USER_ID = ""

selected_product = dict()
selected_supplier = dict()
filtered_products = dict()
selected_stocks = dict()


def addStock(page: ft.Page, conn: create_engine, user_id):
    global CONN, products, USER_ID, filtered_products, SESSION

    CONN = conn
    SESSION = Session(CONN)
    USER_ID = user_id

    # Convert SQL to SQLAlchemy
    products_query = SESSION.query(DB.Product).limit(5).all()
    products = [p.__dict__ for p in products_query]

    # Convert SQL to SQLAlchemy
    units_query = SESSION.query(DB.Unit).all()
    for unit in units_query:
        units[unit.id] = unit.unit

    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.fonts = {
        "Roboto": "https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap"
    }
    page.theme = ft.Theme(font_family="Roboto")

    # State variables
    filtered_products = products.copy()

    # Header with date
    header = ft.Row(
        controls=[
            ft.Column(
                controls=[
                    ft.Text("Add Stock", size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_900),
                    ft.Text("Add new inventory to your store", color=ft.Colors.GREY_600)
                ],
                spacing=0
            ),
            ft.Row(
                controls=[
                    ft.Icon(ft.Icons.CALENDAR_TODAY, size=16, color="#6b7280"),
                    ft.Text(datetime.now().strftime("%B %d, %Y"), color="#6b7280")
                ],
                spacing=5
            )
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
    )

    def validate_quantity(e):
        pay(None)
        if not selected_product:
            return
        try:
            qty = float(quantity.value)
            if units[selected_product["unit_id"]] == "pc" and not qty.is_integer():
                quantity.error_text = "Quantity must be a whole number for pieces"
            elif qty <= 0:
                quantity.error_text = "Quantity must be greater than 0"
            else:
                quantity.error_text = None
        except ValueError:
            quantity.error_text = "Please enter a valid number"

        quantity.update()

    def validate_pricing(e):
        try:
            min_p = float(min_price.value) if min_price.value else 0
            max_p = float(max_price.value) if max_price.value else 0

            if min_p and max_p and min_p > max_p:
                max_price.error_text = "Maximum price must be greater than minimum price"
            else:
                max_price.error_text = None
        except ValueError:
            max_price.error_text = "Please enter valid prices"

        max_price.update()

    def filter_products(e):
        global filtered_products
        query = e.control.value.lower()
        if not query:
            product_dropdown_container.visible = False
        else:
            # Convert SQL to SQLAlchemy
            filtered_products_query = SESSION.query(DB.Product).filter(
                or_(
                    DB.Product.code.ilike(f"%{query}%"),
                    DB.Product.id.ilike(f"%{query}%"),
                    DB.Product.title.ilike(f"%{query}%"),
                    DB.Product.note.ilike(f"%{query}%")
                )
            ).limit(5).all()

            filtered_products = [p.__dict__ for p in filtered_products_query]
            page.update()

            if filtered_products:
                product_dropdown.controls = [
                    ft.ListTile(
                        title=ft.Text(fp["title"]),
                        subtitle=ft.Text(f"Code: {fp['code']}", size=12),
                        trailing=ft.Container(
                            content=ft.Text(units[fp["unit_id"]], size=12),
                            bgcolor="#dbeafe",
                            padding=5,
                            border_radius=10
                        ),
                        on_click=lambda e, p=fp: select_product(p),
                        data=fp
                    ) for fp in filtered_products
                ]
            else:
                product_dropdown_container.visible = False

        product_dropdown.update()
        page.update()

    def filter_supplier(e):
        query = e.control.value.lower()
        if not query:
            supplier_dropdown_container.visible = False
        else:
            # Convert SQL to SQLAlchemy
            filtered_suppliers_query = SESSION.query(DB.Supplier).filter(
                or_(
                    DB.Supplier.code.ilike(f"%{query}%"),
                    DB.Supplier.id.ilike(f"%{query}%"),
                    DB.Supplier.name.ilike(f"%{query}%"),
                    DB.Supplier.company_name.ilike(f"%{query}%"),
                    DB.Supplier.email.ilike(f"%{query}%"),
                    DB.Supplier.phone_number.ilike(f"%{query}%"),
                    DB.Supplier.land_line.ilike(f"%{query}%")
                )
            ).limit(5).all()

            filtered_suppliers = [s.__dict__ for s in filtered_suppliers_query]

            if filtered_suppliers:
                supplier_dropdown.controls = [
                    ft.ListTile(
                        title=ft.Text(ss["name"]),
                        subtitle=ft.Text(f"Company: {ss['company_name']}", size=12),
                        trailing=ft.Container(
                            content=ft.Text(ss["phone_number"], size=12),
                            bgcolor="#dbeafe",
                            padding=5,
                            border_radius=10
                        ),
                        on_click=lambda e, s=ss: select_supplier(s),
                        data=ss
                    ) for ss in filtered_suppliers
                ]
            else:
                supplier_dropdown_container.visible = False
        page.update()

    # Product search dropdown
    product_search = ft.TextField(
        label="Product",
        hint_text="Search and select product...",
        prefix_icon=ft.Icons.INVENTORY_2,
        on_change=filter_products,
        border_radius=10,
        border_color="#d1d5db",
        focused_border_color="#3b82f6",
        focused_border_width=2,
        suffix=ft.IconButton(
            icon=ft.Icons.SEARCH,
            icon_size=20,
            icon_color="#9ca3af",
        ),
        expand=True
    )

    product_dropdown = ft.ListView(
        height=200,
        padding=0
    )

    product_dropdown_container = ft.Container(
        content=product_dropdown,
        margin=ft.margin.only(top=5),
        animate=ft.Animation(300, ft.AnimationCurve.EASE_IN_OUT),
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
        visible=False,
    )

    supplier_search = ft.TextField(
        label="Supplier",
        hint_text="Search and select supplier...",
        prefix_icon=ft.Icons.SUPPORT_AGENT,
        on_change=filter_supplier,
        border_radius=10,
        border_color="#d1d5db",
        focused_border_color="#3b82f6",
        focused_border_width=2,
        suffix=ft.IconButton(
            icon=ft.Icons.SEARCH,
            icon_size=20,
            icon_color="#9ca3af"
        ),
        expand=True
    )

    supplier_dropdown = ft.ListView(
        height=200,
        padding=0
    )

    supplier_dropdown_container = ft.Container(
        content=supplier_dropdown,
        margin=ft.margin.only(top=5),
        animate=ft.Animation(300, ft.AnimationCurve.EASE_IN_OUT),
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
        visible=False,
    )

    selected_product_id = ft.TextField(visible=False)
    selected_supplier_id = ft.TextField(visible=False)
    quantity_unit = ft.Text("units", color="#6b7280", size=12)

    # Form fields
    quantity = ft.TextField(
        label="Quantity",
        hint_text="Enter quantity",
        keyboard_type=ft.KeyboardType.NUMBER,
        border_radius=10,
        border_color="#d1d5db",
        focused_border_color="#3b82f6",
        focused_border_width=2,
        suffix=quantity_unit,
        on_change=validate_quantity,

    )

    status = ft.Dropdown(
        label="Status",
        options=[
            ft.dropdown.Option("ACTIVE", "Active"),
            ft.dropdown.Option("INACTIVE", "Inactive"),
            ft.dropdown.Option("RESERVED", "Reserved"),
        ],
        value="ACTIVE",
        border_radius=10,
        border_color="#d1d5db",
        focused_border_color="#3b82f6",
        focused_border_width=2,
        expand=True
    )

    min_price = ft.TextField(
        label="Minimum Sell Price",
        hint_text="0.00",
        keyboard_type=ft.KeyboardType.NUMBER,
        border_radius=10,
        border_color="#d1d5db",
        focused_border_color="#3b82f6",
        focused_border_width=2,
        prefix_text="Rs. ",
        on_change=validate_pricing
    )

    max_price = ft.TextField(
        label="Maximum Sell Price",
        hint_text="0.00",
        keyboard_type=ft.KeyboardType.NUMBER,
        border_radius=10,
        border_color="#d1d5db",
        focused_border_color="#3b82f6",
        focused_border_width=2,
        prefix_text="Rs. ",
        on_change=validate_pricing
    )

    def pay(e):
        try:
            amount = (float(quantity.value if quantity.value else 0)
                      * float(buying_price.value if buying_price.value else 0))

            amount -= (float(cheque_amount.value if cheque_amount.value else 0)
                       + float(card_amount.value if card_amount.value else 0)
                       + float(bank_amount.value if bank_amount.value else 0)
                       + float(discount_amount.value if discount_amount.value else 0)
                       + float(cash_amount.value if cash_amount.value else 0)
                       )

            credit_amount.value = round(amount, 2)
            if e:
                if e.control.prefix_text == "Rs. " and not float(credit_amount.value):
                    credit_amount.border_color = ft.Colors.GREEN,
                    credit_amount.color = ft.Colors.GREEN
                else:
                    credit_amount.border_color = "#d1d5db",
                    credit_amount.color = "#d1d5db"

            if bank_amount.value and not bank_transaction_id.value:
                bank_transaction_id.error_text = "Enter the bank transaction ID"
            else:
                bank_transaction_id.error_text = None

            if cheque_amount.value:
                if cheque_number.suffix_text == "date":
                    cheque_number.error_text = "Enter the cheque date"
                else:
                    cheque_number.error_text = None

                if not cheque_number.value:
                    cheque_number.error_text = "Enter the cheque number"
                elif cheque_number.suffix_text != "date":
                    cheque_number.error_text = None
            else:
                cheque_number.error_text = None

            if card_amount.value and not card_transaction_id.value:
                card_transaction_id.error_text = "Enter the card transaction ID"
            else:
                card_transaction_id.error_text = None

            page.update()
        except ValueError as e:
            print(e)

    buying_price = ft.TextField(
        label="Buying Price",
        hint_text="0.00",
        keyboard_type=ft.KeyboardType.NUMBER,
        border_radius=10,
        border_color="#d1d5db",
        focused_border_color="#3b82f6",
        focused_border_width=2,
        prefix_text="Rs. ",
        on_change=pay
    )

    def select_date(e):
        cheque_number.suffix_text = e.control.value.strftime('%Y-%m-%d')
        pay(None)
        page.update()

    def date_picker(e):
        page.open(
            ft.DatePicker(
                first_date=datetime.now(),
                on_change=select_date,
            )
        )

    cash_amount = ft.TextField(
        label="Cash",
        hint_text="0.00",
        keyboard_type=ft.KeyboardType.NUMBER,
        border_radius=10,
        border_color="#d1d5db",
        focused_border_color="#3b82f6",
        focused_border_width=2,
        prefix_text="Rs. ",
        on_change=pay
    )

    card_amount = ft.TextField(
        label="Card",
        hint_text="0.00",
        keyboard_type=ft.KeyboardType.NUMBER,
        border_radius=10,
        border_color="#d1d5db",
        focused_border_color="#3b82f6",
        focused_border_width=2,
        prefix_text="Rs. ",
        on_change=pay,
        expand=True
    )

    bank_amount = ft.TextField(
        label="Bank",
        hint_text="0.00",
        keyboard_type=ft.KeyboardType.NUMBER,
        border_radius=10,
        border_color="#d1d5db",
        focused_border_color="#3b82f6",
        focused_border_width=2,
        prefix_text="Rs. ",
        on_change=pay,
        expand=True
    )

    card_transaction_id = ft.TextField(
        label="Transaction ID",
        hint_text="Transaction Number",
        prefix_icon=ft.Icons.CREDIT_CARD,
        border_radius=10,
        border_color="#d1d5db",
        focused_border_color="#3b82f6",
        focused_border_width=2,
        expand=True,
        on_change=pay
    )

    cheque_number = ft.TextField(
        label="Cheque Number",
        hint_text="Cheque Number",
        prefix_icon=ft.Icons.MONEY,
        border_radius=10,
        border_color="#d1d5db",
        focused_border_color="#3b82f6",
        focused_border_width=2,
        suffix_text="date",
        on_change=pay,
        expand=True
    )

    cheque_date = ft.IconButton(
        icon=ft.Icons.CALENDAR_MONTH,
        on_click=date_picker,
    )

    cheque_amount = ft.TextField(
        label="Cheque Amount",
        prefix_text="Rs. ",
        hint_text="0.00",
        border_radius=10,
        border_color="#d1d5db",
        focused_border_color="#3b82f6",
        focused_border_width=2,
        on_change=pay,
        expand=True
    )

    cheque_area = ft.Row(
        [
            cheque_number,
            cheque_date,
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        expand=True
    )

    bank_transaction_id = ft.TextField(
        label="Bank Transaction ID",
        hint_text="Bank Transaction Number",
        prefix_icon=ft.Icons.BUSINESS,
        border_radius=10,
        border_color="#d1d5db",
        focused_border_color="#3b82f6",
        focused_border_width=2,
        expand=True,
        on_change=pay
    )

    credit_amount = ft.TextField(
        label="Credit Amount",
        prefix_text="Rs. ",
        hint_text="0.00",
        border_radius=10,
        border_color="#d1d5db",
        focused_border_color="#3b82f6",
        focused_border_width=2,
        read_only=True,
    )

    def handle_change(e):
        expire_date.value = e.control.value.strftime('%Y-%m-%d')
        expire_date.on_focus = False
        page.update()

    def date_picker(e):
        page.open(
            ft.DatePicker(
                first_date=datetime.now(),
                on_change=handle_change,
                help_text="Cheque Date"
            )
        ),

    expire_date = ft.TextField(
        label="Expire Date",
        keyboard_type=ft.KeyboardType.DATETIME,
        border_radius=10,
        border_color="#d1d5db",
        focused_border_color="#3b82f6",
        focused_border_width=2,
        disabled=True,
        on_focus=lambda e: date_picker(e),
        on_click=lambda e: date_picker(e),
    )

    expire_info = ft.Text(
        "Select a product first to determine if expiry date is required",
        color="#6b7280",
        size=12
    )

    discount_amount = ft.TextField(
        label="Discount Amount",
        prefix_text="Rs. ",
        hint_text="0.00",
        border_radius=10,
        border_color="#d1d5db",
        focused_border_color="#3b82f6",
        focused_border_width=2,
        on_change=pay,

    )

    # Active stock container
    active_stock_container = ft.Column(
        controls=[
            ft.Row(
                [
                    ft.Container(
                        ft.Column(
                            controls=[
                                ft.Icon(ft.Icons.INVENTORY_2, size=48, color="#9ca3af"),
                                ft.Text("Select a product to view active stock", color="#6b7280")
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            alignment=ft.MainAxisAlignment.CENTER,
                            height=200,
                        ),
                        expand=True
                    )
                ],
                expand=True,
            )
        ],
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )

    def select_product(product):
        global selected_product, selected_stocks

        selected_product = product

        # Convert SQL to SQLAlchemy
        stock_query = SESSION.query(DB.Stock).filter(DB.Stock.product_id == selected_product['id']).all()

        # Convert to list of dictionaries
        stock_list = []
        for stock in stock_query:
            stock_dict = {c.name: getattr(stock, c.name) for c in stock.__table__.columns}
            stock_list.append(stock_dict)

        # Create DataFrame for easier manipulation
        stock = pd.DataFrame(stock_list)
        if not stock.empty:
            stock.drop(columns="product_id", inplace=True, errors='ignore')

        temp = stock["status"].copy() if not stock.empty else pd.Series()

        # Update status for expired items
        if not stock.empty and 'expire_date' in stock.columns:
            stock["status"] = [
                ("Expired" if date and date < datetime.now().date() else status_val)
                for date, status_val in zip(stock["expire_date"], stock["status"])
            ]

            # Update database for expired items
            for i, (old_status, new_status) in enumerate(zip(temp, stock["status"])):
                if old_status != new_status and new_status == "Expired":
                    SESSION.execute(
                        update(DB.Stock)
                        .where(DB.Stock.id == stock['id'].iloc[i])
                        .values(status='Expired')
                    )
            SESSION.commit()

        selected_stocks = stock.to_dict("records") if not stock.empty else []

        product_search.value = product["title"]
        selected_product_id.value = product["id"]
        quantity_unit.value = units[product["unit_id"]]

        # Handle expire date
        if product["has_expire"]:
            expire_date.disabled = False
            expire_info.value = "This product requires an expiry date"
        else:
            expire_date.disabled = True
            expire_date.value = ""
            expire_info.value = "This product does not require an expiry date"

        product_dropdown_container.visible = False
        load_active_stock(product["id"])
        page.update()

    def select_supplier(supplier):
        global selected_supplier
        selected_supplier = supplier

        supplier_search.value = supplier["name"]
        selected_supplier_id.value = supplier["id"]

        supplier_dropdown_container.visible = False
        page.update()

    def load_active_stock(product_id):
        if not selected_stocks:
            active_stock_container.controls = [
                ft.Column(
                    controls=[
                        ft.Icon(ft.Icons.INBOX, size=48, color="#9ca3af"),
                        ft.Text("No active stock for this product", color="#6b7280")
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                    height=200
                )
            ]
        else:
            active_stock_container.controls = [
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text(f"Stock #{stock['id']}", weight=ft.FontWeight.BOLD),
                                    ft.Container(
                                        content=ft.Text(
                                            stock["status"],
                                            size=12,
                                            color=ft.Colors.WHITE if "expired" == stock[
                                                "status"].lower() else ft.Colors.BLACK),
                                        bgcolor=ft.Colors.RED if "expired" == stock["status"].lower() else "#d1fae5",
                                        padding=ft.padding.symmetric(horizontal=8, vertical=3),
                                        border_radius=10
                                    )
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                            ),
                            ft.Column(
                                controls=[
                                    ft.Row(
                                        controls=[
                                            ft.Text("Stock In:", color="#6b7280", size=12),
                                            ft.Text(f"{stock['stock_in']} {units[selected_product['unit_id']]}",
                                                    weight=ft.FontWeight.BOLD, size=12)
                                        ],
                                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                                    ),
                                    ft.Row(
                                        controls=[
                                            ft.Text("Stock Out:", color="#6b7280", size=12),
                                            ft.Text(f"{stock['stock_out']} {units[selected_product['unit_id']]}",
                                                    weight=ft.FontWeight.BOLD, size=12)
                                        ],
                                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                                    ),
                                    ft.Row(
                                        controls=[
                                            ft.Text("Current Stock:", color="#6b7280", size=12),
                                            ft.Text(f"{stock['current_stock']} {units[selected_product['unit_id']]}",
                                                    weight=ft.FontWeight.BOLD, size=12)
                                        ],
                                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                                    ),
                                    ft.Row(
                                        controls=[
                                            ft.Text("Return Stock:", color=ft.Colors.RED, size=12),
                                            ft.Text(f"{stock['return_stock']} {units[selected_product['unit_id']]}",
                                                    weight=ft.FontWeight.BOLD, size=12, color=ft.Colors.RED)
                                        ],
                                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                                    ),
                                    ft.Row(
                                        controls=[
                                            ft.Text("Price Range:", color="#6b7280", size=12),
                                            ft.Text(f"Rs. {stock['min_selling_price']} - Rs. {stock['selling_price']}",
                                                    weight=ft.FontWeight.BOLD, size=12)
                                        ],
                                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                                    ),
                                    ft.Row(
                                        controls=[
                                            ft.Text("Buying Price:", color="#6b7280", size=12),
                                            ft.Text(f"Rs. {stock['actual_price']}",
                                                    weight=ft.FontWeight.BOLD, size=12)
                                        ],
                                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                        visible=bool(stock.get("actual_price"))
                                    ),
                                    ft.Row(
                                        controls=[
                                            ft.Text("Expires:", color="#6b7280", size=12),
                                            ft.Row(
                                                [
                                                    ft.Text(
                                                        stock["expire_date"],
                                                        weight=ft.FontWeight.BOLD,
                                                        size=12,
                                                        color=ft.Colors.RED if stock[
                                                                                   "status"].lower() == "expired" else "orange"
                                                    )
                                                ]
                                            )
                                        ],
                                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                        visible=bool(stock.get("expire_date"))
                                    ),
                                ],
                                spacing=5
                            )
                        ],
                        spacing=10,
                    ),
                    padding=10,
                    bgcolor="#f9fafb",
                    border_radius=10,
                    border=ft.border.only(left=ft.border.BorderSide(4, ft.Colors.RED if stock[
                                                                                            "status"].lower() == "expired" else ft.Colors.GREEN)),
                ) for stock in selected_stocks
            ]

            active_stock_container.update()

    def reset_form(e):
        global selected_product
        product_search.value = ""
        selected_product_id.value = ""
        quantity.value = ""
        min_price.value = ""
        max_price.value = ""
        buying_price.value = ""
        expire_date.value = ""
        expire_date.disabled = True
        quantity_unit.value = "units"
        product_dropdown_container.visible = False
        cheque_number.value = ""
        cheque_amount.value = ""
        cash_amount.value = ""
        card_amount.value = ""
        card_transaction_id.value = ""
        bank_amount.value = ""
        bank_transaction_id.value = ""
        discount_amount.value = ""
        pay(None)

        # Reset active stock display
        active_stock_container.controls = [
            ft.Row(
                [
                    ft.Container(
                        ft.Column(
                            controls=[
                                ft.Icon(ft.Icons.INVENTORY_2, size=48, color="#9ca3af"),
                                ft.Text("Select a product to view active stock", color="#6b7280")
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            alignment=ft.MainAxisAlignment.CENTER,
                            height=200,
                        ),
                        expand=True
                    )
                ],
                expand=True,
            )
        ]

        selected_product = dict()
        page.update()

    def alert(txt, clr=ft.Colors.WHITE, bg_clr=ft.Colors.RED):
        page.open(
            ft.SnackBar(
                ft.Text(
                    txt,
                    color=clr
                ),
                open=True,
                bgcolor=bg_clr
            )
        )
        page.update()

    def submit_form(e):
        global selected_product
        if not selected_product:
            alert("Please select a product")
            print("not selected")
            return

        if not supplier_search.value:
            alert("Please select the supplier")
            print("not selected")
            return

        if quantity.error_text or max_price.error_text or quantity.error_text or cheque_number.error_text or card_transaction_id.error_text or bank_transaction_id.error_text:
            alert("Please fix the errors in the form")
            print("errors")
            return

        form_data = {
            "stock_in": quantity.value,
            "current_stock": quantity.value,
            "product_id": selected_product['id'],
            "actual_price": buying_price.value,
            "min_selling_price": min_price.value,
            "selling_price": max_price.value,
            "expire_date": expire_date.value,
            "status": status.value
        }

        product_dropdown_container.visible = False

        # Create new stock using SQLAlchemy
        new_stock = DB.Stock(
            stock_in=form_data["stock_in"],
            current_stock=form_data["current_stock"],
            product_id=form_data["product_id"],
            actual_price=form_data["actual_price"],
            min_selling_price=form_data["min_selling_price"],
            selling_price=form_data["selling_price"],
            status=form_data["status"]
        )

        SESSION.add(new_stock)
        SESSION.commit()

        if selected_product["has_expire"]:
            # Update the expire date for the newly created stock
            new_stock.expire_date = form_data["expire_date"]
            SESSION.commit()

        # Show success message
        alert_dialog = ft.AlertDialog(
            title=ft.Text("Success!"),
            content=ft.Text(f"Stock added successfully for {selected_product['title']}"),
            actions=[ft.OutlinedButton(text="OK", on_click=lambda e: page.close(alert_dialog))]
        )

        page.open(alert_dialog)
        page.update()

        # Reset form after submission
        reset_form(e)

    submit_btn = ft.ElevatedButton(
        text="Add Stock",
        icon=ft.Icons.ADD,
        on_click=submit_form,
        expand=True,
        height=50,
        bgcolor=ft.Colors.BLUE,
        color=ft.Colors.WHITE,
    )

    # Main layout
    main_content = ft.Column(
        controls=[
            header,
            ft.Container(
                ft.ResponsiveRow(
                    controls=[
                        # Form column
                        ft.Container(
                            ft.Column(
                                controls=[
                                    ft.Container(
                                        content=ft.Column(
                                            controls=[
                                                ft.Column(
                                                    controls=[
                                                        ft.Row(
                                                            controls=[
                                                                ft.Icon(ft.Icons.ADD_CIRCLE,
                                                                        color="#3b82f6"),
                                                                ft.Text("Stock Information", size=20,
                                                                        weight=ft.FontWeight.BOLD)
                                                            ],
                                                        ),
                                                        ft.Container(
                                                            height=1,
                                                            expand=True,
                                                            bgcolor=ft.Colors.GREY
                                                        )
                                                    ],
                                                    expand=True,
                                                ),
                                                ft.Column(
                                                    controls=[
                                                        # Product selection
                                                        ft.ResponsiveRow(
                                                            controls=[
                                                                ft.Column(
                                                                    controls=[
                                                                        product_search,
                                                                        product_dropdown_container,
                                                                        selected_product_id
                                                                    ],
                                                                    spacing=5,
                                                                    col={"sm": 12, "md": 6}
                                                                ),
                                                                ft.Column(
                                                                    controls=[
                                                                        supplier_search,
                                                                        supplier_dropdown_container,
                                                                        selected_supplier_id
                                                                    ],
                                                                    spacing=5,
                                                                    col={"sm": 12, "md": 6}
                                                                )
                                                            ]
                                                        ),
                                                        # Quantity and Status
                                                        ft.ResponsiveRow(
                                                            controls=[
                                                                ft.Column(
                                                                    col={"sm": 12, "md": 6},
                                                                    controls=[
                                                                        quantity,
                                                                    ]
                                                                ),
                                                                ft.Column(
                                                                    col={"sm": 12, "md": 6},
                                                                    controls=[
                                                                        ft.Column(
                                                                            controls=[
                                                                                expire_date,
                                                                                expire_info
                                                                            ],
                                                                            spacing=3
                                                                        )
                                                                    ]
                                                                )
                                                            ],
                                                            spacing=10
                                                        ),
                                                        # Pricing
                                                        ft.ResponsiveRow(
                                                            controls=[
                                                                ft.Column(
                                                                    col={"sm": 12, "md": 4},
                                                                    controls=[
                                                                        min_price
                                                                    ]
                                                                ),
                                                                ft.Column(
                                                                    col={"sm": 12, "md": 4},
                                                                    controls=[
                                                                        max_price
                                                                    ]
                                                                ),
                                                                ft.Column(
                                                                    col={"sm": 12, "md": 4},
                                                                    controls=[
                                                                        buying_price
                                                                    ]
                                                                )
                                                            ],
                                                            spacing=10
                                                        ),
                                                        ft.Row(
                                                            [
                                                                ft.Container(
                                                                    ft.Column(
                                                                        controls=[
                                                                            ft.Row(
                                                                                controls=[
                                                                                    ft.Icon(ft.Icons.PAYMENT,
                                                                                            color="#3b82f6"),
                                                                                    ft.Text("Payment", size=20,
                                                                                            weight=ft.FontWeight.BOLD)
                                                                                ],
                                                                            ),
                                                                            ft.Container(
                                                                                height=1,
                                                                                expand=True,
                                                                                bgcolor=ft.Colors.GREY
                                                                            )
                                                                        ],
                                                                        expand=True,
                                                                    ),
                                                                    margin=ft.margin.only(0, 10, 0, 0),
                                                                    expand=True,
                                                                ),
                                                            ],
                                                            expand=True,
                                                        ),
                                                        # payment options
                                                        ft.ResponsiveRow(
                                                            controls=[
                                                                ft.Column(
                                                                    col={"sm": 12, "md": 4},
                                                                    controls=[
                                                                        cheque_amount,
                                                                        cheque_area
                                                                    ],
                                                                ),
                                                                ft.Column(
                                                                    col={"sm": 12, "md": 4},
                                                                    controls=[
                                                                        card_amount,
                                                                        card_transaction_id
                                                                    ]
                                                                ),
                                                                ft.Column(
                                                                    col={"sm": 12, "md": 4},
                                                                    controls=[
                                                                        bank_amount,
                                                                        bank_transaction_id
                                                                    ]
                                                                )
                                                            ]
                                                        ),
                                                        ft.ResponsiveRow(
                                                            [
                                                                ft.Column(
                                                                    col={"sm": 12, "md": 4},
                                                                    controls=[
                                                                        discount_amount
                                                                    ]
                                                                ),
                                                                ft.Column(
                                                                    col={"sm": 12, "md": 4},
                                                                    controls=[
                                                                        cash_amount,
                                                                    ]
                                                                ),
                                                                ft.Column(
                                                                    col={"sm": 12, "md": 4},
                                                                    controls=[
                                                                        credit_amount,
                                                                    ]
                                                                )
                                                            ],
                                                            alignment=ft.MainAxisAlignment.CENTER,
                                                        ),
                                                        # Buttons
                                                        ft.Row(
                                                            controls=[
                                                                ft.OutlinedButton(
                                                                    text="Reset",
                                                                    icon=ft.Icons.REFRESH,
                                                                    on_click=reset_form,
                                                                    expand=True,
                                                                    height=50,
                                                                ),
                                                                submit_btn
                                                            ],
                                                            spacing=10
                                                        )
                                                    ],
                                                    spacing=20
                                                )
                                            ],
                                            spacing=20
                                        ),
                                        padding=20,
                                        bgcolor=ft.Colors.WHITE,
                                        border_radius=15,
                                        shadow=ft.BoxShadow(
                                            spread_radius=0.81,
                                            blur_radius=3,
                                            color=ft.Colors.BLACK12,
                                            offset=ft.Offset(1, 1),
                                            blur_style=ft.ShadowBlurStyle.NORMAL,
                                        )
                                    ),
                                ],
                                spacing=20
                            ),
                            col={"sm": 12, "md": 8},
                        ),
                        # Active stock column
                        ft.Container(
                            ft.Column(
                                controls=[
                                    ft.Container(
                                        content=ft.Column(
                                            controls=[
                                                ft.Row(
                                                    controls=[
                                                        ft.Icon(ft.Icons.LIST, color="#10b981"),
                                                        ft.Text("Active Stock", size=20, weight=ft.FontWeight.BOLD)
                                                    ],
                                                    spacing=10
                                                ),
                                                ft.Container(
                                                    ft.Column(
                                                        [
                                                            active_stock_container
                                                        ],
                                                        expand=True,
                                                    ),
                                                    expand=True,
                                                    bgcolor=ft.Colors.WHITE,
                                                )
                                            ],
                                            spacing=20
                                        ),
                                        padding=20,
                                        shadow=ft.BoxShadow(
                                            spread_radius=0.81,
                                            blur_radius=3,
                                            color=ft.Colors.BLACK12,
                                            offset=ft.Offset(1, 1),
                                            blur_style=ft.ShadowBlurStyle.NORMAL,
                                        ),
                                        border_radius=15,
                                        bgcolor=ft.Colors.WHITE,
                                        expand=True
                                    )
                                ],
                                spacing=20,
                                expand=True
                            ),
                            col={"sm": 12, "md": 4},
                            expand=True
                        )
                    ],
                    spacing=20,
                    expand=True,
                ),
                expand=True
            )
        ],
        spacing=20,
        expand=True,
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
    )

    # Page layout
    return ft.Container(
        content=main_content,
        expand=True
    )