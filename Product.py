import flet as ft
from datetime import datetime
import math


class Product:
    def __init__(self, id, title, category, status, min_price, max_price, quantity, created_at):
        self.id = id
        self.title = title
        self.category = category
        self.status = status
        self.min_price = min_price
        self.max_price = max_price
        self.quantity = quantity
        self.created_at = created_at


def main(page: ft.Page):
    page.title = "Bathware Ceramic Shop - Product Listing"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.scroll = ft.ScrollMode.AUTO

    # Sample data
    products = [
        Product(1, "Premium Toilet Suite", "Toilets", "Active", 250, 450, 15, "2024-01-15"),
        Product(2, "Ceramic Basin White", "Basins", "Active", 120, 200, 8, "2024-01-20"),
        Product(3, "Luxury Bathtub", "Bathtubs", "Low Stock", 800, 1200, 3, "2024-01-18"),
        Product(4, "Floor Tiles Ceramic", "Tiles", "Active", 25, 45, 200, "2024-01-22"),
        Product(5, "Bathroom Accessories Set", "Accessories", "Active", 35, 85, 25, "2024-01-25"),
        Product(6, "Wall Mount Basin", "Basins", "Inactive", 180, 280, 0, "2024-01-12"),
        Product(7, "Corner Toilet", "Toilets", "Active", 320, 520, 12, "2024-01-28"),
        Product(8, "Mosaic Tiles Blue", "Tiles", "Active", 45, 75, 150, "2024-01-30"),
    ]

    # State variables
    current_page = 1
    results_per_page = 25
    sort_column = "created_at"
    sort_direction = "desc"
    current_view = "list"
    filtered_products = products.copy()

    # UI Components
    title_filter = ft.TextField(
        label="Title",
        hint_text="Search by title...",
        expand=True,
    )

    category_filter = ft.Dropdown(
        label="Category",
        options=[
            ft.dropdown.Option("", "All Categories"),
            ft.dropdown.Option("Toilets"),
            ft.dropdown.Option("Basins"),
            ft.dropdown.Option("Bathtubs"),
            ft.dropdown.Option("Tiles"),
            ft.dropdown.Option("Accessories"),
        ],
        expand=True,
    )

    status_filter = ft.Dropdown(
        label="Status",
        options=[
            ft.dropdown.Option("", "All Status"),
            ft.dropdown.Option("Active"),
            ft.dropdown.Option("Inactive"),
            ft.dropdown.Option("Low Stock"),
        ],
        expand=True,
    )

    results_per_page_dropdown = ft.Dropdown(
        width=100,
        options=[
            ft.dropdown.Option("10"),
            ft.dropdown.Option("25"),
            ft.dropdown.Option("50"),
            ft.dropdown.Option("100"),
        ],
        value="25",
    )

    # Header
    header = ft.Container(
        content=ft.Row(
            controls=[
                ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.BATHTUB, color=ft.Colors.BLUE),
                        ft.Text("Bathware Ceramic Shop", size=20, weight=ft.FontWeight.BOLD),
                    ],
                    alignment=ft.MainAxisAlignment.START,
                ),
                ft.ElevatedButton(
                    "Add Product",
                    icon=ft.Icons.ADD,
                    on_click=lambda e: print("Add Product clicked"),
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        padding=ft.padding.symmetric(vertical=20, horizontal=40),
        bgcolor=ft.Colors.WHITE,
        border=ft.border.only(bottom=ft.border.BorderSide(1, ft.Colors.GREY_300)),
    )

    # Filters Section
    filters_section = ft.Card(
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.FILTER_ALT, color=ft.Colors.BLUE),
                        ft.Text("Filters", size=16, weight=ft.FontWeight.BOLD),
                    ],
                ),
                ft.Row(
                    controls=[
                        title_filter,
                        category_filter,
                        status_filter,
                    ],
                    spacing=20,
                ),
                ft.Row(
                    controls=[
                        ft.ElevatedButton(
                            "Apply Filters",
                            icon=ft.Icons.SEARCH,
                            # on_click=apply_filters,
                        ),
                        ft.OutlinedButton(
                            "Clear",
                            icon=ft.Icons.CLEAR,
                            # on_click=clear_filters,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.END,
                    spacing=10,
                ),
            ],
            spacing=20,
        ),
        margin=ft.margin.symmetric(vertical=10, horizontal=40),
    )

    # Controls Section
    controls_section = ft.Card(
        content=ft.Row(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text("Show:"),
                        results_per_page_dropdown,
                        ft.Text("results per page"),
                    ],
                    alignment=ft.MainAxisAlignment.START,
                    spacing=10,
                ),
                ft.Row(
                    controls=[
                        ft.Text("View:"),
                        ft.IconButton(
                            icon=ft.Icons.LIST,
                            selected=True,
                            on_click=lambda e: switch_view("list"),
                        ),
                        ft.IconButton(
                            icon=ft.Icons.GRID_VIEW,
                            on_click=lambda e: switch_view("grid"),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.END,
                    spacing=5,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        margin=ft.margin.symmetric(vertical=10, horizontal=40),
    )

    # Table View
    table_view = ft.Container(
        content=ft.Column(),
        margin=ft.margin.symmetric(horizontal=40),
    )

    # Grid View
    grid_view = ft.GridView(
        runs_count=4,
        child_aspect_ratio=1,
        spacing=20,
        run_spacing=20,
        padding=40,
        visible=False,
    )

    # Pagination
    showing_from = ft.Text("1")
    showing_to = ft.Text("25")
    total_results = ft.Text(str(len(products)))

    pagination_section = ft.Card(
        content=ft.Row(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text("Showing"),
                        showing_from,
                        ft.Text("to"),
                        showing_to,
                        ft.Text("of"),
                        total_results,
                        ft.Text("results"),
                    ],
                    spacing=5,
                ),
                ft.Row(
                    controls=[
                        ft.OutlinedButton(
                            "Previous",
                            icon=ft.Icons.CHEVRON_LEFT,
                            # on_click=previous_page,
                        ),
                        # ft.Row(id="page_numbers"),
                        ft.OutlinedButton(
                            "Next",
                            icon=ft.Icons.CHEVRON_RIGHT,
                            # icon_right=True,
                            # on_click=next_page,
                        ),
                    ],
                    spacing=5,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        margin=ft.margin.symmetric(vertical=10, horizontal=40),
    )

    # Main content column
    main_content = ft.Column(
        controls=[
            filters_section,
            controls_section,
            table_view,
            grid_view,
            pagination_section,
        ],
        spacing=0,
        expand=True,
    )

    # Add everything to page
    page.add(
        ft.Column(
            controls=[
                header,
                main_content,
            ],
            spacing=0,
            expand=True,
        )
    )

    # Helper functions
    def get_status_color(status):
        if status == "Active":
            return ft.Colors.GREEN
        elif status == "Inactive":
            return ft.Colors.RED
        elif status == "Low Stock":
            return ft.Colors.AMBER
        else:
            return ft.Colors.GREY

    def format_date(date_string):
        date_obj = datetime.strptime(date_string, "%Y-%m-%d")
        return date_obj.strftime("%b %d, %Y")

    def sort_products():
        reverse = sort_direction == "desc"

        if sort_column == "id":
            filtered_products.sort(key=lambda p: p.id, reverse=reverse)
        elif sort_column == "title":
            filtered_products.sort(key=lambda p: p.title, reverse=reverse)
        elif sort_column == "status":
            filtered_products.sort(key=lambda p: p.status, reverse=reverse)
        elif sort_column == "min_price":
            filtered_products.sort(key=lambda p: p.min_price, reverse=reverse)
        elif sort_column == "quantity":
            filtered_products.sort(key=lambda p: p.quantity, reverse=reverse)
        elif sort_column == "created_at":
            filtered_products.sort(key=lambda p: p.created_at, reverse=reverse)

    def render_products():
        sort_products()

        start_index = (current_page - 1) * results_per_page
        end_index = start_index + results_per_page
        paginated_products = filtered_products[start_index:end_index]

        if current_view == "list":
            render_table_view(paginated_products)
        else:
            render_grid_view(paginated_products)

        update_pagination()

    def render_table_view(products):
        rows = []

        # Header row
        header_row = ft.DataRow(
            cells=[
                ft.DataCell(ft.Text("ID", weight=ft.FontWeight.BOLD), on_tap=lambda e: sort_by("id")),
                ft.DataCell(ft.Text("Title", weight=ft.FontWeight.BOLD), on_tap=lambda e: sort_by("title")),
                ft.DataCell(ft.Text("Status", weight=ft.FontWeight.BOLD), on_tap=lambda e: sort_by("status")),
                ft.DataCell(ft.Text("Price Range", weight=ft.FontWeight.BOLD), on_tap=lambda e: sort_by("min_price")),
                ft.DataCell(ft.Text("Quantity", weight=ft.FontWeight.BOLD), on_tap=lambda e: sort_by("quantity")),
                ft.DataCell(ft.Text("Created At", weight=ft.FontWeight.BOLD), on_tap=lambda e: sort_by("created_at")),
                ft.DataCell(ft.Text("Actions", weight=ft.FontWeight.BOLD)),
            ],
        )
        rows.append(header_row)

        # Data rows
        for product in products:
            row = ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(str(product.id))),
                    ft.DataCell(
                        ft.Column([
                            ft.Text(product.title, weight=ft.FontWeight.BOLD),
                            ft.Text(product.category, color=ft.Colors.GREY),
                        ], spacing=0)
                    ),
                    ft.DataCell(
                        ft.Container(
                            content=ft.Text(product.status),
                            padding=ft.padding.symmetric(horizontal=10, vertical=5),
                            border_radius=20,
                            bgcolor=get_status_color(product.status).with_opacity(0.2),
                            border=ft.border.all(1, get_status_color(product.status)),
                        )
                    ),
                    ft.DataCell(ft.Text(f"${product.min_price} - ${product.max_price}")),
                    ft.DataCell(
                        ft.Text(
                            str(product.quantity),
                            color=ft.Colors.RED if product.quantity < 5 else None,
                            weight=ft.FontWeight.BOLD if product.quantity < 5 else None,
                        )
                    ),
                    ft.DataCell(ft.Text(format_date(product.created_at))),
                    ft.DataCell(
                        ft.Row([
                            ft.TextButton(
                                "Edit Stocks",
                                icon=ft.Icons.INVENTORY,
                                on_click=lambda e, p=product: edit_stocks(p),
                            ),
                            ft.TextButton(
                                "Edit Product",
                                icon=ft.Icons.EDIT,
                                on_click=lambda e, p=product: edit_product(p),
                            ),
                        ], spacing=5)
                    ),
                ],
            )
            rows.append(row)

        table_view.content = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("ID")),
                ft.DataColumn(ft.Text("Title")),
                ft.DataColumn(ft.Text("Status")),
                ft.DataColumn(ft.Text("Price Range")),
                ft.DataColumn(ft.Text("Quantity")),
                ft.DataColumn(ft.Text("Created At")),
                ft.DataColumn(ft.Text("Actions")),
            ],
            rows=rows,
            divider_thickness=1,
            vertical_lines=ft.border.BorderSide(1, ft.Colors.GREY_300),
            horizontal_lines=ft.border.BorderSide(1, ft.Colors.GREY_300),
        )

    def render_grid_view(products):
        grid_view.controls = []

        for product in products:
            card = ft.Card(
                content=ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text(product.title, weight=ft.FontWeight.BOLD, expand=True),
                                    ft.Container(
                                        content=ft.Text(product.status),
                                        padding=ft.padding.symmetric(horizontal=10, vertical=5),
                                        border_radius=20,
                                        bgcolor=get_status_color(product.status).with_opacity(0.2),
                                        border=ft.border.all(1, get_status_color(product.status)),
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            ),
                            ft.Divider(),
                            ft.Row(
                                controls=[
                                    ft.Text("Category:"),
                                    ft.Text(product.category, weight=ft.FontWeight.BOLD),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            ),
                            ft.Row(
                                controls=[
                                    ft.Text("Price Range:"),
                                    ft.Text(f"${product.min_price}-${product.max_price}", weight=ft.FontWeight.BOLD),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            ),
                            ft.Row(
                                controls=[
                                    ft.Text("Quantity:"),
                                    ft.Text(
                                        str(product.quantity),
                                        color=ft.Colors.RED if product.quantity < 5 else None,
                                        weight=ft.FontWeight.BOLD if product.quantity < 5 else None,
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            ),
                            ft.Row(
                                controls=[
                                    ft.Text("Created:"),
                                    ft.Text(format_date(product.created_at)),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            ),
                            ft.Divider(),
                            ft.Row(
                                controls=[
                                    ft.ElevatedButton(
                                        "Edit Stocks",
                                        icon=ft.Icons.INVENTORY,
                                        on_click=lambda e, p=product: edit_stocks(p),
                                        expand=True,
                                    ),
                                    ft.ElevatedButton(
                                        "Edit Product",
                                        icon=ft.Icons.EDIT,
                                        on_click=lambda e, p=product: edit_product(p),
                                        expand=True,
                                    ),
                                ],
                                spacing=10,
                            ),
                        ],
                        spacing=10,
                    ),
                    padding=20,
                    width=300,
                ),
            )
            grid_view.controls.append(card)

    def sort_by(column):
        nonlocal sort_column, sort_direction

        if sort_column == column:
            sort_direction = "desc" if sort_direction == "asc" else "asc"
        else:
            sort_column = column
            sort_direction = "asc"

        current_page = 1
        render_products()

    def apply_filters(e):
        nonlocal filtered_products, current_page

        title = title_filter.value.lower() if title_filter.value else ""
        category = category_filter.value if category_filter.value else ""
        status = status_filter.value if status_filter.value else ""

        filtered_products = [
            p for p in products
            if (not title or title in p.title.lower()) and
               (not category or category == p.category) and
               (not status or status == p.status)
        ]

        current_page = 1
        render_products()

    def clear_filters(e):
        title_filter.value = ""
        category_filter.value = ""
        status_filter.value = ""
        filtered_products = products.copy()
        current_page = 1
        render_products()

    def switch_view(view):
        nonlocal current_view

        current_view = view

        if view == "list":
            table_view.visible = True
            grid_view.visible = False
        else:
            table_view.visible = False
            grid_view.visible = True

        render_products()

    def change_results_per_page(e):
        nonlocal results_per_page, current_page

        results_per_page = int(results_per_page_dropdown.value)
        current_page = 1
        render_products()

    def update_pagination():
        total = len(filtered_products)
        pages = math.ceil(total / results_per_page)

        start = (current_page - 1) * results_per_page + 1
        end = min(current_page * results_per_page, total)

        showing_from.value = str(start)
        showing_to.value = str(end)
        total_results.value = str(total)

        # Update page numbers
        page_numbers = page.controls[0].content.controls[1].controls[3].controls[1]
        page_numbers.controls = []

        start_page = max(1, current_page - 2)
        end_page = min(pages, current_page + 2)

        for i in range(start_page, end_page + 1):
            page_button = ft.TextButton(
                str(i),
                on_click=lambda e, p=i: go_to_page(p),
                style=ft.ButtonStyle(
                    bgcolor=ft.Colors.BLUE if i == current_page else None,
                    color=ft.Colors.WHITE if i == current_page else None,
                ),
            )
            page_numbers.controls.append(page_button)

        page.update()

    def go_to_page(page_num):
        nonlocal current_page
        current_page = page_num
        render_products()

    def previous_page(e):
        nonlocal current_page
        if current_page > 1:
            current_page -= 1
            render_products()

    def next_page(e):
        nonlocal current_page
        total_pages = math.ceil(len(filtered_products) / results_per_page)
        if current_page < total_pages:
            current_page += 1
            render_products()

    def edit_stocks(product):
        print(f"Editing stocks for product: {product.title}")

    def edit_product(product):
        print(f"Editing product: {product.title}")

    # Initialize
    results_per_page_dropdown.on_change = change_results_per_page
    render_products()


ft.app(target=main)