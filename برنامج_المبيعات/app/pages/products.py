# -*- coding: utf-8 -*-
"""إدارة المنتجات والمخزون: إضافة، تعديل، حذف، بحث، وتنبيهات المخزون المنخفض."""
import customtkinter as ctk
from tkinter import messagebox

from ..config import COLORS, ar, money
from ..widgets import F, label, primary_button, ghost_button, entry, make_treeview, fill_tree
from .base import BasePage
from .form_dialog import FormDialog


class ProductsPage(BasePage):
    title = "المنتجات والمخزون"
    subtitle = "إدارة الأصناف والكميات والأسعار"
    icon = "📦"

    def build(self, parent):
        self.cur = self.db.get_setting("currency", "د.ع")
        parent.grid_rowconfigure(1, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        bar = ctk.CTkFrame(parent, fg_color="transparent")
        bar.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.search = entry(bar, "🔍 ابحث عن منتج بالاسم أو الباركود", width=320)
        self.search.pack(side="right")
        self.search.bind("<KeyRelease>", lambda e: self.refresh())

        if self._can_edit():
            primary_button(bar, "＋ منتج جديد", self._add, color="green", width=150).pack(side="left", padx=4)
            ghost_button(bar, "✎ تعديل", self._edit, width=110).pack(side="left", padx=4)
            ghost_button(bar, "🗑 حذف", self._delete, width=100).pack(side="left", padx=4)
        self.summary = label(bar, "", 12, color=COLORS["text_2"])
        self.summary.pack(side="left", padx=14)

        cols = ("status", "price", "cost", "qty", "category", "name", "barcode")
        frame, self.tree = make_treeview(
            parent, cols,
            ["الحالة", "سعر البيع", "التكلفة", "الكمية", "التصنيف", "اسم المنتج", "الباركود"],
            widths={"status": 90, "price": 100, "cost": 100, "qty": 90,
                    "category": 120, "name": 200, "barcode": 130})
        frame.grid(row=1, column=0, sticky="nsew")
        self.tree.bind("<Double-1>", lambda e: self._edit())
        self._row_ids = []

    def _can_edit(self):
        return self.user["role"] in ("admin", "manager")

    # ------------------------------------------------------------------
    def refresh(self):
        self.cur = self.db.get_setting("currency", "د.ع")
        term = self.search.get().strip() if hasattr(self, "search") else ""
        sql = ("SELECT p.*, c.name cat FROM products p "
               "LEFT JOIN categories c ON c.id=p.category_id WHERE p.active=1 ")
        params = []
        if term:
            sql += "AND (p.name LIKE ? OR p.barcode LIKE ?) "
            params = [f"%{term}%", f"%{term}%"]
        sql += "ORDER BY p.name"
        rows = self.db.q(sql, params)
        self._row_ids = [r["id"] for r in rows]

        data = []
        total_value = 0
        low = 0
        for r in rows:
            total_value += r["cost"] * r["quantity"]
            if r["quantity"] <= 0:
                status, tag = "نفد", "danger"
                low += 1
            elif r["quantity"] <= r["reorder_level"]:
                status, tag = "منخفض", "warn"
                low += 1
            else:
                status, tag = "متوفر", "even"
            data.append(([status, money(r["price"], self.cur), money(r["cost"]),
                          f"{money(r['quantity'])} {r['unit']}", r["cat"] or "—",
                          r["name"], r["barcode"] or "—"], tag))
        fill_tree(self.tree, data)
        self.summary.configure(text=ar(
            f"عدد الأصناف: {len(rows)}   |   تنبيهات: {low}   |   "
            f"قيمة المخزون: {money(total_value, self.cur)}"))

    def _selected_id(self):
        sel = self.tree.selection()
        if not sel:
            return None
        idx = self.tree.index(sel[0])
        return self._row_ids[idx] if 0 <= idx < len(self._row_ids) else None

    def _category_names(self):
        return [c["name"] for c in self.db.q("SELECT name FROM categories ORDER BY name")]

    def _fields(self):
        cats = self._category_names()
        return [
            ("name", "اسم المنتج", "text"),
            ("barcode", "الباركود", "text"),
            ("category", "التصنيف", "combo", cats),
            ("cost", "سعر التكلفة", "number"),
            ("price", "سعر البيع", "number"),
            ("quantity", "الكمية المتوفرة", "number"),
            ("reorder_level", "حد التنبيه (إعادة الطلب)", "number"),
            ("unit", "وحدة القياس", "text"),
        ]

    def _add(self):
        def save(d):
            if not d["name"]:
                return "اسم المنتج مطلوب"
            cat_id = self._cat_id(d["category"])
            self.db.run(
                "INSERT INTO products(name,barcode,category_id,cost,price,quantity,"
                "reorder_level,unit) VALUES(?,?,?,?,?,?,?,?)",
                (d["name"], d["barcode"], cat_id, d["cost"], d["price"],
                 d["quantity"], d["reorder_level"] or 5, d["unit"] or "قطعة"))
            self.refresh()
            self.toast("تمت إضافة المنتج ✓")
        FormDialog(self.app, "منتج جديد", self._fields(), save,
                   initial={"unit": "قطعة", "reorder_level": 5})

    def _edit(self):
        if not self._can_edit():
            return
        pid = self._selected_id()
        if pid is None:
            self.toast("اختر منتجاً أولاً", "info")
            return
        p = self.db.one("SELECT p.*, c.name cat FROM products p "
                        "LEFT JOIN categories c ON c.id=p.category_id WHERE p.id=?", (pid,))
        initial = {"name": p["name"], "barcode": p["barcode"], "category": p["cat"] or "",
                   "cost": money(p["cost"]), "price": money(p["price"]),
                   "quantity": money(p["quantity"]),
                   "reorder_level": money(p["reorder_level"]), "unit": p["unit"]}

        def save(d):
            if not d["name"]:
                return "اسم المنتج مطلوب"
            cat_id = self._cat_id(d["category"])
            self.db.run(
                "UPDATE products SET name=?,barcode=?,category_id=?,cost=?,price=?,"
                "quantity=?,reorder_level=?,unit=? WHERE id=?",
                (d["name"], d["barcode"], cat_id, d["cost"], d["price"],
                 d["quantity"], d["reorder_level"], d["unit"], pid))
            self.refresh()
            self.toast("تم تحديث المنتج ✓")
        FormDialog(self.app, "تعديل المنتج", self._fields(), save, initial=initial)

    def _cat_id(self, name):
        if not name:
            return None
        r = self.db.one("SELECT id FROM categories WHERE name=?", (name,))
        if r:
            return r["id"]
        return self.db.run("INSERT INTO categories(name) VALUES(?)", (name,))

    def _delete(self):
        pid = self._selected_id()
        if pid is None:
            self.toast("اختر منتجاً أولاً", "info")
            return
        p = self.db.one("SELECT name FROM products WHERE id=?", (pid,))
        if messagebox.askyesno(ar("تأكيد الحذف"),
                               ar(f"هل تريد حذف المنتج «{p['name']}»؟")):
            self.db.run("UPDATE products SET active=0 WHERE id=?", (pid,))
            self.refresh()
            self.toast("تم حذف المنتج")
