# -*- coding: utf-8 -*-
"""النافذة الرئيسية: الشريط الجانبي (يمين) + منطقة المحتوى المتبدّلة."""
import customtkinter as ctk

from .config import COLORS, APP_NAME, APP_VERSION, ar
from .widgets import F, label
from .pages.dashboard import DashboardPage
from .pages.pos import POSPage
from .pages.invoices import InvoicesPage
from .pages.products import ProductsPage
from .pages.customers import CustomersPage
from .pages.suppliers import SuppliersPage
from .pages.purchases import PurchasesPage
from .pages.reports import ReportsPage
from .pages.settings import SettingsPage


# (المفتاح، العنوان، الأيقونة، الصلاحية المطلوبة)
NAV_ITEMS = [
    ("dashboard", "لوحة التحكم", "📊", "all"),
    ("pos",       "نقطة البيع",  "🛒", "all"),
    ("invoices",  "الفواتير",    "🧾", "all"),
    ("products",  "المنتجات والمخزون", "📦", "all"),
    ("customers", "العملاء",     "👥", "all"),
    ("suppliers", "الموردون",    "🏭", "manager"),
    ("purchases", "المشتريات",   "📥", "manager"),
    ("reports",   "التقارير",    "📈", "manager"),
    ("settings",  "الإعدادات",   "⚙️", "admin"),
]

ROLE_LEVEL = {"cashier": 1, "manager": 2, "admin": 3}
REQUIRED_LEVEL = {"all": 1, "manager": 2, "admin": 3}


class MainWindow(ctk.CTk):
    def __init__(self, db, user):
        super().__init__()
        self.db = db
        self.user = user
        self.pages = {}
        self.nav_btns = {}
        self.current = None

        company = db.get_setting("company_name", APP_NAME)
        self.title(f"{APP_NAME} — {company}")
        self.geometry("1360x840")
        self.minsize(1180, 720)
        self.configure(fg_color=COLORS["bg_deep"])
        try:
            self.state("zoomed")
        except Exception:
            pass

        self.grid_columnconfigure(0, weight=1)   # المحتوى (يسار)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_content_area()
        self.show_page("dashboard")

    # ------------------------------------------------------------------
    def _build_sidebar(self):
        sb = ctk.CTkFrame(self, width=240, fg_color=COLORS["bg_panel"], corner_radius=0)
        sb.grid(row=0, column=1, sticky="nsew")
        sb.grid_propagate(False)
        sb.grid_rowconfigure(99, weight=1)

        # الشعار
        logo = ctk.CTkFrame(sb, fg_color="transparent")
        logo.grid(row=0, column=0, sticky="ew", padx=20, pady=(24, 6))
        ctk.CTkLabel(logo, text="🧾", font=("Segoe UI Emoji", 26)).pack(side="right")
        ctk.CTkLabel(logo, text=ar(APP_NAME), font=("Tahoma", 24, "bold"),
                     text_color=COLORS["text_1"]).pack(side="right", padx=8)
        label(sb, "نظام إدارة المبيعات", 10, color=COLORS["text_3"]).grid(
            row=1, column=0, sticky="e", padx=22, pady=(0, 18))

        ctk.CTkFrame(sb, height=1, fg_color=COLORS["border"]).grid(
            row=2, column=0, sticky="ew", padx=16, pady=(0, 12))

        # أزرار التنقل
        user_level = ROLE_LEVEL.get(self.user["role"], 1)
        r = 3
        for key, title, icon, perm in NAV_ITEMS:
            if user_level < REQUIRED_LEVEL[perm]:
                continue
            btn = ctk.CTkButton(
                sb, text=f"  {ar(title)}   {icon}", anchor="e",
                font=F(14), fg_color="transparent", hover_color=COLORS["bg_hover"],
                text_color=COLORS["text_2"], corner_radius=10, height=46,
                command=lambda k=key: self.show_page(k))
            btn.grid(row=r, column=0, sticky="ew", padx=12, pady=3)
            self.nav_btns[key] = btn
            r += 1

        # بطاقة المستخدم + خروج
        card = ctk.CTkFrame(sb, fg_color=COLORS["bg_card"], corner_radius=12)
        card.grid(row=100, column=0, sticky="sew", padx=12, pady=12)
        role_ar = {"admin": "مدير عام", "manager": "مدير", "cashier": "كاشير"}
        label(card, self.user.get("full_name") or self.user["username"], 13, bold=True).pack(
            anchor="e", padx=12, pady=(12, 0))
        label(card, role_ar.get(self.user["role"], self.user["role"]), 11,
              color=COLORS["accent"]).pack(anchor="e", padx=12, pady=(0, 8))
        ctk.CTkButton(card, text=ar("تسجيل الخروج  ⟲"), font=F(12),
                      fg_color=COLORS["bg_panel"], hover_color=COLORS["red"],
                      text_color=COLORS["text_2"], corner_radius=8, height=34,
                      command=self._logout).pack(fill="x", padx=12, pady=(0, 8))
        label(card, f"الإصدار {APP_VERSION}", 9, color=COLORS["text_3"]).pack(
            anchor="e", padx=12, pady=(0, 10))

    def _build_content_area(self):
        self.content = ctk.CTkFrame(self, fg_color=COLORS["bg_deep"])
        self.content.grid(row=0, column=0, sticky="nsew")
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

    # ------------------------------------------------------------------
    PAGE_CLASSES = {
        "dashboard": DashboardPage, "pos": POSPage, "invoices": InvoicesPage,
        "products": ProductsPage, "customers": CustomersPage,
        "suppliers": SuppliersPage, "purchases": PurchasesPage,
        "reports": ReportsPage, "settings": SettingsPage,
    }

    def show_page(self, key):
        # تمييز الزر النشط
        for k, btn in self.nav_btns.items():
            if k == key:
                btn.configure(fg_color=COLORS["accent_dim"], text_color=COLORS["accent"])
            else:
                btn.configure(fg_color="transparent", text_color=COLORS["text_2"])

        if self.current is not None:
            self.current.grid_forget()

        if key not in self.pages:
            cls = self.PAGE_CLASSES[key]
            self.pages[key] = cls(self.content, self)
        page = self.pages[key]
        page.grid(row=0, column=0, sticky="nsew")
        if hasattr(page, "on_show"):
            page.on_show()
        self.current = page

    def _logout(self):
        self.destroy()
        from .login import LoginWindow
        from .main_window import MainWindow as MW

        def after_login(user):
            MW(self.db, user).mainloop()

        LoginWindow(self.db, after_login).mainloop()
