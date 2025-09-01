"""
Expense Tracker (Flet ≥ 0.28)
=============================
Fully‑functioning single‑file prototype that compiles to an **Android APK** with
`flet build apk`.  All interactions requested by the spec are implemented:

* First‑run wizard → account names + opening balances
* Bottom navigation: **Records · Report · Options**
* Drag‑and‑drop: account → category to create an expense
* Tap account = add income · long‑press account = update balance
* Pie‑chart report with totals per category
* Light/dark theme toggle
* Persistent local storage (no external DB needed)

Run
---
```bash
pip install --upgrade flet   # ensure 0.28+
flet run main.py             # desktop / web preview
flet build apk --release     # Android APK
```
"""
from __future__ import annotations
import json, uuid
from datetime import datetime
from typing import List, Dict, Callable

import flet as ft

###############################################################################
# ── Persistence helpers ─────────────────────────────────────────────────────#
###############################################################################

def load_state(page: ft.Page) -> Dict:
    """Return persisted JSON, or first‑run defaults."""
    raw = page.client_storage.get("state")
    if raw:
        return json.loads(raw)
    return {
        "accounts": [],
        "categories": [
            {"id": "food", "name": "Food & Drink", "icon": "🍔"},
            {"id": "rent", "name": "Rent", "icon": "🏠"},
            {"id": "vehicle", "name": "Vehicle", "icon": "🚗"},
            {"id": "bills", "name": "Bills", "icon": "💡"},
            {"id": "groceries", "name": "Groceries", "icon": "🥕"},
            {"id": "household", "name": "Household", "icon": "🏡"},
            {"id": "fuel", "name": "Fuel", "icon": "⛽"},
            {"id": "personal", "name": "Personal Care", "icon": "💆"},
        ],
        "transactions": [],  # list of expense dictionaries
    }


def save_state(page: ft.Page, state: Dict):
    page.client_storage.set("state", json.dumps(state))

###############################################################################
# ── Composite control: Account card ─────────────────────────────────────────#
###############################################################################

class Account(ft.Row):
    """A draggable/tappable account card (built without UserControl)."""

    def __init__(self, data: Dict, refresh_home: Callable[[], None]):
        super().__init__()
        self.data = data
        self.refresh_home = refresh_home  # callback supplied by view
        self.spacing = 0
        self.controls.append(self._wrap_gestures())

    # ── card visuals ────────────────────────────────────────────────────
    def _card(self):
        return ft.Card(
            content=ft.Container(
                width=160,
                padding=10,
                border_radius=15,
                gradient=ft.LinearGradient(["#7dd5ff", "#4b0082"]),
                content=ft.Column([
                    ft.Text(self.data["name"], weight=ft.FontWeight.BOLD),
                    ft.Text(f"Rs. {self.data['balance']:.2f}", size=12),
                ]),
            )
        )

    def _wrap_gestures(self):
        drag = ft.Draggable(content=self._card(), data=self.data)
        return ft.GestureDetector(
            content=drag,
            on_tap=lambda _: self._add_income_dialog(),
            on_long_press_start=lambda _: self._update_balance_dialog(),
        )

    # ── dialogs ─────────────────────────────────────────────────────────
    def _add_income_dialog(self):
        tf = ft.TextField(label="Amount", keyboard_type=ft.KeyboardType.NUMBER)

        def _submit(_):
            try:
                self.data["balance"] += float(tf.value or "0")
            except ValueError:
                return
            self.refresh_home()
            dlg.open = False; dlg.update()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Add income → {self.data['name']}"),
            content=tf,
            actions=[ft.ElevatedButton("Submit", on_click=_submit)],
        )
        self.page.dialog = dlg; dlg.open = True; dlg.update()

    def _update_balance_dialog(self):
        tf = ft.TextField(label="New balance", value=str(self.data["balance"]),
                          keyboard_type=ft.KeyboardType.NUMBER)

        def _submit(_):
            try:
                self.data["balance"] = float(tf.value or "0")
            except ValueError:
                return
            self.refresh_home()
            dlg.open = False; dlg.update()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Update balance → {self.data['name']}"),
            content=tf,
            actions=[ft.ElevatedButton("Update", on_click=_submit)],
        )
        self.page.dialog = dlg; dlg.open = True; dlg.update()

###############################################################################
# ── First‑run wizard ────────────────────────────────────────────────────────#
###############################################################################

def setup_wizard(page: ft.Page, state: Dict):
    """Collect account names then their opening balances."""
    accounts: List[Dict] = []
    tf_name = ft.TextField(hint_text="Account name (e.g. Hand, Bank)")
    list_view = ft.Column()

    def add_name(_):
        if tf_name.value.strip():
            accounts.append({"id": str(uuid.uuid4()), "name": tf_name.value.strip(), "balance": 0.0})
            list_view.controls.append(ft.Text(f"• {tf_name.value.strip()}"))
            tf_name.value = ""; page.update()

    def next_step(_):
        if not accounts:
            page.snack_bar = ft.SnackBar(ft.Text("Add at least one account")); page.snack_bar.open = True; page.update(); return
        balance_fields = [ft.TextField(label=f"Opening balance for {a['name']}", keyboard_type=ft.KeyboardType.NUMBER) for a in accounts]

        def finish(__):
            for acc, tf in zip(accounts, balance_fields):
                try: acc["balance"] = float(tf.value or "0")
                except ValueError: acc["balance"] = 0.0
            state["accounts"] = accounts; save_state(page, state); page.go("/home")

        page.views.append(ft.View("/balances", [ft.Column(balance_fields + [ft.ElevatedButton("Finish", on_click=finish)])])); page.update()

    page.views.append(
        ft.View(
            route="/setup",
            controls=[
                ft.Text("Welcome! Add your accounts", size=20),
                tf_name,
                ft.Row([ft.IconButton(ft.Icons.ADD, on_click=add_name), ft.ElevatedButton("Next", on_click=next_step)]),
                ft.Divider(),
                list_view,
            ],
        )
    )

###############################################################################
# ── Main application ────────────────────────────────────────────────────────#
###############################################################################

def main(page: ft.Page):
    page.title = "Expense Tracker"

    # theme toggle --------------------------------------------------------
    def toggle_theme(_):
        page.theme_mode = ft.ThemeMode.DARK if page.theme_mode == ft.ThemeMode.LIGHT else ft.ThemeMode.LIGHT; page.update()

    state = load_state(page)

    def persist(): save_state(page, state)

    # ---------- dialogs & helpers shared across views --------------------
    def refresh(): route_change(page.route)
    def refresh_home(): page.go("/home")  # used by Account controls

    # ---------- Home view -----------------------------------------------
    def home_controls():
        # categories as DragTargets (revealed all the time for simplicity)
        cat_wrap = ft.Row(spacing=10)
        for cat in state["categories"]:
            cat_target = ft.DragTarget(
                data=cat,
                content=ft.Container(
                    content=ft.Text(f"{cat['icon']}{cat['name']}", size=14),
                    padding=10,
                    border_radius=10,
                    bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.GREEN),
                ),
                on_will_accept=lambda _: True,
                on_accept=lambda e, cid=cat["id"]: expense_dialog(e.data, cid),
            )
            cat_wrap.controls.append(cat_target)

        acc_wrap = ft.Row(spacing=10)
        for acc in state["accounts"]:
            acc_wrap.controls.append(Account(acc, refresh_home))

        return [
            ft.Text("Accounts", weight=ft.FontWeight.BOLD),
            acc_wrap,
            ft.Divider(),
            ft.Text("Drag an account onto a category to add an expense", size=12, italic=True),
            cat_wrap,
        ]

    # ---------- Expense dialog (after drag) -----------------------------
    def expense_dialog(account_data: Dict, category_id: str):
        acc = next(a for a in state["accounts"] if a["id"] == account_data["id"])
        cat = next(c for c in state["categories"] if c["id"] == category_id)
        tf_amt = ft.TextField(label="Amount", keyboard_type=ft.KeyboardType.NUMBER)
        tf_desc = ft.TextField(label="Description (optional)")

        def _submit(_):
            try: amt = float(tf_amt.value or "0")
            except ValueError: amt = 0.0
            if amt <= 0: return
            acc["balance"] -= amt
            state["transactions"].append({
                "id": str(uuid.uuid4()), "account_id": acc["id"], "category_id": cat["id"],
                "amount": amt, "desc": tf_desc.value, "ts": datetime.now().isoformat(),
            })
            persist(); refresh(); dlg.open = False; dlg.update()

        dlg = ft.AlertDialog(modal=True, title=ft.Text(f"Expense → {acc['name']} · {cat['name']}"),
                             content=ft.Column([tf_amt, tf_desc]), actions=[ft.ElevatedButton("Add", on_click=_submit)])
        page.dialog = dlg; dlg.open = True; dlg.update()

    # ---------- Report view ---------------------------------------------
    def report_controls():
        totals: Dict[str, float] = {}
        for tr in state["transactions"]: totals[tr["category_id"]] = totals.get(tr["category_id"], 0) + tr["amount"]
        if not totals: return [ft.Text("No data yet…", italic=True)]
        sections = [ft.PieChartSection(value=v, title=next(c["name"] for c in state["categories"] if c["id"] == k)) for k, v in totals.items()]
        pie = ft.PieChart(sections=sections, sections_space=2, center_space_radius=40)
        return [pie, ft.Text(f"Total expenses: Rs. {sum(totals.values()):.2f}")]

    # ---------- Options view --------------------------------------------
    def options_controls():
        # list + delete accounts ----------------------------------------
        def del_acc(acc_id):
            state["accounts"] = [a for a in state["accounts"] if a["id"] != acc_id]; persist(); refresh()

        acc_rows = [ft.Row([ft.Text(f"{a['name']} — Rs. {a['balance']:.2f}"), ft.IconButton(ft.Icons.DELETE, on_click=lambda e, aid=a['id']: del_acc(aid))]) for a in state["accounts"]]

        def add_acc_dialog(_):
            tf_name = ft.TextField(label="Account name")
            tf_bal = ft.TextField(label="Opening balance", keyboard_type=ft.KeyboardType.NUMBER)
            def _submit(__):
                try: bal = float(tf_bal.value or "0")
                except ValueError: bal = 0.0
                state["accounts"].append({"id": str(uuid.uuid4()), "name": tf_name.value, "balance": bal}); persist(); dlg.open = False; dlg.update(); refresh()
            dlg = ft.AlertDialog(modal=True, content=ft.Column([tf_name, tf_bal]), actions=[ft.ElevatedButton("Add", on_click=_submit)])
            page.dialog = dlg; dlg.open = True; dlg.update()

        theme_toggle = ft.Row([ft.Text("Dark mode"), ft.Switch(value=page.theme_mode == ft.ThemeMode.DARK, on_change=toggle_theme)])
        cats_col = ft.Column([ft.Text("Categories", weight=ft.FontWeight.BOLD)] + [ft.Text(f"{c['icon']}  {c['name']}") for c in state["categories"]])
        return [ft.Text("Accounts", weight=ft.FontWeight.BOLD), *acc_rows, ft.ElevatedButton("Add account", on_click=add_acc_dialog), ft.Divider(), cats_col, ft.Divider(), theme_toggle]

    # ---------- Router / nav --------------------------------------------
    def route_change(route):
        page.views.clear()
        if route == "/setup": setup_wizard(page, state); return
        if not state["accounts"]: page.go("/setup"); return

        index = {"/home": 0, "/report": 1, "/options": 2}.get(route, 0)
        def on_nav_change(e): page.go({0:"/home", 1:"/report", 2:"/options"}[e.control.selected_index])
        nav = ft.NavigationBar(selected_index=index, on_change=on_nav_change, destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.LIST, label="Records"),
            ft.NavigationBarDestination(icon=ft.Icons.PIE_CHART, label="Report"),
            ft.NavigationBarDestination(icon=ft.Icons.MENU, label="Options"),
        ])
        body_builders = [home_controls, report_controls, options_controls]
        body = ft.Column(body_builders[index](), expand=True, scroll=ft.ScrollMode.AUTO)
        page.views.append(ft.View(route, [body, nav]))

    page.on_route_change = route_change
    page.go("/home" if state["accounts"] else "/setup")

###############################################################################
# ── Bootstrap ───────────────────────────────────────────────────────────────#
###############################################################################

if __name__ == "__main__":
    ft.app(target=main)
