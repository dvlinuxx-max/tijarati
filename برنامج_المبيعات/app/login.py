# -*- coding: utf-8 -*-
"""شاشة تسجيل الدخول."""
import customtkinter as ctk

from .config import COLORS, APP_NAME, APP_SUBTITLE, ar
from .widgets import F, primary_button, entry, label


class LoginWindow(ctk.CTk):
    def __init__(self, db, on_success):
        super().__init__()
        self.db = db
        self.on_success = on_success
        self.user = None

        self.title(f"{APP_NAME} — تسجيل الدخول")
        self.geometry("980x620")
        self.minsize(900, 560)
        self.configure(fg_color=COLORS["bg_deep"])

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_brand()
        self._build_form()

    # ------------------------------------------------------------------
    def _build_brand(self):
        """الجهة اليمنى: هوية البرنامج (في RTL تكون يمين)."""
        brand = ctk.CTkFrame(self, fg_color=COLORS["bg_panel"], corner_radius=0)
        brand.grid(row=0, column=1, sticky="nsew")
        brand.grid_propagate(False)

        wrap = ctk.CTkFrame(brand, fg_color="transparent")
        wrap.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(wrap, text="🧾", font=("Segoe UI Emoji", 64)).pack(pady=(0, 10))
        ctk.CTkLabel(wrap, text=ar(APP_NAME), font=(("Tahoma"), 42, "bold"),
                     text_color=COLORS["text_1"]).pack()
        ctk.CTkLabel(wrap, text=ar(APP_SUBTITLE), font=F(15),
                     text_color=COLORS["accent"]).pack(pady=(4, 24))

        for feat in ["نقطة بيع سريعة (POS)", "إدارة المخزون والباركود",
                     "فواتير وعملاء وموردين", "تقارير وأرباح لحظية"]:
            row = ctk.CTkFrame(wrap, fg_color="transparent")
            row.pack(anchor="e", pady=4)
            label(row, feat, 13, color=COLORS["text_2"]).pack(side="right")
            ctk.CTkLabel(row, text="✓", font=F(14, True),
                         text_color=COLORS["green"]).pack(side="right", padx=8)

    # ------------------------------------------------------------------
    def _build_form(self):
        form = ctk.CTkFrame(self, fg_color=COLORS["bg_deep"])
        form.grid(row=0, column=0, sticky="nsew")
        box = ctk.CTkFrame(form, fg_color="transparent")
        box.place(relx=0.5, rely=0.5, anchor="center")

        label(box, "مرحباً بك 👋", 26, bold=True).pack(anchor="e")
        label(box, "سجّل دخولك للمتابعة إلى لوحة التحكم", 13,
              color=COLORS["text_2"]).pack(anchor="e", pady=(4, 28))

        label(box, "اسم المستخدم", 12, color=COLORS["text_2"]).pack(anchor="e", pady=(0, 4))
        self.user_entry = entry(box, "أدخل اسم المستخدم", width=320)
        self.user_entry.pack()
        self.user_entry.insert(0, "admin")

        label(box, "كلمة المرور", 12, color=COLORS["text_2"]).pack(anchor="e", pady=(16, 4))
        self.pass_entry = entry(box, "أدخل كلمة المرور", width=320, show="●")
        self.pass_entry.pack()
        self.pass_entry.bind("<Return>", lambda e: self._login())

        self.error_lbl = label(box, "", 12, color=COLORS["red"])
        self.error_lbl.pack(anchor="e", pady=(10, 0))

        primary_button(box, "تسجيل الدخول", self._login, width=320, height=46).pack(pady=(16, 0))

        hint = ctk.CTkFrame(box, fg_color=COLORS["bg_card"], corner_radius=8)
        hint.pack(fill="x", pady=(24, 0))
        label(hint, "للتجربة:  admin / admin   —   cashier / 1234", 11,
              color=COLORS["text_3"]).pack(padx=12, pady=8)

        self.pass_entry.focus()

    # ------------------------------------------------------------------
    def _login(self):
        username = self.user_entry.get().strip()
        password = self.pass_entry.get()
        user = self.db.authenticate(username, password)
        if user:
            self.user = user
            self.destroy()
            self.on_success(user)
        else:
            self.error_lbl.configure(text=ar("✗ اسم المستخدم أو كلمة المرور غير صحيحة"))
            self.pass_entry.delete(0, "end")
