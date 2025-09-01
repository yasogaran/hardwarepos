import flet as ft
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from DB import Variables, Category, SubCategory

# Global variables
CONN: create_engine = None
USER_ID = None
SESSION: Session = None
pop = ft.AlertDialog()
PAGE: ft.Page


def settings(page: ft.Page, conn, user_id: int):
    global CONN, USER_ID, SESSION, pop, PAGE
    PAGE = page
    CONN = conn
    USER_ID = user_id
    SESSION = Session(CONN)

    # Load existing settings
    settings_data = load_settings()

    # Load categories and subcategories
    categories = load_categories()
    subcategories = load_subcategories()

    # Create UI components for system settings
    tax_field = ft.TextField(
        label="Tax Percentage (%)",
        value=settings_data.get('tax_percentage', '0'),
        keyboard_type=ft.KeyboardType.NUMBER,
        width=300
    )

    billing_date_checkbox = ft.Checkbox(
        label="Ask Date for Each Billing",
        value=settings_data.get('ask_billing_date', False)
    )

    grn_date_checkbox = ft.Checkbox(
        label="Ask Date for Each GRN",
        value=settings_data.get('ask_grn_date', False)
    )

    cheque_days_field = ft.TextField(
        label="Days Before Cheque Date",
        value=settings_data.get('cheque_reminder_days', '3'),
        keyboard_type=ft.KeyboardType.NUMBER,
        width=300
    )

    email_field = ft.TextField(
        label="Email for Cheque Reminders",
        value=settings_data.get('cheque_reminder_email', ''),
        width=300
    )

    invoice_export_radio = ft.RadioGroup(
        content=ft.Column([
            ft.Radio(value="pdf", label="PDF"),
            ft.Radio(value="png", label="PNG"),
            ft.Radio(value="jpg", label="JPG")
        ]),
        value=settings_data.get('invoice_export_type', 'pdf')
    )

    grn_export_radio = ft.RadioGroup(
        content=ft.Column([
            ft.Radio(value="pdf", label="PDF"),
            ft.Radio(value="png", label="PNG"),
            ft.Radio(value="jpg", label="JPG")
        ]),
        value=settings_data.get('grn_export_type', 'pdf')
    )

    theme_switch = ft.Switch(
        label="Dark Mode",
        value=settings_data.get('theme', 'light') == 'dark',
        label_position=ft.LabelPosition.LEFT
    )

    # Category Management Components
    category_name_field = ft.TextField(
        label="Category Name",
        width=300,
        expand=True
    )

    category_dropdown = ft.Dropdown(
        label="Select Category",
        width=300,
        options=[ft.dropdown.Option(text=c.name, key=str(c.id)) for c in categories],
        on_change=lambda e: update_ui()
    )

    subcategory_name_field = ft.TextField(
        label="Subcategory Name",
        width=300,
        expand=True
    )

    # Replace ListView with ResponsiveRow for categories
    categories_container = ft.ResponsiveRow(
        spacing=10,
        run_spacing=10,
        controls=[]  # Will be populated in update_categories_list
    )

    # Replace ListView with ResponsiveRow for subcategories
    subcategories_container = ft.ResponsiveRow(
        spacing=10,
        run_spacing=10,
        controls=[]  # Will be populated in update_subcategory_list
    )

    def update_ui():
        update_categories_list()
        update_subcategory_list()
        page.update()

    def update_categories_list():
        categories_container.controls.clear()
        for category in categories:
            category_card = ft.Container(
                content=ft.Column(
                    [
                        ft.Text(category.name, size=16, weight=ft.FontWeight.BOLD),
                        ft.Row(
                            [
                                ft.IconButton(
                                    icon=ft.Icons.EDIT,
                                    tooltip="Edit Category",
                                    on_click=lambda e, cat=category: edit_category(cat)
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE,
                                    tooltip="Delete Category",
                                    on_click=lambda e, cat=category: delete_category(cat)
                                )
                            ],
                            alignment=ft.MainAxisAlignment.END
                        )
                    ],
                    spacing=5
                ),
                padding=15,
                border_radius=10,
                border=ft.border.all(1, ft.Colors.OUTLINE),
                col={"sm": 12, "md": 6, "lg": 4, "xl": 3}
            )
            categories_container.controls.append(category_card)

    def update_subcategory_list():
        subcategories_container.controls.clear()
        if category_dropdown.value:
            category_id = int(category_dropdown.value)
            subcats = [sc for sc in subcategories if sc.category_id == category_id]

            for subcat in subcats:
                subcategory_card = ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(subcat.name, size=14, weight=ft.FontWeight.BOLD),
                            ft.Row(
                                [
                                    ft.IconButton(
                                        icon=ft.Icons.EDIT,
                                        icon_size=18,
                                        tooltip="Edit Subcategory",
                                        on_click=lambda e, sc=subcat: edit_subcategory(sc)
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.DELETE,
                                        icon_size=18,
                                        tooltip="Delete Subcategory",
                                        on_click=lambda e, sc=subcat: delete_subcategory(sc)
                                    )
                                ],
                                alignment=ft.MainAxisAlignment.END
                            )
                        ],
                        spacing=5
                    ),
                    padding=12,
                    border_radius=8,
                    bgcolor=ft.Colors.SECONDARY_CONTAINER,
                    border=ft.border.all(1, ft.Colors.OUTLINE),
                    col={"sm": 12, "md": 6, "lg": 4, "xl": 3}
                )
                subcategories_container.controls.append(subcategory_card)

    def add_category(e):
        if category_name_field.value:
            new_category = Category(name=category_name_field.value)
            SESSION.add(new_category)
            SESSION.commit()
            categories.append(new_category)
            category_dropdown.options.append(
                ft.dropdown.Option(text=new_category.name, key=str(new_category.id))
            )
            category_name_field.value = ""
            update_ui()

    def edit_category(category):
        def save_edit(e):
            category.name = edit_field.value
            SESSION.commit()
            # Update dropdown options
            for option in category_dropdown.options:
                if option.key == str(category.id):
                    option.text = category.name
            update_ui()
            page.close(pop)

        edit_field = ft.TextField(value=category.name, width=300, label="Category Name")
        pop = ft.AlertDialog(
            title=ft.Text("Edit Category"),
            content=edit_field,
            actions=[
                ft.TextButton("Save", on_click=save_edit),
                ft.TextButton("Cancel", on_click=lambda e: page.close(pop))
            ]
        )
        page.open(pop)
        page.update()

    def delete_category(category):
        # Check if category has subcategories
        category_subcategories = [sc for sc in subcategories if sc.category_id == category.id]

        if category_subcategories:
            # Show warning if category has subcategories
            pop = ft.AlertDialog(
                title=ft.Text("Cannot Delete Category"),
                content=ft.Text(
                    f"Category '{category.name}' has {len(category_subcategories)} subcategories. "
                    "Please delete all subcategories first."
                ),
                actions=[
                    ft.TextButton("OK", on_click=lambda e: page.close(pop))
                ]
            )
        else:
            # Confirm deletion
            def confirm_delete(e):
                SESSION.delete(category)
                SESSION.commit()
                categories.remove(category)
                # Remove from dropdown
                category_dropdown.options = [
                    opt for opt in category_dropdown.options if opt.key != str(category.id)
                ]
                if category_dropdown.value == str(category.id):
                    category_dropdown.value = None
                update_ui()
                page.close(pop)

            pop = ft.AlertDialog(
                title=ft.Text("Confirm Delete"),
                content=ft.Text(f"Delete category '{category.name}'?"),
                actions=[
                    ft.TextButton("Delete", on_click=confirm_delete),
                    ft.TextButton("Cancel", on_click=lambda e: page.close(pop))
                ]
            )

        page.open(pop)
        page.update()

    def add_subcategory(e):
        if subcategory_name_field.value and category_dropdown.value:
            new_subcategory = SubCategory(
                name=subcategory_name_field.value,
                category_id=int(category_dropdown.value)
            )
            SESSION.add(new_subcategory)
            SESSION.commit()
            subcategories.append(new_subcategory)
            update_ui()
            subcategory_name_field.value = ""

    def edit_subcategory(subcategory):
        def save_edit(e):
            subcategory.name = edit_field.value
            SESSION.commit()
            update_ui()
            page.close(pop)

        edit_field = ft.TextField(value=subcategory.name, width=300, label="Subcategory Name")
        pop = ft.AlertDialog(
            title=ft.Text("Edit Subcategory"),
            content=edit_field,
            actions=[
                ft.TextButton("Save", on_click=save_edit),
                ft.TextButton("Cancel", on_click=lambda e: page.close(pop))
            ]
        )
        page.open(pop)
        page.update()

    def delete_subcategory(subcategory):
        def confirm_delete(e):
            SESSION.delete(subcategory)
            SESSION.commit()
            subcategories.remove(subcategory)
            update_ui()
            page.close(pop)

        pop = ft.AlertDialog(
            title=ft.Text("Confirm Delete"),
            content=ft.Text(f"Delete subcategory '{subcategory.name}'?"),
            actions=[
                ft.TextButton("Delete", on_click=confirm_delete),
                ft.TextButton("Cancel", on_click=lambda e: page.close(pop))
            ]
        )
        page.open(pop)
        page.update()

    # Save button for system settings
    save_settings_button = ft.ElevatedButton(
        "Save System Settings",
        icon=ft.Icons.SAVE,
        on_click=lambda e: save_settings(
            tax_field.value,
            billing_date_checkbox.value,
            grn_date_checkbox.value,
            cheque_days_field.value,
            email_field.value,
            invoice_export_radio.value,
            grn_export_radio.value,
            'dark' if theme_switch.value else 'light'
        )
    )

    # Create tabs for better organization
    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        tabs=[
            ft.Tab(
                text="System Settings",
                content=ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text("System Settings", size=24, weight=ft.FontWeight.BOLD),
                            ft.Divider(),
                            ft.Row([tax_field], alignment=ft.MainAxisAlignment.START),
                            ft.Row([billing_date_checkbox], alignment=ft.MainAxisAlignment.START),
                            ft.Row([grn_date_checkbox], alignment=ft.MainAxisAlignment.START),
                            ft.Text("Cheque Reminder Settings", weight=ft.FontWeight.BOLD),
                            ft.Row([cheque_days_field, email_field], alignment=ft.MainAxisAlignment.START),
                            ft.Text("Export Settings", weight=ft.FontWeight.BOLD),
                            ft.Row(
                                [
                                    ft.Column(
                                        [
                                            ft.Text("Invoice Export Type:"),
                                            invoice_export_radio
                                        ]
                                    ),
                                    ft.Column(
                                        [
                                            ft.Text("GRN Export Type:"),
                                            grn_export_radio
                                        ]
                                    )
                                ]
                            ),
                            ft.Text("Theme:", weight=ft.FontWeight.BOLD),
                            ft.Row([
                                theme_switch,
                                ft.Icon(ft.Icons.LIGHT_MODE if not theme_switch.value else ft.Icons.DARK_MODE)
                            ], spacing=10),
                            ft.Divider(),
                            ft.Row([save_settings_button], alignment=ft.MainAxisAlignment.CENTER)
                        ],
                        spacing=15,
                        scroll=ft.ScrollMode.AUTO
                    ),
                    padding=20
                )
            ),
            ft.Tab(
                text="Categories",
                content=ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text("Category Management", size=24, weight=ft.FontWeight.BOLD),
                            ft.Divider(),

                            ft.Text("All Categories", size=18, weight=ft.FontWeight.BOLD),
                            categories_container,
                            ft.Divider(),

                            ft.Text("Add New Category", size=18, weight=ft.FontWeight.BOLD),
                            ft.ResponsiveRow(
                                [
                                    ft.Container(
                                        category_name_field,
                                        col={"sm": 12, "md": 8, "lg": 6}
                                    ),
                                    ft.Container(
                                        ft.ElevatedButton(
                                            "Add Category",
                                            icon=ft.Icons.ADD,
                                            on_click=add_category
                                        ),
                                        col={"sm": 12, "md": 4, "lg": 3}
                                    )
                                ],
                                spacing=10
                            ),
                            ft.Divider(),

                            ft.Text("Subcategory Management", size=18, weight=ft.FontWeight.BOLD),
                            ft.ResponsiveRow(
                                [
                                    ft.Container(
                                        category_dropdown,
                                        col={"sm": 12, "md": 6, "lg": 4}
                                    ),
                                    ft.Container(
                                        subcategory_name_field,
                                        col={"sm": 12, "md": 6, "lg": 4}
                                    ),
                                    ft.Container(
                                        ft.ElevatedButton(
                                            "Add Subcategory",
                                            icon=ft.Icons.ADD,
                                            on_click=add_subcategory
                                        ),
                                        col={"sm": 12, "md": 6, "lg": 4}
                                    )
                                ],
                                spacing=10
                            ),
                            ft.Divider(),

                            ft.Text("Subcategories in Selected Category", size=18, weight=ft.FontWeight.BOLD),
                            subcategories_container
                        ],
                        spacing=15,
                        scroll=ft.ScrollMode.AUTO
                    ),
                    padding=20
                )
            )
        ]
    )

    # Create the settings container
    settings_container = ft.Container(
        content=tabs,
        padding=10,
        expand=True
    )

    # Initialize UI
    update_ui()

    return settings_container


def load_settings():
    settings_dict = {}
    try:
        settings = SESSION.query(Variables).all()
        for setting in settings:
            if setting.name in ['ask_billing_date', 'ask_grn_date']:
                settings_dict[setting.name] = setting.value.lower() == 'true'
            else:
                settings_dict[setting.name] = setting.value
    except Exception as e:
        snackbar = ft.SnackBar(
            ft.Text(f"Error loading settings: {e}", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            bgcolor=ft.Colors.RED,
            duration=2000
        )
        PAGE.open(snackbar)
        PAGE.update()


    return settings_dict


def load_categories():
    try:
        return SESSION.query(Category).order_by(Category.name).all()
    except Exception as e:
        snackbar = ft.SnackBar(
            ft.Text(f"Error loading categories: {e}", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            bgcolor=ft.Colors.RED,
            duration=2000
        )
        PAGE.open(snackbar)
        PAGE.update()
        return []


def load_subcategories():
    try:
        return SESSION.query(SubCategory).order_by(SubCategory.name).all()
    except Exception as e:
        snackbar = ft.SnackBar(
            ft.Text(f"Error loading subcategories: {e}", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            bgcolor=ft.Colors.RED,
            duration=2000
        )
        PAGE.open(snackbar)
        PAGE.update()
        return []


def save_settings(tax_percentage, ask_billing_date, ask_grn_date,
                  cheque_days, email, invoice_export, grn_export, theme):
    try:
        settings_to_save = {
            'tax_percentage': str(tax_percentage),
            'ask_billing_date': str(ask_billing_date),
            'ask_grn_date': str(ask_grn_date),
            'cheque_reminder_days': str(cheque_days),
            'cheque_reminder_email': email,
            'invoice_export_type': invoice_export,
            'grn_export_type': grn_export,
            'theme': theme
        }

        for name, value in settings_to_save.items():
            existing_setting = SESSION.query(Variables).filter_by(name=name).first()
            if existing_setting:
                existing_setting.value = value
            else:
                new_setting = Variables(name=name, value=value)
                SESSION.add(new_setting)

        SESSION.commit()
        snackbar = ft.SnackBar(
            ft.Text(f"Settings saved successfully!", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            bgcolor=ft.Colors.GREEN,
            duration=2000
        )
        PAGE.open(snackbar)
        PAGE.update()

    except Exception as e:
        SESSION.rollback()

        snackbar = ft.SnackBar(
            ft.Text(f"Error saving settings: {e}", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            bgcolor=ft.Colors.RED,
            duration=2000
        )
        PAGE.open(snackbar)
        PAGE.update()