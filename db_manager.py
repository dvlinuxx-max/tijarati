import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
import threading
import time
import random
import json
from datetime import datetime, timedelta

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

COLORS = {
    "bg_deep":     "#0D0F14",
    "bg_panel":    "#13161E",
    "bg_card":     "#1A1E2A",
    "bg_hover":    "#21263A",
    "accent":      "#4F8EF7",
    "accent2":     "#7C5CFC",
    "accent_dim":  "#2A3A5C",
    "green":       "#2ECC71",
    "amber":       "#F59E0B",
    "red":         "#EF4444",
    "text_1":      "#F0F2FF",
    "text_2":      "#8B92A8",
    "text_3":      "#4A5168",
    "border":      "#252A3A",
    "border2":     "#2F3650",
}

DEMO_TABLES = {
    "employees": {
        "columns": ["id", "name", "department", "salary", "hire_date", "status"],
        "data": [
            [1, "Ahmed Al-Rashid",   "Engineering",  95000, "2020-03-15", "Active"],
            [2, "Sara Mohammed",     "Marketing",    72000, "2019-07-22", "Active"],
            [3, "Omar Khalid",       "Engineering",  88000, "2021-01-10", "Active"],
            [4, "Fatima Al-Hassan",  "HR",           65000, "2018-11-05", "Active"],
            [5, "Youssef Ibrahim",   "Finance",      91000, "2020-08-30", "Inactive"],
            [6, "Nour Al-Ahmad",     "Engineering", 102000, "2017-04-18", "Active"],
            [7, "Khalid Mansour",    "Marketing",    68000, "2022-02-14", "Active"],
            [8, "Layla Hassan",      "Finance",      84000, "2019-09-03", "Active"],
            [9, "Ziad Al-Farsi",     "Engineering",  97000, "2021-06-25", "Active"],
            [10,"Rania Saad",        "HR",           62000, "2023-01-08", "Active"],
            [11,"Tariq Nasser",      "Engineering",  89000, "2020-11-20", "Active"],
            [12,"Hana Al-Turki",     "Marketing",    75000, "2018-05-12", "Inactive"],
        ]
    },
    "products": {
        "columns": ["id", "name", "category", "price", "stock", "supplier"],
        "data": [
            [1,  "Laptop Pro X1",     "Electronics",  1299.99, 45,  "TechCorp"],
            [2,  "Wireless Mouse",    "Accessories",    29.99, 230, "PeriphCo"],
            [3,  "USB-C Hub",         "Accessories",    49.99, 180, "PeriphCo"],
            [4,  "Monitor 27\"",      "Electronics",   449.99, 30,  "DisplayTech"],
            [5,  "Mechanical KB",     "Accessories",    89.99, 95,  "PeriphCo"],
            [6,  "Tablet Air",        "Electronics",   699.99, 60,  "TechCorp"],
            [7,  "Headphones Pro",    "Audio",         199.99, 75,  "SoundMax"],
            [8,  "Webcam HD",         "Accessories",    79.99, 120, "PeriphCo"],
            [9,  "SSD 1TB",           "Storage",       129.99, 200, "DataStore"],
            [10, "RAM 32GB",          "Components",    149.99, 85,  "DataStore"],
        ]
    },
    "orders": {
        "columns": ["id", "customer", "product_id", "quantity", "total", "date", "status"],
        "data": [
            [1001, "Al-Fahad Corp",    3,  5,  249.95, "2024-01-15", "Delivered"],
            [1002, "Gulf Trading",     1,  2, 2599.98, "2024-01-18", "Processing"],
            [1003, "Riyadh Tech",      7,  10,1999.90, "2024-01-20", "Shipped"],
            [1004, "Dubai Solutions",  4,  3, 1349.97, "2024-01-22", "Delivered"],
            [1005, "Jeddah Systems",   2,  50,1499.50, "2024-01-25", "Processing"],
            [1006, "Amman Digital",    9,  8, 1039.92, "2024-01-28", "Delivered"],
            [1007, "Cairo Imports",    6,  4, 2799.96, "2024-02-01", "Shipped"],
            [1008, "Kuwait Trade",     5,  15,1349.85, "2024-02-03", "Processing"],
            [1009, "Beirut Tech",      10, 6,  899.94, "2024-02-05", "Delivered"],
            [1010, "Doha Solutions",   8,  20,1599.80, "2024-02-08", "Shipped"],
        ]
    },
    "departments": {
        "columns": ["id", "name", "manager", "budget", "headcount", "location"],
        "data": [
            [1, "Engineering",  "Nour Al-Ahmad",    850000, 5, "Floor 3"],
            [2, "Marketing",    "Sara Mohammed",    320000, 3, "Floor 2"],
            [3, "Finance",      "Layla Hassan",     410000, 2, "Floor 4"],
            [4, "HR",           "Fatima Al-Hassan", 280000, 2, "Floor 1"],
        ]
    },
}

AI_RESPONSES = {
    "sort":    "Sorting records by {col} — {n} rows reordered.",
    "search":  "Found {n} matching records for \"{q}\".",
    "analyze": [
        "Average salary in Engineering is $94,200 — 18% above company average.",
        "Top revenue department: Engineering with 42% of total output.",
        "Stock alert: Monitor 27\" is running low (30 units). Recommend reorder.",
        "Order fulfillment rate: 40% Delivered, 30% Shipped, 30% Processing.",
        "Headcount distribution: Engineering leads with 5 employees (42%).",
    ],
    "query": [
        "Returned 8 rows matching your natural language query.",
        "Query translated to SQL and executed in 12ms.",
        "3 tables joined — result set contains 24 columns.",
        "Aggregation complete: grouped by department with SUM on salary.",
    ]
}


class DBManagerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("QueryAI  —  Database Manager")
        self.geometry("1280x800")
        self.minsize(1100, 700)
        self.configure(fg_color=COLORS["bg_deep"])

        self.current_table = "employees"
        self.all_data = list(DEMO_TABLES[self.current_table]["data"])
        self.filtered_data = list(self.all_data)
        self.sort_col = None
        self.sort_asc = True
        self.ai_busy = False

        self._build_ui()
        self._load_table(self.current_table)

    def _build_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_main()

    def _build_sidebar(self):
        sb = ctk.CTkFrame(self, width=220, fg_color=COLORS["bg_panel"],
                          corner_radius=0, border_width=0)
        sb.grid(row=0, column=0, sticky="nsew")
        sb.grid_propagate(False)
        sb.grid_rowconfigure(10, weight=1)

        logo_f = ctk.CTkFrame(sb, fg_color="transparent")
        logo_f.grid(row=0, column=0, padx=20, pady=(24, 8), sticky="w")
        ctk.CTkLabel(logo_f, text="Query", font=("Georgia", 20, "bold"),
                     text_color=COLORS["text_1"]).pack(side="left")
        ctk.CTkLabel(logo_f, text="AI", font=("Georgia", 20, "bold"),
                     text_color=COLORS["accent"]).pack(side="left")

        ctk.CTkLabel(sb, text="DATABASE MANAGER", font=("Courier", 9),
                     text_color=COLORS["text_3"]).grid(row=1, column=0, padx=20, pady=(0, 20), sticky="w")

        ctk.CTkFrame(sb, height=1, fg_color=COLORS["border"]).grid(
            row=2, column=0, sticky="ew", padx=14, pady=(0, 16))

        ctk.CTkLabel(sb, text="TABLES", font=("Courier", 10, "bold"),
                     text_color=COLORS["text_3"]).grid(row=3, column=0, padx=20, pady=(0, 8), sticky="w")

        self.table_btns = {}
        icons = {"employees": "👤", "products": "📦", "orders": "🛒", "departments": "🏢"}
        for i, tbl in enumerate(DEMO_TABLES.keys()):
            n = len(DEMO_TABLES[tbl]["data"])
            btn = ctk.CTkButton(
                sb, text=f"  {tbl.capitalize()}",
                font=("Courier", 13), anchor="w",
                fg_color="transparent", hover_color=COLORS["bg_hover"],
                text_color=COLORS["text_2"], corner_radius=8, height=38,
                command=lambda t=tbl: self._load_table(t)
            )
            btn.grid(row=4+i, column=0, padx=10, pady=2, sticky="ew")
            self.table_btns[tbl] = btn

        ctk.CTkFrame(sb, height=1, fg_color=COLORS["border"]).grid(
            row=9, column=0, sticky="ew", padx=14, pady=16)

        stats_f = ctk.CTkFrame(sb, fg_color=COLORS["bg_card"], corner_radius=10)
        stats_f.grid(row=10, column=0, padx=12, pady=(0, 12), sticky="sew")
        ctk.CTkLabel(stats_f, text="CONNECTIONS", font=("Courier", 9),
                     text_color=COLORS["text_3"]).pack(anchor="w", padx=12, pady=(10, 4))
        dot_f = ctk.CTkFrame(stats_f, fg_color="transparent")
        dot_f.pack(anchor="w", padx=12, pady=(0, 10))
        ctk.CTkLabel(dot_f, text="●", font=("Arial", 10),
                     text_color=COLORS["green"]).pack(side="left")
        ctk.CTkLabel(dot_f, text=" demo_db  :5432", font=("Courier", 11),
                     text_color=COLORS["text_2"]).pack(side="left")

    def _build_main(self):
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        main.grid_rowconfigure(2, weight=1)
        main.grid_columnconfigure(0, weight=1)

        self._build_topbar(main)
        self._build_toolbar(main)
        self._build_content(main)
        self._build_ai_bar(main)

    def _build_topbar(self, parent):
        top = ctk.CTkFrame(parent, height=56, fg_color=COLORS["bg_panel"],
                           corner_radius=0)
        top.grid(row=0, column=0, sticky="ew")
        top.grid_propagate(False)
        top.grid_columnconfigure(1, weight=1)

        self.table_title = ctk.CTkLabel(top, text="employees",
                                        font=("Georgia", 18, "bold"),
                                        text_color=COLORS["text_1"])
        self.table_title.grid(row=0, column=0, padx=24, pady=16, sticky="w")

        self.row_count_lbl = ctk.CTkLabel(top, text="12 rows",
                                          font=("Courier", 11),
                                          text_color=COLORS["text_3"])
        self.row_count_lbl.grid(row=0, column=1, padx=8, pady=16, sticky="w")

        right_f = ctk.CTkFrame(top, fg_color="transparent")
        right_f.grid(row=0, column=2, padx=16, pady=10, sticky="e")

        for label, color in [("●  Live", COLORS["green"]), ("  Export", COLORS["text_2"])]:
            ctk.CTkLabel(right_f, text=label, font=("Courier", 11),
                         text_color=color).pack(side="left", padx=10)

    def _build_toolbar(self, parent):
        tb = ctk.CTkFrame(parent, height=52, fg_color=COLORS["bg_card"],
                          corner_radius=0)
        tb.grid(row=1, column=0, sticky="ew")
        tb.grid_propagate(False)
        tb.grid_columnconfigure(1, weight=1)

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._on_search)
        search_f = ctk.CTkFrame(tb, fg_color=COLORS["bg_panel"],
                                corner_radius=8, border_width=1,
                                border_color=COLORS["border2"])
        search_f.grid(row=0, column=0, padx=16, pady=10, sticky="w")
        ctk.CTkLabel(search_f, text="⌕", font=("Arial", 15),
                     text_color=COLORS["text_3"]).pack(side="left", padx=(10, 4))
        ctk.CTkEntry(search_f, textvariable=self.search_var,
                     placeholder_text="Search records...",
                     font=("Courier", 12), width=240,
                     fg_color="transparent", border_width=0,
                     text_color=COLORS["text_1"],
                     placeholder_text_color=COLORS["text_3"]).pack(side="left", padx=(0, 10), pady=6)

        btn_f = ctk.CTkFrame(tb, fg_color="transparent")
        btn_f.grid(row=0, column=2, padx=16, pady=10, sticky="e")

        sort_btn = ctk.CTkButton(btn_f, text="Sort", width=72, height=32,
                                 font=("Courier", 12),
                                 fg_color=COLORS["bg_panel"],
                                 hover_color=COLORS["bg_hover"],
                                 border_width=1, border_color=COLORS["border2"],
                                 text_color=COLORS["text_2"], corner_radius=8,
                                 command=self._ai_sort)
        sort_btn.pack(side="left", padx=4)

        analyze_btn = ctk.CTkButton(btn_f, text="AI Analyze", width=100, height=32,
                                    font=("Courier", 12),
                                    fg_color=COLORS["accent2"],
                                    hover_color="#6A4EE0",
                                    text_color=COLORS["text_1"], corner_radius=8,
                                    command=self._ai_analyze)
        analyze_btn.pack(side="left", padx=4)

        query_btn = ctk.CTkButton(btn_f, text="AI Query", width=90, height=32,
                                  font=("Courier", 12),
                                  fg_color=COLORS["accent"],
                                  hover_color="#3A7AE0",
                                  text_color=COLORS["text_1"], corner_radius=8,
                                  command=self._ai_query)
        query_btn.pack(side="left", padx=(4, 0))

    def _build_content(self, parent):
        content = ctk.CTkFrame(parent, fg_color="transparent")
        content.grid(row=2, column=0, sticky="nsew", padx=0, pady=0)
        content.grid_rowconfigure(0, weight=1)
        content.grid_columnconfigure(0, weight=1)

        tree_frame = ctk.CTkFrame(content, fg_color=COLORS["bg_panel"],
                                  corner_radius=0)
        tree_frame.grid(row=0, column=0, sticky="nsew")
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("DB.Treeview",
                         background=COLORS["bg_panel"],
                         fieldbackground=COLORS["bg_panel"],
                         foreground=COLORS["text_1"],
                         font=("Courier", 12),
                         rowheight=34,
                         borderwidth=0,
                         relief="flat")
        style.configure("DB.Treeview.Heading",
                         background=COLORS["bg_card"],
                         foreground=COLORS["text_2"],
                         font=("Courier", 11, "bold"),
                         borderwidth=0,
                         relief="flat",
                         padding=(12, 8))
        style.map("DB.Treeview",
                  background=[("selected", COLORS["accent_dim"])],
                  foreground=[("selected", COLORS["text_1"])])
        style.map("DB.Treeview.Heading",
                  background=[("active", COLORS["bg_hover"])])
        style.layout("DB.Treeview", [('DB.Treeview.treearea', {'sticky': 'nswe'})])

        self.tree = ttk.Treeview(tree_frame, style="DB.Treeview",
                                 show="headings", selectmode="browse")
        self.tree.grid(row=0, column=0, sticky="nsew")

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        vsb.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=vsb.set)

        self.tree.bind("<ButtonRelease-1>", self._on_row_click)

    def _build_ai_bar(self, parent):
        ai_frame = ctk.CTkFrame(parent, fg_color=COLORS["bg_card"],
                                corner_radius=0, border_width=1,
                                border_color=COLORS["border"])
        ai_frame.grid(row=3, column=0, sticky="ew")
        ai_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(ai_frame, text="AI",
                     font=("Courier", 10, "bold"),
                     text_color=COLORS["accent"],
                     fg_color=COLORS["accent_dim"],
                     corner_radius=4, width=28, height=20).grid(
            row=0, column=0, padx=(14, 8), pady=10)

        self.ai_status = ctk.CTkLabel(ai_frame,
                                      text="Ready — ask me anything about your data.",
                                      font=("Courier", 12),
                                      text_color=COLORS["text_2"],
                                      anchor="w")
        self.ai_status.grid(row=0, column=1, sticky="ew", pady=10)

        self.ai_input = ctk.CTkEntry(ai_frame,
                                     placeholder_text="Ask AI about this table...",
                                     font=("Courier", 12), width=300, height=32,
                                     fg_color=COLORS["bg_panel"],
                                     border_color=COLORS["border2"],
                                     text_color=COLORS["text_1"],
                                     placeholder_text_color=COLORS["text_3"],
                                     corner_radius=8)
        self.ai_input.grid(row=0, column=2, padx=8, pady=10)
        self.ai_input.bind("<Return>", self._ai_natural_query)

        ctk.CTkButton(ai_frame, text="Ask", width=60, height=32,
                      font=("Courier", 12),
                      fg_color=COLORS["accent"],
                      hover_color="#3A7AE0",
                      text_color="white", corner_radius=8,
                      command=self._ai_natural_query).grid(
            row=0, column=3, padx=(0, 14), pady=10)

    def _load_table(self, table_name):
        self.current_table = table_name
        tbl = DEMO_TABLES[table_name]
        self.all_data = list(tbl["data"])
        self.filtered_data = list(self.all_data)
        self.sort_col = None

        for btn_name, btn in self.table_btns.items():
            if btn_name == table_name:
                btn.configure(fg_color=COLORS["accent_dim"],
                              text_color=COLORS["accent"])
            else:
                btn.configure(fg_color="transparent",
                              text_color=COLORS["text_2"])

        self.table_title.configure(text=table_name)
        cols = tbl["columns"]
        self.tree.configure(columns=cols)

        for col in cols:
            self.tree.heading(col, text=col.upper(),
                              command=lambda c=col: self._sort_by(c))
            w = 140 if col in ("name", "customer", "manager", "supplier") else 100
            self.tree.column(col, width=w, minwidth=60, anchor="w")

        self._refresh_tree()
        self._update_row_count()
        self._set_ai_status(f"Table '{table_name}' loaded — {len(self.all_data)} rows ready.")

    def _refresh_tree(self):
        self.tree.delete(*self.tree.get_children())
        for i, row in enumerate(self.filtered_data):
            tag = "even" if i % 2 == 0 else "odd"
            self.tree.insert("", "end", values=row, tags=(tag,))
        self.tree.tag_configure("even", background=COLORS["bg_panel"])
        self.tree.tag_configure("odd",  background=COLORS["bg_card"])

    def _update_row_count(self):
        total = len(self.all_data)
        shown = len(self.filtered_data)
        if shown < total:
            self.row_count_lbl.configure(
                text=f"{shown} of {total} rows",
                text_color=COLORS["amber"])
        else:
            self.row_count_lbl.configure(
                text=f"{total} rows",
                text_color=COLORS["text_3"])

    def _on_search(self, *_):
        q = self.search_var.get().lower().strip()
        if not q:
            self.filtered_data = list(self.all_data)
        else:
            self.filtered_data = [
                row for row in self.all_data
                if any(q in str(v).lower() for v in row)
            ]
        self._refresh_tree()
        self._update_row_count()
        if q:
            self._set_ai_status(
                AI_RESPONSES["search"].format(n=len(self.filtered_data), q=q))

    def _sort_by(self, col):
        cols = DEMO_TABLES[self.current_table]["columns"]
        idx = cols.index(col)
        asc = not self.sort_asc if self.sort_col == col else True
        self.sort_col = col
        self.sort_asc = asc
        try:
            self.filtered_data.sort(key=lambda r: r[idx], reverse=not asc)
        except TypeError:
            self.filtered_data.sort(key=lambda r: str(r[idx]), reverse=not asc)
        self._refresh_tree()
        arrow = "↑" if asc else "↓"
        self._set_ai_status(
            AI_RESPONSES["sort"].format(col=col, n=len(self.filtered_data)) + f"  {arrow}")

    def _on_row_click(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        vals = self.tree.item(sel[0], "values")
        cols = DEMO_TABLES[self.current_table]["columns"]
        summary = "  |  ".join(f"{c}: {v}" for c, v in zip(cols[:4], vals[:4]))
        self._set_ai_status(f"Selected → {summary}")

    def _ai_sort(self):
        cols = DEMO_TABLES[self.current_table]["columns"]
        col = random.choice(cols[1:])
        self._sort_by(col)

    def _ai_analyze(self):
        self._set_ai_status("Analyzing table...", thinking=True)
        def run():
            time.sleep(1.2)
            msg = random.choice(AI_RESPONSES["analyze"])
            self.after(0, lambda: self._set_ai_status(msg))
        threading.Thread(target=run, daemon=True).start()

    def _ai_query(self):
        self._set_ai_status("Executing AI query...", thinking=True)
        def run():
            time.sleep(1.5)
            msg = random.choice(AI_RESPONSES["query"])
            sample = random.sample(self.all_data, min(len(self.all_data), random.randint(3, 8)))
            self.after(0, lambda: self._apply_query_result(sample, msg))
        threading.Thread(target=run, daemon=True).start()

    def _apply_query_result(self, sample, msg):
        self.filtered_data = sample
        self._refresh_tree()
        self._update_row_count()
        self._set_ai_status(msg)

    def _ai_natural_query(self, *_):
        q = self.ai_input.get().strip()
        if not q:
            return
        self.ai_input.delete(0, "end")
        self._set_ai_status(f'Processing: "{q}"', thinking=True)
        def run():
            time.sleep(1.4)
            responses = [
                f'Found 6 records matching "{q}" — sorted by relevance.',
                f'AI translated your query to SQL and returned 4 rows.',
                f'Insight: Based on "{q}", top 3 entries highlighted.',
                f'Query complete — 9 matching rows for "{q}".',
            ]
            msg = random.choice(responses)
            sample = random.sample(self.all_data, min(len(self.all_data), random.randint(4, 9)))
            self.after(0, lambda: self._apply_query_result(sample, msg))
        threading.Thread(target=run, daemon=True).start()

    def _set_ai_status(self, text, thinking=False):
        color = COLORS["amber"] if thinking else COLORS["text_2"]
        prefix = "⟳  " if thinking else "✦  "
        self.ai_status.configure(text=prefix + text, text_color=color)


if __name__ == "__main__":
    app = DBManagerApp()
    app.mainloop()
