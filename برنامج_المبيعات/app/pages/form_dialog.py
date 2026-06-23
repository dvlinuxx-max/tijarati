# -*- coding: utf-8 -*-
"""نافذة نموذج عامة (Modal) لإضافة/تعديل السجلات — تقلل تكرار الشيفرة."""
import customtkinter as ctk

from ..config import COLORS, ar
from ..widgets import F, label, primary_button, ghost_button, entry


class FormDialog(ctk.CTkToplevel):
    """fields: قائمة من (key, label, kind, options?)
       kind: text | number | combo | multiline
       initial: dict للقيم الابتدائية
       on_save: دالة تستلم dict القيم؛ تُرجع رسالة خطأ نصية أو None عند النجاح.
    """
    def __init__(self, app, title, fields, on_save, initial=None):
        super().__init__(app)
        self.on_save = on_save
        self.fields = fields
        self.widgets = {}
        initial = initial or {}

        self.title(ar(title))
        self.configure(fg_color=COLORS["bg_deep"])
        self.attributes("-topmost", True)
        self.resizable(False, False)
        self.grab_set()

        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=24, pady=(20, 6))
        label(head, title, 18, bold=True).pack(anchor="e")

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24, pady=6)

        for key, lbl, kind, *rest in fields:
            row = ctk.CTkFrame(body, fg_color="transparent")
            row.pack(fill="x", pady=6)
            label(row, lbl, 12, color=COLORS["text_2"]).pack(anchor="e", pady=(0, 3))
            val = initial.get(key, "")
            if kind == "combo":
                options = rest[0] if rest else []
                w = ctk.CTkOptionMenu(
                    row, values=[ar(o) for o in options], font=F(13),
                    fg_color=COLORS["bg_panel"], button_color=COLORS["accent_dim"],
                    text_color=COLORS["text_1"], dropdown_font=F(12),
                    corner_radius=10, width=320, height=40)
                if val:
                    try:
                        w.set(ar(str(val)))
                    except Exception:
                        pass
                w.pack(fill="x")
                w._raw_options = options
            elif kind == "multiline":
                w = ctk.CTkTextbox(row, font=F(13), height=70, width=320,
                                   fg_color=COLORS["bg_panel"], corner_radius=10,
                                   text_color=COLORS["text_1"])
                if val:
                    w.insert("1.0", str(val))
                w.pack(fill="x")
            else:
                w = entry(row, "", width=320)
                if val != "" and val is not None:
                    w.insert(0, str(val))
                w.pack(fill="x")
            self.widgets[key] = (w, kind)

        self.error = label(self, "", 12, color=COLORS["red"])
        self.error.pack(padx=24)

        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=24, pady=(8, 20))
        primary_button(bar, "حفظ", self._save, color="green", width=140).pack(
            side="right", padx=4)
        ghost_button(bar, "إلغاء", self.destroy, width=120).pack(side="right", padx=4)

        self.update_idletasks()
        w = max(420, self.winfo_reqwidth())
        h = self.winfo_reqheight()
        x = app.winfo_rootx() + (app.winfo_width() - w) // 2
        y = app.winfo_rooty() + (app.winfo_height() - h) // 2
        self.geometry(f"{w}x{h}+{max(0,x)}+{max(0,y)}")

    def _collect(self):
        out = {}
        for key, (w, kind) in self.widgets.items():
            if kind == "multiline":
                out[key] = w.get("1.0", "end").strip()
            elif kind == "combo":
                shown = w.get()
                # حوّل القيمة المعروضة (المُشكّلة) إلى القيمة الأصلية
                raw = shown
                for o in getattr(w, "_raw_options", []):
                    if ar(str(o)) == shown:
                        raw = o
                        break
                out[key] = raw
            elif kind == "number":
                txt = w.get().strip().replace(",", "")
                try:
                    out[key] = float(txt) if txt else 0
                except ValueError:
                    out[key] = 0
            else:
                out[key] = w.get().strip()
        return out

    def _save(self):
        data = self._collect()
        err = self.on_save(data)
        if err:
            self.error.configure(text=ar("✗ " + err))
        else:
            self.destroy()
