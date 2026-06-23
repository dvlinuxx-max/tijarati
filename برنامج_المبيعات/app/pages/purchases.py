# -*- coding: utf-8 -*-
"""المشتريات: تسجيل فواتير الشراء من الموردين (تزيد المخزون) + سجل المشتريات."""
import customtkinter as ctk

from ..config import COLORS, ar, money
from ..widgets import (F, label, primary_button, ghost_button, entry,
                       make_treeview, fill_tree, Card)
from .base import BasePage


class PurchasesPage(BasePage):
    title = "المشتريات"
    subtitle = "تسجيل المشتريات من الموردين وزيادة المخزون"
    icon = "📥"

    def build(self, parent):
        self.cur = self.db.get_setting("currency", "د.ع")
        parent.grid_rowconfigure(1, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        bar = ctk.CTkFrame(parent, fg_color="transparent")
        bar.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        primary_button(bar, "＋ فاتورة شراء جديدة", self._new_purchase,
                       color="green", width=200).pack(side="left", padx=4)
        self.summary = label(bar, "", 12, color=COLORS["text_2"])
        self.summary.pack(side="right", padx=14)

        cols = ("total", "items", "supplier", "date", "no")
        frame, self.tree = make_treeview(
            parent, cols, ["الإجمالي", "الأصناف", "المورّد", "التاريخ", "رقم الفاتورة"],
            widths={"total": 130, "items": 90, "supplier": 200, "date": 150, "no": 120})
        frame.grid(row=1, column=0, sticky="nsew")
        self._row_ids = []

    def refresh(self):
        self.cur = self.db.get_setting("currency", "د.ع")
        rows = self.db.q(
            "SELECT p.*, s.name sup, "
            "(SELECT COUNT(*) FROM purchase_items WHERE purchase_id=p.id) n "
            "FROM purchases p LEFT JOIN suppliers s ON s.id=p.supplier_id "
            "ORDER BY p.id DESC LIMIT 300")
        self._row_ids = [r["id"] for r in rows]
        data = []
        total = 0
        for r in rows:
            total += r["total"]
            data.append([money(r["total"], self.cur), str(r["n"]),
                         r["sup"] or "—", r["date"], r["purchase_no"]])
        fill_tree(self.tree, data)
        self.summary.configure(text=ar(
            f"عدد فواتير الشراء: {len(rows)}   |   الإجمالي: {money(total, self.cur)}"))

    def _new_purchase(self):
        PurchaseDialog(self.app, self.db, self.user, on_done=self.refresh)


class PurchaseDialog(ctk.CTkToplevel):
    """نافذة تسجيل فاتورة شراء: اختيار المورّد + إضافة أصناف بكمية وتكلفة."""
    def __init__(self, app, db, user, on_done):
        super().__init__(app)
        self.db = db
        self.user = user
        self.on_done = on_done
        self.cur = db.get_setting("currency", "د.ع")
        self.items = []   # dict(product_id, name, qty, cost)

        self.title(ar("فاتورة شراء جديدة"))
        self.geometry("760x640")
        self.configure(fg_color=COLORS["bg_deep"])
        self.attributes("-topmost", True)
        self.after(200, lambda: self.attributes("-topmost", False))
        self.grab_set()
        self._build()

    def _build(self):
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=20, pady=(18, 6))
        label(head, "📥 فاتورة شراء", 18, bold=True).pack(side="right")

        # المورّد
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=20, pady=4)
        label(top, "المورّد:", 12, color=COLORS["text_2"]).pack(side="right", padx=(0, 8))
        self.suppliers = self.db.q("SELECT id,name FROM suppliers ORDER BY name")
        self.sup_menu = ctk.CTkOptionMenu(
            top, values=[ar(s["name"]) for s in self.suppliers] or [ar("—")],
            font=F(12), fg_color=COLORS["bg_panel"], button_color=COLORS["accent_dim"],
            text_color=COLORS["text_1"], corner_radius=8, width=220)
        self.sup_menu.pack(side="right")

        # إضافة صنف
        add = Card(self)
        add.pack(fill="x", padx=20, pady=10)
        inner = ctk.CTkFrame(add, fg_color="transparent")
        inner.pack(fill="x", padx=12, pady=12)
        label(inner, "المنتج:", 11, color=COLORS["text_2"]).pack(side="right", padx=(0, 6))
        self.products = self.db.q("SELECT id,name,cost FROM products WHERE active=1 ORDER BY name")
        self.prod_menu = ctk.CTkOptionMenu(
            inner, values=[ar(p["name"]) for p in self.products] or [ar("—")],
            font=F(11), fg_color=COLORS["bg_panel"], button_color=COLORS["accent_dim"],
            text_color=COLORS["text_1"], corner_radius=8, width=200,
            command=self._on_pick)
        self.prod_menu.pack(side="right", padx=4)
        label(inner, "كمية:", 11, color=COLORS["text_2"]).pack(side="right", padx=(8, 4))
        self.qty_e = entry(inner, "1", width=70, height=34)
        self.qty_e.pack(side="right")
        label(inner, "تكلفة:", 11, color=COLORS["text_2"]).pack(side="right", padx=(8, 4))
        self.cost_e = entry(inner, "0", width=90, height=34)
        self.cost_e.pack(side="right")
        primary_button(inner, "＋ إضافة", self._add_item, width=100, height=34).pack(side="left")
        self._on_pick()

        # جدول الأصناف
        cols = ("total", "cost", "qty", "name")
        frame, self.tree = make_treeview(
            self, cols, ["الإجمالي", "التكلفة", "الكمية", "المنتج"],
            widths={"total": 110, "cost": 100, "qty": 80, "name": 220})
        frame.pack(fill="both", expand=True, padx=20, pady=6)
        self.tree.bind("<Delete>", lambda e: self._remove())
        ghost_button(self, "حذف الصنف المحدد", self._remove, width=160, height=32).pack(
            anchor="e", padx=20)

        # الحساب
        bottom = ctk.CTkFrame(self, fg_color=COLORS["bg_panel"], corner_radius=12)
        bottom.pack(fill="x", padx=20, pady=10)
        row = ctk.CTkFrame(bottom, fg_color="transparent")
        row.pack(fill="x", padx=14, pady=10)
        label(row, "المدفوع:", 12, color=COLORS["text_2"]).pack(side="right", padx=(0, 4))
        self.paid_e = entry(row, "0", width=120, height=34)
        self.paid_e.pack(side="right", padx=(0, 14))
        self.total_lbl = label(row, money(0, self.cur), 18, bold=True, color=COLORS["green"])
        self.total_lbl.pack(side="left")
        label(row, "الإجمالي:", 14, bold=True).pack(side="left", padx=8)

        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=20, pady=(0, 16))
        primary_button(bar, "💾 حفظ فاتورة الشراء", self._save, color="green", width=200).pack(side="right")
        ghost_button(bar, "إلغاء", self.destroy, width=120).pack(side="right", padx=6)

    def _on_pick(self, _=None):
        name = self.prod_menu.get()
        for p in self.products:
            if ar(p["name"]) == name:
                self.cost_e.delete(0, "end")
                self.cost_e.insert(0, money(p["cost"]))
                break

    def _add_item(self):
        name = self.prod_menu.get()
        prod = next((p for p in self.products if ar(p["name"]) == name), None)
        if not prod:
            return
        try:
            qty = float(self.qty_e.get() or 0)
            cost = float((self.cost_e.get() or "0").replace(",", ""))
        except ValueError:
            return
        if qty <= 0:
            return
        self.items.append({"product_id": prod["id"], "name": prod["name"],
                           "qty": qty, "cost": cost})
        self._refresh()

    def _refresh(self):
        data = [[money(it["qty"] * it["cost"]), money(it["cost"]),
                 money(it["qty"]), it["name"]] for it in self.items]
        fill_tree(self.tree, data)
        total = sum(it["qty"] * it["cost"] for it in self.items)
        self.total_lbl.configure(text=ar(money(total, self.cur)))

    def _remove(self):
        sel = self.tree.selection()
        if sel:
            idx = self.tree.index(sel[0])
            if 0 <= idx < len(self.items):
                del self.items[idx]
                self._refresh()

    def _save(self):
        if not self.items:
            return
        sup_name = self.sup_menu.get()
        sup = next((s for s in self.suppliers if ar(s["name"]) == sup_name), None)
        sup_id = sup["id"] if sup else None
        try:
            paid = float((self.paid_e.get() or "0").replace(",", ""))
        except ValueError:
            paid = 0
        self.db.create_purchase(sup_id, self.user["id"], self.items, paid=paid)
        self.on_done()
        self.destroy()
