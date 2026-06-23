# -*- coding: utf-8 -*-
"""الإعدادات: تخصيص بيانات الشركة + إدارة المستخدمين + التصنيفات."""
import customtkinter as ctk
from tkinter import messagebox

from ..config import COLORS, ar
from ..widgets import (F, label, primary_button, ghost_button, entry,
                       make_treeview, fill_tree, Card)
from .base import BasePage
from .form_dialog import FormDialog


class SettingsPage(BasePage):
    title = "الإعدادات"
    subtitle = "تخصيص البرنامج لشركتك وإدارة المستخدمين"
    icon = "⚙️"

    def build(self, parent):
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_columnconfigure(1, weight=1)

        self._build_company(parent)
        self._build_users(parent)

    # ------------------------------------------------------------------
    def _build_company(self, parent):
        card = Card(parent)
        card.grid(row=0, column=1, sticky="nsew", padx=(0, 8), pady=0)
        scroll = ctk.CTkScrollableFrame(card, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=8, pady=8)

        label(scroll, "🏢 بيانات الشركة (تظهر على الفواتير)", 16, bold=True).pack(
            anchor="e", pady=(6, 14), padx=8)

        self.fields = {}
        specs = [
            ("company_name", "اسم الشركة / المتجر"),
            ("phone", "رقم الهاتف"),
            ("address", "العنوان"),
            ("currency", "رمز العملة (مثل: د.ع، $، ر.س)"),
            ("tax_rate", "نسبة الضريبة % (0 لتعطيلها)"),
            ("invoice_prefix", "بادئة رقم الفاتورة"),
            ("footer_note", "ملاحظة أسفل الفاتورة"),
        ]
        for key, lbl in specs:
            label(scroll, lbl, 12, color=COLORS["text_2"]).pack(anchor="e", padx=8, pady=(8, 3))
            e = entry(scroll, "", width=10)
            e.insert(0, self.db.get_setting(key, ""))
            e.pack(fill="x", padx=8)
            self.fields[key] = e

        primary_button(scroll, "💾 حفظ بيانات الشركة", self._save_company,
                       color="green", height=46).pack(fill="x", padx=8, pady=18)

    def _save_company(self):
        for key, e in self.fields.items():
            self.db.set_setting(key, e.get().strip())
        self.toast("تم حفظ الإعدادات ✓ — ستظهر على الفواتير الجديدة")
        # حدّث عنوان النافذة
        company = self.db.get_setting("company_name", "")
        from ..config import APP_NAME
        self.app.title(f"{APP_NAME} — {company}")

    # ------------------------------------------------------------------
    def _build_users(self, parent):
        card = Card(parent)
        card.grid(row=0, column=0, sticky="nsew", padx=(8, 0))
        card.grid_rowconfigure(2, weight=1)
        card.grid_columnconfigure(0, weight=1)

        head = ctk.CTkFrame(card, fg_color="transparent")
        head.grid(row=0, column=0, sticky="ew", padx=14, pady=(14, 6))
        label(head, "👤 المستخدمون والصلاحيات", 16, bold=True).pack(side="right")
        primary_button(head, "＋ مستخدم", self._add_user, color="green", width=120).pack(side="left", padx=3)
        ghost_button(head, "🔑 كلمة المرور", self._reset_pass, width=130).pack(side="left", padx=3)
        ghost_button(head, "🗑 حذف", self._del_user, width=90).pack(side="left", padx=3)

        cols = ("role", "username", "name")
        frame, self.tree = make_treeview(
            card, cols, ["الصلاحية", "اسم الدخول", "الاسم الكامل"],
            widths={"role": 110, "username": 140, "name": 200})
        frame.grid(row=2, column=0, sticky="nsew", padx=12, pady=12)
        self._row_ids = []

        # التصنيفات
        cat_card = ctk.CTkFrame(card, fg_color=COLORS["bg_panel"], corner_radius=10)
        cat_card.grid(row=3, column=0, sticky="ew", padx=12, pady=(0, 12))
        crow = ctk.CTkFrame(cat_card, fg_color="transparent")
        crow.pack(fill="x", padx=10, pady=10)
        label(crow, "تصنيفات المنتجات:", 12, color=COLORS["text_2"]).pack(side="right")
        self.cat_entry = entry(crow, "اسم تصنيف جديد", width=180, height=34)
        self.cat_entry.pack(side="right", padx=8)
        primary_button(crow, "＋", self._add_cat, width=44, height=34).pack(side="right")
        self.cat_label = label(cat_card, "", 11, color=COLORS["text_3"])
        self.cat_label.pack(anchor="e", padx=12, pady=(0, 8))

    ROLE_AR = {"admin": "مدير عام", "manager": "مدير", "cashier": "كاشير"}
    ROLE_FROM_AR = {"مدير عام": "admin", "مدير": "manager", "كاشير": "cashier"}

    def refresh(self):
        users = self.db.q("SELECT * FROM users ORDER BY id")
        self._row_ids = [u["id"] for u in users]
        data = [[self.ROLE_AR.get(u["role"], u["role"]), u["username"],
                 u["full_name"] or "—"] for u in users]
        fill_tree(self.tree, data)
        cats = [c["name"] for c in self.db.q("SELECT name FROM categories ORDER BY name")]
        self.cat_label.configure(text=ar("التصنيفات الحالية: " + "، ".join(cats)))

    def _selected_user(self):
        sel = self.tree.selection()
        if not sel:
            return None
        idx = self.tree.index(sel[0])
        return self._row_ids[idx] if 0 <= idx < len(self._row_ids) else None

    def _add_user(self):
        def save(d):
            if not d["username"] or not d["password"]:
                return "اسم الدخول وكلمة المرور مطلوبان"
            if self.db.one("SELECT 1 FROM users WHERE username=?", (d["username"],)):
                return "اسم الدخول مستخدم مسبقاً"
            role = self.ROLE_FROM_AR.get(d["role"], "cashier")
            self.db.add_user(d["username"], d["password"], d["full_name"], role)
            self.refresh()
            self.toast("تمت إضافة المستخدم ✓")
        FormDialog(self.app, "مستخدم جديد", [
            ("full_name", "الاسم الكامل", "text"),
            ("username", "اسم الدخول", "text"),
            ("password", "كلمة المرور", "text"),
            ("role", "الصلاحية", "combo", ["كاشير", "مدير", "مدير عام"]),
        ], save, initial={"role": "كاشير"})

    def _reset_pass(self):
        uid = self._selected_user()
        if uid is None:
            self.toast("اختر مستخدماً أولاً", "info")
            return
        dlg = ctk.CTkInputDialog(text=ar("أدخل كلمة المرور الجديدة:"),
                                 title=ar("تغيير كلمة المرور"))
        val = dlg.get_input()
        if val:
            self.db.set_user_password(uid, val)
            self.toast("تم تغيير كلمة المرور ✓")

    def _del_user(self):
        uid = self._selected_user()
        if uid is None:
            self.toast("اختر مستخدماً أولاً", "info")
            return
        if uid == self.user["id"]:
            self.toast("لا يمكنك حذف حسابك الحالي", "error")
            return
        u = self.db.one("SELECT username FROM users WHERE id=?", (uid,))
        if messagebox.askyesno(ar("تأكيد"), ar(f"حذف المستخدم «{u['username']}»؟")):
            self.db.run("DELETE FROM users WHERE id=?", (uid,))
            self.refresh()
            self.toast("تم الحذف")

    def _add_cat(self):
        name = self.cat_entry.get().strip()
        if not name:
            return
        if self.db.one("SELECT 1 FROM categories WHERE name=?", (name,)):
            self.toast("التصنيف موجود مسبقاً", "info")
            return
        self.db.run("INSERT INTO categories(name) VALUES(?)", (name,))
        self.cat_entry.delete(0, "end")
        self.refresh()
        self.toast("تمت إضافة التصنيف ✓")
