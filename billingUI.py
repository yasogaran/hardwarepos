import decimal
import time

import flet as ft
from datetime import datetime
import pandas as pd
from invoice_generator import export_invoice_from_db
from sqlalchemy import insert, create_engine, select, or_
from sqlalchemy.orm import Session
import DB
from sqlalchemy import or_, func, cast
from sqlalchemy.types import String
from sqlalchemy.exc import IntegrityError

SESSION: Session

TAX = 0

units = dict()

filtered_products = dict()

invoice_tab = None

currency = "Rs. "

bill_tabs = ft.Tabs(
    animation_duration=300,
    expand_loose=True,
    adaptive=True,
)

products_list = ft.ResponsiveRow(
    expand=True,
    spacing=5,
)

customers = dict()

CONN: create_engine
USER_ID: int
ACCOUNT_ID: int = 1

class Bill:
    bills = []
    def __init__(self, page):
        self.new_customer = False
        self.head_text = ft.TextStyle(
            weight=ft.FontWeight.BOLD,
            size=24,
        )

        self.body_text = ft.TextStyle(
            size=18,
        )

        self.page = page
        self.customer_id = None
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
                    ft.Text("Item Name"),
                    heading_row_alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.DataColumn(
                    ft.Text("Qty"),
                    heading_row_alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.DataColumn(
                    ft.Text("Price"),
                    heading_row_alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.DataColumn(
                    ft.Text("Total"),
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
                    ft.Text(f"Item Name"),
                    heading_row_alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.DataColumn(
                    ft.Text("Qty"),
                    heading_row_alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.DataColumn(
                    ft.Text("Price"),
                    heading_row_alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.DataColumn(
                    ft.Text("Total"),
                    heading_row_alignment=ft.MainAxisAlignment.CENTER,
                )
            ],
            data_row_max_height=0,
            data_row_min_height=0,
            expand=True,
        )

        self.customer_name = ft.TextField(
            label="Customer Name",
            hint_text="Search and select customer...",
            prefix_icon=ft.Icons.PERSON,
            on_change=self.filter_customer,
            border_radius=10,
            border_color="#d1d5db",
            focused_border_color="#3b82f6",
            focused_border_width=2,
            expand=True
        )

        self.customer_dropdown = ft.ListView(
            height=200,
            visible=False,
            padding=0
        )

        self.customer_dropdown_container = ft.Container(
            content=self.customer_dropdown,
            margin=ft.margin.only(top=5),
            animate=ft.Animation(300, "easeInOut"),
            clip_behavior=ft.ClipBehavior.HARD_EDGE
        )

        self.customer_mobile = ft.TextField(
            label="Customer Mobile Number",
            hint_text="Mobile Number",
            prefix_icon=ft.Icons.PHONE,
            border_radius=10,
            border_color="#d1d5db",
            focused_border_color="#3b82f6",
            focused_border_width=2,
            expand=True,
            error_style=ft.TextStyle(
                color=ft.Colors.RED,
            ),
            input_filter=ft.InputFilter(
                regex_string=r"[0-9+\-\s()]",
                allow=True,
                replacement_string=""
            ),
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
            expand=True
        )

        self.cheque_date = ft.IconButton(
            icon=ft.Icons.CALENDAR_MONTH,
            on_click=self.date_picker
        )

        self.cheque_amount = ft.TextField(
            label="Cheque Amount",
            prefix_text=currency,
            hint_text="Cheque Amount",
            border_radius=10,
            border_color="#d1d5db",
            focused_border_color="#3b82f6",
            focused_border_width=2,
            width=200,
            text_size=24,
            on_change=self.pay,
            input_filter=ft.InputFilter(
                regex_string=r"[0-9.]",
                allow=True,
                replacement_string=""
            ),
        )

        self.cheque_area = ft.Row(
            [
                self.cheque_number,
                self.cheque_date,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        self.total_amount = ft.Text(
            value=str(round(sum(self.grandTotal.values()), 2)),
            style=self.body_text
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
                regex_string=r"[0-9.]",
                allow=True,
                replacement_string=""
            )
        )

        self.tax_amount = ft.Text(
            text_align=ft.TextAlign.RIGHT,
            value=currency + str(round(sum(self.grandTotal.values()) * float(TAX) / 100, 2)),
            style=self.body_text
        )

        self.amount_to_be_paid = ft.Text(
            value=currency + str(round(sum(self.grandTotal.values()) * (100+float(TAX)) / 100, 2)),
            style=self.body_text
        )

        self.paid_amount = ft.TextField(
            label_style=ft.TextStyle(
                size=16,
            ),
            label="Paid Amount (Cash)",
            prefix_text=currency,
            hint_text="Paid Amount",
            border_radius=10,
            border_color="#d1d5db",
            focused_border_color="#3b82f6",
            focused_border_width=2,
            on_change=self.pay,
            width=220,
            text_size=24,
            on_submit=self.print_bill,
            input_filter=ft.InputFilter(
                regex_string=r"[0-9.]",
                allow=True,
                replacement_string=""
            ),
        )

        self.balance = ft.Text(
            value=currency + str(round(sum(self.grandTotal.values()), 2)),
            style=self.body_text,
            color=ft.Colors.RED
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

        self.payment_area = ft.Container(
            ft.Column(
                [
                    ft.Container(
                        ft.Column(
                            [
                                ft.Container(
                                    ft.Column(
                                        [
                                            ft.Container(
                                                ft.Column(
                                                    [
                                                        ft.Text(
                                                            "Customer Details".upper(),
                                                            style=self.head_text,
                                                        ),
                                                        self.customer_name,
                                                        self.customer_dropdown_container,
                                                        self.customer_mobile,
                                                    ],
                                                    spacing=5
                                                )
                                            ),
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
                                                                            "VAT".upper(),
                                                                            style=self.body_text,
                                                                        ),
                                                                        self.tax_amount
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
                                                        self.cheque_area,
                                                    ],
                                                    spacing=5
                                                )
                                            ),
                                            ft.Container(
                                                ft.Column(
                                                    [
                                                        ft.Text(
                                                            "Payment".upper(),
                                                            style=self.head_text,
                                                        ),
                                                        ft.Row(
                                                            [
                                                                self.paid_amount,
                                                                self.cheque_amount
                                                            ],
                                                            alignment=ft.MainAxisAlignment.SPACE_AROUND,
                                                        ),
                                                    ],
                                                    spacing=5
                                                )
                                            )
                                        ],
                                        expand=True,
                                        spacing=30,
                                        scroll=ft.ScrollMode.AUTO,
                                    ),
                                    expand=True
                                ),
                                ft.Container(
                                    ft.Row(
                                        [
                                            ft.Text(
                                                "Balance",
                                                style=self.body_text,
                                                color=ft.Colors.RED
                                            ),
                                            self.balance,
                                        ],
                                        alignment=ft.MainAxisAlignment.END,
                                    )
                                )
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        bgcolor=ft.Colors.WHITE,
                        shadow=ft.BoxShadow(
                            spread_radius=0.81,
                            blur_radius=3,
                            color=ft.Colors.BLACK12,
                            offset=ft.Offset(1, 1),
                            blur_style=ft.ShadowBlurStyle.NORMAL,
                        ),
                        padding=15,
                        border_radius=15,
                        expand=True,
                    ),
                    ft.Container(
                        ft.Column(
                            [
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
            padding=ft.padding.only(25, 5, 25, 5),
            expand=True
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

    def load_bill(self, e=None):
        """
        Method to transition from bill view to payment view.
        Called when 'Proceed to Payment' button is clicked.
        """
        Tab.tabs[bill_tabs.selected_index].content = self.payment_area
        self.total_amount.value = currency + str(round(sum(self.grandTotal.values()), 2))
        self.tax_amount.value = currency + str(round(sum(self.grandTotal.values()) * float(TAX) / 100, 2))
        self.amount_to_be_paid.value = currency + str(round(sum(self.grandTotal.values()) * (100+float(TAX)) / 100, 2))
        self.balance.value = currency + str(round(float(self.paid_amount.value if self.paid_amount.value else "0.00") - float(self.amount_to_be_paid.value.split(" ")[1]), 2))
        self.paid_amount.value = ""
        self.page.update()
    
    def validate_mobile_uniqueness(self, mobile_number):
        """
        Check if mobile number already exists for another customer
        Returns True if unique, False if duplicate
        """
        if not mobile_number or not mobile_number.strip():
            return True
            
        try:
            existing_customer = SESSION.query(DB.Customer).filter(
                DB.Customer.mobile == mobile_number.strip()
            ).first()
            
            if existing_customer:
                # If we're updating an existing customer and it's their own mobile, allow it
                if not self.new_customer and existing_customer.id == self.customer_id:
                    return True
                # Otherwise it's a duplicate
                return False
            return True
        except Exception as e:
            print(f"Error checking mobile uniqueness: {e}")
            return True  # Allow if we can't check

    def print_bill(self, e):
        global filtered_products, SESSION

        from decimal import Decimal
        now_dt = datetime.now()

        balance_amount = float(self.balance.value.split(" ")[1])

        # Clear any existing error messages
        self.customer_mobile.error_text = ""
        self.cheque_number.error_text = ""
        self.cheque_amount.error_text = ""

        # Enhanced mobile number validation
        if self.new_customer:
            if not self.customer_mobile.value or not self.customer_mobile.value.strip():
                self.customer_mobile.error_text = "Mobile number is required for new customers"
                self.page.update()
                return
            
            # Check for duplicate mobile number
            if not self.validate_mobile_uniqueness(self.customer_mobile.value):
                self.customer_mobile.error_text = f"Mobile number '{self.customer_mobile.value}' already exists. Please use a different number."
                self.page.open(ft.SnackBar(
                    ft.Text("Duplicate mobile number detected!", color=ft.Colors.WHITE), 
                    bgcolor=ft.Colors.RED, 
                    duration=3000
                ))
                self.page.update()
                return

        # Existing validation for credit
        if balance_amount < -1 and (not self.customer_mobile.value or not self.customer_mobile.value.strip()):
            self.customer_mobile.error_text = "Mobile number is required when customer has credit balance"
            self.page.update()
            return

        # Cheque validation
        if self.cheque_amount.value and ((not self.cheque_number.value) or self.cheque_number.suffix_text == "date"):
            if not self.cheque_number.value:
                self.cheque_number.error_text = "Please enter the cheque number"
            elif self.cheque_number.suffix_text == "date":
                self.cheque_number.error_text = "Please select the cheque date"
            elif not self.cheque_amount.value:
                self.cheque_amount.error_text = "Please enter the cheque amount"
            self.page.update()
            return

        # Begin a fresh transaction
        try:
            # Start a new transaction context
            SESSION.close()
            SESSION = Session(CONN)
            SESSION.begin()
            
            # Create new customer if needed (ORM)
            if self.new_customer:
                try:
                    new_cust = DB.Customer(
                        name=self.customer_name.value,
                        mobile=self.customer_mobile.value.strip(),
                    )
                    SESSION.add(new_cust)
                    SESSION.flush()  # allocate id
                    self.customer_id = new_cust.id
                except IntegrityError as err:
                    SESSION.rollback()
                    self.customer_mobile.error_text = "This mobile number already exists in the system"
                    self.page.open(ft.SnackBar(
                        ft.Text("Cannot create customer: Mobile number already exists!", color=ft.Colors.WHITE), 
                        bgcolor=ft.Colors.RED, 
                        duration=3000
                    ))
                    self.page.update()
                    return

            # Create invoice (ORM)
            inv = DB.Invoice(
                created_on=now_dt,
                total=Decimal(self.amount_to_be_paid.value.split(' ')[1]),
                discount_amount=Decimal(self.discount_amount.value or "0"),
                tax_amount=Decimal(self.tax_amount.value.split(' ')[1]),
                paid_amount=Decimal(self.paid_amount.value or "0"),
                status='paid' if balance_amount >= -0.01 else 'pending',  # Fixed balance comparison
                customer_id=self.customer_id,
                user_id=USER_ID,
            )
            SESSION.add(inv)
            SESSION.flush() 
            invoice_id = inv.id

            # Payment transaction (ORM)
            paid_decimal = Decimal(self.paid_amount.value or "0")
            if paid_decimal > 0:
                txn = DB.InvoiceTransaction(
                    amount=paid_decimal,
                    date=now_dt,
                    invoice_id=invoice_id,
                    account_id=ACCOUNT_ID,
                    transaction_type='payment',
                    cheque_number=self.cheque_number.value if self.cheque_number.value else None,
                )
                SESSION.add(txn)

                expense_entry = DB.ExpenseTracker(
                    description=f"Invoice #{invoice_id} - {self.customer_name.value}",
                    income=paid_decimal,
                    outcome=Decimal(0),
                    date=now_dt
                )
                
                SESSION.add(expense_entry)

            # Update stock + movements + invoice items (ORM)
            for stock_id, stock in Item.items.items():
                qty = Decimal(str(stock["count"]))
                unit_price = Decimal(str(stock["price"]))
                max_price = Decimal(str(stock["max_price"]))

                stock_obj = SESSION.get(DB.Stock, stock_id)
                if stock_obj:
                    stock_obj.stock_out = (stock_obj.stock_out or 0) + qty
                    stock_obj.current_stock = (stock_obj.current_stock or 0) - qty
                    stock_obj.updated_at = now_dt
                    if stock_obj.current_stock <= 0:
                        stock_obj.status = 'out'

                SESSION.add(DB.StockMovement(
                    stock_id=stock_id,
                    movement_type='out',
                    quantity=qty,
                    reference_id=invoice_id,
                    reference_type='invoice'
                ))

                SESSION.add(DB.InvoiceHasStock(
                    invoice_id=invoice_id,
                    stock_id=stock_id,
                    quantity=qty,
                    unit_price=unit_price,
                    discount_amount=max_price - unit_price
                ))

            # Handle cheque if present
            if self.cheque_amount.value:
                try:
                    date = self.cheque_number.suffix_text.split("-")
                    yr = int(date[0])
                    mon = int(date[1])
                    day = int(date[2])
                    cheque = DB.Cheque(
                        cheque_number=self.cheque_number.value,
                        cheque_date=datetime(yr, mon, day),
                        customer_id=self.customer_id,
                        invoice_id=invoice_id,
                        amount=Decimal(self.cheque_amount.value),
                        status='pending',
                    )
                    expenses = DB.ExpenseTracker(
                        description=f"Cheque #{self.cheque_number.value} - Invoice #{invoice_id} - {self.customer_name.value}",
                        outcome=Decimal(self.cheque_amount.value),
                        income=Decimal(0),
                        date=now_dt
                    )
                    SESSION.add(cheque)
                    SESSION.add(expenses)
                except (ValueError, IndexError) as date_err:
                    print(f"Invalid cheque date format: {date_err}")

            # Customer credit handling - only if balance is significantly negative
            if balance_amount < -0.01 and self.customer_id:
                customer_obj = SESSION.get(DB.Customer, self.customer_id)
                if customer_obj:
                    # balance_amount is negative; subtracting increases credit owed
                    customer_obj.credit = (customer_obj.credit or 0) - Decimal(str(balance_amount))

            # Single commit for the entire transaction
            SESSION.commit()

            # Export PDF/PNG/JPG (uses ORM inside helper)
            print(SESSION)
            # export_invoice_pdf_png_jpg(SESSION, invoice_id, TAX)
            export_invoice_from_db(SESSION, invoice_id, TAX)
            # generator = ProfessionalInvoiceGenerator()
            # generator.create_invoice(
            #     invoice_number=SESSION.get(DB.Invoice, invoice_id).id,
            #     invoice_date="2024/03/15",
            #     due_date="2024/04/15",
            #     customer=customer,
            #     items=items,
            #     tax_rate=6.25,
            #     notes="Payment due within 30 days.\nLate payments subject to 1.5% monthly service charge.\nAll work performed according to industry standards.",
            #     output_path="multi_page_invoice.pdf"
            # )

            # Reset current bill in UI
            Item.items = dict()
            self.delete_bill(e)

            # Show comprehensive success message
            success_message = f"✓ Invoice #{invoice_id} saved successfully!\n✓ PDF receipt exported to local files"
            self.page.open(ft.SnackBar(
                ft.Text(success_message, color=ft.Colors.WHITE), 
                bgcolor=ft.Colors.GREEN, 
                duration=3000
            ))

            # Reload products (ORM)
            products = (
                SESSION.query(DB.Product)
                .order_by(DB.Product.id.asc())
                .limit(18)
                .all()
            )
            filtered_products = [
                {
                    "id": p.id, "title": p.title, "note": p.note,
                    "unit_id": p.unit_id, "sub_category_id": p.sub_category_id,
                    "code": p.code, "barcode": p.barcode, "has_expire": p.has_expire,
                    "image": p.image,
                } for p in products
            ]
            Product.data = []
            Stock.data = dict()
            for i in filtered_products:
                Product(self.page, i["id"], i["title"], i["note"], i["unit_id"], i["image"])
            products_list.controls = Product.data
            self.page.update()

            # Export PDF/PNG/JPG (uses ORM inside helper)
            # export_invoice_pdf_png_jpg(SESSION, invoice_id, TAX)
            export_invoice_from_db(SESSION, invoice_id, TAX)
            
            return None
            
        except Exception as e:
            # Safe rollback - check if session is still active
            try:
                if SESSION.is_active:
                    SESSION.rollback()
            except Exception as rollback_err:
                print(f"Rollback failed: {rollback_err}")
                # Create a new session if the current one is broken
                SESSION.close()
                SESSION = Session(CONN)
            
            print(f"Error in print_bill: {e}")
            self.page.open(ft.SnackBar(ft.Text(f"Error: {str(e)}"), bgcolor=ft.Colors.RED, duration=3000))
            return None

    def pay(self, e=None):
        try:
            self.balance.value = (currency +
                                str(round(
                                    float(self.paid_amount.value if self.paid_amount.value else "0.0")
                                    - float(self.amount_to_be_paid.value.split(" ")[1])
                                    + float(self.cheque_amount.value
                                            if self.cheque_amount.value and self.cheque_amount.visible
                                            else "0.0"
                                    ), 2
                                    ))
                                )
            self.page.update()
        except:
            pass

    def discount(self, e):
        self.discount_amount.width = (len(e.control.value) + 3) * 11

        try:
            self.amount_to_be_paid.value = (
                currency
                + str(
                    round(
                        (
                            float(
                                self.total_amount.value.split(" ")[1]
                            )
                            - float(
                                self.discount_amount.value if e.control.value else "0.0"
                            )
                        ) * (100+float(TAX)) / 100,
                        2
                    )
                )
            )
        except:
            self.amount_to_be_paid.value = (
                currency
                + str(
                    round(
                        float(
                            self.total_amount.value.split(" ")[1]
                        ) * (100+float(TAX)) / 100,
                        2
                    )
                )
            )

        self.paid_amount.value = str(round(float(self.amount_to_be_paid.value.split(" ")[1]), 2))
        self.pay()
        self.page.update()

    def date_picker(self, e):
        self.page.open(
            ft.DatePicker(
                first_date=datetime.now(),
                on_change=self.select_date,
            )
        ),

    def select_date(self, e):
        self.cheque_number.suffix_text = e.control.value.strftime('%Y-%m-%d')
        self.page.update()

    def back(self, e=None):
        Tab.tabs[bill_tabs.selected_index].content = self.bill_area
        self.page.update()

    def hide_dropdown(self):
        self.customer_dropdown.visible = False
        self.page.update()

    def select_customer(self, customer):
        try:
            self.customer_id = customer["id"]
            self.customer_mobile.value = customer["mobile"]
            self.new_customer = False
        except:
            self.new_customer = True
            self.customer_id = None
            self.customer_mobile.value = ""
        self.customer_name.value = customer["name"].title()
        self.hide_dropdown()

    def show_dropdown(self, e=None):
        self.customer_dropdown.visible = True
        self.page.update()

    def filter_customer(self, e):
        global customers
        query = (self.customer_name.value or "").lower().strip()
        if query == "":
            self.hide_dropdown()
            return

        self.show_dropdown()

        # ORM
        results = (
            SESSION.query(DB.Customer)
            .filter(
                or_(
                    DB.Customer.name.ilike(f"%{query}%"),
                    DB.Customer.mobile.ilike(f"%{query}%"),
                )
            )
            .limit(5)
            .all()
        )

        customers = [
            {
                "id": c.id,
                "name": c.name or "",
                "mobile": c.mobile or "",
                "credit": str(c.credit or 0),
            }
            for c in results
        ]

        self.customer_dropdown.controls = [
                                            ft.ListTile(
                                                title=ft.Text(customer["name"]),
                                                subtitle=ft.Text(f"Mobile: {customer['mobile']}", size=12),
                                                trailing=ft.Container(
                                                    content=ft.Text(customer["credit"], size=12),
                                                    bgcolor="#dbeafe",
                                                    padding=5,
                                                    border_radius=10
                                                ),
                                                on_click=lambda e, c=customer: self.select_customer(c),
                                                data=customer
                                            ) for customer in customers
                                        ] + [
                                            ft.ListTile(
                                                title=ft.Row(
                                                    [ft.Text("Create "),
                                                    ft.Text(query.title(), weight=ft.FontWeight.BOLD)]
                                                ),
                                                subtitle=ft.Text("Mobile: xxxxxxxxxx", size=12),
                                                trailing=ft.Container(
                                                    content=ft.Text("0.0", size=12),
                                                    bgcolor="#dbeafe",
                                                    padding=5,
                                                    border_radius=10
                                                ),
                                                on_click=lambda e, c={"name": query.title()}: self.select_customer(c),
                                            )
                                        ]
        self.page.update()

    def delete_bill(self, e):
        n = self.bills.index(self)-1
        Tab.tabs.pop(n)
        if n:
            bill_tabs.selected_index = n -1
        else:
            bill_tabs.selected_index = n

        self.bills.remove(self)

        for i, t in enumerate(Tab.tabs[:-1]):
            t.tab_content = ft.Row([ft.Text(f"Bill {i+1}")])

        if len(Bill.bills) == 1:
            invoice_tab.add_tab()

        self.page.update()


class Tab:
    tabs = []

    def __init__(self, page):
        self.page = page
        bill_tabs.page = self.page
        # Add the "+" tab
        self.tabs.append(ft.Tab(
            icon=ft.Icons.ADD,
            icon_margin=0,
        ))
        bill_tabs.on_change = self.add_tab
        self.add_tab()  # Add initial bill tab

    def add_tab(self, e=None):
        # Only proceed if the "+" tab was clicked or it's the initial tab creation
        if e and bill_tabs.selected_index != len(self.tabs) - 1:
            return

        bill = Bill(self.page)  # Create new bill instance
        new_tab = ft.Tab(
            tab_content=ft.Row([ft.Text(f"Bill {len(self.tabs)}")]),
            content=ft.Container(bill.bill_area),
        )
        self.tabs.insert(-1, new_tab)  # Insert before the "+" tab
        bill_tabs.tabs = self.tabs

        self.page.update()

        bill_tabs.selected_index = 0

        self.page.update()
        time.sleep(0.01)
        bill_tabs.selected_index = len(self.tabs) - 2

        bill_tabs.animation_duration = 300
        self.page.update()


class Item:
    items = dict()

    def __init__(self, page, p_id, s_id, p_name, price, min_price, stock, unit):
        self.page = page
        self.p_id = p_id
        self.s_id = s_id
        self.rate = price
        self.p_name = p_name
        self.min_price = min_price
        self.stock = stock
        self.unit = unit

        if Bill.bills[bill_tabs.selected_index + 1].data.get(self.s_id, [ft.Row(), 0])[1] < self.stock:
            self.counter = Bill.bills[bill_tabs.selected_index + 1].data.get(self.s_id, [ft.Row(), 0])[1] + 1
        else:
            self.counter = Bill.bills[bill_tabs.selected_index + 1].data.get(self.s_id, [ft.Row(), 0])[1]
        self.add_btn = ft.ElevatedButton(
            text="+",
            width=30,
            on_click=self.add,
            height=30,
        )
        self.reduce_btn = ft.ElevatedButton(
            text="🗑" if self.counter == 1 else "-",
            width=30,
            on_click=self.reduce,
            height=30,
        )
        self.count = ft.TextField(
            value=str(self.counter),
            suffix_text=self.unit,
            fit_parent_size=True,
            text_size=12,
            height=35,
            prefix=self.reduce_btn,
            suffix=self.add_btn,
            content_padding=0,
            border=ft.InputBorder(ft.InputBorder.NONE),
            text_align=ft.TextAlign.CENTER,
            on_change=self.cal,
            input_filter=ft.InputFilter(
                regex_string=r"[0-9]",
                allow=True,
                replacement_string=""
            ),
        )
        self.price = ft.TextField(
            value=str(self.rate),
            keyboard_type=ft.KeyboardType.NUMBER,
            fit_parent_size=True,
            input_filter=ft.InputFilter(
                regex_string=r"[0-9.]",
                allow=True,
                replacement_string=""
            ),
            text_align=ft.TextAlign.CENTER,
            autofill_hints=ft.AutofillHint.COUNTRY_CODE,
            text_size=12,
            height=35,
            content_padding=5,
            border=ft.InputBorder(ft.InputBorder.NONE),
            on_change=self.cal,
            tooltip="min: " + str(self.min_price)
        )
        self.total = ft.TextField(
            value=str(round(self.counter * float(self.price.value), 2)),
            text_size=12,
            expand=True,
            border=ft.InputBorder(ft.InputBorder.NONE),
            read_only=True,
            text_align=ft.TextAlign.CENTER,
        )

        Bill.bills[bill_tabs.selected_index + 1].grandTotal[self.s_id] = round(self.counter * float(self.price.value), 2)

        Bill.bills[bill_tabs.selected_index + 1].grand_total.value = currency + str(round(sum(Bill.bills[bill_tabs.selected_index + 1].grandTotal.values()), 2))
        Bill.bills[bill_tabs.selected_index + 1].total_items.value = str(len(Bill.bills[bill_tabs.selected_index + 1].grandTotal.values())) + " Item(s)"

        self.row = ft.DataRow(
            [
                ft.DataCell(
                    ft.Text(self.p_name, size=12),
                ),
                ft.DataCell(
                    self.count,
                ),
                ft.DataCell(
                    self.price
                ),
                ft.DataCell(
                    self.total,
                )
            ]
        )

        self.dummy_count = ft.Text(width=self.count.width)
        self.dummy_price = ft.Text(width=self.price.width)
        self.dummy_total = ft.Text(width=self.total.width)

        self.dummy_row = ft.DataRow(
            [
                ft.DataCell(
                    ft.Text(self.p_name, size=12),
                ),
                ft.DataCell(
                    self.dummy_count,
                ),
                ft.DataCell(
                    self.dummy_price,
                ),
                ft.DataCell(
                    self.dummy_total,
                )
            ],
        )

        Bill.bills[bill_tabs.selected_index + 1].data[self.s_id] = [self.row, self.counter]

        Bill.bills[bill_tabs.selected_index + 1].dummy_data[self.s_id] = [self.dummy_row, self.counter]
        Bill.bills[bill_tabs.selected_index + 1].bill_table.rows = [i[0] for i in Bill.bills[bill_tabs.selected_index + 1].data.values()]

        Bill.bills[bill_tabs.selected_index + 1].dummy_table.rows = [i[0] for i in Bill.bills[bill_tabs.selected_index + 1].dummy_data.values()]

        try:
            scroll_to_end()
        except:
            pass
        if int(self.count.value) == self.stock:
            self.add_btn.disabled = True

        Bill.bills[bill_tabs.selected_index + 1].proceed_to_payment.disabled = False
        Bill.bills[bill_tabs.selected_index + 1].proceed_to_payment.style = ft.ButtonStyle(color=ft.Colors.GREEN,)

        temp = {
            "count": 0,
            "price": self.rate,
            "max_price": self.rate,
        }

        self.items[self.s_id] = {"count": self.items.get(self.s_id, temp)["count"] + 1, "price":self.rate, "max_price": self.rate}

        self.page.update()

    def add(self, e):
        self.count.value = str(int(self.count.value) + 1)
        self.reduce_btn.disabled = False
        self.cal()
        if int(self.count.value) == self.stock:
            self.add_btn.disabled = True

        self.reduce_btn.text = "-"
        self.reduce_btn.icon = None
        Bill.bills[bill_tabs.selected_index + 1].grand_total.value = currency + str(round(sum(Bill.bills[bill_tabs.selected_index + 1].grandTotal.values()), 2))
        Bill.bills[bill_tabs.selected_index + 1].total_items.value = str(len(Bill.bills[bill_tabs.selected_index + 1].grandTotal.values())) + " Item(s)"

        Bill.bills[bill_tabs.selected_index + 1].proceed_to_payment.opacity = False
        Bill.bills[bill_tabs.selected_index + 1].proceed_to_payment.style = ft.ButtonStyle(color=ft.Colors.GREEN,)
        self.page.update()

    def cal(self, e=None):
        try:
            self.counter = int(self.count.value)
        except:
            pass
        if self.counter > self.stock:
            self.counter = self.stock
            self.count.value = str(int(self.stock))

        if self.count.value == "0":
            self.reduce(e)
            return 0

        if self.count.value == "":
            self.count.value = "0"

        if int(self.count.value) == 1:
            self.reduce_btn.text = "🗑"

        self.total.value = str(round(float(self.price.value) * float(self.count.value), 2))
        self.dummy_count.width = self.count.width
        self.dummy_price.width = self.price.width
        self.dummy_total.width = self.total.width

        self.counter = int(self.count.value)

        if Bill.bills[bill_tabs.selected_index + 1].data[self.s_id]:
            Bill.bills[bill_tabs.selected_index + 1].data[self.s_id] = [self.row, self.counter]

        Bill.bills[bill_tabs.selected_index + 1].grandTotal[self.s_id] = round(self.counter * float(self.price.value), 2)

        Bill.bills[bill_tabs.selected_index + 1].grand_total.value = currency + str(round(sum(Bill.bills[bill_tabs.selected_index + 1].grandTotal.values()), 2))
        Bill.bills[bill_tabs.selected_index + 1].total_items.value = str(len(Bill.bills[bill_tabs.selected_index + 1].grandTotal.values())) + " Item(s)"

        if not Bill.bills[bill_tabs.selected_index + 1].grandTotal:
            Bill.bills[bill_tabs.selected_index + 1].proceed_to_payment.disabled = True
            Bill.bills[bill_tabs.selected_index + 1].proceed_to_payment.style = ft.ButtonStyle(color=ft.Colors.GREY,)

        self.dummy_row.update()
        self.items[self.s_id]["count"] = self.count.value
        self.items[self.s_id]["price"] = self.price.value

        self.page.update()

    def reduce(self, e):
        if self.reduce_btn.text == "🗑":
            del Bill.bills[bill_tabs.selected_index + 1].data[self.s_id]
            del Bill.bills[bill_tabs.selected_index + 1].grandTotal[self.s_id]
        else:
            self.count.value = str(int(self.count.value) - 1)
            self.add_btn.disabled = False

            if int(self.count.value) == 1:
                self.reduce_btn.text = "🗑"

            self.cal()

        Bill.bills[bill_tabs.selected_index + 1].grand_total.value = currency + str(round(sum(Bill.bills[bill_tabs.selected_index + 1].grandTotal.values()), 2))
        Bill.bills[bill_tabs.selected_index + 1].total_items.value = str(len(Bill.bills[bill_tabs.selected_index + 1].grandTotal.values())) + " Item(s)"

        Bill.bills[bill_tabs.selected_index + 1].bill_table.rows = [i[0] for i in Bill.bills[bill_tabs.selected_index + 1].data.values()]

        if not Bill.bills[bill_tabs.selected_index + 1].grandTotal:
            Bill.bills[bill_tabs.selected_index + 1].proceed_to_payment.disabled = True
            Bill.bills[bill_tabs.selected_index + 1].proceed_to_payment.style = ft.ButtonStyle(color=ft.Colors.GREY,)

        self.page.update()


class Stock:
    data = dict()

    def __init__(self, page, s_id, p_id, min_price, price, exp_date, available, unit, p_name):
        self.page = page
        self.s_id = s_id
        self.p_id = p_id
        self.min_price = min_price
        self.price = price
        self.exp_date = exp_date
        self.available = available
        self.unit = unit
        self.p_name = p_name

        self.stck = ft.Container(
            ft.ListTile(
                title=ft.Text(f'Rs. {self.min_price} - {self.price}'),
                subtitle=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Text('Expire Date:', size=12),
                                ft.Text(f'{self.exp_date}', size=12, color=ft.Colors.RED,
                                        weight=ft.FontWeight.BOLD),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,

                        ),
                        ft.Row(
                            [
                                ft.Text('Available:', size=12),
                                ft.Text(f'{self.available} {self.unit}', size=12,
                                        color=ft.Colors.GREEN, weight=ft.FontWeight.BOLD),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        ),
                    ],

                ),
                content_padding=5,
            ),
            border_radius=10,
            border=ft.border.only(bottom=ft.BorderSide(2, ft.Colors.BLACK)),
            on_click=self.select,
            padding=0,
            on_hover=lambda e: hover(e),
            bgcolor=ft.Colors.GREY_100
        )

        def hover(event):
            if event.data == "true":
                self.stck.bgcolor = ft.Colors.GREY_400
            else:
                self.stck.bgcolor = ft.Colors.GREY_100
            self.page.update()

        if self.stck not in self.data.get(self.p_id, []):
            self.data[self.p_id] = self.data.get(self.p_id, []) + [self.stck]

    def select(self, e):
        if Tab.tabs[bill_tabs.selected_index].content == Bill.bills[bill_tabs.selected_index + 1].payment_area:
            Bill.bills[bill_tabs.selected_index + 1].back()
        Item(self.page, self.p_id, self.s_id, self.p_name, self.price, self.min_price, self.available, self.unit)
        self.page.update()


class Product:
    data = []

    def __init__(self, page, p_id, title, note, unit, image):
        global SESSION
        self.page = page
        self.id = p_id
        self.title = title
        self.note = note
        self.unit = unit
        self.image = image

        # ORM: load active stocks for this product
        stocks = (
            SESSION.query(DB.Stock)
            .filter(DB.Stock.product_id == self.id, DB.Stock.status == 'active')
            .order_by(DB.Stock.id.asc())
            .all()
        )

        # respect expire_date filter like your original
        today = datetime.now().date()
        filtered = []
        for s in stocks:
            # include if expire_date is None or >= today
            if s.expire_date is None or s.expire_date >= today:
                filtered.append(s)

        # Convert to dicts that make_card() expected earlier
        self.stocks = [
            {
                "stock_id": s.id,
                "product_id": s.product_id,
                "current_stock": s.current_stock,
                "min_selling_price": s.min_selling_price,
                "selling_price": s.selling_price,
                "expire_date": s.expire_date,
                "status": s.status,
                # unit name is on Product -> Unit; use cached 'unit' arg
                "unit_name": units.get(self.unit, ""),
            }
            for s in filtered
        ]

        self.make_card()

    def hover(self, e):
        if e.data == "true":
            self.stock_details.visible = True
            self.img.visible = False
        else:
            self.stock_details.visible = False
            self.img.visible = True
        self.page.update()

    def make_card(self):
        for i in self.stocks:
            Stock(
                self.page,
                i["stock_id"],
                i["product_id"],
                i["min_selling_price"],
                i["selling_price"],
                i["expire_date"],
                i["current_stock"],
                i["unit_name"],
                self.title
            )

        self.stock_details = ft.Column(
            Stock.data.get(self.id, []),
            visible=False,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

        self.img = ft.Stack(
            [
                ft.Container(
                    ft.Image(
                        "src/" + self.image if self.image else "src/",
                        aspect_ratio=1,
                        border_radius=5,

                    ),
                    bgcolor=ft.Colors.WHITE,
                    shadow=ft.BoxShadow(
                        spread_radius=0.51,
                        blur_radius=3,
                        color=ft.Colors.BLACK12,
                        offset=ft.Offset(1, 1),
                        blur_style=ft.ShadowBlurStyle.NORMAL,
                    ),
                ),

                ft.Container(
                    ft.Text(
                        self.title.title(),
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                        expand=True,
                        opacity=0
                    ),
                    bgcolor=ft.Colors.WHITE,
                    opacity=0.75,
                    alignment=ft.alignment.top_center,
                    padding=5
                ),
                ft.Container(
                    ft.Text(
                        self.title.title(),
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                        expand=True,
                    ),
                    alignment=ft.alignment.top_center,
                    padding=5
                ),
            ]
        )
        d = ft.Container(
            ft.Column(
                [

                    ft.Container(
                        self.stock_details,
                    ),
                    ft.Container(
                        self.img
                    )
                ],
                expand=True,
                alignment=ft.MainAxisAlignment.START,
                scroll=ft.ScrollMode.AUTO,

            ),
            border_radius=5,
            padding=5,
            col={"sm": 12, "lg":6 ,"xl": 4, "xxl": 3},
            bgcolor=ft.Colors.WHITE,
            shadow=ft.BoxShadow(
                spread_radius=0.51,
                blur_radius=3,
                color=ft.Colors.BLACK12,
                offset=ft.Offset(1, 1),
                blur_style=ft.ShadowBlurStyle.NORMAL,
            ),
            on_hover=self.hover,
            expand=True,
            aspect_ratio=1

        )
        self.data.append(d)


def scroll_to_end():
    Bill.bills[bill_tabs.selected_index+1].bill_box.scroll_to(offset=-1, duration=0, curve=ft.AnimationCurve.EASE_IN_OUT)


def bill(page: ft.Page, conn, user_id):
    global filtered_products, CONN, USER_ID, SESSION, TAX

    CONN = conn
    SESSION = Session(CONN)
    USER_ID = user_id

    # TAX (ORM)
    tax_row = SESSION.query(DB.Variables.value).filter(DB.Variables.name == 'tax_percentage').first()
    TAX = float(tax_row[0]) if tax_row else 0.0

    # Products (ORM)
    products = (
        SESSION.query(DB.Product)
        .order_by(DB.Product.id.asc())
        .limit(18)
        .all()
    )
    filtered_products = [
        {
            "id": p.id,
            "title": p.title,
            "note": p.note,
            "unit_id": p.unit_id,
            "sub_category_id": p.sub_category_id,
            "code": p.code,
            "barcode": p.barcode,
            "has_expire": p.has_expire,
            "image": p.image,
        }
        for p in products
    ]

    # Units map (ORM)
    units.clear()
    for uid, uname in SESSION.query(DB.Unit.id, DB.Unit.unit).all():
        units[uid] = uname

    if not Tab.tabs:
        global invoice_tab
        Bill(page)
        invoice_tab = Tab(page)

    Product.data = []
    Stock.data = dict()

    for i in filtered_products:
        Product(page, i["id"], i["title"], i["note"], i["unit_id"], i["image"])

    def filter_products(e=None, q=None):
        global filtered_products, customers
        query = (e.control.value if e else q or "").strip()

        # Products filter (ORM)
        products_q = (
            SESSION.query(DB.Product)
            .filter(
                or_(
                    DB.Product.code.ilike(f"%{query}%"),
                    cast(DB.Product.id, String).ilike(f"%{query}%"),
                    DB.Product.title.ilike(f"%{query}%"),
                    DB.Product.note.ilike(f"%{query}%"),
                )
            )
            .order_by(DB.Product.id.asc())
            .limit(18)
        )
        products = products_q.all()
        filtered_products = [
            {
                "id": p.id,
                "title": p.title,
                "note": p.note,
                "unit_id": p.unit_id,
                "sub_category_id": p.sub_category_id,
                "code": p.code,
                "barcode": p.barcode,
                "has_expire": p.has_expire,
                "image": p.image,
            }
            for p in products
        ]

        Product.data = []
        Stock.data = dict()
        for i in filtered_products:
            Product(page, i["id"], i["title"], i["note"], i["unit_id"], i["image"])

        products_list.controls = Product.data
        page.update()

    search_bar = ft.TextField(
        label="Search Product",
        expand=True,
        focused_border_color=ft.Colors.BLUE,
        border_radius=10,
        border_width=2,
        prefix_icon=ft.Icons.INVENTORY,
        suffix_icon=ft.Icons.SEARCH,
        on_change=lambda e: filter_products(e),
    )

    products_list.controls = Product.data

    product_display = ft.Container(
        ft.Column(
            [products_list],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        ),
    )

    search_area = ft.Container(
        ft.Column(
            controls=[
                ft.Container(
                    search_bar
                ),
                ft.Container(
                    product_display,
                    expand=True,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            expand=True,
        )
    )

    return ft.Container(
        ft.ResponsiveRow(
            [
                ft.Container(
                    search_area,
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
                    expand=True,
                    col={"sm": 12, "md": 5, "lg": 6, "xl": 7, "xxl": 8}
                ),
                ft.Container(
                    bill_tabs,
                    col={"sm": 12, "md": 7, "lg": 6, "xl": 5, "xxl": 4},
                )
            ],
            expand=True,
        ),
        expand=True,
    )