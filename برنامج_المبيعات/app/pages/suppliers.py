# -*- coding: utf-8 -*-
"""إدارة الموردين — يرث من صفحة العملاء مع تغيير الجدول والمسميات."""
from .customers import CustomersPage


class SuppliersPage(CustomersPage):
    title = "الموردون"
    subtitle = "سجل الموردين والمستحقات"
    icon = "🏭"
    table = "suppliers"
    person = "المورّد"
