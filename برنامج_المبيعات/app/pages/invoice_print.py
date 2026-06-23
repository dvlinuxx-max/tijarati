# -*- coding: utf-8 -*-
"""نافذة معاينة الفاتورة + الطباعة (توليد HTML وفتحه للطباعة)."""
import os
import tempfile
import webbrowser
import customtkinter as ctk

from ..config import COLORS, APP_NAME, ar, money
from ..widgets import F, label, primary_button, ghost_button


def show_invoice(app, db, invoice_id):
    InvoiceWindow(app, db, invoice_id)


class InvoiceWindow(ctk.CTkToplevel):
    def __init__(self, app, db, invoice_id):
        super().__init__(app)
        self.db = db
        self.invoice_id = invoice_id
        self.inv, self.items = db.invoice_full(invoice_id)
        self.cur = db.get_setting("currency", "د.ع")

        self.title(ar(f"فاتورة {self.inv['invoice_no']}"))
        self.geometry("440x640")
        self.configure(fg_color=COLORS["bg_deep"])
        self.attributes("-topmost", True)
        self.after(200, lambda: self.attributes("-topmost", False))

        self._build()

    def _build(self):
        company = self.db.get_setting("company_name", APP_NAME)
        phone = self.db.get_setting("phone", "")
        address = self.db.get_setting("address", "")
        footer = self.db.get_setting("footer_note", "")
        cust = self.db.one("SELECT name FROM customers WHERE id=?", (self.inv["customer_id"],))

        # إيصال على شكل ورقة بيضاء
        receipt = ctk.CTkScrollableFrame(self, fg_color="white", corner_radius=8)
        receipt.pack(fill="both", expand=True, padx=16, pady=(16, 8))

        def rlabel(text, size=12, bold=False, color="#111", anchor="center"):
            ctk.CTkLabel(receipt, text=ar(text), font=F(size, bold),
                         text_color=color).pack(anchor=anchor, padx=14)

        rlabel(company, 20, True)
        if address:
            rlabel(address, 11, color="#555")
        if phone:
            rlabel(f"هاتف: {phone}", 11, color="#555")
        ctk.CTkFrame(receipt, height=2, fg_color="#ddd").pack(fill="x", padx=14, pady=8)

        info = ctk.CTkFrame(receipt, fg_color="white")
        info.pack(fill="x", padx=14)
        ctk.CTkLabel(info, text=ar(f"فاتورة: {self.inv['invoice_no']}"),
                     font=F(11, True), text_color="#111").pack(side="right")
        ctk.CTkLabel(info, text=ar(self.inv["date"]), font=F(10),
                     text_color="#555").pack(side="left")
        if cust:
            rlabel(f"العميل: {cust['name']}", 11, color="#333", anchor="e")

        ctk.CTkFrame(receipt, height=1, fg_color="#ddd").pack(fill="x", padx=14, pady=6)

        # رؤوس الأعمدة
        hdr = ctk.CTkFrame(receipt, fg_color="white")
        hdr.pack(fill="x", padx=14)
        for txt, side, w in [("الإجمالي", "left", 70), ("سعر", "left", 60),
                             ("كمية", "left", 40), ("الصنف", "right", 0)]:
            ctk.CTkLabel(hdr, text=ar(txt), font=F(10, True), text_color="#888",
                         width=w).pack(side=side)

        for it in self.items:
            row = ctk.CTkFrame(receipt, fg_color="white")
            row.pack(fill="x", padx=14, pady=1)
            ctk.CTkLabel(row, text=ar(money(it["total"])), font=F(10),
                         text_color="#111", width=70).pack(side="left")
            ctk.CTkLabel(row, text=ar(money(it["price"])), font=F(10),
                         text_color="#111", width=60).pack(side="left")
            ctk.CTkLabel(row, text=ar(money(it["qty"])), font=F(10),
                         text_color="#111", width=40).pack(side="left")
            ctk.CTkLabel(row, text=ar(it["name"]), font=F(10),
                         text_color="#111").pack(side="right")

        ctk.CTkFrame(receipt, height=2, fg_color="#ddd").pack(fill="x", padx=14, pady=8)

        def total_row(title, value, bold=False, color="#111"):
            f = ctk.CTkFrame(receipt, fg_color="white")
            f.pack(fill="x", padx=14, pady=1)
            ctk.CTkLabel(f, text=ar(money(value, self.cur)), font=F(13 if bold else 11, bold),
                         text_color=color).pack(side="left")
            ctk.CTkLabel(f, text=ar(title), font=F(13 if bold else 11, bold),
                         text_color=color).pack(side="right")

        total_row("المجموع الفرعي", self.inv["subtotal"])
        if self.inv["discount"]:
            total_row("الخصم", self.inv["discount"], color="#c0392b")
        if self.inv["tax"]:
            total_row("الضريبة", self.inv["tax"])
        total_row("الإجمالي", self.inv["total"], bold=True, color="#1a7a3a")
        total_row("المدفوع", self.inv["paid"])
        remaining = self.inv["total"] - self.inv["paid"]
        if remaining > 0.001:
            total_row("المتبقي", remaining, color="#c0392b")

        ctk.CTkFrame(receipt, height=1, fg_color="#ddd").pack(fill="x", padx=14, pady=8)
        rlabel(footer or "شكراً لتعاملكم معنا", 11, color="#555")
        rlabel(f"طريقة الدفع: {self.inv['payment_method']}", 10, color="#888")

        # أزرار
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=16, pady=(0, 14))
        primary_button(bar, "🖨  طباعة", self._print, width=10).pack(
            side="right", fill="x", expand=True, padx=(0, 6))
        ghost_button(bar, "إغلاق", self.destroy, width=120).pack(side="left")

    # ------------------------------------------------------------------
    def _print(self):
        html = self._build_html()
        path = os.path.join(tempfile.gettempdir(), f"invoice_{self.inv['invoice_no']}.html")
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        webbrowser.open("file://" + path.replace("\\", "/"))

    def _build_html(self):
        company = self.db.get_setting("company_name", APP_NAME)
        phone = self.db.get_setting("phone", "")
        address = self.db.get_setting("address", "")
        footer = self.db.get_setting("footer_note", "")
        cust = self.db.one("SELECT name FROM customers WHERE id=?", (self.inv["customer_id"],))
        cust_name = cust["name"] if cust else ""

        rows = ""
        for it in self.items:
            rows += (f"<tr><td>{it['name']}</td><td>{money(it['qty'])}</td>"
                     f"<td>{money(it['price'])}</td><td>{money(it['total'])}</td></tr>")

        extra = ""
        if self.inv["discount"]:
            extra += f"<div class='line'><span>الخصم</span><span>{money(self.inv['discount'], self.cur)}</span></div>"
        if self.inv["tax"]:
            extra += f"<div class='line'><span>الضريبة</span><span>{money(self.inv['tax'], self.cur)}</span></div>"

        return f"""<!DOCTYPE html>
<html dir="rtl" lang="ar"><head><meta charset="utf-8">
<title>فاتورة {self.inv['invoice_no']}</title>
<style>
  @media print {{ .noprint {{ display:none; }} }}
  body {{ font-family: Tahoma, Arial; max-width: 360px; margin: 20px auto; color:#111; }}
  h1 {{ text-align:center; margin:0; font-size:22px; }}
  .muted {{ text-align:center; color:#666; font-size:12px; margin:2px 0; }}
  hr {{ border:none; border-top:1px dashed #aaa; margin:10px 0; }}
  table {{ width:100%; border-collapse:collapse; font-size:12px; }}
  th,td {{ padding:5px 4px; text-align:right; }}
  th {{ border-bottom:1px solid #333; color:#555; }}
  tr td {{ border-bottom:1px solid #eee; }}
  .line {{ display:flex; justify-content:space-between; font-size:13px; margin:3px 0; }}
  .total {{ font-weight:bold; font-size:16px; color:#1a7a3a; }}
  .info {{ display:flex; justify-content:space-between; font-size:12px; }}
  .footer {{ text-align:center; color:#666; font-size:12px; margin-top:12px; }}
  button {{ display:block; margin:16px auto; padding:10px 30px; font-size:14px;
            background:#2ECC71; color:#fff; border:none; border-radius:8px; cursor:pointer; }}
</style></head><body>
  <h1>{company}</h1>
  <div class="muted">{address}</div>
  <div class="muted">هاتف: {phone}</div>
  <hr>
  <div class="info"><span>فاتورة: {self.inv['invoice_no']}</span><span>{self.inv['date']}</span></div>
  <div class="info"><span>العميل: {cust_name}</span><span>الدفع: {self.inv['payment_method']}</span></div>
  <hr>
  <table><tr><th>الصنف</th><th>كمية</th><th>سعر</th><th>إجمالي</th></tr>{rows}</table>
  <hr>
  <div class="line"><span>المجموع الفرعي</span><span>{money(self.inv['subtotal'], self.cur)}</span></div>
  {extra}
  <div class="line total"><span>الإجمالي</span><span>{money(self.inv['total'], self.cur)}</span></div>
  <div class="line"><span>المدفوع</span><span>{money(self.inv['paid'], self.cur)}</span></div>
  <hr>
  <div class="footer">{footer}</div>
  <button class="noprint" onclick="window.print()">🖨 طباعة الفاتورة</button>
</body></html>"""
