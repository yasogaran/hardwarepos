import flet as ft
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import select, or_, func
import DB

theme_color = ft.Colors.BLUE


class SupplierDetails:
    def __init__(self, page: ft.Page, conn, user_id):
        self.page = page
        self.conn = conn
        self.user_id = user_id
        self.session = Session(self.conn)

        # Load initial suppliers data using SQLAlchemy
        suppliers_query = self.session.query(DB.Supplier).limit(20).all()
        self.suppliers = [s.__dict__ for s in suppliers_query]

        self.header = ft.Column(
            [
                ft.Text("Supplier Details", size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_900),
                ft.Text("Search and view detailed supplier information", color=ft.Colors.GREY_600)
            ],
            spacing=0
        )

        self.search_bar = ft.TextField(
            label='Search Supplier',
            label_style=ft.TextStyle(color=theme_color),
            hint_text="Search Suppliers...",
            border_color=theme_color + "300",
            focused_border_color=theme_color + "500",
            expand=True,
            on_change=lambda e: self.filter_supplier(e)
        )

        self.search_section = ft.Container(
            content=ft.Column([
                ft.Row([
                    self.search_bar
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

        self.supplier_details_container = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.PERSON_SEARCH, size=64, color=ft.Colors.GREY_400),
                    ft.Text("Search for a supplier to view their details", size=16, color=ft.Colors.GREY_600,
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

        self.supplier_details = ft.Container(
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
                                ft.Icons.BUSINESS,
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

        self.grn_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("GRN ID", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)),
                ft.DataColumn(ft.Text("Date", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)),
                ft.DataColumn(ft.Text("Amount", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)),
                ft.DataColumn(ft.Text("Paid Amount", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)),
                ft.DataColumn(ft.Text("Status", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)),
                ft.DataColumn(ft.Text("User", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)),
            ],

            border=ft.border.all(1, ft.Colors.GREY_200),
            bgcolor=theme_color + "100",
            heading_row_color=theme_color + "600",
            border_radius=8,
            expand=True
        )

        self.grn_section = ft.Container(
            ft.Column(
                [
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Icon(ft.Icons.RECEIPT_LONG, color=theme_color + "600", size=24),
                                ft.Text("GRN History", size=18, weight=ft.FontWeight.BOLD,
                                        color=ft.Colors.GREY_900)
                            ],
                            spacing=10),
                    ),
                    self.supplier_details,
                    ft.Container(
                        ft.Row(
                            [
                                ft.Container(
                                    content=self.grn_table,
                                    expand=True,
                                )
                            ],
                            alignment=ft.MainAxisAlignment.START,
                            expand=True
                        ),
                        expand=True,
                        alignment=ft.alignment.top_center
                    )

                ]
            )
        )

        # Initialize suppliers
        self.Supplier.data = dict()
        for supplier in self.suppliers:
            self.Supplier(
                self.page,
                supplier["id"],
                supplier["name"],
                supplier["company_name"],
                supplier["code"],
                supplier["phone_number"],
                supplier["land_line"],
                supplier["email"],
                supplier["address"],
                supplier["credit"],
                self.grn_table,
                self.supplier_details,
                self.conn
            )
        self.page.update()
        print(len(self.Supplier.data))

    class Supplier:
        data = dict()

        def __init__(self, page, sid, name, company_name, code, phone_number, land_line, email, address, credit,
                     grnTable, supplierDetails, conn):
            self.page = page
            self.id = sid
            self.name = name
            self.company_name = company_name
            self.code = code
            self.mobile = phone_number
            self.land_line = land_line
            self.email = email
            self.address = address
            self.credit = credit
            self.conn = conn
            self.session = Session(self.conn)

            # Get GRN data using SQLAlchemy
            grn_query = self.session.query(DB.GRN).filter(DB.GRN.supplier_id == self.id).all()
            self.grn = [g.__dict__ for g in grn_query]

            self.supplierDetails = supplierDetails
            self.grnTable = grnTable

            self.data[self.id] = ft.DataRow(
                [
                    ft.DataCell(
                        ft.Text(str(self.id)),
                    ),
                    ft.DataCell(
                        ft.Column(
                            [
                                ft.Text(str(self.name)),
                                ft.Text(str(self.company_name)),
                            ]
                        )
                    ),
                    ft.DataCell(
                        ft.Text(str(self.credit)),
                    )
                ],
                on_select_changed=self.select,
            )

            self.page.update()

        def id_name(self, iid: str, n):
            v = str(iid)
            for i in [10 ** i for i in range(n, 0, -1)]:
                if iid < i:
                    v = "0" + v
            return v

        def select(self, e):
            for i, row in self.data.items():
                row.color = ft.Colors.WHITE

            e.control.color = theme_color + "50"

            self.supplierDetails.content = ft.Row(
                [
                    ft.Row(
                        [
                            ft.Icon(
                                ft.Icons.ACCOUNT_CIRCLE,
                                color=theme_color
                            ),
                            ft.Text(
                                str(self.name),
                                size=12,
                                weight=ft.FontWeight.BOLD,
                                selectable=True
                            )
                        ]
                    ),
                    ft.Row(
                        [
                            ft.Icon(
                                ft.Icons.BUSINESS,
                                color=theme_color
                            ),
                            ft.Text(
                                f"{self.company_name}, {self.address}",
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
                                f"{self.mobile} | {self.land_line}",
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

            # Get GRN data using SQLAlchemy
            grn_query = self.session.query(DB.GRN).filter(DB.GRN.supplier_id == self.id).all()
            result = [g.__dict__ for g in grn_query]

            self.grnTable.rows = [
                ft.DataRow(
                    [
                        ft.DataCell(
                            ft.Text(f'grn-{self.id_name(grn["id"], 8)}'),
                        ),
                        ft.DataCell(
                            ft.Text(str(grn["created_on"])),
                        ),
                        ft.DataCell(
                            ft.Text(str(grn["total_amount"])),
                        ),
                        ft.DataCell(
                            ft.Text(str(grn["paid_amount"])),
                        ),
                        ft.DataCell(
                            ft.Text(str(grn["status"])),
                        ),
                        ft.DataCell(
                            ft.Text(str(grn["user_id"])),
                        )
                    ]
                ) for grn in result
            ]

            self.page.update()

    def filter_supplier(self, e):
        query = e.control.value.lower()

        # Use SQLAlchemy for supplier search
        suppliers_query = self.session.query(DB.Supplier).filter(
            or_(
                DB.Supplier.name.ilike(f"%{query}%"),
                DB.Supplier.phone_number.ilike(f"%{query}%"),
                DB.Supplier.company_name.ilike(f"%{query}%"),
                DB.Supplier.land_line.ilike(f"%{query}%"),
                DB.Supplier.email.ilike(f"%{query}%"),
                DB.Supplier.address.ilike(f"%{query}%"),
                DB.Supplier.code.ilike(f"%{query}%")
            )
        ).limit(20).all()

        result = [s.__dict__ for s in suppliers_query]

        self.Supplier.data = dict()

        for supplier in result:
            self.Supplier(
                self.page,
                supplier["id"],
                supplier["name"],
                supplier["company_name"],
                supplier["code"],
                supplier["phone_number"],
                supplier["land_line"],
                supplier["email"],
                supplier["address"],
                supplier["credit"],
                self.grn_table,
                self.supplier_details,
                self.conn
            )

        self.supplier_details_container.content = ft.Container(
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
                                                    ft.Text("Name / Company Name")
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
                                                    rows=list(self.Supplier.data.values()),
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

    def build(self):
        self.main_content = ft.Column(
            [
                ft.Container(
                    self.header,
                ),
                ft.Container(
                    ft.ResponsiveRow(
                        [
                            ft.Container(
                                ft.Column(
                                    [
                                        self.search_section,
                                        self.supplier_details_container
                                    ],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                    expand=True
                                ),
                                expand=True,
                                col={"sm": 12, "md": 12, "lg": 5, "xl": 4},
                            ),
                            ft.Container(
                                ft.Column(
                                    [
                                        ft.Container(
                                            self.grn_section,
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
                                col={"sm": 12, "md": 12, "lg": 7, "xl": 8},
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


def supplierDetails(page: ft.Page, conn, user_id):
    app = SupplierDetails(page, conn, user_id)
    return app.build()


if __name__ == "__main__":
    ft.app(supplierDetails)