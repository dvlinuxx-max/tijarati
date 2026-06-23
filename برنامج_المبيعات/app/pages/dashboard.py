# -*- coding: utf-8 -*-
"""لوحة التحكم: إحصائيات سريعة + رسم بياني للمبيعات + أفضل المنتجات + تنبيهات المخزون."""
import tkinter as tk
import customtkinter as ctk

from ..config import COLORS, FONT_AR, ar, money
from ..widgets import F, label, Card, StatCard
from .base import BasePage


class DashboardPage(BasePage):
    title = "لوحة التحكم"
    subtitle = "نظرة عامة على أداء نشاطك التجاري"
    icon = "📊"

    def build(self, parent):
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(2, weight=1)
        self.cur = self.db.get_setting("currency", "د.ع")

        # صف بطاقات الإحصائيات
        cards = ctk.CTkFrame(parent, fg_color="transparent")
        cards.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        for i in range(4):
            cards.grid_columnconfigure(i, weight=1, uniform="c")

        self.card_sales = StatCard(cards, "مبيعات اليوم", "0", "💰", "green")
        self.card_month = StatCard(cards, "مبيعات الشهر", "0", "📈", "accent")
        self.card_profit = StatCard(cards, "أرباح الشهر", "0", "🪙", "accent2")
        self.card_debts = StatCard(cards, "ديون العملاء", "0", "🧾", "amber")
        for i, c in enumerate([self.card_sales, self.card_month, self.card_profit, self.card_debts]):
            c.grid(row=0, column=i, sticky="ew", padx=8)

        # صف بطاقات ثانوية
        cards2 = ctk.CTkFrame(parent, fg_color="transparent")
        cards2.grid(row=1, column=0, sticky="ew", pady=(0, 16))
        for i in range(4):
            cards2.grid_columnconfigure(i, weight=1, uniform="c")
        self.card_inv = StatCard(cards2, "فواتير اليوم", "0", "🧾", "accent")
        self.card_prod = StatCard(cards2, "عدد المنتجات", "0", "📦", "accent")
        self.card_cust = StatCard(cards2, "عدد العملاء", "0", "👥", "accent")
        self.card_low = StatCard(cards2, "مخزون منخفض", "0", "⚠️", "red")
        for i, c in enumerate([self.card_inv, self.card_prod, self.card_cust, self.card_low]):
            c.grid(row=0, column=i, sticky="ew", padx=8)

        # المنطقة السفلى: رسم بياني (يسار) + قوائم (يمين)
        bottom = ctk.CTkFrame(parent, fg_color="transparent")
        bottom.grid(row=2, column=0, sticky="nsew")
        bottom.grid_columnconfigure(0, weight=2)
        bottom.grid_columnconfigure(1, weight=1)
        bottom.grid_rowconfigure(0, weight=1)

        # الرسم البياني
        chart_card = Card(bottom)
        chart_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        chart_card.grid_rowconfigure(1, weight=1)
        chart_card.grid_columnconfigure(0, weight=1)
        label(chart_card, "مبيعات آخر 14 يوم", 15, bold=True).grid(
            row=0, column=0, sticky="e", padx=18, pady=(16, 4))
        self.canvas = tk.Canvas(chart_card, bg=COLORS["bg_card"],
                                highlightthickness=0, bd=0)
        self.canvas.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 14))
        self.canvas.bind("<Configure>", lambda e: self._draw_chart())

        # العمود الأيمن: أفضل المنتجات + تنبيهات المخزون
        side = ctk.CTkFrame(bottom, fg_color="transparent")
        side.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        side.grid_rowconfigure(0, weight=1)
        side.grid_rowconfigure(1, weight=1)
        side.grid_columnconfigure(0, weight=1)

        self.top_card = Card(side)
        self.top_card.grid(row=0, column=0, sticky="nsew", pady=(0, 8))
        label(self.top_card, "الأكثر مبيعاً 🏆", 14, bold=True).pack(anchor="e", padx=16, pady=(14, 6))
        self.top_box = ctk.CTkFrame(self.top_card, fg_color="transparent")
        self.top_box.pack(fill="both", expand=True, padx=12, pady=(0, 10))

        self.low_card = Card(side)
        self.low_card.grid(row=1, column=0, sticky="nsew", pady=(8, 0))
        label(self.low_card, "تنبيهات المخزون ⚠️", 14, bold=True).pack(anchor="e", padx=16, pady=(14, 6))
        self.low_box = ctk.CTkFrame(self.low_card, fg_color="transparent")
        self.low_box.pack(fill="both", expand=True, padx=12, pady=(0, 10))

        self._chart_data = []

    # ------------------------------------------------------------------
    def refresh(self):
        self.cur = self.db.get_setting("currency", "د.ع")
        s = self.db.stats_summary()
        self.card_sales.set_value(money(s["sales_today"], self.cur))
        self.card_month.set_value(money(s["sales_month"], self.cur))
        self.card_profit.set_value(money(s["profit_month"], self.cur))
        self.card_debts.set_value(money(s["debts"], self.cur))
        self.card_inv.set_value(str(s["invoices_today"]))
        self.card_prod.set_value(str(s["products"]))
        self.card_cust.set_value(str(s["customers"]))
        self.card_low.set_value(str(s["low_stock"]),
                                sub="منتجات تحتاج إعادة طلب" if s["low_stock"] else "كل شيء جيد")

        self._chart_data = self.db.sales_last_days(14)
        self._draw_chart()
        self._fill_top()
        self._fill_low()

    def _fill_top(self):
        for w in self.top_box.winfo_children():
            w.destroy()
        rows = self.db.top_products(5)
        if not rows:
            label(self.top_box, "لا توجد مبيعات بعد", 12, color=COLORS["text_3"]).pack(pady=10)
        medals = ["🥇", "🥈", "🥉", "4", "5"]
        for i, r in enumerate(rows):
            row = ctk.CTkFrame(self.top_box, fg_color="transparent")
            row.pack(fill="x", pady=3)
            label(row, money(r["t"], self.cur), 11, color=COLORS["green"]).pack(side="left", padx=6)
            label(row, r["name"], 12).pack(side="right")
            ctk.CTkLabel(row, text=medals[i], font=F(12)).pack(side="right", padx=(0, 6))

    def _fill_low(self):
        for w in self.low_box.winfo_children():
            w.destroy()
        rows = self.db.low_stock_products()
        if not rows:
            label(self.low_box, "لا توجد تنبيهات — المخزون بحالة جيدة ✓", 12,
                  color=COLORS["green"]).pack(pady=10)
            return
        for r in rows[:6]:
            row = ctk.CTkFrame(self.low_box, fg_color="transparent")
            row.pack(fill="x", pady=3)
            label(row, f"{money(r['quantity'])} {r['unit']}", 11,
                  color=COLORS["red"]).pack(side="left", padx=6)
            label(row, r["name"], 12).pack(side="right")
            ctk.CTkLabel(row, text="●", text_color=COLORS["red"],
                         font=F(10)).pack(side="right", padx=(0, 6))

    # ------------------------------------------------------------------
    def _draw_chart(self):
        c = self.canvas
        c.delete("all")
        data = self._chart_data
        if not data:
            return
        w = c.winfo_width()
        h = c.winfo_height()
        if w < 50 or h < 50:
            return
        pad_l, pad_r, pad_t, pad_b = 20, 20, 20, 36
        plot_w = w - pad_l - pad_r
        plot_h = h - pad_t - pad_b
        max_v = max((v for _, v in data), default=0) or 1

        # خطوط شبكية
        for i in range(5):
            y = pad_t + plot_h * i / 4
            c.create_line(pad_l, y, w - pad_r, y, fill=COLORS["border"])

        n = len(data)
        gap = plot_w / n
        bar_w = gap * 0.55
        for i, (lbl, v) in enumerate(data):
            x_center = pad_l + gap * (i + 0.5)
            bar_h = plot_h * (v / max_v)
            x0 = x_center - bar_w / 2
            x1 = x_center + bar_w / 2
            y0 = pad_t + plot_h - bar_h
            y1 = pad_t + plot_h
            self._round_bar(c, x0, y0, x1, y1, COLORS["accent"])
            # تسمية اليوم (كل يومين لتجنب الازدحام)
            if i % 2 == 0 or n <= 8:
                c.create_text(x_center, y1 + 14, text=lbl, fill=COLORS["text_3"],
                              font=(FONT_AR, 8))

    @staticmethod
    def _round_bar(c, x0, y0, x1, y1, color):
        r = min(6, (x1 - x0) / 2)
        if y1 - y0 < r:
            c.create_rectangle(x0, y0, x1, y1, fill=color, outline="")
            return
        c.create_rectangle(x0, y0 + r, x1, y1, fill=color, outline="")
        c.create_arc(x0, y0, x0 + 2 * r, y0 + 2 * r, start=90, extent=90,
                     fill=color, outline="")
        c.create_arc(x1 - 2 * r, y0, x1, y0 + 2 * r, start=0, extent=90,
                     fill=color, outline="")
        c.create_rectangle(x0 + r, y0, x1 - r, y0 + r, fill=color, outline="")
