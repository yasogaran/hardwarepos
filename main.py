import threading
import time
from datetime import datetime

import flet as ft
from flet import (
    Page, Row, Column, Text, Icon, Icons, Container,
    Colors, margin, IconButton
)

from DB import connect_db
from dashboardUI import dashboard
from addStockUI import addStock
from addProductUI import addProduct
from recentTransactionUI import recentTransaction
from billingUI import bill
from grnUI import grn
from customersDetailsUI import customerDetails
from supplierDetailsUI import supplierDetails
from accountsUI import accounts
from settingsUI import settings
from chequeManagementUI import chequeManagement

CONN, engine = connect_db()

USER_ID = 1
ACCOUNT_ID = 1

def main(page: Page):
    global ACCOUNT_ID

    page.window.maximized = True

    def handle_resize(e):
        if page.width < 1080:
            toggle_sidebar()
        page.update()

    page.title = "Dashboard"
    page.theme_mode = "light"
    page.padding = 5
    page.window.center()
    page.on_resized = handle_resize

    # Nav items
    nav_items = [
        {"icon": Icons.DASHBOARD, "label": "Dashboard", "function": dashboard},
        {"icon": Icons.RECEIPT, "label": "Billing", "function": bill},
        {"icon": Icons.HISTORY, "label": "Recent Transactions", "function": recentTransaction},
        {"icon": Icons.PEOPLE, "label": "Customer Details", "function": customerDetails},
        {"icon": Icons.INVENTORY, "label": "Add Stock", "function": grn},
        {"icon": Icons.ADD_SHOPPING_CART, "label": "Add Product", "function": addProduct},
        {"icon": Icons.BUSINESS, "label": "Supplier Details", "function": supplierDetails},
        {"icon": Icons.CURRENCY_EXCHANGE, "label": "Report", "function": accounts},
        {"icon": Icons.PAYMENTS, "label": "Cheque", "function": chequeManagement},
        {"icon": Icons.SETTINGS, "label": "Settings", "function": settings},
    ]

    # State variables
    selected_index = 0  # Changed from 3 to 0 to avoid index issues
    is_sidebar_compact = True

    # Create a nav item widget
    def create_nav_item(item, index):
        return Container(
            expand=True,
            content=Row(
                controls=[
                    Icon(item["icon"], size=24),
                    Text(item["label"], size=14, opacity=1 if not is_sidebar_compact else 0),
                ],
                spacing=15,
            ),
            padding=15,
            border_radius=5,
            bgcolor=Colors.BLUE_200 if selected_index == index else None,
            on_hover=lambda e: highlight_item(e, index),
            on_click=lambda e: select_nav_item(index),
            tooltip=item["label"] if is_sidebar_compact else None,
        )

    # Highlight item on hover
    def highlight_item(e, index):
        if selected_index != index:
            e.control.bgcolor = Colors.BLUE_100 if e.data == "true" else None
        e.control.update()

    # Select nav item
    def select_nav_item(index):
        nonlocal selected_index
        # try:
        #     CONN.commit()
        # except:
        #     CONN.rollback()
        #     CONN.begin()

        selected_index = index
        update_nav_items()
        update_content()
        page.update()
        CONN.commit()

    # Toggle sidebar between compact and full
    def toggle_sidebar(e=None):
        nonlocal is_sidebar_compact
        is_sidebar_compact = not is_sidebar_compact
        nav_container.width = 250 if not is_sidebar_compact and page.width > 720 else 50
        toggle_btn.icon = Icons.ARROW_FORWARD if is_sidebar_compact else Icons.ARROW_BACK
        update_nav_items()
        page.update()

    # Update all nav items
    def update_nav_items():
        nav_column.controls = [create_nav_item(item, i) for i, item in enumerate(nav_items)]
        page.update()

    # Update content area
    def update_content():
        # Create the header row
        header_row = Container(
            content=Row(
                controls=[
                    Row([
                        Container(
                            ft.Image(
                                "src/profile.png",
                                width=50,
                                height=50,
                                fit=ft.ImageFit.COVER
                            ),
                            border_radius=25, height=50, width=50,
                        ),
                        Column(
                            controls=[
                                Text("Welcome back, Admin!", size=24, weight=ft.FontWeight.BOLD),
                                Text("Here's what's happening with your store today", size=14)
                            ],
                            spacing=0,
                        )
                    ]),
                    Column([clock, date_display])
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            ),
        )

        # Get the content from the selected function
        try:
            content_widget = nav_items[selected_index]["function"](page, CONN, USER_ID)
        except Exception as e:
            print(f"Error loading content: {e}")
            content_widget = Text(f"Error loading {nav_items[selected_index]['label']}")

        # Update content area
        content_area.content = Column(
            controls=[
                header_row,
                Container(bgcolor=Colors.GREY, height=3),
                content_widget
            ],
            expand=True
        )
        page.update()

    # Navigation column with custom items
    nav_column = Column(
        controls=[create_nav_item(item, i) for i, item in enumerate(nav_items)],
        spacing=5,
    )

    toggle_btn = IconButton(
        icon=Icons.ARROW_FORWARD,
        on_click=toggle_sidebar,
        icon_size=20,
    )

    # Navigation container
    nav_container = Container(
        width=50,
        bgcolor=Colors.GREY_100,
        animate=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
        content=Column(
            controls=[
                toggle_btn,
                Container(height=20),
                nav_column,
            ],
        )
    )

    # Clock and date display
    clock = Text(
        value=datetime.now().strftime("%H:%M:%S"),
        weight=ft.FontWeight.BOLD,
        text_align=ft.TextAlign.RIGHT,
    )

    date_display = Text(
        value=datetime.now().strftime("%A, %B %d, %Y"),
        text_align=ft.TextAlign.RIGHT,
    )

    # Function to update time
    def update_time():
        while True:
            now = datetime.now()
            clock.value = now.strftime("%H:%M:%S")
            date_display.value = now.strftime("%A, %B %d, %Y")
            try:
                page.update()
            except:
                break  # Stop if page is closed
            time.sleep(1)

    # Start the clock update thread
    clock_thread = threading.Thread(target=update_time, daemon=True)
    clock_thread.start()

    # Content area
    content_area = Container(
        expand=True,
        padding=20,
        content=Column(
            controls=[
                # Header will be added in update_content
                # Main content will be added in update_content
            ],
            expand=True
        )
    )

    # Initialize the content
    update_content()

    def cls(e):
        CONN.commit()
        CONN.close()

    page.on_close = cls

    # Main layout
    page.add(
        Row(
            expand=True,
            controls=[
                nav_container,
                Container(width=1, bgcolor=Colors.GREY_300),
                content_area,
            ],
            spacing=0
        )
    )

if __name__ == "__main__":
    ft.app(target=main, upload_dir="")