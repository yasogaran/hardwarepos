import decimal
import time
from datetime import datetime

import flet as ft
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
import DB
from sqlalchemy import or_, select

theme_color = ft.Colors.GREEN

SELECTED_CUSTOMER_ID = None
CONN:create_engine
SESSION:Session
ACCOUNT_ID = 0
CURRENCY = "Rs. "

class CustomerDetailsApp:
    def __init__(self, page: ft.Page):
        self.page = page

        self.invoice_table_data = []

        self.selected_customer_id = None

        self.dummy_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Invoice ID", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)),
                ft.DataColumn(ft.Text("Date", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)),
                ft.DataColumn(ft.Text("Amount", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)),
                ft.DataColumn(ft.Text("Paid Amount", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)),
                ft.DataColumn(ft.Text("Status", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)),
            ],

            border=ft.border.all(1, ft.Colors.GREY_200),
            bgcolor=theme_color + "100",
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
                ft.DataColumn(ft.Text("Amount", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)),
                ft.DataColumn(ft.Text("Paid Amount", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)),
                ft.DataColumn(ft.Text("Status", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)),
            ],

            border=ft.border.all(1, ft.Colors.GREY_200),
            bgcolor=theme_color + "100",
            heading_row_color=theme_color + "600",
            border_radius=8,
            heading_row_height=0,
            expand=True
        )
        self.customer_details = ft.Container(
            ft.Row(
                [
                    ft.Row(
                        [
                            ft.Icon(
                                ft.Icons.ACCOUNT_CIRCLE,
                                color=theme_color
                            ),
                            ft.Text(
                                "",
                                size=12,
                                weight=ft.FontWeight.BOLD,
                                selectable=True
                            )
                        ]
                    ),
                    ft.Row(
                        [
                            ft.Icon(
                                ft.Icons.CONTACT_PHONE,
                                color=theme_color
                            ),
                            ft.Text(
                                "",
                                size=12,
                                weight=ft.FontWeight.BOLD,
                            )
                        ]
                    ),
                    ft.Row(
                        [
                            ft.Icon(
                                ft.Icons.CURRENCY_EXCHANGE,
                                color=theme_color
                            ),
                            ft.Text(
                                "",
                                size=12,
                                weight=ft.FontWeight.BOLD,
                            )
                        ]
                    ),

                ],
                expand=True,
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            )
        )

        self.invoice_section = ft.Container(
            ft.Column(
                [
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Icon(ft.Icons.RECEIPT_LONG, color=theme_color + "600", size=24),
                                ft.Text("Invoice History", size=18, weight=ft.FontWeight.BOLD,
                                        color=ft.Colors.GREY_900)
                            ],
                            spacing=10),
                    ),
                    self.customer_details,
                    ft.Stack(
                        [
                            ft.Column(
                                [
                                    ft.Container(
                                        ft.Row(
                                            [
                                                ft.Container(
                                                    content=self.dummy_table,
                                                    expand=True,
                                                )
                                            ],
                                            expand=True
                                        ),
                                    ),
                                    ft.Container(
                                        ft.Column(
                                            [
                                                ft.Row(
                                                    [
                                                        ft.Container(
                                                            content=self.invoice_table,
                                                            expand=True,
                                                        )
                                                    ],
                                                    expand=True
                                                ),
                                            ],
                                            scroll=ft.ScrollMode.AUTO
                                        ),
                                        expand=True,
                                    )
                                ],
                                spacing=0,
                                expand=True,
                                alignment=ft.MainAxisAlignment.START
                            ),
                            ft.FloatingActionButton(
                                icon=ft.Icons.ADD,
                                on_click=self.add_amount,
                                bgcolor=theme_color + "300",
                                bottom=0,
                                right=0,
                            )
                        ],
                        expand=True,
                    )

                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            )
        )


    class Customer:
        data = dict()

        def __init__(self, page, cid, name, mobile, credit, invoices, dummyTable, invoiceTable, customerDetails):
            self.page:ft.Page = page
            self.id = cid
            self.name = name
            self.mobile = mobile
            self.credit = credit
            self.invoices = invoices
            self.dummyTable = dummyTable
            self.invoiceTable = invoiceTable
            self.customerDetails = customerDetails
            self.rows = ft.DataRow(
                [
                    ft.DataCell(
                        ft.Text(self.id),
                    ),
                    ft.DataCell(
                        ft.Column(
                            [
                                ft.Text(self.name),
                                ft.Text(self.mobile),
                            ]
                        )
                    ),
                    ft.DataCell(
                        ft.Text(self.credit),
                    )
                ],
                on_select_changed=self.select,
            )

            self.data[self.id] = self

            self.page.update()

        def id_name(self, iid: str, n):
            v = str(iid)
            for i in [10 ** i for i in range(n, 0, -1)]:
                if iid < i:
                    v = "0" + v
            return v

        def select(self, e=None):
            print("url:", self.page.url)
            # Using pandas to read invoice data for the selected customer
            stmt = select(
                DB.Invoice.id,
                DB.Invoice.created_on,
                DB.Invoice.total,
                DB.Invoice.paid_amount,
                DB.Invoice.status
            ).where(
                DB.Invoice.customer_id == self.id
            )

            # Use pandas to read the SQL query
            invoices_df = pd.read_sql(stmt, CONN)
            result = invoices_df.to_dict('records')

            for i, cstmr in self.data.items():
                cstmr.rows.color = ft.Colors.WHITE

            if e:
                e.control.color = theme_color + "50"

            self.customerDetails.content = ft.Row(
                [
                    ft.Row(
                        [
                            ft.Icon(
                                ft.Icons.ACCOUNT_CIRCLE,
                                color=theme_color
                            ),
                            ft.Text(
                                self.name,
                                size=12,
                                weight=ft.FontWeight.BOLD,
                                selectable=True
                            )
                        ]
                    ),
                    ft.Row(
                        [
                            ft.Icon(
                                ft.Icons.CONTACT_PHONE,
                                color=theme_color
                            ),
                            ft.Text(
                                self.mobile,
                                size=12,
                                weight=ft.FontWeight.BOLD,
                            )
                        ]
                    ),
                    ft.Row(
                        [
                            ft.Icon(
                                ft.Icons.CURRENCY_EXCHANGE,
                                color=theme_color
                            ),
                            ft.Text(
                                str(self.credit),
                                size=12,
                                weight=ft.FontWeight.BOLD,
                            )
                        ]
                    ),
                ],
                expand=True,
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            )

            self.invoiceTable.rows = [
                ft.DataRow(
                    [
                        ft.DataCell(
                            ft.Text(f'inv-{self.id_name(invoice["id"], 9)}'),
                        ),
                        ft.DataCell(
                            ft.Text(str(invoice["created_on"]).upper()),
                        ),
                        ft.DataCell(
                            ft.Text(str(invoice["total"])),
                        ),
                        ft.DataCell(
                            ft.Text(str(invoice["paid_amount"])),
                        ),
                        ft.DataCell(
                            ft.Text(str(invoice["status"])),
                        )
                    ]
                ) for invoice in result
            ]

            self.dummyTable.rows = [
                ft.DataRow(
                    [
                        ft.DataCell(
                            ft.Text(f'inv-{self.id_name(invoice["id"], 9)}'),
                        ),
                        ft.DataCell(
                            ft.Text(str(invoice["created_on"])),
                        ),
                        ft.DataCell(
                            ft.Text(str(invoice["total"])),
                        ),
                        ft.DataCell(
                            ft.Text(str(invoice["paid_amount"])),
                        ),
                        ft.DataCell(
                            ft.Text(str(invoice["status"])),
                        )
                    ]
                ) for invoice in result
            ]
            global SELECTED_CUSTOMER_ID
            SELECTED_CUSTOMER_ID = self.id

            self.page.update()

    def pay(self, e):
        amount =  float(self.pay_cash.value) if self.pay_cash.value else 0
        cheque_date = self.cheque_number.suffix_text
        cheque_number = int(self.cheque_number.value) if self.cheque_number.value else 0
        cheque_amount = float(self.cheque_amount.value) if self.cheque_amount.value else 0



        if cheque_amount and ((not cheque_number) or cheque_date=='date'):
            if not cheque_number:
                self.cheque_number.error_text = "Please enter the cheque number"
            elif cheque_date == "date":
                self.cheque_number.error_text = "Please select the date"
            elif not cheque_amount:
                self.cheque_amount.error_text = "Please enter the cheque amount"
            self.page.update()
            return

        customer = SESSION.get(DB.Customer, SELECTED_CUSTOMER_ID)
        customer.credit -= decimal.Decimal(amount) + decimal.Decimal(cheque_amount)
        SESSION.commit()

        stmt = select(
            DB.Invoice.id,
            DB.Invoice.total,
            DB.Invoice.paid_amount
        ).where(
            DB.Invoice.customer_id == SELECTED_CUSTOMER_ID,
            DB.Invoice.status == 'pending'
        )

        # Use pandas to read the SQL query
        invoices_df = pd.read_sql(stmt, SESSION.bind)
        invs = invoices_df.to_dict('records')

        if amount:
            expenses = DB.ExpenseTracker(
                description=f"Money deposit - {customer.name}",
                income=cheque_amount,
            )

            SESSION.add(expenses)
            SESSION.commit()
            CONN.commit()
            for invoice in invs:
                inv = SESSION.get(DB.Invoice, invoice["id"])
                transfer = DB.InvoiceTransaction()
                balance = invoice["total"] - invoice["paid_amount"]

                transfer.invoice_id = inv.id
                transfer.amount = decimal.Decimal(amount)
                transfer.account_id = ACCOUNT_ID

                if balance <= amount:
                    inv.paid_amount += decimal.Decimal(balance)
                    inv.status = "paid"
                    amount -= balance
                else:
                    inv.paid_amount += decimal.Decimal(amount)
                    SESSION.commit()
                    break

                SESSION.commit()

            CONN.commit()

            time.sleep(0.1)


            invoices_df = pd.read_sql(stmt, SESSION.bind)
            invs = invoices_df.to_dict('records')

        if cheque_amount:
            cheque = DB.Cheque()
            cheque.cheque_number = cheque_number
            cheque.amount = decimal.Decimal(cheque_amount)
            cheque.cheque_date = cheque_date
            cheque.customer_id = SELECTED_CUSTOMER_ID
            cheque.status = "pending"

            expenses = DB.ExpenseTracker(
                description=f"Cheque deposit - {cheque_number} - {customer.name}",
                income=cheque_amount,
            )

            SESSION.add(cheque)
            SESSION.commit()
            SESSION.add(expenses)
            SESSION.commit()
            CONN.commit()

            for invoice in invs:
                inv = SESSION.get(DB.Invoice, invoice["id"])
                transfer = DB.InvoiceTransaction()

                balance = invoice["total"] - invoice["paid_amount"]

                transfer.amount = decimal.Decimal(cheque_amount)
                transfer.cheque_number = cheque_number
                print(inv.id)
                transfer.invoice_id = inv.id
                transfer.account_id = ACCOUNT_ID

                if balance <= cheque_amount:
                    inv.paid_amount += decimal.Decimal(balance)
                    inv.status = "paid"
                    cheque_amount -= balance

                else:
                    inv.paid_amount += decimal.Decimal(cheque_amount)

                    SESSION.commit()
                    break

            CONN.commit()

        self.page.close(self.pop)

        CONN.commit()

        #self.filter_customer()
        self.Customer.data[SELECTED_CUSTOMER_ID].select()
        self.page.update()



    def add_amount(self, e):
        if not SELECTED_CUSTOMER_ID:
            return
        def on_type(e):
            if e.control.value:
                yes.disabled = False
            else:
                yes.disabled = True
            self.page.update()

        yes = ft.TextButton(
            "Update",
            disabled=True,
            on_click=self.pay,
        )
        no = ft.TextButton("Cancel", on_click=lambda e: self.page.close(self.pop))

        def date_picker(e):
            self.page.open(
                ft.DatePicker(
                    first_date=datetime.now(),
                    on_change=select_date,
                )
            ),

        def select_date(e):
            self.cheque_number.suffix_text = e.control.value.strftime('%Y-%m-%d')
            self.page.update()

        self.cheque_number = ft.TextField(
            label="Cheque Number",
            hint_text="Cheque Number",
            prefix_icon=ft.Icons.MONEY,
            border_radius=10,
            border_color="#d1d5db",
            focused_border_color="#3b82f6",
            focused_border_width=2,
            suffix_text="date",
            expand=True,
            on_change=on_type,
        )

        cheque_date = ft.IconButton(
            icon=ft.Icons.CALENDAR_MONTH,
            on_click=date_picker
        )

        self.cheque_amount = ft.TextField(
            label="Cheque Amount",
            prefix_text=CURRENCY,
            hint_text="Cheque Amount",
            border_radius=10,
            border_color="#d1d5db",
            focused_border_color="#3b82f6",
            focused_border_width=2,
            on_change=on_type,
        )

        cheque_area = ft.Row(
            [
                self.cheque_number,
                cheque_date,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )


        customer = pd.read_sql(select(
            DB.Customer.name,
            DB.Customer.credit
        ).where(
            DB.Customer.id == SELECTED_CUSTOMER_ID
        ), CONN).to_dict("records")[0]

        self.pay_cash = ft.TextField(
            label="Deposit Amount",
            hint_text="0.00",
            prefix_text="Rs. ",
            suffix_text=customer["credit"],
            input_filter=ft.InputFilter(
                allow=True,
                regex_string=r"\d\b"
            ),
            on_change=on_type,
            border_radius=10,
            border_color="#d1d5db",
            focused_border_color="#3b82f6",
            focused_border_width=2,
        )

        content = ft.Container(
            ft.Column(
            [
                self.pay_cash,
                cheque_area,
                self.cheque_amount
            ]
        ),
            width=400,
            height=200,
            expand=False
        )

        self.pop = ft.AlertDialog(
            title=customer["name"],
            content=content,
            actions=[
                yes, no
            ],



        )
        self.page.open(self.pop)
        self.page.update()

    def filter_customer(self, e=None):
        query = e.control.value.lower() if e else ''

        # Using pandas to search customers with LIKE functionality

        search_pattern = f"%{query}%"

        customer_query = select(
            DB.Customer.id,
            DB.Customer.name,
            DB.Customer.mobile,
            DB.Customer.credit
        ).where(
            or_(
                DB.Customer.name.ilike(search_pattern),
                DB.Customer.mobile.ilike(search_pattern)
            )
        ).limit(20)

        customers_df = pd.read_sql(customer_query, CONN)
        result = customers_df.to_dict("records")

        self.Customer.data = dict()

        for customer in result:
            # Get invoices for each customer using pandas
            invoices = SESSION.query(DB.Invoice.id) \
                .filter(DB.Invoice.customer_id == customer['id']) \
                .all()

            # Extract just the ID values
            invoices = [invoice.id for invoice in invoices]


            self.Customer(
                self.page,
                customer["id"],
                customer["name"],
                customer["mobile"],
                customer["credit"],
                invoices,
                self.dummy_table,
                self.invoice_table,
                self.customer_details
            )

        self.customer_details_container.content = ft.Container(
            ft.Row(
                [
                    ft.Column(
                        [
                            ft.Container(
                                ft.Row(
                                    [
                                        ft.DataTable(
                                            columns=[
                                                ft.DataColumn(
                                                    ft.Text("ID")
                                                ),
                                                ft.DataColumn(
                                                    ft.Text("Name / Mobile")
                                                ),
                                                ft.DataColumn(
                                                    ft.Text("Credit")
                                                )
                                            ],
                                            expand=True,
                                        ),
                                    ],
                                    expand=True,
                                )
                            ),
                            ft.Container(
                                ft.Column(
                                    [
                                        ft.Row(
                                            [
                                                ft.DataTable(
                                                    columns=[
                                                        ft.DataColumn(
                                                            ft.Text("ID")
                                                        ),
                                                        ft.DataColumn(
                                                            ft.Text("Name / Mobile")
                                                        ),
                                                        ft.DataColumn(
                                                            ft.Text("Credit")
                                                        )
                                                    ],
                                                    heading_row_height=0,
                                                    rows=list(i.rows for i in self.Customer.data.values()),
                                                    expand=True,
                                                ),
                                            ],
                                            expand=True,
                                        )
                                    ],
                                    expand=True,
                                    scroll=ft.ScrollMode.AUTO
                                ),
                                expand=True
                            ),
                        ],
                        spacing=0,
                        alignment=ft.MainAxisAlignment.START,
                        expand=True,
                    ),
                ],
                expand=True,
                alignment=ft.MainAxisAlignment.START,
            ),
            alignment=ft.Alignment(0, 0),
        )

        self.page.update()

    def get_status_color(self, status):
        Colors = {
            "Paid": (ft.Colors.GREEN_100, ft.Colors.GREEN_800),
            "Pending": (ft.Colors.YELLOW_100, ft.Colors.YELLOW_800),
            "Refunded": (ft.Colors.RED_100, ft.Colors.RED_800)
        }
        return Colors.get(status, (ft.Colors.GREY_100, ft.Colors.GREY_800))

    def build(self):
        # Header
        header = ft.Column(
            [
                ft.Text("Customer Details", size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_900),
                ft.Text("Search and view detailed customer information", color=ft.Colors.GREY_600)
            ],
            spacing=0
        )

        # Search Section
        self.search_field = ft.TextField(
            label="Search Customer",
            label_style=ft.TextStyle(color=theme_color),
            hint_text="Enter customer name or email address...",
            border_color=theme_color + "300",
            focused_border_color=theme_color + "500",
            expand=True,
            on_change=lambda e: self.filter_customer(e)
        )

        search_section = ft.Container(
            content=ft.Column([
                ft.Row([
                    self.search_field
                ])
            ], spacing=15),
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

        # Customer Details Container (initially empty)
        self.customer_details_container = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.PERSON_SEARCH, size=64, color=ft.Colors.GREY_400),
                    ft.Text("Search for a customer to view their details", size=16, color=ft.Colors.GREY_600,
                            text_align=ft.TextAlign.CENTER)
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=20,
            ),
            alignment=ft.Alignment(0, 0),
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

        # Main layout
        self.main_content = ft.Column(
            [
                ft.Container(
                    header,
                ),
                ft.Container(
                    ft.ResponsiveRow(
                        [
                            ft.Container(
                                ft.Column(
                                    [
                                        search_section,
                                        self.customer_details_container
                                    ],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                    expand=True
                                ),
                                expand=True,
                                col={"sm": 12, "md": 12, "lg": 6, "xl": 5},
                            ),
                            ft.Container(
                                ft.Column(
                                    [
                                        ft.Container(
                                            self.invoice_section,
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
                                col={"sm": 12, "md": 12, "lg": 6, "xl": 7},
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


        return self.main_content


def customerDetails(page: ft.Page, conn, user_id):
    global CONN, SELECTED_CUSTOMER_ID, SESSION

    SELECTED_CUSTOMER_ID = None
    CONN = conn
    SESSION = Session(CONN)
    app = CustomerDetailsApp(page)

    return app.build()


if __name__ == "__main__":
    ft.app(target=customerDetails)