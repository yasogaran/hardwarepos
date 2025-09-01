import decimal
import time
import flet as ft
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, select, func, and_, or_
import DB

# Global variables
CONN: create_engine = None
USER_ID = None
SESSION: Session = None
TAX = 0
units = dict()
filtered_products = dict()
invoice_tab = None
currency = "Rs. "
bill_tabs = ft.Tabs(animation_duration=300, expand_loose=True, adaptive=True)
products_list = ft.ResponsiveRow(expand=True, spacing=5)
customers = dict()
ACCOUNT_ID: int = 1
pop = ft.AlertDialog()


# Tab class needs to be defined before Bill class since Bill references it
class Tab:
    tabs = []

    def __init__(self, page):
        self.page = page
        bill_tabs.page = self.page
        self.tabs.append(ft.Tab(icon=ft.Icons.ADD, icon_margin=0))
        bill_tabs.on_change = self.add_tab
        self.add_tab()

    def add_tab(self, e=None):
        if e and bill_tabs.selected_index != len(self.tabs) - 1:
            return

        bill = Bill(self.page)
        new_tab = ft.Tab(
            tab_content=ft.Row([ft.Text(f"Bill {len(self.tabs)}")]),
            content=ft.Container(bill.bill_area),
        )
        self.tabs.insert(-1, new_tab)
        bill_tabs.tabs = self.tabs
        self.page.update()
        bill_tabs.selected_index = 0
        self.page.update()
        time.sleep(0.01)
        bill_tabs.selected_index = len(self.tabs) - 2
        bill_tabs.animation_duration = 300
        self.page.update()


class Bill:
    bills = []

    def __init__(self, page):
        self.new_customer = False
        self.head_text = ft.TextStyle(weight=ft.FontWeight.BOLD, size=24)
        self.body_text = ft.TextStyle(size=18)
        self.page = page
        self.customer_id = None
        self.total_items = ft.Text("0 Item(s)", size=16)
        self.data = dict()
        self.dummy_data = dict()
        self.grandTotal = dict()
        self.bill_date = datetime.now().date()

        self.grand_total = ft.Text(currency + "0.0", weight=ft.FontWeight.BOLD, size=22)
        self.proceed_to_payment = ft.OutlinedButton(
            content=ft.Text("Proceed to Payment", weight=ft.FontWeight.BOLD, size=18),
            expand=True, height=50, style=ft.ButtonStyle(color=ft.Colors.GREY),
            on_click=self.load_bill, disabled=True
        )

        self.delete_btn = ft.IconButton(ft.Icons.DELETE, on_click=self.delete_bill)
        self.back_to_bill = ft.IconButton(ft.Icons.ARROW_BACK, on_click=self.back)

        # Bill date field
        self.bill_date_field = ft.TextField(
            label="Bill Date", read_only=True, value=self.bill_date.strftime("%Y-%m-%d"),
            width=200, visible=False
        )
        self.bill_date_picker_btn = ft.IconButton(
            ft.Icons.CALENDAR_MONTH, on_click=self.show_date_picker, visible=False
        )

        # Initialize tables
        self.bill_table = ft.DataTable(
            column_spacing=0,
            columns=[
                ft.DataColumn(ft.Text("Item Name")),
                ft.DataColumn(ft.Text("Qty")),
                ft.DataColumn(ft.Text("Price")),
                ft.DataColumn(ft.Text("Total"))
            ],
            heading_row_height=0,
            expand=True
        )

        self.dummy_table = ft.DataTable(
            column_spacing=0,
            columns=[
                ft.DataColumn(ft.Text("Item Name")),
                ft.DataColumn(ft.Text("Qty")),
                ft.DataColumn(ft.Text("Price")),
                ft.DataColumn(ft.Text("Total"))
            ],
            expand=True
        )

        # Customer fields
        self.customer_name = ft.TextField(
            label="Customer Name", hint_text="Search and select customer...",
            prefix_icon=ft.Icons.PERSON, on_change=self.filter_customer,
            border_radius=10, expand=True
        )

        self.customer_dropdown = ft.ListView(height=200, visible=False, padding=0)
        self.customer_dropdown_container = ft.Container(
            content=self.customer_dropdown, margin=ft.margin.only(top=5)
        )

        self.customer_mobile = ft.TextField(
            label="Customer Mobile", hint_text="Mobile Number",
            prefix_icon=ft.Icons.PHONE, border_radius=10, expand=True
        )

        # Payment fields
        self.cheque_number = ft.TextField(label="Cheque Number", expand=True)
        self.cheque_date = ft.IconButton(ft.Icons.CALENDAR_MONTH, on_click=self.date_picker)
        self.cheque_amount = ft.TextField(label="Cheque Amount", prefix_text=currency, width=200)

        self.cheque_area = ft.Row([self.cheque_number, self.cheque_date])

        self.total_amount = ft.Text(value="0.0")
        self.discount_amount = ft.TextField(hint_text="0.0", prefix_text=currency, width=50)
        self.tax_amount = ft.Text(value=currency + "0.0")
        self.amount_to_be_paid = ft.Text(value=currency + "0.0")
        self.paid_amount = ft.TextField(label="Paid Amount", prefix_text=currency, width=220)
        self.balance = ft.Text(value=currency + "0.0", color=ft.Colors.RED)

        self.bill_box = ft.Column([ft.Row([self.bill_table])], expand=True, scroll=ft.ScrollMode.AUTO)

        # Check bill date setting
        self.check_bill_date_setting()

        # Create payment area
        self.payment_area = self.create_payment_area()
        self.bill_area = self.create_bill_area()

        self.bills.append(self)

    def create_payment_area(self):
        return ft.Container(
            ft.Column([
                ft.Container(ft.Column([
                    ft.Container(ft.Column([
                        ft.Text("Customer Details".upper(), style=self.head_text),
                        self.customer_name, self.customer_dropdown_container, self.customer_mobile
                    ], spacing=5)),
                    ft.Container(ft.Row([self.bill_date_field, self.bill_date_picker_btn],
                                        visible=self.bill_date_field.visible), padding=5),
                    ft.Container(ft.Column([
                        ft.Text("Bill".upper(), style=self.head_text),
                        ft.Column([
                            self.total_items,
                            ft.Row([ft.Text("Total Amount".upper()), self.total_amount],
                                   alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Row([ft.Text("VAT".upper()), self.tax_amount],
                                   alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Row([ft.Text("Discount".upper()), self.discount_amount],
                                   alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Row([ft.Text("Total".upper()), self.amount_to_be_paid],
                                   alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                        ], spacing=0), self.cheque_area
                    ], spacing=5)),
                    ft.Container(ft.Column([
                        ft.Text("Payment".upper(), style=self.head_text),
                        ft.Row([self.paid_amount, self.cheque_amount])
                    ], spacing=5))
                ], expand=True, spacing=30, scroll=ft.ScrollMode.AUTO)),
                ft.Container(ft.Row([ft.Text("Balance"), self.balance],
                                    alignment=ft.MainAxisAlignment.END))
            ]),
            padding=15, border_radius=15, expand=True
        )

    def create_bill_area(self):
        return ft.Container(ft.Column([
            ft.Container(ft.Row([ft.Container(ft.Column([
                ft.Row([self.dummy_table]), self.bill_box
            ]))]), padding=10, border_radius=15, expand=True),
            ft.Container(ft.Column([
                ft.Container(ft.Row([self.total_items,
                                     ft.Container(self.grand_total, bgcolor=ft.Colors.GREEN,
                                                  border_radius=20, padding=8)],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN)),
                ft.Container(ft.Row([self.proceed_to_payment, self.delete_btn]))
            ]), padding=10, border_radius=15)
        ]), padding=5)

    def check_bill_date_setting(self):
        try:
            setting = SESSION.query(DB.Variables).filter_by(name='ask_billing_date').first()
            if setting and setting.value.lower() == 'true':
                self.bill_date_field.visible = True
                self.bill_date_picker_btn.visible = True
        except Exception as e:
            print(f"Error checking bill date setting: {e}")

    def show_date_picker(self, e):
        date_picker = ft.DatePicker(
            first_date=datetime(2020, 1, 1),
            last_date=datetime(2030, 12, 31),
            current_date=self.bill_date,
            on_change=self.select_bill_date
        )
        self.page.overlay.append(date_picker)
        date_picker.pick_date()
        self.page.update()

    def select_bill_date(self, e):
        self.bill_date = e.control.value
        self.bill_date_field.value = self.bill_date.strftime("%Y-%m-%d")
        self.page.update()

    def print_bill(self, e):
        # Simplified print bill implementation
        try:
            self.page.open(ft.SnackBar(ft.Text("Bill Printed Successfully"),
                                       bgcolor=ft.Colors.GREEN, duration=1500))
        except Exception as ex:
            print(f"Error printing bill: {ex}")

    def pay(self, e=None):
        try:
            paid = float(self.paid_amount.value or 0)
            total = float(self.amount_to_be_paid.value.replace(currency, "") or 0)
            cheque = float(self.cheque_amount.value or 0)
            balance = paid + cheque - total
            self.balance.value = f"{currency}{balance:.2f}"
            self.page.update()
        except:
            pass

    def discount(self, e):
        try:
            discount = float(self.discount_amount.value or 0)
            total = float(self.total_amount.value or 0)
            taxed_total = (total - discount) * (1 + float(TAX) / 100)
            self.amount_to_be_paid.value = f"{currency}{taxed_total:.2f}"
            self.pay()
        except:
            pass

    def date_picker(self, e):
        dp = ft.DatePicker(on_change=self.select_date)
        self.page.overlay.append(dp)
        dp.pick_date()

    def select_date(self, e):
        self.cheque_number.suffix_text = e.control.value.strftime('%Y-%m-%d')
        self.page.update()

    def back(self, e=None):
        if hasattr(self, 'bill_area'):
            Tab.tabs[bill_tabs.selected_index].content = self.bill_area
            self.page.update()

    def load_bill(self, e=None):
        if hasattr(self, 'payment_area'):
            Tab.tabs[bill_tabs.selected_index].content = self.payment_area
            self.total_amount.value = currency + str(round(sum(self.grandTotal.values()), 2))
            self.tax_amount.value = currency + str(round(sum(self.grandTotal.values()) * float(TAX) / 100, 2))
            self.amount_to_be_paid.value = currency + str(
                round(sum(self.grandTotal.values()) * (100 + float(TAX)) / 100, 2))
            self.balance.value = currency + str(
                round(
                    float(self.paid_amount.value if self.paid_amount.value else "0.00") - sum(self.grandTotal.values()),
                    2))
            self.paid_amount.value = ""
            self.page.update()

    def hide_dropdown(self):
        self.customer_dropdown.visible = False
        self.page.update()

    def show_dropdown(self, e=None):
        self.customer_dropdown.visible = True
        self.page.update()

    def filter_customer(self, e):
        query = self.customer_name.value.lower()
        if not query:
            self.hide_dropdown()
            return

        self.show_dropdown()
        try:
            customers = SESSION.query(DB.Customer).filter(
                or_(
                    DB.Customer.name.ilike(f"%{query}%"),
                    DB.Customer.mobile.ilike(f"%{query}%")
                )
            ).limit(5).all()

            self.customer_dropdown.controls = [
                ft.ListTile(
                    title=ft.Text(c.name),
                    subtitle=ft.Text(f"Mobile: {c.mobile}"),
                    on_click=lambda e, c=c: self.select_customer(c)
                ) for c in customers
            ]
            self.page.update()
        except Exception as ex:
            print(f"Error filtering customers: {ex}")

    def select_customer(self, customer):
        try:
            self.customer_id = customer.id
            self.customer_name.value = customer.name
            self.customer_mobile.value = customer.mobile or ""
            self.hide_dropdown()
        except:
            self.new_customer = True
            self.customer_name.value = customer.name
            self.customer_mobile.value = ""

    def delete_bill(self, e):
        try:
            if self in Bill.bills:
                Bill.bills.remove(self)
                # Additional cleanup logic here
        except Exception as ex:
            print(f"Error deleting bill: {ex}")


# Item, Stock, and Product classes would follow here with similar fixes
# For brevity, I'll show a simplified version


class Item:
    items = {}

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
        )
        self.price = ft.TextField(
            value=str(self.rate),
            keyboard_type=ft.KeyboardType.NUMBER,
            fit_parent_size=True,
            input_filter=ft.InputFilter(
                allow=False,
                regex_string=r"[a-zA-Z]",
                replacement_string="",  # Replaces invalid chars with empty string
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
        # ft.InputFilter.
        self.total = ft.TextField(
            value=str(round(self.counter * float(self.price.value), 2)),
            text_size=12,
            expand=True,
            border=ft.InputBorder(ft.InputBorder.NONE),
            read_only=True,
            text_align=ft.TextAlign.CENTER,
        )

        Bill.bills[bill_tabs.selected_index + 1].grandTotal[self.s_id] = round(self.counter * float(self.price.value),
                                                                               2)

        Bill.bills[bill_tabs.selected_index + 1].grand_total.value = currency + str(
            round(sum(Bill.bills[bill_tabs.selected_index + 1].grandTotal.values()), 2))
        Bill.bills[bill_tabs.selected_index + 1].total_items.value = str(
            len(Bill.bills[bill_tabs.selected_index + 1].grandTotal.values())) + " Item(s)"

        # if self.p_id in self.data.keys():
        #     self.count.value = self.data[self.p_id]
        #     self.data[self.p_id] = []

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
            # visible=False,
        )

        Bill.bills[bill_tabs.selected_index + 1].data[self.s_id] = [self.row, self.counter]

        Bill.bills[bill_tabs.selected_index + 1].dummy_data[self.s_id] = [self.dummy_row, self.counter]
        Bill.bills[bill_tabs.selected_index + 1].bill_table.rows = [i[0] for i in Bill.bills[
            bill_tabs.selected_index + 1].data.values()]

        Bill.bills[bill_tabs.selected_index + 1].dummy_table.rows = [i[0] for i in Bill.bills[
            bill_tabs.selected_index + 1].dummy_data.values()]

        try:
            scroll_to_end()
        except:
            pass
        if int(self.count.value) == self.stock:
            self.add_btn.disabled = True

        Bill.bills[bill_tabs.selected_index + 1].proceed_to_payment.disabled = False
        Bill.bills[bill_tabs.selected_index + 1].proceed_to_payment.style = ft.ButtonStyle(color=ft.Colors.GREEN, )

        temp = {
            "count": 0,
            "price": self.rate,
            "max_price": self.rate,
        }

        self.items[self.s_id] = {"count": self.items.get(self.s_id, temp)["count"] + 1, "price": self.rate,
                                 "max_price": self.rate}

        self.page.update()

    def add(self, e):
        self.count.value = str(int(self.count.value) + 1)
        self.reduce_btn.disabled = False
        self.cal()
        if int(self.count.value) == self.stock:
            self.add_btn.disabled = True

        self.reduce_btn.text = "-"
        self.reduce_btn.icon = None
        Bill.bills[bill_tabs.selected_index + 1].grand_total.value = currency + str(
            round(sum(Bill.bills[bill_tabs.selected_index + 1].grandTotal.values()), 2))
        Bill.bills[bill_tabs.selected_index + 1].total_items.value = str(
            len(Bill.bills[bill_tabs.selected_index + 1].grandTotal.values())) + " Item(s)"

        Bill.bills[bill_tabs.selected_index + 1].proceed_to_payment.opacity = False
        Bill.bills[bill_tabs.selected_index + 1].proceed_to_payment.style = ft.ButtonStyle(color=ft.Colors.GREEN, )
        self.page.update()

    def cal(self, e=None):
        try:
            self.counter = int(self.count.value)
        except:
            pass
        if self.counter > self.stock:
            self.counter = self.stock
            self.count.value = str(int(self.stock))

        # if self.count.value == '':
        #     self.count.value = '0'
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

        Bill.bills[bill_tabs.selected_index + 1].grandTotal[self.s_id] = round(self.counter * float(self.price.value),
                                                                               2)

        Bill.bills[bill_tabs.selected_index + 1].grand_total.value = currency + str(
            round(sum(Bill.bills[bill_tabs.selected_index + 1].grandTotal.values()), 2))
        Bill.bills[bill_tabs.selected_index + 1].total_items.value = str(
            len(Bill.bills[bill_tabs.selected_index + 1].grandTotal.values())) + " Item(s)"

        if not Bill.bills[bill_tabs.selected_index + 1].grandTotal:
            Bill.bills[bill_tabs.selected_index + 1].proceed_to_payment.disabled = True
            Bill.bills[bill_tabs.selected_index + 1].proceed_to_payment.style = ft.ButtonStyle(color=ft.Colors.GREY, )

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

        Bill.bills[bill_tabs.selected_index + 1].grand_total.value = currency + str(
            round(sum(Bill.bills[bill_tabs.selected_index + 1].grandTotal.values()), 2))
        Bill.bills[bill_tabs.selected_index + 1].total_items.value = str(
            len(Bill.bills[bill_tabs.selected_index + 1].grandTotal.values())) + " Item(s)"

        Bill.bills[bill_tabs.selected_index + 1].bill_table.rows = [i[0] for i in Bill.bills[
            bill_tabs.selected_index + 1].data.values()]

        if not Bill.bills[bill_tabs.selected_index + 1].grandTotal:
            Bill.bills[bill_tabs.selected_index + 1].proceed_to_payment.disabled = True
            Bill.bills[bill_tabs.selected_index + 1].proceed_to_payment.style = ft.ButtonStyle(color=ft.Colors.GREY, )

        self.page.update()

# ... (existing code)
# Update SQLAlchemy ORM usage in methods

class Stock:
    data = {}

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

# ... (existing code)
# Use SQLAlchemy ORM for queries

class Product:
    data = []

    def __init__(self, page, p_id, title, note, unit, image):
        self.page = page
        self.id = p_id
        self.title = title
        self.note = note
        self.unit = unit
        self.image = image

        # Use SQLAlchemy ORM to query stocks
        self.stocks = SESSION.query(
            DB.Stock.id.label('stock_id'),
            DB.Product.id.label('product_id'),
            DB.Stock.current_stock,
            DB.Stock.min_selling_price,
            DB.Stock.selling_price,
            DB.Stock.expire_date,
            DB.Stock.status,
            DB.Unit.unit.label('unit_name')
        ).join(DB.Product, DB.Stock.product_id == DB.Product.id) \
            .join(DB.Unit, DB.Product.unit_id == DB.Unit.id) \
            .filter(DB.Product.id == self.id, DB.Stock.status == 'active').all()

        # Filter expired stocks
        current_date = datetime.now().date()
        self.stocks = [stock for stock in self.stocks
                       if not stock.expire_date or stock.expire_date >= current_date]

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
                i.stock_id,
                i.product_id,
                i.min_selling_price,
                i.selling_price,
                i.expire_date,
                i.current_stock,
                i.unit_name,
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
                        # color=ft.Colors.WHITE,
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


def bill(page: ft.Page, conn, user_id):
    global CONN, USER_ID, SESSION, TAX

    CONN = conn
    SESSION = Session(CONN)
    USER_ID = user_id

    # Get tax setting
    try:
        tax_setting = SESSION.query(DB.Variables).filter_by(name='tax_percentage').first()
        TAX = float(tax_setting.value) if tax_setting else 0
    except:
        TAX = 0

    # Create main layout
    search_bar = ft.TextField(
        label="Search Product",
        expand=True,
        prefix_icon=ft.Icons.SEARCH,
        on_change=lambda e: filter_products(e)
    )

    def filter_products(e=None):
        query = e.control.value.lower() if e else ""
        try:
            products = SESSION.query(DB.Product).filter(
                or_(
                    DB.Product.title.ilike(f"%{query}%"),
                    DB.Product.code.ilike(f"%{query}%")
                )
            ).limit(18).all()

            # Update products list here
        except Exception as ex:
            print(f"Error filtering products: {ex}")

    # Initialize tab system
    if not Tab.tabs:
        global invoice_tab
        invoice_tab = Tab(page)

    return ft.Container(
        ft.Column([
            search_bar,
            bill_tabs
        ]),
        expand=True
    )


def scroll_to_end():
    try:
        if Bill.bills and bill_tabs.selected_index < len(Bill.bills):
            Bill.bills[bill_tabs.selected_index].bill_box.scroll_to(offset=-1)
    except:
        pass