"""
Oltremare — Главное окно
"""
import tkinter as tk
from tkinter import messagebox
from src.views.guest_views import GuestHomeView
from src.utils.theme import *

ROLE_LABELS = {
    'admin':'Администратор','waiter':'Официант','kitchen':'Кухня','client':'Клиент','guest':'Гость'
}
NAV_STRUCTURE = {
    'admin':  [('Схема зала','🪑','tables'),('Брони','📅','reservations'),
               ('Смены','👥','shifts'),('Заказы', '📋', 'admin_orders'),
               ('Меню / склад','🍽️','menu'),('Акции','🏷️','promotions'),
               ('Пользователи','👤','users'),('Статистика','📊','stats')],
    'waiter': [('Моя смена','⏱️','shift'),('Схема зала','🪑','layout'),
               ('Заказы','📋','orders'),('Брони','📅','reservations')],
    'kitchen':[('Заказы','🍳','kitchen_orders'),('Склад / стоп','📦','stock')],
    'client': [
        ('Главная', '🏠', 'client_home'),
        ('Схема зала','🪑','table_layout'),
        ('Мои заказы','📋','my_orders'),   # ← ДОБАВЛЯЕМ
        ('Мои брони','📅','my_reservations'),
        ('Меню','🍽️','menu_view'),
    ],
    'guest':  [
        ('Главная', '🏠', 'home'),
        ('Меню', '🍽️', 'menu_view'),
    ],
}


class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Oltremare — Управление рестораном")
        self.geometry("1280x800")
        self.minsize(1100, 700)
        self.configure(bg=BG_DARK)
        configure_ttk_styles()
        self.current_user = None
        self._pages = {}
        self._nav_buttons = {}
        self._build_skeleton()
        self._show_login()

    def _build_skeleton(self):
        self.sidebar = OFrame(self, bg=BG_PANEL, width=SIDEBAR_W)
        self.sidebar.pack_propagate(False)
        self.content_area = OFrame(self, bg=BG_DARK)
        self.content_area.pack(side='left', fill='both', expand=True)

        logo_frame = OFrame(self.sidebar, bg=BG_PANEL)
        logo_frame.pack(fill='x')
        tk.Label(logo_frame, text="Oltremare", font=(FONT_FAMILY, 17, "bold italic"),
                 fg=GOLD, bg=BG_PANEL, pady=22).pack()
        Divider(logo_frame).pack(fill='x')

        self.nav_frame = OFrame(self.sidebar, bg=BG_PANEL)
        self.nav_frame.pack(fill='both', expand=True, pady=6)

        self.bottom_frame = OFrame(self.sidebar, bg=BG_PANEL)
        self.bottom_frame.pack(fill='x', side='bottom')
        Divider(self.bottom_frame).pack(fill='x')
        self.lbl_user = tk.Label(self.bottom_frame, text="",
                                  font=FONT_TINY, fg=MUTED, bg=BG_PANEL, pady=6)
        self.lbl_user.pack()
        OButton(self.bottom_frame, "Выйти", command=self._logout,
                variant='ghost').pack(fill='x', padx=8, pady=8)

    def _show_login(self):
        from src.views.login_view import LoginWindow
        self.withdraw()
        LoginWindow(self, on_success=self._on_login, on_guest=self._on_guest)

    def _on_login(self, user: dict):
        self.current_user = user
        self.deiconify()
        self.sidebar.pack(side='left', fill='y')
        self._build_nav()
        self._build_pages()

    def _on_guest(self):
        self.current_user = {'id': None, 'full_name': 'Гость', 'role': 'guest'}
        self.deiconify()
        self.sidebar.pack(side='left', fill='y')
        self._build_nav()
        self._build_pages()

    def _build_nav(self):
        for w in self.nav_frame.winfo_children():
            w.destroy()
        role = self.current_user['role']
        name = self.current_user['full_name']
        self.lbl_user.configure(
            text=f"{name}\n({ROLE_LABELS.get(role, role)})")
        self._nav_buttons = {}
        for (label, icon, page_key) in NAV_STRUCTURE.get(role, []):
            btn = _NavButton(self.nav_frame, f" {icon}  {label}",
                             command=lambda k=page_key: self._show_page(k))
            btn.pack(fill='x', padx=8, pady=2)
            self._nav_buttons[page_key] = btn

    def _build_pages(self):
        for w in self.content_area.winfo_children():
            w.destroy()
        self._pages = {}
        role = self.current_user['role']

        if role == 'admin':
            from src.views.admin_views import (
                TablesView, ReservationsView, ShiftsView,
                MenuView, UsersView, StatisticsView, PromotionsView, AdminOrdersView)
            self._pages = {
                'tables': TablesView(self.content_area, self.current_user),
                'reservations': ReservationsView(self.content_area, self.current_user),
                'shifts': ShiftsView(self.content_area, self.current_user),
                'admin_orders': AdminOrdersView(self.content_area, self.current_user),  # ДОБАВЛЯЕМ
                'menu': MenuView(self.content_area, self.current_user),
                'promotions': PromotionsView(self.content_area, self.current_user),
                'users': UsersView(self.content_area, self.current_user),
                'stats': StatisticsView(self.content_area, self.current_user),
            }
        elif role == 'waiter':
            from src.views.waiter_views import (
                WaiterShiftView, TablesLayoutView, OrdersView, WaiterReservationsView)
            self._pages = {
                'shift': WaiterShiftView(self.content_area, self.current_user),
                'layout': TablesLayoutView(self.content_area, self.current_user),
                'orders': OrdersView(self.content_area, self.current_user),
                'reservations': WaiterReservationsView(self.content_area, self.current_user),
            }
        elif role == 'kitchen':
            from src.views.kitchen_views import KitchenOrdersView, StockView
            self._pages = {
                'kitchen_orders': KitchenOrdersView(self.content_area, self.current_user),
                'stock': StockView(self.content_area, self.current_user),
            }
        elif role == 'client':
            from src.views.client_views import (
                ClientHomeView, ClientTableLayoutView, ClientReservationView, ClientMenuView, ClientOrdersView)
            self._pages = {
                'client_home': ClientHomeView(self.content_area, self.current_user),  # ← своя главная
                'table_layout': ClientTableLayoutView(self.content_area, self.current_user),
                'my_reservations': ClientReservationView(self.content_area, self.current_user),
                'my_orders': ClientOrdersView(self.content_area, self.current_user),
                'menu_view': ClientMenuView(self.content_area, self.current_user),
            }
        elif role == 'guest':
            from src.views.guest_views import GuestHomeView
            from src.views.client_views import ClientMenuView
            self._pages = {
                'home': GuestHomeView(self.content_area, self.current_user),  # ← приветственная
                'menu_view': ClientMenuView(self.content_area, self.current_user),
            }

        first = next(iter(self._pages), None)
        if first:
            self._show_page(first)

    def _show_page(self, key: str):
        for page in self._pages.values():
            page.pack_forget()
        if key in self._pages:
            self._pages[key].pack(fill='both', expand=True)
            if hasattr(self._pages[key], 'refresh'):
                self._pages[key].refresh()
        for k, btn in self._nav_buttons.items():
            btn.set_active(k == key)

    def _logout(self):
        if messagebox.askyesno("Выход", "Выйти из системы?", parent=self):
            self.current_user = None
            self.sidebar.pack_forget()
            for w in self.content_area.winfo_children():
                w.destroy()
            self._pages = {}
            self._show_login()


class _NavButton(tk.Button):
    def __init__(self, master, text, command=None, **kw):
        super().__init__(master, text=text, command=command,
                         bg=BG_PANEL, fg=GOLD,
                         font=FONT_NAV, relief='flat', anchor='w',
                         padx=16, pady=12, cursor='hand2', borderwidth=0,
                         activebackground=BG_HOVER, activeforeground=GOLD, **kw)
        self._active = False
        self.bind('<Enter>', lambda e: self._hover(True))
        self.bind('<Leave>', lambda e: self._hover(False))

    def _hover(self, on):
        if not self._active:
            self.configure(bg=BG_HOVER if on else BG_PANEL)

    def set_active(self, active: bool):
        self._active = active
        if active:
            self.configure(bg=GOLD, fg=BG_DARK, font=(FONT_SANS, 14, 'bold'))
        else:
            self.configure(bg=BG_PANEL, fg=GOLD, font=FONT_NAV)