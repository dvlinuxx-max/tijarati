# -*- coding: utf-8 -*-
"""صنف أساسي للصفحات: ترويسة موحّدة + منطقة محتوى."""
import customtkinter as ctk

from ..config import COLORS, ar
from ..widgets import F, label, Toast


class BasePage(ctk.CTkFrame):
    title = "صفحة"
    subtitle = ""
    icon = ""

    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.db = app.db
        self.user = app.user
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self._build_header()
        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 20))
        self.build(self.body)

    def _build_header(self):
        head = ctk.CTkFrame(self, fg_color="transparent", height=80)
        head.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 12))
        right = ctk.CTkFrame(head, fg_color="transparent")
        right.pack(side="right")
        ctk.CTkLabel(right, text=self.icon, font=("Segoe UI Emoji", 26)).pack(side="right", padx=(0, 10))
        txt = ctk.CTkFrame(right, fg_color="transparent")
        txt.pack(side="right")
        label(txt, self.title, 22, bold=True).pack(anchor="e")
        if self.subtitle:
            label(txt, self.subtitle, 12, color=COLORS["text_2"]).pack(anchor="e")
        self.header_actions = ctk.CTkFrame(head, fg_color="transparent")
        self.header_actions.pack(side="left")

    # يُعاد تعريفها في الصفحات الفرعية
    def build(self, parent):
        pass

    def on_show(self):
        if hasattr(self, "refresh"):
            self.refresh()

    def toast(self, text, kind="success"):
        Toast(self.app, text, kind)
