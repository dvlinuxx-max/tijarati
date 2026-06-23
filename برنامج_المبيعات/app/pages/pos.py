# -*- coding: utf-8 -*-
"""نقطة البيع (POS) — قلب البرنامج: بحث المنتجات، سلة، حساب، وإتمام البيع."""
import customtkinter as ctk

from ..config import COLORS, ar, money
from ..widgets import F, label, Card, primary_button, ghost_button, entry, make_treeview, fill_tree
from .base import BasePage
from .invoice_print import show_invoice


class POSPage(BasePage):
    title = "نقطة البيع"
    subtitle = "أضف المنتجات إلى السلة وأتمم عملية البيع"
    icon = "🛒"

    def build(self, parent):
        self.cart = {}     # product_id -> dict(name, price, qty, cost)
        self.cur = self.db.get_setting("currency", "د.ع")
        self.active_cat = None

        parent.grid_columnconfigure(0, weight=2)   # السلة (يسار)
        parent.grid_columnconfigure(1, weight=3)   # المنتجات (يمين)
        parent.grid_rowconfigure(0, weight=1)

        self._build_products(parent)
        self._build_cart(parent)
        self._load_products()

    # ------------------------------------------------------------------
    # لوحة المنتجات
    # ------------------------------------------------------------------
    def _build_products(self, parent):
        panel = Card(parent)
        panel.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        panel.grid_rowconfigure(2, weight=1)
        panel.grid_columnconfigure(0, weight=1)

        # بحث + باركود
        top = ctk.CTkFrame(panel, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=14, pady=(14, 6))
        self.search = entry(top, "🔍 ابحث بالاسم أو امسح الباركود ثم Enter", width=10)
        self.search.pack(fill="x")
        self.search.bind("<KeyRelease>", self._on_search)
        self.search.bind("<Return>", self._on_barcode)

        # شريط التصنيفات
        self.cat_bar = ctk.CTkScrollableFrame(panel, fg_color="transparent",
                                              orientation="horizontal", height=48)
        self.cat_bar.grid(row=1, column=0, sticky="ew", padx=10)

        # شبكة المنتجات
        self.grid_scroll = ctk.CTkScrollableFrame(panel, fg_color="transparent")
        self.grid_scroll.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)
        for i in range(3):
            self.grid_scroll.grid_columnconfigure(i, weight=1, uniform="p")

    def _load_products(self):
        # التصنيفات
        for w in self.cat_bar.winfo_children():
            w.destroy()
        cats = self.db.q("SELECT * FROM categories ORDER BY name")
        self._cat_btn = {}
        all_btn = ctk.CTkButton(self.cat_bar, text=ar("الكل"), font=F(12),
                                width=80, height=34, corner_radius=16,
                                fg_color=COLORS["accent"] if self.active_cat is None else COLORS["bg_panel"],
                                hover_color=COLORS["accent_h"], text_color="white",
                                command=lambda: self._filter_cat(None))
        all_btn.pack(side="right", padx=4)
        for cat in cats:
            b = ctk.CTkButton(
                self.cat_bar, text=ar(cat["name"]), font=F(12), width=90, height=34,
                corner_radius=16,
                fg_color=COLORS["accent"] if self.active_cat == cat["id"] else COLORS["bg_panel"],
                hover_color=COLORS["accent_h"],
                text_color="white" if self.active_cat == cat["id"] else COLORS["text_2"],
                command=lambda c=cat["id"]: self._filter_cat(c))
            b.pack(side="right", padx=4)
        self._render_products()

    def _filter_cat(self, cat_id):
        self.active_cat = cat_id
        self._load_products()

    def _render_products(self, term=""):
        for w in self.grid_scroll.winfo_children():
            w.destroy()
        sql = "SELECT * FROM products WHERE active=1"
        params = []
        if self.active_cat:
            sql += " AND category_id=?"
            params.append(self.active_cat)
        if term:
            sql += " AND (name LIKE ? OR barcode LIKE ?)"
            params += [f"%{term}%", f"%{term}%"]
        sql += " ORDER BY name"
        products = self.db.q(sql, params)

        if not products:
            label(self.grid_scroll, "لا توجد منتجات مطابقة", 13,
                  color=COLORS["text_3"]).grid(row=0, column=0, columnspan=3, pady=30)
            return

        for idx, p in enumerate(products):
            r, c = divmod(idx, 3)
            self._product_tile(p).grid(row=r, column=c, sticky="nsew", padx=6, pady=6)

    def _product_tile(self, p):
        out = p["quantity"] <= 0
        tile = ctk.CTkButton(
            self.grid_scroll, text="", height=96, corner_radius=12,
            fg_color=COLORS["bg_panel"], hover_color=COLORS["bg_hover"],
            border_width=1, border_color=COLORS["border2"],
            command=(lambda: None) if out else (lambda pid=p["id"]: self._add_to_cart(pid)))
        inner = ctk.CTkFrame(tile, fg_color="transparent")
        inner.place(relx=0.5, rely=0.5, anchor="center")
        name = p["name"] if len(p["name"]) <= 22 else p["name"][:21] + "…"
        label(inner, name, 12, bold=True).pack()
        label(inner, money(p["price"], self.cur), 13, color=COLORS["green"]).pack(pady=(2, 0))
        stock_color = COLORS["red"] if out else (
            COLORS["amber"] if p["quantity"] <= p["reorder_level"] else COLORS["text_3"])
        label(inner, ("نفد المخزون" if out else f"المتوفر: {money(p['quantity'])} {p['unit']}"),
              10, color=stock_color).pack()
        return tile

    def _on_search(self, _e=None):
        self._render_products(self.search.get().strip())

    def _on_barcode(self, _e=None):
        term = self.search.get().strip()
        if not term:
            return
        p = self.db.one("SELECT * FROM products WHERE barcode=? AND active=1", (term,))
        if p:
            self._add_to_cart(p["id"])
            self.search.delete(0, "end")
            self._render_products()
        else:
            self._on_search()

    # ------------------------------------------------------------------
    # السلة
    # ------------------------------------------------------------------
    def _build_cart(self, parent):
        panel = Card(parent)
        panel.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        panel.grid_rowconfigure(2, weight=1)
        panel.grid_columnconfigure(0, weight=1)

        head = ctk.CTkFrame(panel, fg_color="transparent")
        head.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 6))
        label(head, "🧾 الفاتورة الحالية", 16, bold=True).pack(side="right")
        ghost_button(head, "تفريغ 🗑", self._clear_cart, width=90, height=32).pack(side="left")

        # العميل
        cust_f = ctk.CTkFrame(panel, fg_color="transparent")
        cust_f.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 6))
        label(cust_f, "العميل:", 12, color=COLORS["text_2"]).pack(side="right", padx=(0, 8))
        self.customers = self.db.q("SELECT id,name FROM customers ORDER BY name")
        names = [c["name"] for c in self.customers]
        self.customer_menu = ctk.CTkOptionMenu(
            cust_f, values=[ar(n) for n in names] or [ar("عميل نقدي")],
            font=F(12), fg_color=COLORS["bg_panel"], button_color=COLORS["accent_dim"],
            button_hover_color=COLORS["bg_hover"], text_color=COLORS["text_1"],
            dropdown_font=F(12), corner_radius=8, width=180)
        self.customer_menu.pack(side="right")

        # جدول السلة
        cols = ("total", "price", "qty", "name")
        frame, self.tree = make_treeview(
            panel, cols, ["الإجمالي", "السعر", "الكمية", "المنتج"],
            widths={"total": 90, "price": 80, "qty": 70, "name": 160})
        frame.grid(row=2, column=0, sticky="nsew", padx=14, pady=6)
        self.tree.bind("<Double-1>", self._edit_qty)
        self.tree.bind("<Delete>", lambda e: self._remove_selected())

        # أزرار تعديل الكمية + حذف
        qty_bar = ctk.CTkFrame(panel, fg_color="transparent")
        qty_bar.grid(row=3, column=0, sticky="ew", padx=14, pady=(0, 6))
        ghost_button(qty_bar, "－", lambda: self._bump(-1), width=44, height=34).pack(side="right", padx=3)
        ghost_button(qty_bar, "＋", lambda: self._bump(1), width=44, height=34).pack(side="right", padx=3)
        ghost_button(qty_bar, "حذف الصنف", self._remove_selected, width=110, height=34).pack(side="right", padx=3)
        label(qty_bar, "نقرتين لتعديل الكمية", 10, color=COLORS["text_3"]).pack(side="left")

        # الحساب
        totals = ctk.CTkFrame(panel, fg_color=COLORS["bg_panel"], corner_radius=12)
        totals.grid(row=4, column=0, sticky="ew", padx=14, pady=(6, 6))
        totals.grid_columnconfigure(0, weight=1)

        self.lbl_subtotal = self._total_row(totals, "المجموع الفرعي", "0", 0)

        disc_f = ctk.CTkFrame(totals, fg_color="transparent")
        disc_f.grid(row=1, column=0, sticky="ew", padx=14, pady=4)
        label(disc_f, "الخصم:", 12, color=COLORS["text_2"]).pack(side="right")
        self.discount_entry = entry(disc_f, "0", width=110, height=32)
        self.discount_entry.pack(side="left")
        self.discount_entry.bind("<KeyRelease>", lambda e: self._recalc())

        self.lbl_total = self._total_row(totals, "الإجمالي النهائي", "0", 2, big=True)

        pay_f = ctk.CTkFrame(totals, fg_color="transparent")
        pay_f.grid(row=3, column=0, sticky="ew", padx=14, pady=4)
        label(pay_f, "المدفوع:", 12, color=COLORS["text_2"]).pack(side="right")
        self.paid_entry = entry(pay_f, "0", width=110, height=32)
        self.paid_entry.pack(side="left")
        self.paid_entry.bind("<KeyRelease>", lambda e: self._recalc())
        self.method_menu = ctk.CTkOptionMenu(
            pay_f, values=[ar("نقدي"), ar("بطاقة"), ar("آجل")], font=F(12),
            fg_color=COLORS["bg_card"], button_color=COLORS["accent_dim"],
            text_color=COLORS["text_1"], width=90, corner_radius=8,
            command=lambda v: self._recalc())
        self.method_menu.pack(side="right", padx=8)

        self.lbl_change = self._total_row(totals, "الباقي للعميل", "0", 4)

        # زر الدفع
        self.pay_btn = primary_button(panel, "💵  إتمام البيع وطباعة الفاتورة",
                                      self._checkout, color="green", height=52)
        self.pay_btn.grid(row=5, column=0, sticky="ew", padx=14, pady=(4, 14))

        self._recalc()

    def _total_row(self, parent, title, value, row, big=False):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.grid(row=row, column=0, sticky="ew", padx=14, pady=(6 if big else 3))
        size = 18 if big else 13
        color = COLORS["green"] if big else COLORS["text_1"]
        val = label(f, money(value, self.cur), size, bold=big, color=color)
        val.pack(side="left")
        label(f, title, size if big else 12, bold=big,
              color=COLORS["text_1"] if big else COLORS["text_2"]).pack(side="right")
        return val

    # ------------------------------------------------------------------
    # عمليات السلة
    # ------------------------------------------------------------------
    def _add_to_cart(self, pid):
        p = self.db.one("SELECT * FROM products WHERE id=?", (pid,))
        if not p:
            return
        if pid in self.cart:
            if self.cart[pid]["qty"] + 1 > p["quantity"]:
                self.toast("الكمية المطلوبة أكبر من المخزون المتوفر", "error")
                return
            self.cart[pid]["qty"] += 1
        else:
            if p["quantity"] <= 0:
                self.toast("هذا المنتج نفد من المخزون", "error")
                return
            self.cart[pid] = {"name": p["name"], "price": p["price"],
                              "qty": 1, "cost": p["cost"], "max": p["quantity"]}
        self._refresh_cart()

    def _refresh_cart(self):
        rows = []
        for pid, it in self.cart.items():
            rows.append(([money(it["qty"] * it["price"]), money(it["price"]),
                          money(it["qty"]), it["name"]],))
        # احتفظ بترتيب ثابت عبر معرفات السلة
        self._cart_order = list(self.cart.keys())
        fill_tree(self.tree, [r[0] for r in rows])
        self._recalc()

    def _selected_pid(self):
        sel = self.tree.selection()
        if not sel:
            return None
        idx = self.tree.index(sel[0])
        if 0 <= idx < len(self._cart_order):
            return self._cart_order[idx]
        return None

    def _bump(self, delta):
        pid = self._selected_pid()
        if pid is None:
            return
        it = self.cart[pid]
        new_q = it["qty"] + delta
        if new_q <= 0:
            del self.cart[pid]
        elif new_q > it["max"]:
            self.toast("تجاوزت الكمية المتوفرة في المخزون", "error")
            return
        else:
            it["qty"] = new_q
        self._refresh_cart()

    def _edit_qty(self, _e=None):
        pid = self._selected_pid()
        if pid is None:
            return
        dlg = ctk.CTkInputDialog(text=ar("أدخل الكمية الجديدة:"), title=ar("تعديل الكمية"))
        val = dlg.get_input()
        if val is None:
            return
        try:
            q = float(val)
        except ValueError:
            return
        if q <= 0:
            del self.cart[pid]
        elif q > self.cart[pid]["max"]:
            self.toast("الكمية أكبر من المخزون المتوفر", "error")
            return
        else:
            self.cart[pid]["qty"] = q
        self._refresh_cart()

    def _remove_selected(self):
        pid = self._selected_pid()
        if pid is not None:
            del self.cart[pid]
            self._refresh_cart()

    def _clear_cart(self):
        self.cart.clear()
        self._refresh_cart()

    def _recalc(self):
        subtotal = sum(it["qty"] * it["price"] for it in self.cart.values())
        try:
            discount = float(self.discount_entry.get() or 0)
        except ValueError:
            discount = 0
        total = max(0, subtotal - discount)
        try:
            paid = float(self.paid_entry.get() or 0)
        except ValueError:
            paid = 0
        change = paid - total
        self.lbl_subtotal.configure(text=ar(money(subtotal, self.cur)))
        self.lbl_total.configure(text=ar(money(total, self.cur)))
        self.lbl_change.configure(
            text=ar(money(change if change > 0 else 0, self.cur)))
        self._current_total = total

    # ------------------------------------------------------------------
    def _checkout(self):
        if not self.cart:
            self.toast("السلة فارغة — أضف منتجات أولاً", "error")
            return
        self._recalc()
        total = self._current_total
        try:
            discount = float(self.discount_entry.get() or 0)
        except ValueError:
            discount = 0
        try:
            paid = float(self.paid_entry.get() or 0)
        except ValueError:
            paid = 0
        method = self.method_menu.get()
        # في الدفع النقدي اعتبر المبلغ مدفوعاً بالكامل إن لم يُدخل المستخدم رقماً
        if paid == 0 and ar("آجل") not in method:
            paid = total

        cust_idx = self.customer_menu._values.index(self.customer_menu.get()) \
            if self.customer_menu.get() in self.customer_menu._values else 0
        customer_id = self.customers[cust_idx]["id"] if self.customers else None

        items = [{"product_id": pid, "name": it["name"], "qty": it["qty"],
                  "price": it["price"], "cost": it["cost"]}
                 for pid, it in self.cart.items()]

        inv_id, inv_no = self.db.create_sale(
            customer_id, self.user["id"], items, discount=discount,
            paid=paid, payment_method=method.replace("‏", ""))

        self.toast(f"تم إنشاء الفاتورة {inv_no} بنجاح ✓")
        show_invoice(self.app, self.db, inv_id)
        self._clear_cart()
        self.discount_entry.delete(0, "end")
        self.paid_entry.delete(0, "end")
        self._load_products()

    def on_show(self):
        self._load_products()
        # حدّث قائمة العملاء
        self.customers = self.db.q("SELECT id,name FROM customers ORDER BY name")
        self.customer_menu.configure(values=[ar(c["name"]) for c in self.customers])
        self.cur = self.db.get_setting("currency", "د.ع")
