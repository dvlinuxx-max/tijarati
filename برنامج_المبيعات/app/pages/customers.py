# -*- coding: utf-8 -*-
"""إدارة العملاء: إضافة، تعديل، حذف، وتسديد الديون."""
import customtkinter as ctk
from tkinter import messagebox

from ..config import COLORS, ar, money
from ..widgets import F, label, primary_button, ghost_button, entry, make_treeview, fill_tree
from .base import BasePage
from .form_dialog import FormDialog


class CustomersPage(BasePage):
    title = "العملاء"
    subtitle = "سجل العملاء والديون"
    icon = "👥"
    table = "customers"
    person = "العميل"

    def build(self, parent):
        self.cur = self.db.get_setting("currency", "د.ع")
        parent.grid_rowconfigure(1, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        bar = ctk.CTkFrame(parent, fg_color="transparent")
        bar.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.search = entry(bar, f"🔍 ابحث عن {self.person} بالاسم أو الهاتف", width=320)
        self.search.pack(side="right")
        self.search.bind("<KeyRelease>", lambda e: self.refresh())

        primary_button(bar, f"＋ {self.person} جديد", self._add, color="green", width=160).pack(side="left", padx=4)
        ghost_button(bar, "✎ تعديل", self._edit, width=100).pack(side="left", padx=4)
        ghost_button(bar, "💵 تسديد دين", self._settle, width=120).pack(side="left", padx=4)
        ghost_button(bar, "🗑 حذف", self._delete, width=90).pack(side="left", padx=4)
        self.summary = label(bar, "", 12, color=COLORS["text_2"])
        self.summary.pack(side="left", padx=14)

        cols = ("balance", "address", "phone", "name")
        frame, self.tree = make_treeview(
            parent, cols, [self._balance_label(), "العنوان", "الهاتف", "الاسم"],
            widths={"balance": 140, "address": 220, "phone": 150, "name": 220})
        frame.grid(row=1, column=0, sticky="nsew")
        self.tree.bind("<Double-1>", lambda e: self._edit())
        self._row_ids = []

    def _balance_label(self):
        return "الدين (له علينا)" if self.table == "suppliers" else "الدين (عليه)"

    def refresh(self):
        self.cur = self.db.get_setting("currency", "د.ع")
        term = self.search.get().strip() if hasattr(self, "search") else ""
        sql = f"SELECT * FROM {self.table} "
        params = []
        if term:
            sql += "WHERE name LIKE ? OR phone LIKE ? "
            params = [f"%{term}%", f"%{term}%"]
        sql += "ORDER BY name"
        rows = self.db.q(sql, params)
        self._row_ids = [r["id"] for r in rows]

        data = []
        total_debt = 0
        for r in rows:
            total_debt += r["balance"]
            tag = "warn" if r["balance"] > 0 else "even"
            bal = money(r["balance"], self.cur) if r["balance"] else "—"
            data.append(([bal, r["address"] or "—", r["phone"] or "—", r["name"]], tag))
        fill_tree(self.tree, data)
        self.summary.configure(text=ar(
            f"العدد: {len(rows)}   |   إجمالي الديون: {money(total_debt, self.cur)}"))

    def _selected_id(self):
        sel = self.tree.selection()
        if not sel:
            return None
        idx = self.tree.index(sel[0])
        return self._row_ids[idx] if 0 <= idx < len(self._row_ids) else None

    def _fields(self):
        return [
            ("name", "الاسم", "text"),
            ("phone", "رقم الهاتف", "text"),
            ("address", "العنوان", "text"),
            ("balance", "الرصيد/الدين الافتتاحي", "number"),
            ("notes", "ملاحظات", "multiline"),
        ]

    def _add(self):
        def save(d):
            if not d["name"]:
                return "الاسم مطلوب"
            self.db.run(
                f"INSERT INTO {self.table}(name,phone,address,balance,notes) "
                "VALUES(?,?,?,?,?)",
                (d["name"], d["phone"], d["address"], d["balance"], d["notes"]))
            self.refresh()
            self.toast("تمت الإضافة ✓")
        FormDialog(self.app, f"{self.person} جديد", self._fields(), save)

    def _edit(self):
        rid = self._selected_id()
        if rid is None:
            self.toast(f"اختر {self.person} أولاً", "info")
            return
        r = self.db.one(f"SELECT * FROM {self.table} WHERE id=?", (rid,))
        initial = {"name": r["name"], "phone": r["phone"], "address": r["address"],
                   "balance": money(r["balance"]), "notes": r["notes"]}

        def save(d):
            if not d["name"]:
                return "الاسم مطلوب"
            self.db.run(
                f"UPDATE {self.table} SET name=?,phone=?,address=?,balance=?,notes=? WHERE id=?",
                (d["name"], d["phone"], d["address"], d["balance"], d["notes"], rid))
            self.refresh()
            self.toast("تم التحديث ✓")
        FormDialog(self.app, f"تعديل {self.person}", self._fields(), save, initial=initial)

    def _settle(self):
        rid = self._selected_id()
        if rid is None:
            self.toast(f"اختر {self.person} أولاً", "info")
            return
        r = self.db.one(f"SELECT * FROM {self.table} WHERE id=?", (rid,))
        if r["balance"] <= 0:
            self.toast("لا يوجد دين على هذا الحساب", "info")
            return
        dlg = ctk.CTkInputDialog(
            text=ar(f"الدين الحالي: {money(r['balance'], self.cur)}\nأدخل المبلغ المُسدّد:"),
            title=ar("تسديد دين"))
        val = dlg.get_input()
        if val is None:
            return
        try:
            amount = float(val.replace(",", ""))
        except ValueError:
            return
        new_bal = max(0, r["balance"] - amount)
        self.db.run(f"UPDATE {self.table} SET balance=? WHERE id=?", (new_bal, rid))
        self.refresh()
        self.toast(f"تم تسديد {money(amount, self.cur)} ✓")

    def _delete(self):
        rid = self._selected_id()
        if rid is None:
            self.toast(f"اختر {self.person} أولاً", "info")
            return
        r = self.db.one(f"SELECT name FROM {self.table} WHERE id=?", (rid,))
        if messagebox.askyesno(ar("تأكيد الحذف"), ar(f"حذف «{r['name']}»؟")):
            self.db.run(f"DELETE FROM {self.table} WHERE id=?", (rid,))
            self.refresh()
            self.toast("تم الحذف")
