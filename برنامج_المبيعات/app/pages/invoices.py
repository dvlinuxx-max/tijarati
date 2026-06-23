# -*- coding: utf-8 -*-
"""سجل الفواتير: عرض، بحث، فتح، وطباعة الفواتير السابقة."""
import customtkinter as ctk

from ..config import COLORS, ar, money
from ..widgets import F, label, primary_button, ghost_button, entry, make_treeview, fill_tree, Card
from .base import BasePage
from .invoice_print import show_invoice


class InvoicesPage(BasePage):
    title = "الفواتير"
    subtitle = "سجل فواتير المبيعات"
    icon = "🧾"

    def build(self, parent):
        self.cur = self.db.get_setting("currency", "د.ع")
        parent.grid_rowconfigure(1, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        # شريط أدوات
        bar = ctk.CTkFrame(parent, fg_color="transparent")
        bar.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.search = entry(bar, "🔍 ابحث برقم الفاتورة أو اسم العميل", width=320)
        self.search.pack(side="right")
        self.search.bind("<KeyRelease>", lambda e: self.refresh())
        primary_button(bar, "🖨 فتح / طباعة", self._open_selected, width=150).pack(side="left", padx=4)

        # ملخص
        self.summary = label(bar, "", 12, color=COLORS["text_2"])
        self.summary.pack(side="left", padx=14)

        cols = ("status", "payment", "total", "customer", "date", "no")
        frame, self.tree = make_treeview(
            parent, cols,
            ["الحالة", "الدفع", "الإجمالي", "العميل", "التاريخ", "رقم الفاتورة"],
            widths={"status": 90, "payment": 90, "total": 120, "customer": 160,
                    "date": 150, "no": 110})
        frame.grid(row=1, column=0, sticky="nsew")
        self.tree.bind("<Double-1>", lambda e: self._open_selected())
        self._row_ids = []

    def refresh(self):
        self.cur = self.db.get_setting("currency", "د.ع")
        term = self.search.get().strip() if hasattr(self, "search") else ""
        sql = ("SELECT i.*, c.name cust FROM invoices i "
               "LEFT JOIN customers c ON c.id=i.customer_id ")
        params = []
        if term:
            sql += "WHERE i.invoice_no LIKE ? OR c.name LIKE ? "
            params = [f"%{term}%", f"%{term}%"]
        sql += "ORDER BY i.id DESC LIMIT 500"
        rows = self.db.q(sql, params)
        self._row_ids = [r["id"] for r in rows]

        data = []
        total_sum = 0
        for r in rows:
            total_sum += r["total"]
            tag = "even"
            if r["status"] == "آجلة":
                tag = "warn"
            data.append(([r["status"], r["payment_method"], money(r["total"], self.cur),
                          r["cust"] or "—", r["date"], r["invoice_no"]], tag))
        fill_tree(self.tree, data)
        self.summary.configure(text=ar(
            f"عدد الفواتير: {len(rows)}   |   الإجمالي: {money(total_sum, self.cur)}"))

    def _open_selected(self):
        sel = self.tree.selection()
        if not sel:
            self.toast("اختر فاتورة أولاً", "info")
            return
        idx = self.tree.index(sel[0])
        if 0 <= idx < len(self._row_ids):
            show_invoice(self.app, self.db, self._row_ids[idx])
