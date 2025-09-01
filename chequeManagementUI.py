import flet as ft
from sqlalchemy import create_engine, and_, or_
from sqlalchemy.orm import Session
from datetime import datetime, date, timedelta
import DB  # Import your existing ORM module

# Global variables
CONN:create_engine = None
SESSION:Session = None
USER_ID = None


class ChequeManager:
    def __init__(self, page):
        self.page = page
        self.cheques = []
        self.selected_cheque = None
        self.search_text = ""

        # Create UI components
        self.create_ui()

    def create_ui(self):
        # Search bar
        self.search_field = ft.TextField(
            label="Search Cheques",
            hint_text="Search by cheque number, customer, supplier...",
            on_change=self.on_search_change,
            expand=True
        )

        # Cheque list
        self.cheque_list = ft.ListView(expand=True, spacing=10)

        # Details section
        self.details_container = ft.Container(
            content=ft.Column([
                ft.Text("Select a cheque to view details", size=20, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Text("No cheque selected", size=16)
            ]),
            padding=20,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=10,
            expand=True
        )

        # Main layout
        self.main_content = ft.Row(
            [
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            self.search_field,
                            ft.IconButton(icon=ft.Icons.SEARCH, on_click=self.search_cheques)
                        ]),
                        ft.Text("Cheque List", size=18, weight=ft.FontWeight.BOLD),
                        self.cheque_list
                    ]),
                    width=400,
                    padding=20,
                    border=ft.border.all(1, ft.Colors.GREY_300),
                    border_radius=10
                ),
                self.details_container
            ],
            expand=True
        )

    def on_search_change(self, e):
        self.search_text = e.control.value
        print(self.search_text)

    def search_cheques(self, e=None):
        self.cheque_list.controls.clear()

        q = SESSION.query(DB.Cheque).all()

        print(q)


        # Query cheques from database
        cheques = SESSION.query(DB.Cheque).filter(
            or_(
                DB.Cheque.cheque_number.ilike(f"%{self.search_text}%"),
                DB.Cheque.status.ilike(f"%{self.search_text}%"),

            )
        ).all()

        print(cheques)

        self.cheques = cheques

        for cheque in cheques:
            # Get associated customer/supplier name
            name = "Unknown"
            if cheque.customer_id:
                customer = SESSION.query(DB.Customer).filter(DB.Customer.id == cheque.customer_id).first()
                if customer:
                    name = customer.name
            elif cheque.supplier_id:
                supplier = SESSION.query(DB.Supplier).filter(DB.Supplier.id == cheque.supplier_id).first()
                if supplier:
                    name = supplier.company_name

            list_item = ft.ListTile(
                title=ft.Text(f"Cheque #: {cheque.cheque_number}"),
                subtitle=ft.Text(f"Amount: Rs. {cheque.amount} - Status: {cheque.status} - From: {name}"),
                on_click=lambda e, c=cheque: self.show_cheque_details(c),
                bgcolor=ft.Colors.GREY_100 if cheque.status == "pending" else
                ft.Colors.GREEN_100 if cheque.status == "paid" else
                ft.Colors.RED_100 if cheque.status == "bounced" else
                ft.Colors.BLUE_100
            )
            self.cheque_list.controls.append(list_item)

        self.page.update()

    def show_cheque_details(self, cheque):
        self.selected_cheque = cheque

        # Get associated entities
        customer_name = ""
        supplier_name = ""
        invoice_ref = ""
        grn_ref = ""

        if cheque.customer_id:
            customer = SESSION.query(DB.Customer).filter(DB.Customer.id == cheque.customer_id).first()
            if customer:
                customer_name = customer.name

        if cheque.supplier_id:
            supplier = SESSION.query(DB.Supplier).filter(DB.Supplier.id == cheque.supplier_id).first()
            if supplier:
                supplier_name = supplier.company_name

        if cheque.invoice_id:
            invoice = SESSION.query(DB.Invoice).filter(DB.Invoice.id == cheque.invoice_id).first()
            if invoice:
                invoice_ref = f"Invoice #{invoice.id}"

        if cheque.grn_id:
            grn = SESSION.query(DB.GRN).filter(DB.GRN.id == cheque.grn_id).first()
            if grn:
                grn_ref = f"GRN #{grn.id}"

        # Create form fields
        fields = [
            ft.Text("Cheque Details", size=20, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            ft.Text(f"Cheque Number: {cheque.cheque_number}"),
            ft.Text(f"Amount: Rs. {cheque.amount}"),
            ft.Text(f"Cheque Date: {cheque.cheque_date}"),
            ft.Text(f"Status: {cheque.status}")
        ]

        fields.append(ft.Text(f"Customer: {customer_name}")) if customer_name else None
        fields.append(ft.Text(f"Supplier: {supplier_name}")) if supplier_name else None
        fields.append(ft.Text(f"Invoice: {invoice_ref}")) if invoice_ref else None
        fields.append(ft.Text(f"GRN: {grn_ref}")) if grn_ref else None

        fields += [
            ft.Text(f"Created: {cheque.created_date.strftime('%m/%d/%Y')}"),
            ft.Text(f"Last Updated: {cheque.updated_at}"),
            ft.Divider()
        ]

        # Add status update options if cheque is pending
        if cheque.status == "pending":
            status_dropdown = ft.Dropdown(
                label="Update Status",
                options=[
                    ft.dropdown.Option("paid"),
                    ft.dropdown.Option("bounced")
                ],
                value="paid"
            )

            update_button = ft.ElevatedButton(
                "Update Status",
                on_click=lambda e: self.update_cheque_status(cheque, status_dropdown.value)
            )

            fields.extend([status_dropdown, update_button])

        self.details_container.content = ft.Column(fields, scroll=ft.ScrollMode.AUTO)
        self.page.update()

    def update_cheque_status(self, cheque, new_status):
        try:
            old_status = cheque.status
            cheque.status = new_status
            cheque.updated_at = datetime.now()

            # Handle financial implications based on status change
            if old_status == "pending" and new_status == "bounced":
                self.handle_bounced_cheque(cheque)
            elif old_status == "pending" and new_status == "paid":
                self.handle_paid_cheque(cheque)

            SESSION.commit()

            # Refresh the UI
            self.search_cheques()
            self.show_cheque_details(cheque)

            self.page.snack_bar = ft.SnackBar(ft.Text(f"Cheque status updated to {new_status}"))
            self.page.snack_bar.open = True
            self.page.update()

        except Exception as e:
            SESSION.rollback()
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Error updating cheque: {str(e)}"))
            self.page.snack_bar.open = True
            self.page.update()

    def handle_bounced_cheque(self, cheque):
        """Handle financial adjustments for bounced cheques"""
        if cheque.invoice_id:
            # Reverse invoice payment
            invoice = SESSION.query(DB.Invoice).filter(DB.Invoice.id == cheque.invoice_id).first()
            if invoice:
                invoice.paid_amount -= cheque.amount
                # Update customer credit if needed
                if invoice.customer_id:
                    customer = SESSION.query(DB.Customer).filter(DB.Customer.id == invoice.customer_id).first()
                    if customer:
                        customer.credit += cheque.amount

        elif cheque.grn_id:
            # Reverse GRN payment
            grn = SESSION.query(DB.GRN).filter(DB.GRN.id == cheque.grn_id).first()
            if grn:
                grn.paid_amount -= cheque.amount
                # Update supplier credit if needed
                if grn.supplier_id:
                    supplier = SESSION.query(DB.Supplier).filter(DB.Supplier.id == grn.supplier_id).first()
                    if supplier:
                        supplier.credit += cheque.amount

    def handle_paid_cheque(self, cheque):
        """Handle financial adjustments for paid cheques"""
        # This is typically handled when the cheque is first recorded
        # Additional processing can be added here if needed
        pass


def check_yesterday_cheques():
    """Check for cheques that were due yesterday and prompt for status update"""
    yesterday = date.today() - timedelta(days=1)

    due_cheques = SESSION.query(DB.Cheque).filter(
        and_(
            DB.Cheque.cheque_date == yesterday,
            DB.Cheque.status == "pending"
        )
    ).all()

    return due_cheques


def show_status_update_dialog(page, due_cheques):
    """Show dialog to update status of due cheques"""
    if not due_cheques:
        return

    cheque_options = []
    for cheque in due_cheques:
        name = "Unknown"
        if cheque.customer_id:
            customer = SESSION.query(DB.Customer).filter(DB.Customer.id == cheque.customer_id).first()
            if customer:
                name = customer.name
        elif cheque.supplier_id:
            supplier = SESSION.query(DB.Supplier).filter(DB.Supplier.id == cheque.supplier_id).first()
            if supplier:
                name = supplier.company_name

        cheque_options.append(
            ft.ListTile(
                title=ft.Text(f"Cheque #{cheque.cheque_number} - ${cheque.amount} - {name}"),
                subtitle=ft.Text(f"Due: {cheque.cheque_date}"),
            )
        )

    status_dropdown = ft.Dropdown(
        label="Status",
        options=[
            ft.dropdown.Option("paid"),
            ft.dropdown.Option("bounced")
        ],
        value="paid"
    )

    selected_cheques = {cheque.id: "paid" for cheque in due_cheques}

    def update_all_status(e):
        try:
            for cheque in due_cheques:
                old_status = cheque.status
                new_status = selected_cheques[cheque.id]
                cheque.status = new_status
                cheque.updated_at = datetime.now()

                # Handle financial implications
                if old_status == "pending" and new_status == "bounced":
                    handle_bounced_cheque_single(cheque)

            SESSION.commit()
            page.snack_bar = ft.SnackBar(ft.Text("All cheque statuses updated successfully"))
            page.snack_bar.open = True
            dialog.open = False
            page.update()

        except Exception as e:
            SESSION.rollback()
            page.snack_bar = ft.SnackBar(ft.Text(f"Error updating cheques: {str(e)}"))
            page.snack_bar.open = True
            page.update()

    def handle_status_change(cheque_id, new_status):
        selected_cheques[cheque_id] = new_status

    # Create individual status selectors for each cheque
    status_controls = []
    for cheque in due_cheques:
        status_controls.append(
            ft.Row([
                ft.Text(f"Cheque #{cheque.cheque_number}:", width=150),
                ft.Dropdown(
                    options=[
                        ft.dropdown.Option("paid"),
                        ft.dropdown.Option("bounced")
                    ],
                    value="paid",
                    on_change=lambda e, cid=cheque.id: handle_status_change(cid, e.control.value),
                    width=100
                )
            ])
        )

    dialog = ft.AlertDialog(
        title=ft.Text("Update Due Cheques Status"),
        content=ft.Column([
            ft.Text(f"You have {len(due_cheques)} cheque(s) that were due yesterday:"),
            *status_controls
        ], height=300, scroll=ft.ScrollMode.AUTO),
        actions=[
            ft.TextButton("Update All", on_click=update_all_status),
            ft.TextButton("Cancel", on_click=lambda e: setattr(dialog, 'open', False))
        ]
    )

    page.dialog = dialog
    dialog.open = True
    page.update()


def handle_bounced_cheque_single(cheque):
    """Handle single bounced cheque (similar to method in ChequeManager)"""
    if cheque.invoice_id:
        invoice = SESSION.query(DB.Invoice).filter(DB.Invoice.id == cheque.invoice_id).first()
        if invoice:
            invoice.paid_amount -= cheque.amount
            if invoice.customer_id:
                customer = SESSION.query(DB.Customer).filter(DB.Customer.id == invoice.customer_id).first()
                if customer:
                    customer.credit += cheque.amount
    elif cheque.grn_id:
        grn = SESSION.query(DB.GRN).filter(DB.GRN.id == cheque.grn_id).first()
        if grn:
            grn.paid_amount -= cheque.amount
            if grn.supplier_id:
                supplier = SESSION.query(DB.Supplier).filter(DB.Supplier.id == grn.supplier_id).first()
                if supplier:
                    supplier.credit += cheque.amount


def chequeManagement(page: ft.Page, conn, user_id):
    global CONN, SESSION, USER_ID
    CONN = conn
    SESSION = Session(bind=conn)
    USER_ID = user_id

    page.title = "Cheque Management System"
    page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH
    page.vertical_alignment = ft.MainAxisAlignment.START

    # Check for due cheques on entry
    due_cheques = check_yesterday_cheques()
    if due_cheques:
        show_status_update_dialog(page, due_cheques)

    # Create cheque manager
    cheque_manager = ChequeManager(page)

    return ft.Container(
        content=ft.Column([
            ft.Text("Cheque Management System", size=24, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            cheque_manager.main_content
        ], expand=True),
        padding=20,
        expand=True
    )