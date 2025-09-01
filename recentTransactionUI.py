import flet as ft
from datetime import datetime
import random
import pandas as pd
from sqlalchemy import create_engine, func, or_
from sqlalchemy.orm import sessionmaker, Session
import DB # Assuming DB.py contains SQLAlchemy models for Invoice, Customer, User, InvoiceHasStock, Stock, and Product

theme_color = ft.Colors.BLUE


class RecentTransaction:
    def __init__(self, page: ft.Page, conn, user_id):
        self.invoice_quarry = None
        self.page = page
        self.conn = conn
        self.session = Session(conn)
        self.user_id = user_id

        self.header = ft.Column(
            [
                ft.Text("Recent Transaction", size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_900),
                ft.Text("Search and view detailed sells information", color=ft.Colors.GREY_600)
            ],
            spacing=0
        )

        def reset_date(e, target):
            target.value = ""
            target.focus = False
            self.page.update()

        self.from_date = ft.TextField(
            label='From Date',
            read_only=True,
            focused_border_width=2,
            border_radius=ft.border_radius.only(
                top_left=10,
                bottom_left=10
            ),
            border_width=2,
            on_click=lambda e: date_picker(e, self.from_date),
            prefix=ft.IconButton(
                icon=ft.Icons.REFRESH,
                on_click=lambda e: reset_date(e, self.from_date),
            ),
            height=50,
            col={"sm": 9}
        )

        self.to_date = ft.TextField(
            label='To Date',
            read_only=True,
            border_radius=ft.border_radius.only(
                top_left=10,
                bottom_left=10
            ),
            border_width=2,
            on_click=lambda e: date_picker(e, self.to_date),
            prefix=ft.IconButton(
                icon=ft.Icons.REFRESH,
                on_click=lambda e: reset_date(e, self.to_date),
                padding=0
            ),
            height=50,
            col={"sm": 9}
        )

        def handle_change(e, target):
            target.value = e.control.value.strftime('%Y-%m-%d')
            self.filter_invoice()
            self.page.update()

        def date_picker(e, target):
            self.page.open(
                ft.DatePicker(
                    last_date=datetime.strptime(self.to_date.value,
                                                '%Y-%m-%d') if target == self.from_date and self.to_date.value else datetime.now(),
                    current_date=datetime.strptime(self.from_date.value,
                                                   '%Y-%m-%d') if target == self.to_date and self.from_date.value else datetime.now(),
                    first_date=datetime.strptime(self.from_date.value,
                                                 '%Y-%m-%d') if target == self.to_date and self.from_date.value else datetime(
                        year=1900, month=1, day=1),
                    on_change=lambda e: handle_change(e, target),
                )
            ),

        def date_btn(target):
            return ft.Container(
                ft.IconButton(
                    icon=ft.Icons.CALENDAR_TODAY,
                    icon_color=ft.Colors.WHITE,
                    bgcolor=ft.Colors.GREY,
                    on_click=lambda e: date_picker(e, target),
                ),
                bgcolor=ft.Colors.GREY,
                border_radius=ft.border_radius.only(
                    top_right=10,
                    bottom_right=10
                ),
                height=49,
                col={"sm": 3},
                border=ft.border.only(
                    ft.BorderSide(2, theme_color),
                    ft.BorderSide(2, theme_color),
                    ft.BorderSide(2, theme_color),
                    ft.BorderSide(2, theme_color),
                )
            )

        self.date_selectors = ft.Container(
            ft.ResponsiveRow(
                controls=[
                    ft.ResponsiveRow(
                        controls=[
                            self.from_date,
                            date_btn(self.from_date)
                        ],
                        spacing=0,
                        col={"sm": 6, "md": 6}
                    ),
                    ft.ResponsiveRow(
                        controls=[
                            self.to_date,
                            date_btn(self.to_date)
                        ],
                        spacing=0,
                        col={"sm": 6, "md": 6}
                    )
                ],
            ),
            col={"sm": 12, "md": 3}
        )

        self.search_bar = ft.TextField(
            label='Invoice Id/ Customer Name/ Phone Number',
            focused_border_color=ft.Colors.BLUE,
            border_radius=10,
            border_width=2,
            col={"sm": 12, "md": 5},
            on_change=self.filter_invoice
        )

        self.price_min = ft.TextField(
            label='Minimum Invoice Amount',
            focused_border_color=ft.Colors.BLUE,
            border_radius=10,
            border_width=2,
            keyboard_type=ft.KeyboardType.NUMBER,
            col={"sm": 12, "md": 2},
            on_change=self.filter_invoice
        )

        self.price_max = ft.TextField(
            label='Maximum Invoice Amount',
            focused_border_color=ft.Colors.BLUE,
            border_radius=10,
            border_width=2,
            keyboard_type=ft.KeyboardType.NUMBER,
            col={"sm": 12, "md": 2},
            on_change=self.filter_invoice
        )

        self.search_section = ft.Container(
            content=ft.ResponsiveRow(
                [
                    self.date_selectors, self.search_bar, self.price_min, self.price_max,
                ],
                spacing=15
            ),
            shadow=ft.BoxShadow(
                spread_radius=0.81,
                blur_radius=3,
                color=ft.Colors.BLACK12,
                offset=ft.Offset(1, 1),
                blur_style=ft.ShadowBlurStyle.NORMAL,
            ),
            padding=20,
            border_radius=15,
            bgcolor=ft.Colors.WHITE,
        )

        self.selected_bill_details = {
            "INVOICE IS": "-",
            "DATE": "-",
            "CUSTOMER NAME": "-",
            "CASHIER NAME": "-",
        }

        self.invoice_details = ft.Container(
            ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text(
                                value=title,
                                weight=ft.FontWeight.BOLD,
                                color=theme_color
                            ),
                            ft.Text(
                                value=value,
                                size=12,
                                weight=ft.FontWeight.BOLD,
                                selectable=True
                            )
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ) for title, value in self.selected_bill_details.items()
                ],
                expand=True,
            )
        )

        self.bill_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Item", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)),
                ft.DataColumn(ft.Text("Qty", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)),
                ft.DataColumn(ft.Text("Price", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)),
                ft.DataColumn(ft.Text("Total", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)),
            ],
            bgcolor=theme_color + "100",
            heading_row_color=theme_color + "600",
            border_radius=ft.BorderRadius(0, 0, 15, 15),
            heading_row_height=0,
            expand=True
        )

        self.dummy_bill_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Item", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)),
                ft.DataColumn(ft.Text("Qty", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)),
                ft.DataColumn(ft.Text("Price", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)),
                ft.DataColumn(ft.Text("Total", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)),
            ],
            heading_row_color=theme_color + "600",
            data_row_max_height=0,
            data_row_min_height=0,
            border_radius=8,
            expand=True
        )

        self.invoice_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Invoice ID", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)),
                ft.DataColumn(ft.Text("Date", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)),
                ft.DataColumn(ft.Text("Total", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)),
                ft.DataColumn(ft.Text("Paid", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)),
                ft.DataColumn(ft.Text("Status", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)),
                ft.DataColumn(ft.Text("Customer", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)),
                ft.DataColumn(ft.Text("Cashier", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)),
            ],
            border=ft.border.all(1, ft.Colors.GREY_200),
            bgcolor=ft.Colors.WHITE,
            border_radius=8,
            heading_row_height=0,
            expand=True
        )

        self.dummy_invoice_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Invoice ID", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                              heading_row_alignment=ft.MainAxisAlignment.CENTER),
                ft.DataColumn(ft.Text("Date", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                              heading_row_alignment=ft.MainAxisAlignment.CENTER),
                ft.DataColumn(ft.Text("Total", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                              heading_row_alignment=ft.MainAxisAlignment.CENTER),
                ft.DataColumn(ft.Text("Paid", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                              heading_row_alignment=ft.MainAxisAlignment.CENTER),
                ft.DataColumn(ft.Text("Status", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                              heading_row_alignment=ft.MainAxisAlignment.CENTER),
                ft.DataColumn(ft.Text("Customer", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                              heading_row_alignment=ft.MainAxisAlignment.CENTER),
                ft.DataColumn(ft.Text("Cashier", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                              heading_row_alignment=ft.MainAxisAlignment.CENTER),
            ],
            heading_row_color=theme_color + "600",
            data_row_max_height=0,
            data_row_min_height=0,
            border_radius=8,
            expand=True
        )

        self.reload_btn = ft.IconButton(
            icon=ft.Icons.REFRESH,
            expand=True,
            on_click=self.filter_invoice
        )

        ft.Container(
            ft.Row(
                [
                    ft.Container(
                        ft.Column(
                            [
                                self.dummy_bill_table,
                                ft.Column(
                                    [
                                        self.bill_table
                                    ],
                                    scroll=ft.ScrollMode.AUTO,
                                    expand=True,
                                )
                            ],
                            spacing=0,
                            expand=True,
                        ),
                        expand=True,
                    )
                ],
                alignment=ft.MainAxisAlignment.START,
                expand=True
            ),
            expand=True,
            alignment=ft.alignment.top_center
        )

        self.invoices_container = ft.Container(
            content=ft.Row(
                [
                    ft.Container(
                        ft.Column(
                            [
                                ft.Row(
                                    [
                                        self.dummy_invoice_table
                                    ]
                                ),
                                ft.Column(
                                    [
                                        ft.Container(
                                            ft.Row(
                                                [
                                                    self.invoice_table,
                                                ]
                                            )
                                        ),
                                        ft.Container(
                                            ft.Row(
                                                [
                                                    self.reload_btn
                                                ],

                                            )
                                        )
                                    ],
                                    scroll=ft.ScrollMode.AUTO,
                                    expand=True
                                )
                            ],
                            spacing=0
                        ),
                        expand=True
                    )
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            alignment=ft.alignment.top_center,
            expand=True,
            shadow=ft.BoxShadow(
                spread_radius=0.81,
                blur_radius=3,
                color=ft.Colors.BLACK12,
                offset=ft.Offset(1, 1),
                blur_style=ft.ShadowBlurStyle.NORMAL,
            ),
            padding=20,
            border_radius=15,
            bgcolor=ft.Colors.WHITE,
        )

        self.bill_section = ft.Container(
            ft.Column(
                [
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Icon(ft.Icons.RECEIPT_LONG, color=theme_color + "600", size=24),
                                ft.Text("Invoice", size=18, weight=ft.FontWeight.BOLD,
                                        color=ft.Colors.GREY_900)
                            ],
                            spacing=10),
                    ),
                    self.invoice_details,
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Container(
                                    ft.Column(
                                        [
                                            ft.Row(
                                                [
                                                    self.dummy_bill_table
                                                ]
                                            ),
                                            ft.Column(
                                                [
                                                    ft.Container(
                                                        ft.Row(
                                                            [
                                                                self.bill_table
                                                            ]
                                                        )
                                                    )
                                                ],
                                                scroll=ft.ScrollMode.AUTO,
                                                expand=True
                                            )
                                        ],
                                        spacing=0
                                    ),
                                    expand=True
                                )
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                        ),
                        alignment=ft.alignment.top_center,
                        expand=True,
                    )
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            )
        )

        # Initialize with initial load
        self.filter_invoice()

    class Invoice:
        data = []
        dummy_data = []

        def __init__(self, page, iid, date, total_amount, paid_amount, status, customer_name, cashier_name, bill_table,
                     dummy_bill_table, bill_details, conn):
            self.page = page
            self.id = iid
            self.date = date
            self.total_amount = total_amount
            self.paid_amount = paid_amount
            self.status = status
            self.customer_name = customer_name
            self.cashier_name = cashier_name
            self.bill_table = bill_table
            self.dummy_bill_table = dummy_bill_table
            self.bill_details = bill_details
            self.session = Session(conn)

            self.bill_data = {
                "INVOICE ID": f"inv-{self.id_name(8)}",
                "DATE": str(self.date),
                "CUSTOMER NAME": str(self.customer_name),
                "CASHIER NAME": str(self.cashier_name)
            }

            status_list = ["paid", "pending"]

            self.data.append(ft.DataRow(
                [
                    ft.DataCell(
                        ft.Container(
                            ft.Text(
                                str(data),
                                weight=ft.FontWeight.BOLD if str(data).lower() in status_list else None,
                                color=ft.Colors.WHITE if str(data).lower() in status_list else ft.Colors.BLACK,
                            ),
                            border_radius=15,
                            padding=2,
                            width=75 if str(data).lower() in status_list else None,
                            height=25 if str(data).lower() in status_list else None,
                            bgcolor=ft.Colors.RED_400 if str(data).lower() == "pending"
                            else ft.Colors.GREEN_400 if str(data).lower() == "paid"
                            else ft.Colors.TRANSPARENT,
                            alignment=ft.Alignment(0, 0)
                        ),
                    ) for data in
                    [f"INV-{self.id_name(8)}", str(self.date), str(self.total_amount), str(self.paid_amount),
                     str(self.status), str(self.customer_name), str(self.cashier_name)]
                ],
                on_select_changed=self.select,
            ))

            self.dummy_data.append(ft.DataRow(
                [
                    ft.DataCell(
                        ft.Text(str(data)),
                    ) for data in
                    [f"INV-{self.id_name(8)}", str(self.date), str(self.total_amount), str(self.paid_amount),
                     str(self.status),
                     str(self.customer_name), str(self.cashier_name)]
                ],
            ))

        def id_name(self, n):
            v = str(self.id)
            for i in [10 ** i for i in range(n, 0, -1)]:
                if int(self.id) < i:
                    v = "0" + v
            return v

        def select(self, e):
            for row in self.data:
                row.color = ft.Colors.WHITE

            e.control.color = theme_color + "50"

            self.bill_details.content = ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text(
                                value=title,
                                weight=ft.FontWeight.BOLD,
                                color=theme_color
                            ),
                            ft.Text(
                                value=str(value).upper(),
                                weight=ft.FontWeight.BOLD,
                                selectable=True
                            )
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ) for title, value in self.bill_data.items()

                ],
                expand=True,
            )

            # Use SQLAlchemy ORM to get invoice items
            invoice_items = (self.session.query(DB.Product.title, DB.InvoiceHasStock.quantity, DB.InvoiceHasStock.unit_price)
                             .join(DB.Stock, DB.InvoiceHasStock.stock_id == DB.Stock.id)
                             .join(DB.Product, DB.Stock.product_id == DB.Product.id)
                             .filter(DB.InvoiceHasStock.invoice_id == self.id)
                             .all())

            self.bill_table.rows = [
                ft.DataRow(
                    [
                        ft.DataCell(
                            ft.Text(item.title),
                        ),
                        ft.DataCell(
                            ft.Text(str(item.quantity)),
                        ),
                        ft.DataCell(
                            ft.Text(str(item.unit_price)),
                        ),
                        ft.DataCell(
                            ft.Text(str(round(item.quantity * item.unit_price, 2))),
                        )
                    ]
                ) for item in invoice_items
            ]

            self.dummy_bill_table.rows = [
                ft.DataRow(
                    [
                        ft.DataCell(
                            ft.Text(item.title),
                        ),
                        ft.DataCell(
                            ft.Text(str(item.quantity)),
                        ),
                        ft.DataCell(
                            ft.Text(str(item.unit_price)),
                        ),
                        ft.DataCell(
                            ft.Text(str(round(item.quantity * item.unit_price, 2))),
                        )
                    ]
                ) for item in invoice_items
            ]
            self.page.update()

    def filter_invoice(self, e=None):
        try:
            self.invoice_quarry = self.search_bar.value.lower() if self.search_bar.value else ""
            self.Invoice.data = []
            self.Invoice.dummy_data = []
            self.reload_btn.disabled = False
            self.reload_btn.height = 40
        except Exception:
            pass

        temp = len(self.Invoice.data)

        query = self.session.query(
            DB.Invoice.id,
            DB.Invoice.created_on,
            DB.Invoice.total,
            DB.Invoice.paid_amount,
            DB.Invoice.status,
            DB.Customer.name.label('customer_name'),
            DB.User.name.label('cashier_name')
            ).outerjoin(DB.Customer, DB.Customer.id == DB.Invoice.customer_id
            ).join(DB.User, DB.User.id == DB.Invoice.user_id
            ).order_by(DB.Invoice.created_on.desc())

        # Apply search conditions
        if self.invoice_quarry:
            search_term = f"%%{self.invoice_quarry}%%"
            query = query.filter(or_(
                DB.Customer.name.ilike(search_term),
                DB.Customer.mobile.ilike(search_term)
            ))

        if self.from_date.value:
            from_date = datetime.strptime(self.from_date.value, '%Y-%m-%d').date()
            query = query.filter(func.date(DB.Invoice.created_on) >= from_date)

        if self.to_date.value:
            to_date = datetime.strptime(self.to_date.value, '%Y-%m-%d').date()
            query = query.filter(func.date(DB.Invoice.created_on) <= to_date)

        try:
            if self.price_min.value:
                query = query.filter(DB.Invoice.total >= float(self.price_min.value))
            if self.price_max.value:
                query = query.filter(DB.Invoice.total <= float(self.price_max.value))
        except ValueError:
            # Handle invalid number input gracefully
            pass

        invoices = query.order_by(DB.Invoice.id.desc()).limit(20).offset(len(self.Invoice.data)).all()

        for invoice in invoices:
            self.Invoice(
                self.page,
                invoice.id,
                invoice.created_on,
                invoice.total,
                invoice.paid_amount,
                invoice.status,
                invoice.customer_name,
                invoice.cashier_name,
                self.bill_table,
                self.dummy_bill_table,
                self.invoice_details,
                self.conn
            )

        self.invoice_table.rows = self.Invoice.data
        self.dummy_invoice_table.rows = self.Invoice.dummy_data

        if temp == len(self.Invoice.data):
            self.reload_btn.disabled = True
            self.reload_btn.height = 0

        self.page.update()

    def build(self):
        self.main_content = ft.Column(
            [
                ft.Container(
                    self.header,
                ),
                self.search_section,
                ft.Container(
                    ft.ResponsiveRow(
                        [
                            ft.Container(
                                self.invoices_container,
                                expand=True,
                                col={"sm": 12, "md": 12, "lg": 8, },
                            ),
                            ft.Container(
                                ft.Column(
                                    [
                                        ft.Container(
                                            self.bill_section,
                                            shadow=ft.BoxShadow(
                                                spread_radius=0.81,
                                                blur_radius=3,
                                                color=ft.Colors.BLACK12,
                                                offset=ft.Offset(1, 1),
                                                blur_style=ft.ShadowBlurStyle.NORMAL,
                                            ),
                                            padding=20,
                                            border_radius=15,
                                            bgcolor=ft.Colors.WHITE,
                                            expand=True
                                        )
                                    ],
                                    expand=True,
                                ),
                                expand=True,
                                col={"sm": 12, "md": 12, "lg": 4},
                            ),
                        ],
                    ),
                    expand=True,
                ),
            ],
            expand=True,
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            spacing=20
        )

        self.page.update()
        return self.main_content


def recentTransaction(page: ft.Page, session, user_id):
    app = RecentTransaction(page, session, user_id)
    app.filter_invoice()
    return app.build()
