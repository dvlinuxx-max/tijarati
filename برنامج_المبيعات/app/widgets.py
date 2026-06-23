# -*- coding: utf-8 -*-
"""
عناصر واجهة مشتركة وقابلة لإعادة الاستخدام (بطاقات، أزرار، حقول، جداول).
كلها تدعم العربية RTL عبر الدالة ar().
"""
import customtkinter as ctk
from tkinter import ttk

from .config import COLORS, FONT_AR, ar


def F(size=13, bold=False):
    """خط عربي بحجم محدد."""
    return (FONT_AR, size, "bold") if bold else (FONT_AR, size)


class Card(ctk.CTkFrame):
    """بطاقة بخلفية وزوايا دائرية."""
    def __init__(self, master, **kw):
        kw.setdefault("fg_color", COLORS["bg_card"])
        kw.setdefault("corner_radius", 14)
        kw.setdefault("border_width", 1)
        kw.setdefault("border_color", COLORS["border"])
        super().__init__(master, **kw)


def label(master, text, size=13, bold=False, color=None, **kw):
    return ctk.CTkLabel(
        master, text=ar(text), font=F(size, bold),
        text_color=color or COLORS["text_1"], **kw)


def primary_button(master, text, command, color="accent", width=140, height=40, **kw):
    hover = {"accent": "accent_h", "accent2": "accent2_h",
             "green": "green_h", "red": "red_h"}.get(color, "accent_h")
    return ctk.CTkButton(
        master, text=ar(text), command=command,
        font=F(13, True), width=width, height=height,
        fg_color=COLORS[color], hover_color=COLORS[hover],
        text_color="white", corner_radius=10, **kw)


def ghost_button(master, text, command, width=120, height=38, **kw):
    return ctk.CTkButton(
        master, text=ar(text), command=command,
        font=F(13), width=width, height=height,
        fg_color=COLORS["bg_panel"], hover_color=COLORS["bg_hover"],
        text_color=COLORS["text_1"], border_width=1,
        border_color=COLORS["border2"], corner_radius=10, **kw)


def entry(master, placeholder="", width=240, height=40, show=None, **kw):
    return ctk.CTkEntry(
        master, placeholder_text=ar(placeholder), font=F(13),
        width=width, height=height, show=show, justify="right",
        fg_color=COLORS["bg_panel"], border_color=COLORS["border2"],
        text_color=COLORS["text_1"], placeholder_text_color=COLORS["text_3"],
        corner_radius=10, **kw)


def field(master, title, placeholder="", width=240, show=None):
    """حقل إدخال مع عنوان فوقه. يُرجع (frame, entry)."""
    f = ctk.CTkFrame(master, fg_color="transparent")
    label(f, title, 12, color=COLORS["text_2"]).pack(anchor="e", padx=2, pady=(0, 4))
    e = entry(f, placeholder, width=width, show=show)
    e.pack(fill="x")
    return f, e


class StatCard(Card):
    """بطاقة إحصائية: عنوان + قيمة كبيرة + أيقونة ملوّنة."""
    def __init__(self, master, title, value, icon="", accent="accent", sub=""):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=16, pady=(16, 4))
        ctk.CTkLabel(top, text=icon, font=("Segoe UI Emoji", 22)).pack(side="right")
        label(top, title, 12, color=COLORS["text_2"]).pack(side="right", padx=8)

        self.value_lbl = ctk.CTkLabel(
            self, text=ar(value), font=F(24, True), text_color=COLORS[accent])
        self.value_lbl.pack(anchor="e", padx=16, pady=(0, 2))

        self.sub_lbl = label(self, sub, 11, color=COLORS["text_3"])
        self.sub_lbl.pack(anchor="e", padx=16, pady=(0, 16))

    def set_value(self, value, sub=None):
        self.value_lbl.configure(text=ar(value))
        if sub is not None:
            self.sub_lbl.configure(text=ar(sub))


def make_treeview(master, columns, headings, widths=None, anchors=None):
    """ينشئ جدول ttk منسّق بالعربية مع شريط تمرير. يُرجع (frame, tree)."""
    frame = ctk.CTkFrame(master, fg_color=COLORS["bg_panel"], corner_radius=12)
    frame.grid_rowconfigure(0, weight=1)
    frame.grid_columnconfigure(0, weight=1)

    style = ttk.Style()
    style.theme_use("clam")
    style.configure(
        "Tj.Treeview",
        background=COLORS["bg_panel"], fieldbackground=COLORS["bg_panel"],
        foreground=COLORS["text_1"], font=(FONT_AR, 12), rowheight=36,
        borderwidth=0, relief="flat")
    style.configure(
        "Tj.Treeview.Heading", background=COLORS["bg_card"],
        foreground=COLORS["text_2"], font=(FONT_AR, 11, "bold"),
        borderwidth=0, relief="flat", padding=(10, 10))
    style.map("Tj.Treeview", background=[("selected", COLORS["accent_dim"])],
              foreground=[("selected", COLORS["text_1"])])
    style.map("Tj.Treeview.Heading", background=[("active", COLORS["bg_hover"])])
    style.layout("Tj.Treeview", [("Tj.Treeview.treearea", {"sticky": "nswe"})])

    tree = ttk.Treeview(frame, style="Tj.Treeview", show="headings",
                        selectmode="browse", columns=columns)
    widths = widths or {}
    anchors = anchors or {}
    for col, head in zip(columns, headings):
        tree.heading(col, text=ar(head), anchor="e")
        tree.column(col, width=widths.get(col, 120),
                    anchor=anchors.get(col, "e"), minwidth=60)
    tree.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)

    vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    vsb.grid(row=0, column=1, sticky="ns")
    tree.configure(yscrollcommand=vsb.set)

    tree.tag_configure("even", background=COLORS["bg_panel"])
    tree.tag_configure("odd", background=COLORS["bg_card"])
    tree.tag_configure("warn", foreground=COLORS["amber"])
    tree.tag_configure("danger", foreground=COLORS["red"])
    return frame, tree


def fill_tree(tree, rows):
    """يملأ الجدول بصفوف مع تلوين متناوب. كل صف: (values, tag?)."""
    tree.delete(*tree.get_children())
    for i, item in enumerate(rows):
        if isinstance(item, tuple) and len(item) == 2 and isinstance(item[0], (list, tuple)):
            values, extra = item
        else:
            values, extra = item, None
        base = "even" if i % 2 == 0 else "odd"
        tags = (base, extra) if extra else (base,)
        vals = [ar(v) for v in values]
        tree.insert("", "end", values=vals, tags=tags)


class Toast(ctk.CTkToplevel):
    """رسالة منبثقة سريعة (إشعار)."""
    def __init__(self, master, text, kind="success"):
        super().__init__(master)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        color = {"success": COLORS["green"], "error": COLORS["red"],
                 "info": COLORS["accent"]}.get(kind, COLORS["green"])
        self.configure(fg_color=color)
        frame = ctk.CTkFrame(self, fg_color=color, corner_radius=10)
        frame.pack(padx=2, pady=2)
        ctk.CTkLabel(frame, text=ar(text), font=F(13, True),
                     text_color="white").pack(padx=20, pady=12)
        self.update_idletasks()
        master.update_idletasks()
        x = master.winfo_rootx() + master.winfo_width() // 2 - self.winfo_width() // 2
        y = master.winfo_rooty() + 80
        self.geometry(f"+{x}+{y}")
        self.after(1800, self.destroy)
