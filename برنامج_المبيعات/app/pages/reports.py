# -*- coding: utf-8 -*-
"""التقارير: ملخص المبيعات والأرباح حسب الفترة + أفضل المنتجات + تصدير CSV."""
import csv
import os
from datetime import datetime, timedelta
import customtkinter as ctk
from tkinter import filedialog

from ..config import COLORS, ar, money
from ..widgets import (F, label, primary_button, ghost_button,
                       make_treeview, fill_tree, Card, StatCard)
from .base import BasePage


class ReportsPage(BasePage):
    title = "التقارير"
    subtitle = "تحليل المبيعات والأرباح حسب الفترة"
    icon = "📈"

    def build(self, parent):
        self.cur = self.db.get_setting("currency", "د.ع")
        parent.grid_rowconfigure(2, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        # اختيار الفترة
        bar = ctk.CTkFrame(parent, fg_color="transparent")
        bar.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        label(bar, "الفترة:", 13, color=COLORS["text_2"]).pack(side="right", padx=(0, 8))
        self.period = ctk.CTkSegmentedButton(
            bar, values=[ar("اليوم"), ar("7 أيام"), ar("هذا الشهر"), ar("الكل")],
            font=F(12), command=lambda v: self.refresh(),
            fg_color=COLORS["bg_card"], selected_color=COLORS["accent"],
            selected_hover_color=COLORS["accent_h"], unselected_color=COLORS["bg_panel"])
        self.period.set(ar("هذا الشهر"))
        self.period.pack(side="right")
        primary_button(bar, "⬇ تصدير CSV", self._export, width=140).pack(side="left")

        # بطاقات ملخص
        cards = ctk.CTkFrame(parent, fg_color="transparent")
        cards.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        for i in range(4):
            cards.grid_columnconfigure(i, weight=1, uniform="r")
        self.c_sales = StatCard(cards, "إجمالي المبيعات", "0", "💰", "green")
        self.c_profit = StatCard(cards, "صافي الأرباح", "0", "🪙", "accent2")
        self.c_count = StatCard(cards, "عدد الفواتير", "0", "🧾", "accent")
        self.c_exp = StatCard(cards, "المصروفات", "0", "📉", "amber")
        for i, c in enumerate([self.c_sales, self.c_profit, self.c_count, self.c_exp]):
            c.grid(row=0, column=i, sticky="ew", padx=8)

        # جدول أفضل المنتجات
        wrap = Card(parent)
        wrap.grid(row=2, column=0, sticky="nsew")
        wrap.grid_rowconfigure(1, weight=1)
        wrap.grid_columnconfigure(0, weight=1)
        label(wrap, "المنتجات الأكثر مبيعاً في الفترة 🏆", 15, bold=True).grid(
            row=0, column=0, sticky="e", padx=16, pady=(14, 6))
        cols = ("revenue", "qty", "name", "rank")
        frame, self.tree = make_treeview(
            wrap, cols, ["الإيراد", "الكمية المباعة", "المنتج", "#"],
            widths={"revenue": 150, "qty": 130, "name": 260, "rank": 50})
        frame.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))

    # ------------------------------------------------------------------
    def _range(self):
        v = self.period.get()
        today = datetime.now()
        if v == ar("اليوم"):
            return today.strftime("%Y-%m-%d 00:00"), "اليوم"
        if v == ar("7 أيام"):
            return (today - timedelta(days=7)).strftime("%Y-%m-%d 00:00"), "آخر 7 أيام"
        if v == ar("هذا الشهر"):
            return today.strftime("%Y-%m-01 00:00"), "هذا الشهر"
        return "0000-00-00", "كل الفترات"

    def refresh(self):
        self.cur = self.db.get_setting("currency", "د.ع")
        start, _ = self._range()

        sales = self.db.one(
            "SELECT COALESCE(SUM(total),0) s, COUNT(*) c FROM invoices WHERE date>=?",
            (start,))
        profit = self.db.one(
            "SELECT COALESCE(SUM((ii.price-ii.cost)*ii.qty),0) p "
            "FROM invoice_items ii JOIN invoices i ON i.id=ii.invoice_id WHERE i.date>=?",
            (start,))
        exp = self.db.one(
            "SELECT COALESCE(SUM(amount),0) s FROM expenses WHERE date>=?",
            (start[:10],))

        self.c_sales.set_value(money(sales["s"], self.cur))
        self.c_profit.set_value(money(profit["p"], self.cur))
        self.c_count.set_value(str(sales["c"]))
        self.c_exp.set_value(money(exp["s"], self.cur))

        top = self.db.q(
            "SELECT ii.name, SUM(ii.qty) q, SUM(ii.total) t "
            "FROM invoice_items ii JOIN invoices i ON i.id=ii.invoice_id "
            "WHERE i.date>=? GROUP BY ii.name ORDER BY t DESC LIMIT 30", (start,))
        data = []
        for i, r in enumerate(top, 1):
            data.append([money(r["t"], self.cur), money(r["q"]), r["name"], str(i)])
        fill_tree(self.tree, data)
        self._last_top = top

    def _export(self):
        start, label_txt = self._range()
        rows = self.db.q(
            "SELECT i.invoice_no, i.date, c.name cust, i.subtotal, i.discount, "
            "i.total, i.paid, i.payment_method, i.status "
            "FROM invoices i LEFT JOIN customers c ON c.id=i.customer_id "
            "WHERE i.date>=? ORDER BY i.id DESC", (start,))
        if not rows:
            self.toast("لا توجد بيانات للتصدير في هذه الفترة", "info")
            return
        default = f"تقرير_المبيعات_{datetime.now().strftime('%Y%m%d')}.csv"
        path = filedialog.asksaveasfilename(
            defaultextension=".csv", initialfile=default,
            filetypes=[("CSV", "*.csv")])
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["رقم الفاتورة", "التاريخ", "العميل", "المجموع الفرعي",
                        "الخصم", "الإجمالي", "المدفوع", "طريقة الدفع", "الحالة"])
            for r in rows:
                w.writerow([r["invoice_no"], r["date"], r["cust"] or "",
                            r["subtotal"], r["discount"], r["total"], r["paid"],
                            r["payment_method"], r["status"]])
        self.toast("تم تصدير التقرير بنجاح ✓")
        try:
            os.startfile(path)
        except Exception:
            pass
