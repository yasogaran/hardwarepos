import flet as ft
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
import calendar

from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import and_
# from your_models import ExpenseTracker  # <- ensure this import matches your project
# Using the class you provided:
from sqlalchemy import Column, Integer, Text, Numeric, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class ExpenseTracker(Base):
    __tablename__ = 'expenseTracker'
    id = Column(Integer, primary_key=True, autoincrement=True)
    description = Column(Text, nullable=False)
    income = Column(Numeric(10, 2), default=0)
    outcome = Column(Numeric(10, 2), default=0)
    date = Column(DateTime, default=datetime.now)


def accounts(page: ft.Page, conn, user_id):
    import flet as ft
    from datetime import datetime, timedelta
    from decimal import Decimal, ROUND_HALF_UP
    import calendar
    from sqlalchemy.orm import Session, sessionmaker
    from sqlalchemy import and_


    # --- make a session from `conn`
    if isinstance(conn, Session):
        session = conn
        _owns_session = False
    else:
        SessionLocal = sessionmaker(bind=conn, autoflush=False, autocommit=False)
        session = SessionLocal()
        _owns_session = True

    # --- helpers
    def money(x):
        try:
            q = Decimal(str(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        except Exception:
            q = Decimal("0.00")
        return f"{q:,.2f}"

    today = datetime.now()
    current_year = today.year
    current_month = today.month

    # --- Top filters: Month & Date
    month_dd = ft.Dropdown(
        label="Month",
        value=str(current_month),
        options=[ft.dropdown.Option(str(i), text=calendar.month_name[i]) for i in range(1, 13)],
        width=180
    )

    def _date_options_for(month: int, year: int):
        days_in_month = calendar.monthrange(year, month)[1]
        return [ft.dropdown.Option("0", text="All days")] + [
            ft.dropdown.Option(str(d)) for d in range(1, days_in_month + 1)
        ]

    date_dd = ft.Dropdown(
        label="Date",
        value="0",
        options=_date_options_for(current_month, current_year),
        width=160
    )

    filter_row = ft.Row(
        controls=[month_dd, date_dd],
        alignment=ft.MainAxisAlignment.START,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    # --- DataTable (wider spacing for readability)
    table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Date")),
            ft.DataColumn(ft.Text("Description")),
            ft.DataColumn(ft.Text("Credit"), numeric=True),
            ft.DataColumn(ft.Text("Debit"), numeric=True),
        ],
        rows=[],
        column_spacing=48,  # wider
        heading_row_color=ft.Colors.with_opacity(0.04, ft.Colors.BLACK),
        divider_thickness=0.8,
        show_bottom_border=True,
    )

    # --- Bottom totals
    total_credit_txt = ft.Text("0.00", weight=ft.FontWeight.BOLD)
    total_debit_txt = ft.Text("0.00", weight=ft.FontWeight.BOLD)
    profit_label = ft.Text("Profit: 0.00", weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN)

    totals_row = ft.Row(
        controls=[
            ft.Container(
                content=ft.Column([ft.Text("Total Credit"), total_credit_txt], spacing=4),
                padding=10, bgcolor=ft.Colors.with_opacity(0.03, ft.Colors.PRIMARY), border_radius=10
            ),
            ft.Container(
                content=ft.Column([ft.Text("Total Debit"), total_debit_txt], spacing=4),
                padding=10, bgcolor=ft.Colors.with_opacity(0.03, ft.Colors.ERROR), border_radius=10
            ),
            ft.Container(
                content=ft.Column([profit_label], spacing=4),
                padding=10, border_radius=10
            ),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )

    # --- Add dialog
    desc_tf = ft.TextField(label="Description", multiline=False, width=400)
    amount_tf = ft.TextField(label="Amount", keyboard_type=ft.KeyboardType.NUMBER, width=200)
    type_dd = ft.Dropdown(
        label="Type",
        options=[ft.dropdown.Option("income"), ft.dropdown.Option("outcome")],
        value="income",
        width=200
    )

    add_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Add Entry"),
        content=ft.Column([desc_tf, amount_tf, type_dd], tight=True, spacing=10),
        actions=[
            ft.TextButton("Cancel", on_click=lambda e: _close_dialog()),
            ft.ElevatedButton("Save", on_click=lambda e: _save_entry()),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    def _open_dialog():
        desc_tf.value, amount_tf.value, type_dd.value = "", "", "income"
        page.open(add_dialog)
        page.update()

    def _close_dialog():
        add_dialog.open = False
        page.update()

    def _snack(msg, color=ft.Colors.PRIMARY):
        page.snack_bar = ft.SnackBar(ft.Text(msg), bgcolor=color)
        page.snack_bar.open = True
        page.update()

    def _selected_month_day():
        return int(month_dd.value), int(date_dd.value)

    def _query_rows():
        m, d = _selected_month_day()
        if d == 0:
            start = datetime(current_year, m, 1)
            end = datetime(current_year + 1, 1, 1) if m == 12 else datetime(current_year, m + 1, 1)
        else:
            start = datetime(current_year, m, d)
            end = start + timedelta(days=1)

        q = session.query(ExpenseTracker).filter(
            and_(ExpenseTracker.date >= start, ExpenseTracker.date < end)
        ).order_by(ExpenseTracker.date.asc(), ExpenseTracker.id.asc())
        return q.all()

    def _load_table():
        rows = _query_rows()
        table.rows.clear()

        total_credit = Decimal("0.00")
        total_debit = Decimal("0.00")

        if not rows:
            table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text("-")),
                        ft.DataCell(ft.Text("No entries")),
                        ft.DataCell(ft.Text("0.00")),
                        ft.DataCell(ft.Text("0.00")),
                    ]
                )
            )
        else:
            for r in rows:
                dstr = r.date.strftime("%Y-%m-%d")
                desc = r.description or ""
                inc = Decimal(str(r.income or 0))
                out = Decimal(str(r.outcome or 0))
                total_credit += inc
                total_debit += out

                table.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(dstr)),
                            ft.DataCell(ft.Text(desc)),
                            ft.DataCell(ft.Text(money(inc))),
                            ft.DataCell(ft.Text(money(out))),
                        ]
                    )
                )

        total_credit_txt.value = money(total_credit)
        total_debit_txt.value = money(total_debit)

        net = total_credit - total_debit
        if net >= 0:
            profit_label.value = f"Profit: {money(net)}"
            profit_label.color = ft.Colors.GREEN
        else:
            profit_label.value = f"Loss: {money(-net)}"
            profit_label.color = ft.Colors.RED

        page.update()

    def _on_month_change(e):
        try:
            m = int(month_dd.value)
        except Exception:
            m = current_month
            month_dd.value = str(m)
        date_dd.options = _date_options_for(m, current_year)
        if int(date_dd.value or "0") > len(date_dd.options) - 1:
            date_dd.value = "0"
        page.update()
        _load_table()

    def _on_date_change(e):
        _load_table()

    month_dd.on_change = _on_month_change
    date_dd.on_change = _on_date_change

    def _save_entry():
        desc = (desc_tf.value or "").strip()
        amt_raw = (amount_tf.value or "").strip()
        kind = (type_dd.value or "income").strip().lower()

        if not desc:
            _snack("Description required", ft.Colors.ERROR)
            return
        try:
            amount = Decimal(amt_raw)
        except Exception:
            _snack("Invalid amount", ft.Colors.ERROR)
            return
        if amount <= 0:
            _snack("Amount must be > 0", ft.Colors.ERROR)
            return

        now = datetime.now()
        if kind == "income":
            rec = ExpenseTracker(description=desc, income=amount, outcome=Decimal("0.00"), date=now)
        else:
            rec = ExpenseTracker(description=desc, income=Decimal("0.00"), outcome=amount, date=now)

        try:
            session.add(rec)
            session.commit()
            _close_dialog()
            _snack("Entry added", ft.Colors.GREEN)
            _load_table()
        except Exception as ex:
            session.rollback()
            _snack(f"DB error: {ex}", ft.Colors.ERROR)

    # --- Make it WIDE + SCROLLABLE ---
    WIDE_TABLE_WIDTH = 1200  # increase if you want it even wider

    # Vertical scroller for long tables
    v_scroller = ft.Column([table], expand=True, scroll=ft.ScrollMode.AUTO)

    # Horizontal scroller wrapping the vertical scroller (for side scroll)


    # Add button bottom-right
    add_btn = ft.FloatingActionButton(icon=ft.Icons.ADD, on_click=lambda e: _open_dialog())

    # Root layout
    root = ft.Container(
        expand=True,
        content=ft.Column(
            controls=[
                filter_row,
                ft.Container(
                    content=v_scroller,
                    alignment=ft.Alignment(0,0),
                    expand=True
                ),
                ft.Row([totals_row, ft.Container(expand=True)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([ft.Container(expand=True), add_btn], alignment=ft.MainAxisAlignment.END),
            ],
            expand=True,
            spacing=12,
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
    )

    _load_table()
    return root

