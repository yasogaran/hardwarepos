import os.path
import shutil
import flet as ft
from datetime import datetime
from sqlalchemy import insert, update, select, func, or_
from sqlalchemy.orm import Session, sessionmaker

# Assuming DB.py contains SQLAlchemy models
import DB

from imggen import generate

selected_unit = ''


def addProduct(page: ft.Page, session: Session, user_id):
    session = Session(session)
    # Load initial data using SQLAlchemy ORM
    products_q = session.query(DB.Product).all()
    products = [p.__dict__ for p in products_q]

    units_q = session.query(DB.Unit.id, DB.Unit.unit).all()
    units = {i.id: i.unit for i in units_q}

    category_q = session.query(DB.Category.id, DB.Category.name).all()
    category = {c.name: c.id for c in category_q}

    sub_category_q = session.query(DB.SubCategory.id, DB.SubCategory.name, DB.SubCategory.category_id).all()
    tmp_sb_ctg = {s.id: [s.name, s.category_id] for s in sub_category_q}

    header = ft.Row(
        controls=[
            ft.Column(
                controls=[
                    ft.Text("Add Product", size=28, weight=ft.FontWeight.BOLD, color="#1f2937"),
                    ft.Text("Add new/ modify old products", color="#6b7280")
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

    def gen_product_code(e):
        if e.control.value:
            image_generate.disabled = False
        else:
            image_generate.disabled = True
        if submit_btn.text == "Add Product":
            # Use SQLAlchemy to get max ID
            max_id = session.query(func.max(DB.Product.id)).scalar()
            i = max_id if max_id is not None else 0

            if i < 10:
                i = "000" + str(i)
            elif i < 100:
                i = "00" + str(i)
            elif i < 1000:
                i = "0" + str(i)

            try:
                title.suffix_text = "".join([part[0] for part in title.value.split(" ")])[:2].upper() + str(i)
            except:
                pass
            page.update()

    title = ft.TextField(
        label="Product Title",
        border_radius=10,
        border_color="#d1d5db",
        focused_border_color="#3b82f6",
        focused_border_width=2,
        on_change=gen_product_code,
        col={"sm": 12, "md": 6}
    )

    note = ft.TextField(
        label="Note (Optional)",
        border_radius=10,
        border_color="#d1d5db",
        focused_border_color="#3b82f6",
        focused_border_width=2,
        hint_text="Additional product notes or description",
        multiline=True,
        enable_suggestions=True,
    )

    categoryOptions = [
        ft.DropdownOption(
            key=k,
            content=ft.Text(
                value=k,
            ),
        ) for k, v in category.items()
    ]

    subCategoryOptions = []
    subCategory = {}

    def select_category(e=None):
        temp = {}
        # Use SQLAlchemy to get subcategories
        subcategory_q = session.query(DB.SubCategory.id, DB.SubCategory.name).filter(
            DB.SubCategory.category_id == category[category_DD.value]
        ).all()
        for s in subcategory_q:
            subCategory[s.name] = s.id
            temp[s.name] = s.id

        sub_category_DD.disabled = False
        category_DD.key = category[category_DD.value]

        subCategoryOptions = [
            ft.DropdownOption(
                key=k,
                content=ft.Text(
                    value=k,
                ),
            ) for k, v in temp.items()
        ]
        sub_category_DD.options = subCategoryOptions
        page.update()

    category_DD = ft.Dropdown(
        label="Category",
        options=categoryOptions,
        on_change=lambda e: select_category(e),
        expand=True,
        border_radius=10,
        border_color="#d1d5db",
        focused_border_color="#3b82f6",
        focused_border_width=2,
        col={"sm": 12, "md": 2},
    )

    sub_category_DD = ft.Dropdown(
        label="Sub Category",
        options=subCategoryOptions,
        disabled=True,
        expand=True,
        border_radius=10,
        border_color="#d1d5db",
        focused_border_color="#3b82f6",
        focused_border_width=2,
        col={"sm": 12, "md": 2},
    )

    has_expire = ft.CupertinoCheckbox(
        label="This product has expire date",
        badge=ft.Badge.padding,
        border_side=ft.BorderSide.color
    )

    def select_unit(unit_value):
        """Handle unit selection"""
        global selected_unit

        selected_unit = unit_value

        # Update all unit buttons
        for button in unit_buttons:
            icon_container = button.content.controls[0]
            unit_id_from_name = {v: k for k, v in units.items()}

            if unit_value and button.data == units[unit_value]:
                # Selected button
                icon_container.content.name = ft.Icons.RADIO_BUTTON_CHECKED
                icon_container.content.color = ft.Colors.BLUE_600
                button.border = ft.border.all(2, ft.Colors.BLUE_400)
                button.bgcolor = ft.Colors.BLUE_50
            else:
                # Unselected buttons
                icon_container.content.name = ft.Icons.RADIO_BUTTON_UNCHECKED
                icon_container.content.color = ft.Colors.GREY_400
                button.border = ft.border.all(1, ft.Colors.GREY_300)
                button.bgcolor = ft.Colors.WHITE

        page.update()

    unit_buttons = [
        ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Icon(
                        ft.Icons.RADIO_BUTTON_UNCHECKED,
                        size=18,
                        color=ft.Colors.GREY_400
                    ),
                    data={"selected": False, "value": v}
                ),
                ft.Text(
                    v,
                    size=14,
                    color=ft.Colors.GREY_700,
                    weight=ft.FontWeight.W_400
                )
            ],
                spacing=8,

            ),
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=10,
            bgcolor=ft.Colors.WHITE,
            on_click=lambda e, unit_val=k: select_unit(unit_val),
            data=v
        ) for k, v in units.items()
    ]

    n = 6
    if page.window.width < 1200: n = 4
    if page.window.width < 992: n = 3
    if page.window.width < 768: n = 2

    unit_area = ft.Container(
        ft.Column(
            [
                ft.Text(
                    "Unit Type",
                    size=14,
                    weight=ft.FontWeight.BOLD
                ),
                ft.Column(
                    [
                        ft.ResponsiveRow([
                            ft.Container(content=j, col={"sm": 6, "md": 4, "lg": 3, "xl": 2})
                            for j in unit_buttons[i:i + n]
                        ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ) for i in range(0, len(unit_buttons), n)
                    ],
                    scroll=ft.ScrollMode.AUTO,
                    expand=False,
                )

            ]
        )
    )

    product_image = ft.Image(
        src="/",
        aspect_ratio=1,
        expand=True,
        border_radius=10,
        error_content=ft.Row(
            controls=[
                ft.Icon(ft.Icons.BROKEN_IMAGE, color=ft.Colors.GREY),
                ft.Text("Image not found", color=ft.Colors.GREY),
            ],
            expand=True,
            alignment=ft.MainAxisAlignment.CENTER,
        )
    )

    image_container = ft.Container(
        product_image,
        expand_loose=True,
        aspect_ratio=1,
        col={"sm": 12, "md": 2},
    )

    def submit(e):
        if submit_btn.text == "Update":
            # Use SQLAlchemy update
            product = session.query(DB.Product).filter(DB.Product.code == title.suffix_text).first()
            if product:
                product.title = title.value
                product.note = note.value
                product.unit_id = selected_unit
                product.sub_category_id = subCategory.get(sub_category_DD.value, None)
                product.has_expire = bool(has_expire.value)
                product.image = os.path.basename(
                    product_image.src) if product_image.src and product_image.src != '/' else None
                session.commit()
        else:
            # Use SQLAlchemy insert
            new_product = DB.Product(
                title=title.value,
                note=note.value,
                unit_id=selected_unit,
                sub_category_id=subCategory.get(sub_category_DD.value, None),
                code=title.suffix_text,
                has_expire=bool(has_expire.value),
                image=os.path.basename(
                    product_image.src) if product_image.src and product_image.src != '/' else None
            )
            session.add(new_product)
            session.commit()

        image_generate.disabled = True
        reset_form(e)

    submit_btn = ft.ElevatedButton(
        text="Add Product",
        icon=ft.Icons.ADD_SHOPPING_CART,
        expand=True,
        height=50,
        bgcolor=ft.Colors.BLUE,
        color=ft.Colors.WHITE,
        on_click=lambda e: submit(e)
    )

    def upload_image(e):
        try:
            for f in e.files:
                cpy = os.path.join(os.getcwd(), "src")
                os.makedirs(cpy, exist_ok=True)
                try:
                    shutil.copy(f.path, os.path.join(cpy, os.path.basename(f.path)))
                except shutil.SameFileError:
                    pass
                product_image.src = "src/" + os.path.basename(f.path)
                page.update()
        except Exception as ex:
            print(f"Error uploading image: {ex}")
            pass

    image_picker = ft.FilePicker(on_result=upload_image)
    page.overlay.append(image_picker)

    image_select = ft.ElevatedButton(
        text="Select Image",
        on_click=lambda e: image_picker.pick_files(),
    )

    def ai_img(e):
        if title.value:
            image_generate.disabled = True
            submit_btn.disabled = True
            image_container.content = ft.Column(
                [ft.ProgressRing(), ft.Text("AI Generating Image...")],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
            page.update()
            unit_name = units.get(selected_unit, "") if selected_unit else ""
            r = generate(title.value, note.value, unit_name)
            product_image.src = r if r else "src/404.png"
            image_container.content = product_image
            image_generate.disabled = False
            submit_btn.disabled = False
            page.update()

    image_generate = ft.ElevatedButton(
        text="Generate Image",
        on_click=ai_img,
        disabled=True,
    )

    def reset_form(e):
        title.value = ""
        note.value = ""
        category_DD.value = ""
        sub_category_DD.value = ""
        sub_category_DD.disabled = True
        has_expire.value = False
        product_image.src = "/"
        title.suffix_text = ""
        select_unit("")
        submit_btn.text = "Add Product"
        page.update()

    data_entry = ft.Container(
        content=ft.Column(
            controls=[
                ft.ResponsiveRow(
                    controls=[
                        image_container,
                        ft.Column(
                            col={"sm": 12, "md": 4},
                            controls=[
                                title,
                                category_DD,
                                sub_category_DD,
                                has_expire,
                                ft.Row(
                                    [
                                        image_select,
                                        image_generate,
                                    ]
                                )
                            ],
                            expand=True,
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        ft.Column(
                            col={"sm": 12, "md": 6},
                            controls=[
                                note,
                                unit_area
                            ],
                            expand=False,
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                    ],
                    spacing=20
                ),
                ft.Row(
                    controls=[
                        ft.OutlinedButton(
                            text="Reset",
                            icon=ft.Icons.REFRESH_SHARP,
                            expand=True,
                            height=50,
                            on_click=lambda e: reset_form(e)
                        ),
                        submit_btn
                    ]
                )
            ],
            spacing=20,
        ),
        bgcolor=ft.Colors.WHITE,
        padding=30,
        border_radius=15,
        shadow=ft.BoxShadow(
            spread_radius=0.81,
            blur_radius=3,
            color=ft.Colors.BLACK12,
            offset=ft.Offset(1, 1),
            blur_style=ft.ShadowBlurStyle.NORMAL,
        )
    )

    class product_data:
        data = []

        def __init__(self, id, title, note, category, sub_category, code, unit, image, hasExpire):
            self.id = id
            self.title = title
            self.note = note
            self.category = category
            self.sub_category = sub_category
            self.code = code
            self.unit = unit
            self.image = image
            self.has_expire = hasExpire
            self.load_data()

        def load_data(self):
            d = ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(str(self.id))),
                    ft.DataCell(ft.Text(str(self.title))),
                    ft.DataCell(ft.Text(str(self.note))),
                    ft.DataCell(ft.Text(str(self.category))),
                    ft.DataCell(ft.Text(str(self.sub_category))),
                    ft.DataCell(ft.Text(str(self.code))),
                    ft.DataCell(ft.Text(str(self.unit))),
                    ft.DataCell(ft.Text(str(self.image), text_align=ft.TextAlign.CENTER, expand=True)),
                    ft.DataCell(
                        ft.Icon(
                            ft.Icons.CHECK if self.has_expire else ft.Icons.CLOSE,
                            color=ft.Colors.GREEN if self.has_expire else ft.Colors.RED
                        )
                    ),
                ],
                on_select_changed=lambda e: edit_product(self.title, self.code, self.note, self.category,
                                                         self.sub_category, self.unit, self.image, self.has_expire)
            )
            self.data.append(d)

    def edit_product(t, cd, n, c, sc, su, pi, he):
        title.value = t
        title.suffix_text = cd
        note.value = n
        category_DD.value = c
        select_category()
        sub_category_DD.value = sc
        has_expire.value = bool(he)
        unit_name_to_id = {v: k for k, v in units.items()}
        select_unit(unit_name_to_id.get(su, ''))
        product_image.src = f"./src/{pi}" if pi else "./src/404.png"
        submit_btn.text = "Update"
        image_generate.disabled = False
        page.update()

    def filter_products(e):
        query = e.control.value.lower()
        product_data.data = []

        # Use SQLAlchemy ORM to filter products
        filtered_products_q = (
            session.query(DB.Product)
            .filter(
                or_(
                    func.lower(DB.Product.code).like(f'%{query}%'),
                    func.lower(DB.Product.title).like(f'%{query}%'),
                    func.lower(DB.Product.note).like(f'%{query}%')
                )
            )
            .limit(5)
            .all()
        )

        for p in filtered_products_q:
            unit_name = units.get(p.unit_id)
            if p.sub_category_id and p.sub_category_id in tmp_sb_ctg:
                sub_category_name = tmp_sb_ctg[p.sub_category_id][0]
                category_id = tmp_sb_ctg[p.sub_category_id][1]
                category_name = next((name for name, id in category.items() if id == category_id), None)
            else:
                sub_category_name = None
                category_name = None

            product_data(
                p.id,
                p.title,
                p.note,
                category_name,
                sub_category_name,
                p.code,
                unit_name,
                p.image,
                p.has_expire
            )

        product_table.rows = product_data.data
        page.update()

    search_bar = ft.TextField(
        label="Product",
        hint_text="Search and select product...",
        prefix_icon=ft.Icons.INVENTORY_2,
        on_change=lambda e: filter_products(e),
        border_radius=10,
        border_color="#d1d5db",
        focused_border_color="#3b82f6",
        focused_border_width=2,
        suffix=ft.Icon(
            name=ft.Icons.SEARCH,
            size=20,
            color="#9ca3af",
        ),
        expand=True
    )

    product_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("ID", text_align=ft.TextAlign.CENTER),
                          heading_row_alignment=ft.MainAxisAlignment.CENTER),
            ft.DataColumn(ft.Text("Title", text_align=ft.TextAlign.CENTER),
                          heading_row_alignment=ft.MainAxisAlignment.CENTER),
            ft.DataColumn(ft.Text("Note", text_align=ft.TextAlign.CENTER),
                          heading_row_alignment=ft.MainAxisAlignment.CENTER),
            ft.DataColumn(ft.Text("Category", text_align=ft.TextAlign.CENTER),
                          heading_row_alignment=ft.MainAxisAlignment.CENTER),
            ft.DataColumn(ft.Text("SubCategory", text_align=ft.TextAlign.CENTER),
                          heading_row_alignment=ft.MainAxisAlignment.CENTER),
            ft.DataColumn(ft.Text("ProductCode", text_align=ft.TextAlign.CENTER),
                          heading_row_alignment=ft.MainAxisAlignment.CENTER),
            ft.DataColumn(ft.Text("Unit Type", text_align=ft.TextAlign.CENTER),
                          heading_row_alignment=ft.MainAxisAlignment.CENTER),
            ft.DataColumn(ft.Text("Image", text_align=ft.TextAlign.CENTER),
                          heading_row_alignment=ft.MainAxisAlignment.CENTER),
            ft.DataColumn(ft.Text("Has Expire", text_align=ft.TextAlign.CENTER),
                          heading_row_alignment=ft.MainAxisAlignment.CENTER),
        ],
        expand=True,
    )

    product_area = ft.Container(
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[search_bar],
                    expand_loose=True,
                ),
                ft.Row(
                    controls=[product_table],
                )
            ],
            expand=True,
        ),
        bgcolor=ft.Colors.WHITE,
        padding=30,
        border_radius=15,
        expand=True,
        shadow=ft.BoxShadow(
            spread_radius=0.81,
            blur_radius=3,
            color=ft.Colors.BLACK12,
            offset=ft.Offset(1, 1),
            blur_style=ft.ShadowBlurStyle.NORMAL,
        )
    )

    return ft.Container(
        content=ft.Column(
            controls=[
                header,
                data_entry,
                product_area,
            ]
        ),
        expand=True
    )