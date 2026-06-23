# -*- coding: utf-8 -*-
"""
برنامج «تجارتي» — نظام إدارة المبيعات والمخزون المتكامل.
نقطة تشغيل البرنامج.

التشغيل:  python main.py
بيانات الدخول التجريبية:  admin / admin   أو   cashier / 1234
"""
import customtkinter as ctk

from app.config import COLORS
from app.database import Database
from app.login import LoginWindow
from app.main_window import MainWindow


def main():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    db = Database()

    def after_login(user):
        app = MainWindow(db, user)
        app.mainloop()

    LoginWindow(db, after_login).mainloop()


if __name__ == "__main__":
    main()
