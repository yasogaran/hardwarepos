import decimal
import time

import flet as ft
from datetime import datetime
import pandas as pd
from sqlalchemy import update, create_engine, insert, select, or_, func
from sqlalchemy.orm import Session
import DB

SESSION: Session
CONN: create_engine
USER_ID: int
ACCOUNT_ID: int = 1

currency = "Rs. "

grn_tab = None

bill_tabs = ft.Tabs(
    animation_duration=300,
    expand_loose=True,
    adaptive=True
)

suppliers = dict()

units = dict()

selected_product = dict()
selected_supplier = dict()
filtered_products = dict()
selected_stocks = dict()


class Bill:
    bills = []

    def __init__(self, page):
        self.page = page
        self.head_text = ft.TextStyle(
            weight=ft.FontWeight.BOLD,
            size=24,
        )

        self.body_text = ft.TextStyle(
            size=18,
        )

        self.supplier_id = None

        self.total_items = ft.Text(
            "0 Item(s)",
            size=16
        )

        self.data = dict()
        self.dummy_data = dict()
        self.grandTotal = dict()

        self.grand_total = ft.Text(
            currency + "0.0",
            weight=ft.FontWeight.BOLD,
            size=22,
        )

        self.proceed_to_payment = ft.OutlinedButton(
            content=ft.Text(
                "Proceed to Payment",
                weight=ft.FontWeight.BOLD,
                size=18,
            ),
            expand=True,
            height=50,
            style=ft.ButtonStyle(
                color=ft.Colors.GREY,
            ),
            on_click=self.load_bill,
            disabled=True,
        )

        self.delete_btn = ft.IconButton(
            ft.Icons.DELETE,
            on_click=self.delete_bill,
        )

        self.back_to_bill = ft.IconButton(
            ft.Icons.ARROW_BACK,
            on_click=self.back
        )

        self.bill_table = ft.DataTable(
            column_spacing=0,
            sort_column_index=1,
            columns=[
                ft.DataColumn(
                    ft.Text("Product Name"),
                    heading_row_alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.DataColumn(
                    ft.Text("Qty"),
                    heading_row_alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.DataColumn(
                    ft.Text("Exp Date"),
                    heading_row_alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.DataColumn(
                    ft.Text("Cost"),
                    heading_row_alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.DataColumn(
                    ft.Text("min rate"),
                    heading_row_alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.DataColumn(
                    ft.Text("sell rate"),
                    heading_row_alignment=ft.MainAxisAlignment.CENTER,
                )
            ],
            heading_row_height=0,
            expand=True,
        )

        self.dummy_table = ft.DataTable(
            column_spacing=0,
            sort_column_index=1,
            columns=[
                ft.DataColumn(
                    ft.Text("Product Name"),
                    heading_row_alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.DataColumn(
                    ft.Text("Qty"),
                    heading_row_alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.DataColumn(
                    ft.Text("Exp Date"),
                    heading_row_alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.DataColumn(
                    ft.Text("Cost"),
                    heading_row_alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.DataColumn(
                    ft.Text("min rate"),
                    heading_row_alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.DataColumn(
                    ft.Text("sell rate"),
                    heading_row_alignment=ft.MainAxisAlignment.CENTER,
                )
            ],
            data_row_max_height=0,
            data_row_min_height=0,
            expand=True,
        )

        self.total_amount = ft.Text(
            value=str(round(sum(self.grandTotal.values()), 2)),
            style=self.body_text
        )

        self.supplier_name = ft.TextField(
            label="Supplier Name",
            hint_text="Search and select supplier...",
            prefix_icon=ft.Icons.PERSON,
            on_change=self.filter_supplier,
            border_radius=10,
            border_color="#d1d5db",
            focused_border_color="#3b82f6",
            focused_border_width=2,
            expand=True
        )

        self.supplier_dropdown = ft.ListView(
            height=200,
            visible=False,
            padding=0
        )

        self.supplier_dropdown_container = ft.Container(
            content=self.supplier_dropdown,
            animate=ft.Animation(300, "easeInOut"),
            clip_behavior=ft.ClipBehavior.HARD_EDGE
        )

        self.company = ft.TextField(
            label="Company Name",
            hint_text="Company",
            prefix_icon=ft.Icons.BUSINESS,
            border_radius=10,
            border_color="#d1d5db",
            focused_border_color="#3b82f6",
            focused_border_width=2,
            expand=True,
            error_style=ft.TextStyle(
                color=ft.Colors.RED,
            ),
        )

        def select_date(e):
            self.cheque_number.suffix_text = e.control.value.strftime('%Y-%m-%d')
            self.pay(None)
            page.update()

        def date_picker(e):
            page.open(
                ft.DatePicker(
                    first_date=datetime.now(),
                    on_change=select_date,
                )
            )

        self.cash_amount = ft.TextField(
            label="Cash",
            hint_text="0.00",
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=10,
            border_color="#d1d5db",
            focused_border_color="#3b82f6",
            focused_border_width=2,
            prefix_text="Rs. ",
            on_change=self.pay,
            col={"sm": 6}
        )

        self.card_amount = ft.TextField(
            label="Card",
            hint_text="0.00",
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=10,
            border_color="#d1d5db",
            focused_border_color="#3b82f6",
            focused_border_width=2,
            prefix_text="Rs. ",
            on_change=self.pay,
            expand=True
        )

        self.bank_amount = ft.TextField(
            label="Bank",
            hint_text="0.00",
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=10,
            border_color="#d1d5db",
            focused_border_color="#3b82f6",
            focused_border_width=2,
            prefix_text="Rs. ",
            on_change=self.pay,
            expand=True
        )

        self.card_transaction_id = ft.TextField(
            label="Transaction ID",
            hint_text="Transaction Number",
            prefix_icon=ft.Icons.CREDIT_CARD,
            border_radius=10,
            border_color="#d1d5db",
            focused_border_color="#3b82f6",
            focused_border_width=2,
            expand=True,
            on_change=self.pay
        )

        self.cheque_number = ft.TextField(
            label="Cheque Number",
            hint_text="Cheque Number",
            prefix_icon=ft.Icons.MONEY,
            border_radius=10,
            border_color="#d1d5db",
            focused_border_color="#3b82f6",
            focused_border_width=2,
            suffix_text="date",
            on_change=self.pay,
            expand=True
        )

        self.cheque_date = ft.IconButton(
            icon=ft.Icons.CALENDAR_MONTH,
            on_click=date_picker,
        )

        self.cheque_amount = ft.TextField(
            label="Cheque Amount",
            prefix_text="Rs. ",
            hint_text="0.00",
            border_radius=10,
            border_color="#d1d5db",
            focused_border_color="#3b82f6",
            focused_border_width=2,
            on_change=self.pay,
            expand=True
        )

        self.cheque_area = ft.Row(
            [
                self.cheque_number,
                self.cheque_date,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            expand=True
        )

        self.bank_transaction_id = ft.TextField(
            label="Bank Transaction ID",
            hint_text="Bank Transaction Number",
            prefix_icon=ft.Icons.BUSINESS,
            border_radius=10,
            border_color="#d1d5db",
            focused_border_color="#3b82f6",
            focused_border_width=2,
            expand=True,
            on_change=self.pay
        )

        self.credit_amount = ft.TextField(
            label="Credit Amount",
            prefix_text="Rs. ",
            hint_text="0.00",
            border_radius=10,
            border_color="#d1d5db",
            focused_border_color="#3b82f6",
            focused_border_width=2,
            read_only=True,
            col={"sm": 6}
        )

        self.discount_amount = ft.TextField(
            hint_text="0.0",
            prefix_text=currency,
            on_change=self.discount,
            content_padding=0,
            border=ft.InputBorder.UNDERLINE,
            text_align=ft.TextAlign.RIGHT,
            adaptive=True,
            width=50,
            text_style=self.body_text,
            input_filter=ft.InputFilter(
                regex_string=r"\d",
                replacement_string="-",
                allow=True
            )
        )

        self.amount_to_be_paid = ft.Text(
            value=currency + str(round(sum(self.grandTotal.values()), 2)),
            style=self.body_text
        )

        self.payment_area_r1 = ft.Container(
            ft.Column(
                [
                    ft.Text(
                        "supplier details".upper(),
                        style=self.head_text,
                    ),
                    self.supplier_name,
                    self.supplier_dropdown_container,
                    self.company
                ]
            )
        )

        self.cheque_payment = ft.Container(
            ft.Column(
                [
                    self.cheque_amount,
                    self.cheque_area
                ]
            ),
            col={"sm": 6, "lg": 4}
        )

        self.card_payment = ft.Container(
            ft.Column(
                [
                    self.card_amount,
                    self.card_transaction_id
                ]
            ),
            col={"sm": 6, "lg": 4}
        )

        self.bank_payment = ft.Container(
            ft.Column(
                [
                    self.bank_amount,
                    self.bank_transaction_id
                ]
            ),
            col={"sm": 6, "lg": 4}
        )

        self.payment_area_r5 = ft.Container(
            ft.ResponsiveRow(
                [
                    self.cash_amount,
                    self.credit_amount
                ]
            )
        )

        self.payment_area_r3 = ft.ResponsiveRow(
            [
                ft.Text(
                    "payment".upper(),
                    style=self.head_text,
                ),
                self.cheque_payment,
                self.card_payment,
                self.bank_payment,
            ]
        )

        self.payment_area_r4 = ft.Row(
            [
                self.cash_amount,
                self.credit_amount
            ]
        )

        self.payment_area = ft.Container(
            ft.Column(
                [
                    ft.Container(
                        ft.Column(
                            [
                                self.payment_area_r1,
                                ft.Container(
                                    ft.Column(
                                        [
                                            ft.Text(
                                                "Bill".upper(),
                                                style=self.head_text,
                                            ),
                                            ft.Column(
                                                [
                                                    self.total_items,
                                                    ft.Row(
                                                        [
                                                            ft.Text(
                                                                "Total Amount".upper(),
                                                                style=self.body_text,
                                                            ),
                                                            self.total_amount
                                                        ],
                                                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                                    ),
                                                    ft.Row(
                                                        [
                                                            ft.Text(
                                                                "Discount".upper(),
                                                                style=self.body_text,
                                                            ),
                                                            self.discount_amount
                                                        ],
                                                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                                    ),
                                                    ft.Row(
                                                        [
                                                            ft.Text(
                                                                "Total".upper(),
                                                                style=self.body_text,
                                                            ),
                                                            self.amount_to_be_paid
                                                        ],
                                                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                                    ),
                                                ],
                                                spacing=0
                                            ),
                                        ],
                                        spacing=5
                                    )
                                ),
                                self.payment_area_r3,
                                self.payment_area_r4
                            ],
                            spacing=20
                        ),
                        bgcolor=ft.Colors.WHITE,
                        shadow=ft.BoxShadow(
                            spread_radius=0.81,
                            blur_radius=3,
                            color=ft.Colors.BLACK12,
                            offset=ft.Offset(1, 1),
                            blur_style=ft.ShadowBlurStyle.NORMAL,
                        ),
                        padding=10,
                        border_radius=15,
                    ),
                    ft.Container(
                        ft.Row(
                            [
                                self.back_to_bill,
                                ft.ElevatedButton(
                                    content=ft.Text(
                                        "Print Bill",
                                        weight=ft.FontWeight.BOLD,
                                        size=18,
                                    ),
                                    expand=True,
                                    height=50,
                                    bgcolor=ft.Colors.GREEN,
                                    color=ft.Colors.WHITE,
                                    on_click=self.print_bill,
                                ),
                                self.delete_btn
                            ]
                        ),
                        bgcolor=ft.Colors.WHITE,
                        shadow=ft.BoxShadow(
                            spread_radius=0.81,
                            blur_radius=3,
                            color=ft.Colors.BLACK12,
                            offset=ft.Offset(1, 1),
                            blur_style=ft.ShadowBlurStyle.NORMAL,
                        ),
                        padding=10,
                        border_radius=15,
                    )
                ],
                scroll=ft.ScrollMode.AUTO
            )
        )

        self.bill_box = ft.Column(
            [
                ft.Container(
                    ft.Row(
                        [
                            self.bill_table
                        ]
                    )
                )
            ],
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        )

        self.bill_area = ft.Container(
            ft.Column(
                [
                    ft.Container(
                        ft.Row(
                            [
                                ft.Container(
                                    ft.Column(
                                        [
                                            ft.Row(
                                                [
                                                    self.dummy_table
                                                ]
                                            ),
                                            self.bill_box
                                        ],
                                        spacing=0
                                    ),
                                    expand=True,
                                )
                            ],
                            expand=True,
                        ),
                        bgcolor=ft.Colors.WHITE,
                        shadow=ft.BoxShadow(
                            spread_radius=0.81,
                            blur_radius=3,
                            color=ft.Colors.BLACK12,
                            offset=ft.Offset(1, 1),
                            blur_style=ft.ShadowBlurStyle.NORMAL,
                        ),
                        padding=10,
                        border_radius=15,
                        expand=True,
                    ),
                    ft.Container(
                        ft.Column(
                            [
                                ft.Container(
                                    ft.Row(
                                        [
                                            self.total_items,
                                            ft.Container(
                                                self.grand_total,
                                                bgcolor=ft.Colors.GREEN,
                                                border_radius=20,
                                                padding=8
                                            )
                                        ],
                                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                    )
                                ),
                                ft.Container(
                                    ft.Row(
                                        [
                                            self.proceed_to_payment,
                                            self.delete_btn
                                        ]
                                    )
                                )
                            ]
                        ),
                        bgcolor=ft.Colors.WHITE,
                        shadow=ft.BoxShadow(
                            spread_radius=0.81,
                            blur_radius=3,
                            color=ft.Colors.BLACK12,
                            offset=ft.Offset(1, 1),
                            blur_style=ft.ShadowBlurStyle.NORMAL,
                        ),
                        padding=10,
                        border_radius=15,
                    ),
                ],
                expand=True,
            ),
            padding=5,
        )
        self.bills.append(self)

    def discount(self, e):
        self.discount_amount.width = (len(e.control.value) + 3) * 11

        try:
            self.amount_to_be_paid.value = currency + str(round(float(self.total_amount.value.split(" ")[1]) - float(
                self.discount_amount.value if e.control.value else "0.0"), 2))
        except:
            self.amount_to_be_paid.value = currency + str(round(float(self.total_amount.value.split(" ")[1]), 2))

        self.credit_amount.value = str(round(float(self.amount_to_be_paid.value.split(" ")[1]), 2))
        self.pay(None)
        self.page.update()

    def pay(self, e):
        amount = float(self.total_amount.value.split(" ")[1])

        amount -= (float(self.cheque_amount.value if self.cheque_amount.value else "0.0")
                   + float(self.bank_amount.value if self.bank_amount.value else "0.0")
                   + float(self.card_amount.value if self.card_amount.value else "0.0")
                   + float(self.discount_amount.value if self.discount_amount.value else "0.0")
                   + float(self.cash_amount.value if self.cash_amount.value else "0.0"))

        self.credit_amount.value = round(amount, 2)

        if self.credit_amount.value:
            self.credit_amount.border_color = ft.Colors.RED
        else:
            self.credit_amount.border_color = ft.Colors.BLUE

        self.page.update()

    def print_bill(self, e):
        # Convert to SQLAlchemy
        new_supplier = DB.Supplier(
            name=self.supplier_name.value,
            company_name=self.company.value,
        )
        SESSION.add(new_supplier)
        SESSION.commit()

        time.sleep(0.1)

        # Convert to SQLAlchemy
        new_grn = DB.GRN(
            total_amount=decimal.Decimal(float(self.amount_to_be_paid.value.split(" ")[1])),
            discount_amount=decimal.Decimal(float(self.discount_amount.value if self.discount_amount.value else "0.0")),
            paid_amount=decimal.Decimal(float(self.total_amount.value.split(' ')[1]) - float(self.credit_amount.value)),
            status='paid' if float(self.credit_amount.value) < 1 else 'pending',
            supplier_id=self.supplier_id,
            user_id=USER_ID
        )
        SESSION.add(new_grn)
        SESSION.commit()

        # Convert to SQLAlchemy
        grnId = SESSION.query(func.max(DB.GRN.id)).scalar()


        expenses = DB.ExpenseTracker(
            description=f"GRN #{grnId} - {self.supplier_name.value}",
            outcome=float(self.total_amount.value.split(" ")[1])
        )

        SESSION.add(expenses)
        SESSION.commit()
        CONN.commit()

        for p_id, stock in Item.items[bill_tabs.selected_index].items():
            # Convert to SQLAlchemy
            new_stock = DB.Stock(
                stock_in=stock.qty,
                current_stock=stock.qty,
                product_id=p_id,
                actual_price=stock.rate,
                min_selling_price=stock.min_price,
                selling_price=stock.sell_price,
                expire_date=stock.exp if stock.exp else None,
            )
            SESSION.add(new_stock)
            SESSION.commit()

            time.sleep(0.1)

            # Convert to SQLAlchemy
            stockId = SESSION.query(func.max(DB.Stock.id)).scalar()

            # Convert to SQLAlchemy
            stock_movement = DB.StockMovement(
                stock_id=stockId,
                movement_type="in",
                quantity=stock.qty,
                reference_id=grnId,
                reference_type="grn"
            )
            SESSION.add(stock_movement)
            SESSION.commit()
            CONN.commit()

        if self.cheque_amount.value:
            date = self.cheque_number.suffix_text.split("-")
            yr = int(date[0])
            mon = int(date[1])
            day = int(date[2])
            cheque = DB.Cheque(
                cheque_number=self.cheque_number.value,
                cheque_date=datetime(yr, mon, day),
                supplier_id=self.supplier_id,
                grn_id=grnId,
                amount=decimal.Decimal(self.cheque_amount.value),
                status='pending',
            )
            expenses = DB.ExpenseTracker(
                description=f"Cheque #{self.cheque_number.value} - GRN #{grnId} - {self.supplier_name.value}",
                outcome=float(self.cheque_amount.value)
            )
            SESSION.add(cheque)
            SESSION.commit()
            SESSION.add(expenses)
            SESSION.commit()
            CONN.commit()


        # Convert to SQLAlchemy
        grn_transaction = DB.GRNTransaction(
            amount=decimal.Decimal(float(self.total_amount.value.split(" ")[1])),
            grn_id=grnId,
            account_id=ACCOUNT_ID,
            transaction_type="payment",
            cheque_number=self.cheque_number.value,
            card_transaction_id=self.card_transaction_id.value,
        )
        SESSION.add(grn_transaction)
        SESSION.commit()

        if self.credit_amount.value:
            sup = SESSION.get(DB.Supplier, self.supplier_id)
            sup.credit += decimal.Decimal(self.credit_amount.value)
            SESSION.commit()

        self.delete_bill(None)

    def back(self, e=None):
        Tab.tabs[bill_tabs.selected_index].content = self.bill_area
        self.page.update()

    def load_bill(self, e=None):
        Tab.tabs[bill_tabs.selected_index].content = self.payment_area
        self.total_amount.value = currency + str(round(sum(self.grandTotal.values()), 2))
        self.pay(None)
        self.page.update()

    def hide_dropdown(self):
        self.supplier_dropdown.visible = False
        self.page.update()

    def select_supplier(self, supplier):
        try:
            self.supplier_id = supplier["id"]
            self.company.value = supplier["company_name"]
        except:
            # Convert to SQLAlchemy
            max_id = SESSION.query(func.max(DB.Supplier.id)).scalar()
            self.supplier_id = max_id + 1 if max_id else 1
            self.company.value = ""
        self.supplier_name.value = supplier["name"].title()
        self.hide_dropdown()
        self.page.update()

    def show_dropdown(self, e=None):
        self.supplier_dropdown.visible = True
        self.page.update()

    def filter_supplier(self, e):
        global suppliers
        query = self.supplier_name.value.lower()
        if query == "":
            self.hide_dropdown()
            return
        self.show_dropdown()

        # Convert to SQLAlchemy
        suppliers_query = SESSION.query(DB.Supplier).filter(
            or_(
                DB.Supplier.name.ilike(f"%{query}%"),
                DB.Supplier.company_name.ilike(f"%{query}%"),
                DB.Supplier.phone_number.ilike(f"%{query}%"),
                DB.Supplier.email.ilike(f"%{query}%")
            )
        ).limit(5).all()

        suppliers = [s.__dict__ for s in suppliers_query]

        self.supplier_dropdown.controls = [
                                              ft.ListTile(
                                                  title=ft.Text(supplier["name"]),
                                                  subtitle=ft.Text(f"Company: {supplier['company_name']}", size=12),
                                                  trailing=ft.Container(
                                                      content=ft.Text(str(supplier["credit"]), size=12),
                                                      bgcolor="#dbeafe",
                                                      padding=5,
                                                      border_radius=10
                                                  ),
                                                  on_click=lambda e, c=supplier: self.select_supplier(c),
                                                  data=supplier
                                              ) for supplier in suppliers
                                          ] + [
                                              ft.ListTile(
                                                  title=ft.Row(
                                                      [
                                                          ft.Text(f"Create "),
                                                          ft.Text(query.title(), weight=ft.FontWeight.BOLD),
                                                      ]
                                                  ),
                                                  subtitle=ft.Text(f"Company: xxxxxxxxxx", size=12),
                                                  trailing=ft.Container(
                                                      content=ft.Text("0.0", size=12),
                                                      bgcolor="#dbeafe",
                                                      padding=5,
                                                      border_radius=10
                                                  ),
                                                  on_click=lambda e, c={"name": query.title()}: self.select_supplier(c),
                                              )
                                          ]
        self.page.update()

    def delete_bill(self, e):
        n = self.bills.index(self) - 1
        Tab.tabs.pop(n)
        if n:
            bill_tabs.selected_index = n - 1
        else:
            bill_tabs.selected_index = n

        self.bills.remove(self)

        for i, t in enumerate(Tab.tabs[:-1]):
            t.tab_content = ft.Row([ft.Text(f"Bill {i + 1}")])

        if len(Bill.bills) == 1:
            grn_tab.add_tab()

        self.page.update()


class Tab:
    tabs = []

    def __init__(self, page):
        self.page = page
        bill_tabs.page = self.page
        self.tabs.append(ft.Tab(
            icon=ft.Icons.ADD,
            icon_margin=0,
        ))
        bill_tabs.on_change = self.add_tab
        self.add_tab()

    def add_tab(self, e=None):
        if e and bill_tabs.selected_index != len(self.tabs) - 1:
            return

        bill = Bill(self.page)
        new_tab = ft.Tab(
            tab_content=ft.Row([ft.Text(f"Bill {len(self.tabs)}")]),
            content=ft.Container(bill.bill_area),
        )
        self.tabs.insert(-1, new_tab)
        bill_tabs.tabs = self.tabs

        self.page.update()
        bill_tabs.selected_index = 0
        self.page.update()
        time.sleep(0.01)
        bill_tabs.selected_index = len(self.tabs) - 2
        bill_tabs.animation_duration = 300
        self.page.update()


def scroll_to_end():
    Bill.bills[bill_tabs.selected_index + 1].bill_box.scroll_to(offset=-1, duration=0,
                                                                curve=ft.AnimationCurve.EASE_IN_OUT)


class Item:
    items = dict()

    def __init__(self, page, p_id, p_name, qty, exp, cost, min_price, sell_price):
        self.page = page
        self.p_id = p_id
        self.p_name = p_name
        self.qty = qty
        self.exp = exp
        self.rate = cost
        self.min_price = min_price
        self.sell_price = sell_price
        self.total = round(float(self.qty if self.qty else 0) * float(self.rate if self.rate else 0), 2)

        Bill.bills[bill_tabs.selected_index + 1].grandTotal[self.p_id] = round(self.total, 2)
        Bill.bills[bill_tabs.selected_index + 1].grand_total.value = currency + str(
            round(sum(Bill.bills[bill_tabs.selected_index + 1].grandTotal.values()), 2))
        Bill.bills[bill_tabs.selected_index + 1].total_items.value = str(
            len(Bill.bills[bill_tabs.selected_index + 1].grandTotal.values())) + " Item(s)"

        self.row = ft.DataRow(
            [
                ft.DataCell(
                    ft.Text(i, size=12)
                ) for i in [self.p_name, self.qty, self.rate, self.min_price, self.sell_price, self.total]
            ]
        )

        self.dummy_row = ft.DataRow(
            [
                ft.DataCell(
                    ft.Text(i, size=12)
                ) for i in [self.p_name, self.qty, self.rate, self.min_price, self.sell_price, self.total]
            ]
        )

        Bill.bills[bill_tabs.selected_index + 1].data[self.p_id] = [self.row, self.qty]
        Bill.bills[bill_tabs.selected_index + 1].dummy_data[self.p_id] = [self.dummy_row, self.qty]
        Bill.bills[bill_tabs.selected_index + 1].bill_table.rows = [i[0] for i in Bill.bills[
            bill_tabs.selected_index + 1].data.values()]
        Bill.bills[bill_tabs.selected_index + 1].dummy_table.rows = [i[0] for i in Bill.bills[
            bill_tabs.selected_index + 1].dummy_data.values()]

        try:
            scroll_to_end()
        except:
            pass

        Bill.bills[bill_tabs.selected_index + 1].proceed_to_payment.disabled = False
        Bill.bills[bill_tabs.selected_index + 1].proceed_to_payment.style = ft.ButtonStyle(color=ft.Colors.GREEN, )

        self.items[bill_tabs.selected_index] = dict()
        self.items[bill_tabs.selected_index][self.p_id] = self
        self.page.update()


def grn(page: ft.Page, conn: create_engine, user_id):
    global CONN, SESSION, USER_ID, ACCOUNT_ID, selected_product

    CONN = conn
    USER_ID = user_id
    SESSION = Session(CONN)

    # Convert to SQLAlchemy
    products_query = SESSION.query(DB.Product).limit(5).all()
    products = [p.__dict__ for p in products_query]

    # Convert to SQLAlchemy
    units_query = SESSION.query(DB.Unit).all()
    for unit in units_query:
        units[unit.id] = unit.unit

    title = ft.Row(
        controls=[
            ft.Column(
                controls=[
                    ft.Text("Add Stock", size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_900),
                    ft.Text("Add new inventory to your store", color=ft.Colors.GREY_600)
                ],
                spacing=0
            )
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
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
        )

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

    if not Tab.tabs:
        global grn_tab
        Bill(page)
        grn_tab = Tab(page)

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
                                            ft.Text(
                                                stock["expire_date"],
                                                weight=ft.FontWeight.BOLD,
                                                size=12,
                                                color=ft.Colors.RED if stock[
                                                                           "status"].lower() == "expired" else "orange"
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

    def select_product(product):
        global selected_product, selected_stocks

        selected_product = product

        # Convert to SQLAlchemy
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

            # Update database for expired items using SQLAlchemy
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
        supplier_dropdown_container.visible = False
        page.update()

    def validate_quantity(e):
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

    def show_product_dropdown(e=None):
        product_dropdown_container.visible = True
        product_dropdown_container.update()

    def show_supplier_dropdown(e=None):
        supplier_dropdown_container.visible = True
        supplier_dropdown_container.update()

    def filter_products(e):
        global filtered_products
        query = e.control.value.lower()
        if not query:
            product_dropdown_container.visible = False
        else:
            # Convert to SQLAlchemy
            filtered_products_query = SESSION.query(DB.Product).filter(
                or_(
                    DB.Product.code.ilike(f"%{query}%"),
                    DB.Product.title.ilike(f"%{query}%"),
                    DB.Product.note.ilike(f"%{query}%")
                )
            ).limit(5).all()

            filtered_products = [p.__dict__ for p in filtered_products_query]

            show_product_dropdown()
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
            # Convert to SQLAlchemy
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

            show_supplier_dropdown()

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

    head = ft.Row(
        controls=[
            ft.Icon(ft.Icons.ADD_CIRCLE, color="#3b82f6"),
            ft.Text("Stock Information", size=20, weight=ft.FontWeight.BOLD)
        ],
    )

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
            on_click=lambda e: show_product_dropdown(e)
        ),
        expand=True,
        content_padding=2
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
            icon_color="#9ca3af",
            on_click=lambda e: show_supplier_dropdown(e)
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

    quantity_unit = ft.Text("units", color="#6b7280", size=12)

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

    row1 = ft.ResponsiveRow(
        controls=[
            ft.Column(
                controls=[
                    product_search,
                    product_dropdown_container
                ],
                spacing=5,
                col={"md": 12, "lg": 6}
            ),
            ft.Column(
                controls=[
                    quantity,
                ],
                col={"md": 12, "lg": 6}
            )
        ]
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

    buying_price = ft.TextField(
        label="Buying Price",
        hint_text="0.00",
        keyboard_type=ft.KeyboardType.NUMBER,
        border_radius=10,
        border_color="#d1d5db",
        focused_border_color="#3b82f6",
        focused_border_width=2,
        prefix_text="Rs. ",
    )

    row2 = ft.ResponsiveRow(
        [
            ft.Container(
                expire_date,
                col={"md": 12, "lg": 6}
            ),
            ft.Container(
                buying_price,
                col={"md": 12, "lg": 6}
            )
        ]
    )

    row3 = ft.ResponsiveRow(
        [
            ft.Container(
                min_price,
                col={"md": 12, "lg": 6}
            ),
            ft.Container(
                max_price,
                col={"md": 12, "lg": 6}
            )
        ]
    )

    def reset(e):
        product_search.value = ""
        quantity.value = ""
        expire_date.value = ""
        buying_price.value = ""
        min_price.value = ""
        max_price.value = ""
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

    reset_btn = ft.OutlinedButton(
        text="Reset",
        icon=ft.Icons.REFRESH,
        on_click=reset,
        expand=True,
        height=50,
    )

    def submit_form(e):
        if Tab.tabs[bill_tabs.selected_index].content == Bill.bills[bill_tabs.selected_index + 1].payment_area:
            Bill.bills[bill_tabs.selected_index + 1].back()
        Item(page, selected_product["id"], selected_product["title"], quantity.value, expire_date.value,
             buying_price.value, min_price.value, max_price.value)
        reset(None)
        page.update()

    submit_btn = ft.ElevatedButton(
        text="Add Product",
        icon=ft.Icons.ADD,
        on_click=submit_form,
        expand=True,
        height=50,
        bgcolor=ft.Colors.BLUE,
        color=ft.Colors.WHITE,
    )

    row4 = ft.Row(
        controls=[
            reset_btn,
            submit_btn
        ]
    )

    product_area = ft.Container(
        ft.Column(
            [
                head,
                row1,
                row2,
                row3,
                row4
            ]
        )
    )

    return ft.Container(
        ft.Column(
            [
                title,
                ft.ResponsiveRow(
                    [
                        ft.Container(
                            ft.Column(
                                [
                                    ft.Container(
                                        product_area,
                                        bgcolor=ft.Colors.WHITE,
                                        shadow=ft.BoxShadow(
                                            spread_radius=0.81,
                                            blur_radius=3,
                                            color=ft.Colors.BLACK12,
                                            offset=ft.Offset(1, 1),
                                            blur_style=ft.ShadowBlurStyle.NORMAL,
                                        ),
                                        padding=30,
                                        border_radius=15
                                    ),
                                    ft.Container(
                                        active_stock_container,
                                        bgcolor=ft.Colors.WHITE,
                                        shadow=ft.BoxShadow(
                                            spread_radius=0.81,
                                            blur_radius=3,
                                            color=ft.Colors.BLACK12,
                                            offset=ft.Offset(1, 1),
                                            blur_style=ft.ShadowBlurStyle.NORMAL,
                                        ),
                                        padding=30,
                                        border_radius=15,
                                        expand=True
                                    ),
                                ]
                            ),
                            col={"sm": 12, "md": 5}
                        ),
                        ft.Container(
                            bill_tabs,
                            col={"sm": 12, "md": 7},
                        )
                    ],
                    expand=True,
                ),
            ]
        ),
        expand=True,
    )