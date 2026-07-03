"""
Oltremare Restaurant Management System
Точка входа в приложение
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox

# Добавляем корень проекта в PATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    # Инициализация БД
    try:
        from src.database.db import init_database
        print("Инициализация базы данных...")
        init_database()
        print("База данных готова.")
    except Exception as e:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Ошибка подключения к БД",
            f"Не удалось подключиться к MySQL/MariaDB:\n\n{e}\n\n"
            "Проверьте:\n"
            "1. MySQL/MariaDB запущен\n"
            "2. Настройки в src/database/db.py (host, user, password)"
        )
        root.destroy()
        sys.exit(1)

    # Запуск главного окна
    from src.views.main_window import MainWindow
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
