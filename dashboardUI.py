import select
import DB
import flet as ft
from flet import (
    Page, Row, Column, Text, Icon, Icons, Container,
    Colors, padding, margin, BorderRadius, IconButton
)
from flet.core.responsive_row import ResponsiveRow
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from datetime import datetime

import pandas as pd

CONN:create_engine

SESSION:Session

def percentage(page, n):
    return page * n / 100

def dashboard_row_1(page):
    def box(title, text, clr, icon, ):
        bgClr = clr + "50"
        out = Row(
                controls=[
                    Container(
                        content=Row(
                            controls=[
                                Container(
                                    content=Column(
                                        controls=[
                                            Text(title, size=14, weight=ft.FontWeight.BOLD,),
                                            Text(text, size=24, weight=ft.FontWeight.BOLD, color=clr),
                                        ],
                                        spacing=15
                                    ),
                                    expand=True,
                                ),
                                Container(
                                    content=Icon(icon, clr, 25),
                                    bgcolor=bgClr,
                                    border_radius=5,
                                    padding=percentage(page.width, 0.5),
                                )
                            ]
                        ),
                        bgcolor=Colors.WHITE,
                        padding=15,
                        border_radius=15,
                        expand=True,
                        shadow=ft.BoxShadow(
                            spread_radius=0.81,
                            blur_radius= 3,
                            color=ft.Colors.BLACK12,
                            offset=ft.Offset(1, 1),
                            blur_style=ft.ShadowBlurStyle.NORMAL,
                        )
                    ),
                ],
                col={"sm": 12, "md": 6, "lg": 6, "xl": 3},
            )
        return out
   
    today = datetime(datetime.today().year, datetime.today().month, datetime.today().day)
    
    todayIncome = 0
    todayExpenses = 0
    pendingPayments = 0
    totalIncome = 0
    totalExpenses = 0

    try:
        todayIncome = \
        pd.read_sql(f"SELECT SUM(paid_amount) FROM invoices WHERE created_on>='{today}' AND status='paid';",
                    CONN).to_dict('records')[0]["SUM(paid_amount)"]
        todayExpenses = \
        pd.read_sql(f"SELECT SUM(paid_amount) FROM grn WHERE created_on>='{today}' AND status='paid';", CONN).to_dict(
            'records')[0]["SUM(paid_amount)"]
        pendingPayments = \
        pd.read_sql(f"SELECT SUM(paid_amount) FROM grn WHERE status = 'pending';", CONN).to_dict('records')[0][
            "SUM(paid_amount)"]

        totalIncome = float(pd.read_sql("SELECT SUM(amount) FROM invoice_transactions;", CONN).to_dict('records')[0]["SUM(amount)"])
        totalExpenses = float(
            pd.read_sql(f"SELECT SUM(amount) FROM grn_transactions; ", CONN).to_dict('records')[0]["SUM(amount)"])
    except:
        pass



    lst = [
        ["Today Income", f"LKR. {todayIncome if todayIncome else 0}", Colors.GREEN, Icons.ARROW_DOWNWARD],
        ["Today Expense", f"LKR. {todayExpenses if todayExpenses else 0}", Colors.RED, Icons.ARROW_UPWARD],
        [f"Current Cash", f"LKR. {round(totalIncome - totalExpenses, 2)}", Colors.BLUE, Icons.WALLET],
        ["Pending Payments", f"LKR. {pendingPayments}", Colors.ORANGE, Icons.PAYMENTS],
    ]


    return ResponsiveRow(
            controls=[
                box(title, amount, clr, icon) for title, amount, clr, icon in lst
            ],
            spacing=percentage(page.width, 2),
        )


def pending_payments_tab(page):
    def box(company_name, amount, text, clr):
        out = Row(
            controls=[
                Container(width=3, bgcolor=clr, height=85, alignment=ft.Alignment(0, 0)),
                Column(
                    controls=[
                        Text(company_name, size=18, weight=ft.FontWeight.BOLD),
                        Text(amount, size=18, weight=ft.FontWeight.BOLD, color=clr),
                        Text(text, size=14),
                    ],
                    spacing=5
                ),
            ],
            spacing=10,

        )
        return out

    lst = [
        ["Ceramic World Ltd.", "LKR. 1250", "Payment for premium bathroom tiles and fixtures delivered last week. Due date: Tomorrow", Colors.ORANGE,],
        ["Royal Bath Supplies", "LKR. 950.00", "Outstanding balance for luxury bathtub collection. Payment overdue by 3 days", Colors.RED,],
        ["Tile Masters Inc.", "1,000.00", "Monthly supply agreement payment for ceramic floor tiles. Due in 5 days", Colors.GREEN_ACCENT_400,],
        ["Ceramic World Ltd.", "LKR. 1250", "Payment for premium bathroom tiles and fixtures delivered last week. Due date: Tomorrow", Colors.ORANGE,],
        ["Royal Bath Supplies", "LKR. 950.00", "Outstanding balance for luxury bathtub collection. Payment overdue by 3 days", Colors.RED,],
    ]

    return Column(
        controls=[
            box(name, amount, text, clr) for name, amount, text, clr in lst
        ],
        spacing=20,
        expand=True,
        scroll=ft.ScrollMode.AUTO


    )


def most_sold_tab(page):
    def box(title, count, clr):
        bgClr = clr+"50"
        out = Container(
            content=Row(
                controls=[
                    Text(title, size=14, expand=True, weight=ft.FontWeight.BOLD),
                    Container(
                        content=Text(f"{count} Units", size=14, color=clr, weight=ft.FontWeight.BOLD),
                        padding=5,
                        border_radius=15,
                        bgcolor=bgClr,
                    )
                ],

            ),
            bgcolor=Colors.GREY_50,
            border_radius=5,
            padding=10,

        )
        return out

    lst = [
        ["Premium Wall Tiles", 142, Colors.BLUE],
        ["Ceramic Floor Tiles", 32, Colors.ORANGE],
        ["Bathroom Fixtures Set", 89, Colors.GREEN],
        ["Designer Washbasins", 76, Colors.YELLOW],
        ["Luxury Bathtubs", 42, Colors.PURPLE],
        ["Premium Wall Tiles", 142, Colors.BLUE]
    ]

    return Column(
        controls=[
            box(title, unit, clr) for title, unit, clr in lst
        ],
        spacing=15,
        expand=True,
        scroll=ft.ScrollMode.AUTO,
    )


def content_box(page, icon, icon_clr, title, content, ht):
    out = Container(
        content=Column(
            controls=[
                Row(
                    controls=[
                        Icon(icon, size=30, color=icon_clr),
                        Text(title, size=20, expand=True, weight=ft.FontWeight.BOLD),
                    ]
                ),
                content
            ],
            spacing=20,
        ),
        height=percentage(page.height, ht),
        padding=20,
        col={"sm": 12, "md": 12, "lg": 6, "xl": 6},
        bgcolor=Colors.WHITE,
        shadow=ft.BoxShadow(
            spread_radius=0.81,
            blur_radius=3,
            color=ft.Colors.BLACK12,
            offset=ft.Offset(1, 1),
            blur_style=ft.ShadowBlurStyle.NORMAL,
        ),
        border_radius=15,
        expand=True,

    )
    return out


def dashboard_row_2(page):
    return ResponsiveRow(
        controls=[
            content_box(page, Icons.WARNING, Colors.ORANGE, "Pending Payments to Suppliers", pending_payments_tab(page), 40),
            content_box(page, Icons.ANALYTICS, Colors.GREEN_300, "Most Sold Products", most_sold_tab(page), 40),
        ],
        spacing=percentage(page.width, 2),
    )


def low_stock_tab(page):
    def box(title, count, clr):
        bdrClr = clr
        bgClr = clr+"50"
        txtClr = clr+"900"
        clr += "100"
        out = Container(
            content=Row(
                controls=[
                    Container(
                        expand=True,
                        content=Row(
                            controls=[
                                Text(title, size=14, expand=True, weight=ft.FontWeight.BOLD),
                                Container(
                                    content=Text(f"{count} Units", size=13, color=txtClr, weight=ft.FontWeight.BOLD),
                                    padding=7,
                                    border_radius=15,
                                    bgcolor=clr,
                                )
                            ]
                        ),
                        padding=10,
                    ),
                ],
            ),
            border_radius=10,
            bgcolor=bgClr,
            expand=True,
            margin=ft.Margin(4, 0, 0, 0),
            border=ft.border.only(left=ft.border.BorderSide(4, bdrClr))
        )


        return out

    lst = [
        ["Premium Wall Tiles", 142, Colors.RED],
        ["Ceramic Floor Tiles", 32, Colors.RED],
        ["Bathroom Fixtures Set", 89 , Colors.RED],
        ["Designer Washbasins", 76 , Colors.RED],
        ["Luxury Bathtubs", 42 , Colors.RED]
    ]

    return Column(
        controls=[
            box(title, unit, clr) for title, unit, clr in lst
        ],
        spacing=12,
        expand=True,
        scroll=ft.ScrollMode.AUTO,
    )

def expiry_alert_tab(page):
    def box(title, days, count, clr):
        bdrClr = clr
        bgClr = clr+"50"
        txtClr = clr+"900"
        clr += "100"
        out = Container(
                content=Row(
                    controls=[
                        Container(
                            expand=True,
                            content=Row(
                                controls=[
                                    Column(
                                        controls=[
                                            Text(title, size=15, expand=True, weight=ft.FontWeight.BOLD),
                                            Text(f"Expires in {days} days", size=13, expand=True),
                                        ],
                                        spacing=2,
                                        expand=True,
                                    ),
                                    Container(
                                        content=Text(f"{count} Units", size=14, color=txtClr, weight=ft.FontWeight.BOLD),
                                        padding=5,
                                        border_radius=15,
                                        bgcolor=clr,
                                    )
                                ]
                            ),
                            padding=10,
                        ),
                    ],
                ),
                border_radius=10,
                bgcolor=bgClr,
                expand=True,
                margin=ft.Margin(4, 0, 0, 0),
                border=ft.border.only(left=ft.border.BorderSide(4, txtClr))
            )

        return out

    lst = [
        ["Tile Adhesive Premium", 15, 25, Colors.PURPLE],
        ["Grout Sealer", 10, 30, Colors.BLUE],
        ["Cleaning Solutions", 45, 50, Colors.GREEN],
        ["Tile Adhesive Premium", 15, 25, Colors.PURPLE],
        ["Grout Sealer", 10, 30, Colors.BLUE],
    ]

    return Column(
        controls=[
            box(title, days, count, clr) for title, days, count, clr in lst
        ],
        spacing=15,
        expand=True,
        scroll=ft.ScrollMode.AUTO,
    )

def dashboard_row_3(page):
    return ResponsiveRow(
        controls=[
            content_box(page, Icons.DANGEROUS, Colors.RED, "Low Stock Alert", low_stock_tab(page), 33),
            content_box(page, Icons.CALENDAR_VIEW_MONTH, Colors.PURPLE, "Expiry Alert", expiry_alert_tab(page), 33)
        ],
        spacing=percentage(page.width, 2),
    )

def dashboard(page, conn, user_id):
    global CONN, SESSION

    CONN = conn
    SESSION = Session(CONN)
    return Container(
        content=Column(
            controls=[
                dashboard_row_1(page),
                dashboard_row_2(page),
                dashboard_row_3(page),
            ],
            spacing=percentage(page.height, 2),
        ),
        padding=percentage(page.width, 1),

    )
