# -*- coding: utf-8 -*-
"""
طبقة قاعدة البيانات (SQLite) — إنشاء الجداول، البيانات الأولية، ودوال الاستعلام.
"""
import sqlite3
import hashlib
import os
from datetime import datetime, timedelta

from .config import DB_PATH


def _hash_password(password: str, salt: str = "tijarati_2026") -> str:
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()


class Database:
    def __init__(self, path: str = DB_PATH):
        self.path = path
        first_time = not os.path.exists(path)
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._create_schema()
        if first_time or not self._has_users():
            self._seed()

    # ------------------------------------------------------------------
    # تنفيذ عام
    # ------------------------------------------------------------------
    def q(self, sql, params=()):
        """استعلام يُرجع قائمة صفوف."""
        cur = self.conn.execute(sql, params)
        return cur.fetchall()

    def one(self, sql, params=()):
        cur = self.conn.execute(sql, params)
        return cur.fetchone()

    def run(self, sql, params=()):
        """تنفيذ مع حفظ، يُرجع المعرّف الأخير."""
        cur = self.conn.execute(sql, params)
        self.conn.commit()
        return cur.lastrowid

    def _has_users(self):
        try:
            r = self.one("SELECT COUNT(*) c FROM users")
            return r and r["c"] > 0
        except sqlite3.Error:
            return False

    # ------------------------------------------------------------------
    # المخطط
    # ------------------------------------------------------------------
    def _create_schema(self):
        c = self.conn
        c.executescript(
            """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT,
            role TEXT DEFAULT 'cashier',     -- admin | manager | cashier
            active INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        );

        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            barcode TEXT,
            name TEXT NOT NULL,
            category_id INTEGER,
            cost REAL DEFAULT 0,
            price REAL DEFAULT 0,
            quantity REAL DEFAULT 0,
            reorder_level REAL DEFAULT 5,
            unit TEXT DEFAULT 'قطعة',
            active INTEGER DEFAULT 1,
            FOREIGN KEY (category_id) REFERENCES categories(id)
        );

        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            address TEXT,
            balance REAL DEFAULT 0,
            notes TEXT
        );

        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            address TEXT,
            balance REAL DEFAULT 0,
            notes TEXT
        );

        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_no TEXT,
            customer_id INTEGER,
            user_id INTEGER,
            date TEXT,
            subtotal REAL DEFAULT 0,
            discount REAL DEFAULT 0,
            tax REAL DEFAULT 0,
            total REAL DEFAULT 0,
            paid REAL DEFAULT 0,
            payment_method TEXT DEFAULT 'نقدي',
            status TEXT DEFAULT 'مكتملة',
            notes TEXT,
            FOREIGN KEY (customer_id) REFERENCES customers(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS invoice_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER,
            product_id INTEGER,
            name TEXT,
            qty REAL,
            price REAL,
            cost REAL,
            total REAL,
            FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            purchase_no TEXT,
            supplier_id INTEGER,
            user_id INTEGER,
            date TEXT,
            subtotal REAL DEFAULT 0,
            discount REAL DEFAULT 0,
            tax REAL DEFAULT 0,
            total REAL DEFAULT 0,
            paid REAL DEFAULT 0,
            status TEXT DEFAULT 'مكتملة',
            notes TEXT,
            FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
        );

        CREATE TABLE IF NOT EXISTS purchase_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            purchase_id INTEGER,
            product_id INTEGER,
            name TEXT,
            qty REAL,
            cost REAL,
            total REAL,
            FOREIGN KEY (purchase_id) REFERENCES purchases(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            category TEXT,
            amount REAL,
            notes TEXT,
            user_id INTEGER
        );
        """
        )
        self.conn.commit()

    # ------------------------------------------------------------------
    # الإعدادات
    # ------------------------------------------------------------------
    def get_setting(self, key, default=""):
        r = self.one("SELECT value FROM settings WHERE key=?", (key,))
        return r["value"] if r else default

    def set_setting(self, key, value):
        self.run(
            "INSERT INTO settings(key,value) VALUES(?,?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, str(value)),
        )

    def all_settings(self):
        return {r["key"]: r["value"] for r in self.q("SELECT key,value FROM settings")}

    # ------------------------------------------------------------------
    # المصادقة
    # ------------------------------------------------------------------
    def authenticate(self, username, password):
        r = self.one(
            "SELECT * FROM users WHERE username=? AND active=1", (username.strip(),)
        )
        if r and r["password"] == _hash_password(password):
            return dict(r)
        return None

    def add_user(self, username, password, full_name, role):
        return self.run(
            "INSERT INTO users(username,password,full_name,role) VALUES(?,?,?,?)",
            (username, _hash_password(password), full_name, role),
        )

    def set_user_password(self, user_id, password):
        self.run("UPDATE users SET password=? WHERE id=?",
                 (_hash_password(password), user_id))

    # ------------------------------------------------------------------
    # منطق العمل: المبيعات والمخزون
    # ------------------------------------------------------------------
    def next_invoice_no(self):
        prefix = self.get_setting("invoice_prefix", "INV-")
        r = self.one("SELECT COUNT(*) c FROM invoices")
        return f"{prefix}{(r['c'] + 1):05d}"

    def next_purchase_no(self):
        r = self.one("SELECT COUNT(*) c FROM purchases")
        return f"PUR-{(r['c'] + 1):05d}"

    def create_sale(self, customer_id, user_id, items, discount=0, tax=0,
                    paid=0, payment_method="نقدي", notes=""):
        """إنشاء فاتورة بيع وخصم الكميات من المخزون.

        items: قائمة من dict فيها product_id, name, qty, price, cost
        تُرجع (invoice_id, invoice_no).
        """
        subtotal = sum(it["qty"] * it["price"] for it in items)
        total = max(0, subtotal - discount + tax)
        inv_no = self.next_invoice_no()
        date = datetime.now().strftime("%Y-%m-%d %H:%M")
        status = "مكتملة" if paid >= total else "آجلة"
        inv_id = self.run(
            "INSERT INTO invoices(invoice_no,customer_id,user_id,date,subtotal,"
            "discount,tax,total,paid,payment_method,status,notes) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
            (inv_no, customer_id, user_id, date, subtotal, discount, tax,
             total, paid, payment_method, status, notes),
        )
        for it in items:
            line = it["qty"] * it["price"]
            self.run(
                "INSERT INTO invoice_items(invoice_id,product_id,name,qty,price,cost,total) "
                "VALUES(?,?,?,?,?,?,?)",
                (inv_id, it.get("product_id"), it["name"], it["qty"],
                 it["price"], it.get("cost", 0), line),
            )
            if it.get("product_id"):
                self.run("UPDATE products SET quantity = quantity - ? WHERE id=?",
                         (it["qty"], it["product_id"]))
        # دين العميل إذا الدفع أقل من الإجمالي
        remaining = total - paid
        if remaining > 0 and customer_id:
            self.run("UPDATE customers SET balance = balance + ? WHERE id=?",
                     (remaining, customer_id))
        return inv_id, inv_no

    def create_purchase(self, supplier_id, user_id, items, discount=0,
                        paid=0, notes=""):
        subtotal = sum(it["qty"] * it["cost"] for it in items)
        total = max(0, subtotal - discount)
        pur_no = self.next_purchase_no()
        date = datetime.now().strftime("%Y-%m-%d %H:%M")
        pur_id = self.run(
            "INSERT INTO purchases(purchase_no,supplier_id,user_id,date,subtotal,"
            "discount,tax,total,paid,status,notes) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (pur_no, supplier_id, user_id, date, subtotal, discount, 0,
             total, paid, "مكتملة", notes),
        )
        for it in items:
            line = it["qty"] * it["cost"]
            self.run(
                "INSERT INTO purchase_items(purchase_id,product_id,name,qty,cost,total) "
                "VALUES(?,?,?,?,?,?)",
                (pur_id, it.get("product_id"), it["name"], it["qty"], it["cost"], line),
            )
            if it.get("product_id"):
                self.run("UPDATE products SET quantity = quantity + ? WHERE id=?",
                         (it["qty"], it["product_id"]))
        remaining = total - paid
        if remaining > 0 and supplier_id:
            self.run("UPDATE suppliers SET balance = balance + ? WHERE id=?",
                     (remaining, supplier_id))
        return pur_id, pur_no

    def invoice_full(self, invoice_id):
        inv = self.one("SELECT * FROM invoices WHERE id=?", (invoice_id,))
        items = self.q("SELECT * FROM invoice_items WHERE invoice_id=?", (invoice_id,))
        return inv, items

    # ------------------------------------------------------------------
    # إحصائيات لوحة التحكم
    # ------------------------------------------------------------------
    def stats_summary(self):
        today = datetime.now().strftime("%Y-%m-%d")
        month = datetime.now().strftime("%Y-%m")
        sales_today = self.one(
            "SELECT COALESCE(SUM(total),0) s, COUNT(*) c FROM invoices WHERE date LIKE ?",
            (today + "%",))
        sales_month = self.one(
            "SELECT COALESCE(SUM(total),0) s FROM invoices WHERE date LIKE ?",
            (month + "%",))
        profit_month = self.one(
            "SELECT COALESCE(SUM((ii.price - ii.cost) * ii.qty),0) p "
            "FROM invoice_items ii JOIN invoices i ON i.id=ii.invoice_id "
            "WHERE i.date LIKE ?", (month + "%",))
        products_count = self.one("SELECT COUNT(*) c FROM products WHERE active=1")
        low_stock = self.one(
            "SELECT COUNT(*) c FROM products WHERE quantity <= reorder_level AND active=1")
        customers_count = self.one("SELECT COUNT(*) c FROM customers")
        debts = self.one("SELECT COALESCE(SUM(balance),0) s FROM customers")
        return {
            "sales_today": sales_today["s"],
            "invoices_today": sales_today["c"],
            "sales_month": sales_month["s"],
            "profit_month": profit_month["p"],
            "products": products_count["c"],
            "low_stock": low_stock["c"],
            "customers": customers_count["c"],
            "debts": debts["s"],
        }

    def sales_last_days(self, days=14):
        out = []
        for d in range(days - 1, -1, -1):
            day = (datetime.now() - timedelta(days=d)).strftime("%Y-%m-%d")
            r = self.one(
                "SELECT COALESCE(SUM(total),0) s FROM invoices WHERE date LIKE ?",
                (day + "%",))
            label = (datetime.now() - timedelta(days=d)).strftime("%m-%d")
            out.append((label, r["s"]))
        return out

    def top_products(self, limit=5):
        return self.q(
            "SELECT name, SUM(qty) q, SUM(total) t FROM invoice_items "
            "GROUP BY name ORDER BY t DESC LIMIT ?", (limit,))

    def low_stock_products(self):
        return self.q(
            "SELECT * FROM products WHERE quantity <= reorder_level AND active=1 "
            "ORDER BY quantity ASC")

    # ------------------------------------------------------------------
    # البيانات الأولية (تجريبية لعرض البرنامج)
    # ------------------------------------------------------------------
    def _seed(self):
        # المستخدمون
        self.add_user("admin", "admin", "المدير العام", "admin")
        self.add_user("cashier", "1234", "موظف الكاشير", "cashier")

        # الإعدادات الافتراضية للشركة
        defaults = {
            "company_name": "شركتك التجارية",
            "currency": "د.ع",
            "tax_rate": "0",
            "phone": "0770 000 0000",
            "address": "العراق - بغداد",
            "footer_note": "شكراً لتعاملكم معنا — نتمنى لكم يوماً سعيداً",
            "invoice_prefix": "INV-",
            "low_stock_alert": "1",
        }
        for k, v in defaults.items():
            self.set_setting(k, v)

        # التصنيفات
        cats = ["إلكترونيات", "ملابس", "أغذية", "أدوات منزلية", "مستلزمات مكتبية"]
        cat_ids = {}
        for name in cats:
            cat_ids[name] = self.run("INSERT INTO categories(name) VALUES(?)", (name,))

        # المنتجات
        products = [
            ("6291041500213", "لابتوب ديل Inspiron", "إلكترونيات", 850000, 1050000, 12, 3, "قطعة"),
            ("6291041500220", "ماوس لاسلكي", "إلكترونيات", 8000, 15000, 120, 20, "قطعة"),
            ("6291041500237", "لوحة مفاتيح ميكانيكية", "إلكترونيات", 35000, 65000, 45, 10, "قطعة"),
            ("6291041500244", "سماعة بلوتوث", "إلكترونيات", 18000, 35000, 80, 15, "قطعة"),
            ("6291041500251", "شاحن سريع 65 واط", "إلكترونيات", 12000, 25000, 4, 10, "قطعة"),
            ("6291041500268", "قميص قطني رجالي", "ملابس", 12000, 25000, 60, 15, "قطعة"),
            ("6291041500275", "بنطلون جينز", "ملابس", 18000, 40000, 35, 10, "قطعة"),
            ("6291041500282", "حذاء رياضي", "ملابس", 30000, 60000, 25, 8, "زوج"),
            ("6291041500299", "علبة شاي فاخر", "أغذية", 4000, 8000, 200, 30, "علبة"),
            ("6291041500305", "قهوة عربية 500غ", "أغذية", 9000, 16000, 90, 20, "كيس"),
            ("6291041500312", "زيت زيتون 1 لتر", "أغذية", 11000, 18000, 2, 12, "زجاجة"),
            ("6291041500329", "طقم أواني طهي", "أدوات منزلية", 45000, 85000, 18, 5, "طقم"),
            ("6291041500336", "مكنسة كهربائية", "أدوات منزلية", 60000, 110000, 9, 4, "قطعة"),
            ("6291041500343", "دفتر ملاحظات A4", "مستلزمات مكتبية", 1500, 3500, 300, 50, "قطعة"),
            ("6291041500350", "علبة أقلام حبر", "مستلزمات مكتبية", 2500, 6000, 150, 40, "علبة"),
        ]
        for bc, name, cat, cost, price, qty, reorder, unit in products:
            self.run(
                "INSERT INTO products(barcode,name,category_id,cost,price,quantity,reorder_level,unit) "
                "VALUES(?,?,?,?,?,?,?,?)",
                (bc, name, cat_ids[cat], cost, price, qty, reorder, unit),
            )

        # العملاء
        customers = [
            ("محمد علي", "0770 111 2233", "بغداد - الكرادة", 0),
            ("زينب حسن", "0771 222 3344", "بغداد - المنصور", 150000),
            ("علي كريم", "0780 333 4455", "البصرة - العشار", 0),
            ("فاطمة جاسم", "0750 444 5566", "أربيل - عنكاوا", 75000),
            ("عميل نقدي", "", "", 0),
        ]
        for name, phone, addr, bal in customers:
            self.run(
                "INSERT INTO customers(name,phone,address,balance) VALUES(?,?,?,?)",
                (name, phone, addr, bal),
            )

        # الموردون
        suppliers = [
            ("شركة الرافدين للإلكترونيات", "0770 555 6677", "بغداد - شارع الرشيد", 0),
            ("مؤسسة النور للملابس", "0771 666 7788", "بغداد - الشورجة", 320000),
            ("موزع المواد الغذائية", "0780 777 8899", "بغداد - جميلة", 0),
        ]
        for name, phone, addr, bal in suppliers:
            self.run(
                "INSERT INTO suppliers(name,phone,address,balance) VALUES(?,?,?,?)",
                (name, phone, addr, bal),
            )

        self._seed_invoices()
        self._seed_expenses()

    def _seed_invoices(self):
        """فواتير مبيعات تجريبية على مدى آخر 14 يوم لإظهار الرسوم البيانية."""
        import random
        products = self.q("SELECT id,name,price,cost FROM products")
        prefix = self.get_setting("invoice_prefix", "INV-")
        counter = 1
        for day in range(14, -1, -1):
            date = (datetime.now() - timedelta(days=day))
            n_invoices = random.randint(1, 5)
            for _ in range(n_invoices):
                items = random.sample(products, random.randint(1, 4))
                subtotal = 0
                rows = []
                for p in items:
                    qty = random.randint(1, 5)
                    line = p["price"] * qty
                    subtotal += line
                    rows.append((p["id"], p["name"], qty, p["price"], p["cost"], line))
                discount = random.choice([0, 0, 0, 5000, 10000])
                total = max(0, subtotal - discount)
                inv_no = f"{prefix}{counter:05d}"
                dt = date.replace(
                    hour=random.randint(9, 21), minute=random.randint(0, 59)
                ).strftime("%Y-%m-%d %H:%M")
                inv_id = self.run(
                    "INSERT INTO invoices(invoice_no,customer_id,user_id,date,subtotal,"
                    "discount,tax,total,paid,payment_method,status) "
                    "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                    (inv_no, random.randint(1, 5), 1, dt, subtotal, discount, 0,
                     total, total, random.choice(["نقدي", "نقدي", "بطاقة"]), "مكتملة"),
                )
                for pid, name, qty, price, cost, line in rows:
                    self.run(
                        "INSERT INTO invoice_items(invoice_id,product_id,name,qty,price,cost,total) "
                        "VALUES(?,?,?,?,?,?,?)",
                        (inv_id, pid, name, qty, price, cost, line),
                    )
                counter += 1

    def _seed_expenses(self):
        import random
        cats = ["إيجار", "رواتب", "كهرباء", "نقل", "صيانة", "متفرقات"]
        for day in range(14, -1, -2):
            date = (datetime.now() - timedelta(days=day)).strftime("%Y-%m-%d")
            self.run(
                "INSERT INTO expenses(date,category,amount,notes,user_id) VALUES(?,?,?,?,?)",
                (date, random.choice(cats), random.randint(10000, 80000), "", 1),
            )
