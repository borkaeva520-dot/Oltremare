"""
Oltremare — Виды клиента и гостя 
"""
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox
from datetime import date
from src.utils.theme import apply_tree_grid

from src.utils.theme import *
from src.models.models import (
    TableModel, ReservationModel, DishModel, OrderModel
)
from src.views.admin_views import BasePage, ReservationDialog
from src.views.login_view import show_register


# ── Схема зала (клиент / гость) ──────────────────────────────────────────────
class ClientTableLayoutView(BasePage):
    def _build(self):
        self._page_header("Схема зала", "доступность столиков")

        # Кнопка "На главную"
        back_frame = OFrame(self, bg=BG_DARK)
        back_frame.pack(fill='x', padx=PAD_LG, pady=(0, PAD))
        OButton(back_frame, "🏠 На главную", 
                command=self._go_home,
                variant='ghost').pack(side='left')

        ctrl = OFrame(self, bg=BG_DARK)
        ctrl.pack(fill='x', padx=PAD_LG, pady=PAD)
        OButton(ctrl, "Обновить", command=self.refresh,
                variant='secondary').pack(side='left', padx=(0, 8))

        if self.user.get('role') == 'client':
            OButton(ctrl, "Забронировать стол",
                    command=self._book_table, variant='gold').pack(side='left', padx=(0, 8))
            OButton(ctrl, "Создать заказ (на месте)",
                    command=self._create_order, variant='primary').pack(side='left')
        elif self.user.get('role') == 'guest':
            OButton(ctrl, "Войти / Зарегистрироваться для бронирования",
                    command=self._prompt_register, variant='gold').pack(side='left', padx=(0, 8))

        # Легенда
        leg = OFrame(self, bg=BG_DARK)
        leg.pack(fill='x', padx=PAD_LG, pady=(0, PAD))
        for lbl, color in [("Свободен", SUCCESS), ("Забронирован", WARNING), ("Занят", ERROR)]:
            f = OFrame(leg, bg=BG_DARK); f.pack(side='left', padx=8)
            tk.Frame(f, bg=color, width=14, height=14).pack(side='left', padx=4)
            OLabel(f, lbl, font=FONT_SMALL, bg=BG_DARK).pack(side='left')

        self.canvas_frame = OCard(self)
        self.canvas_frame.pack(fill='both', expand=True, padx=PAD_LG, pady=(0, PAD_LG))
        self.canvas = tk.Canvas(self.canvas_frame, bg=BG_CARD, highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)
        self.canvas.bind('<Configure>', lambda e: self.refresh())
        self.canvas.bind('<Button-1>', self._on_click)
        self._rects = []
        self._tables_data = []
        self._selected_table_id = None

    def _go_home(self):
        root = self.winfo_toplevel()
        if hasattr(root, '_show_page'):
            if self.user.get('role') == 'guest':
                root._show_page('home')
            else:
                root._show_page('client_home')

    def refresh(self):
        self._tables_data = TableModel.get_layout_status()
        self._draw()

    def _draw(self):
        c = self.canvas
        c.delete('all')
        w = c.winfo_width() or 700
        cols = 5; pad = 20
        cell_w = (w - pad * 2) // cols
        cell_h = 115
        self._rects = []
        for i, t in enumerate(self._tables_data):
            col = i % cols; row = i // cols
            x1 = pad + col * cell_w + 8; y1 = pad + row * cell_h + 8
            x2 = x1 + cell_w - 16;       y2 = y1 + cell_h - 16
            s = t.get('current_status', 'free')
            color = {'free': SUCCESS, 'reserved': WARNING,
                     'occupied': ERROR, 'unavailable': MUTED}.get(s, MUTED)
            is_sel = (self._selected_table_id == t['id'])
            c.create_rectangle(x1, y1, x2, y2, fill=BG_CARD,
                               outline=GOLD if is_sel else color,
                               width=3 if is_sel else 2)
            cx = (x1 + x2) // 2
            c.create_text(cx, y1 + 20, text=f"Стол №{t['number']}", font=FONT_H2, fill=GOLD)
            c.create_text(cx, y1 + 42, text=STATUS_LABELS.get(s, s), font=FONT_SMALL, fill=color)
            c.create_text(cx, y1 + 60, text=f"{t['capacity']} мест", font=FONT_TINY, fill=MUTED)
            c.create_text(cx, y1 + 76, text=t.get('location', ''), font=FONT_TINY, fill=MUTED)
            self._rects.append({'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2, 'table': t})

    def _on_click(self, event):
        for r in self._rects:
            if r['x1'] <= event.x <= r['x2'] and r['y1'] <= event.y <= r['y2']:
                self._selected_table_id = r['table']['id']
                self._draw()
                break

    def _book_table(self):
        ReservationDialog(self, user=self.user, on_save=self.refresh)

    def _create_order(self):
        if not self._selected_table_id:
            return messagebox.showwarning("Выбор", "Кликните на столик на схеме", parent=self)
        ClientOrderDialog(self, table_id=self._selected_table_id,
                          client_id=self.user['id'], on_save=self.refresh)

    def _prompt_register(self):
        if messagebox.askyesno("Регистрация",
                "Для бронирования и заказов нужен аккаунт.\n\n"
                "Зарегистрироваться сейчас?",
                parent=self):
            from src.views.login_view import show_register
            show_register(self.winfo_toplevel(), on_success=self._on_registered)

    def _on_registered(self, user):
        show_toast(self, f"Добро пожаловать, {user['full_name']}!", 'success', 3000)
        self.winfo_toplevel()._on_login(user)


# ── Мои брони (клиент) ───────────────────────────────────────────────────────
class ClientReservationView(BasePage):
    def _build(self):
        self._page_header("Мои брони")

        # Кнопка "На главную"
        back_frame = OFrame(self, bg=BG_DARK)
        back_frame.pack(fill='x', padx=PAD_LG, pady=(0, PAD))
        OButton(back_frame, "🏠 На главную", 
                command=self._go_home,
                variant='ghost').pack(side='left')

        tb = OFrame(self, bg=BG_DARK)
        tb.pack(fill='x', padx=PAD_LG, pady=PAD)
        OButton(tb, "+ Забронировать", command=self._new,
                variant='gold').pack(side='left', padx=(0, 8))
        OButton(tb, "Создать заказ по брони", command=self._order_from_res,  
            variant='primary').pack(side='left', padx=(0, 8))
        OButton(tb, "Отменить бронь", command=self._cancel,
                variant='danger').pack(side='left', padx=(0, 8))
        OButton(tb, "Мои заказы по брони", command=self._view_orders,
                variant='secondary').pack(side='left')

        cols = ('id', 'date', 'time_range', 'guests', 'tables', 'status', 'notes')
        headers = ('№', 'Дата', 'Время', 'Гостей', 'Столики', 'Статус', 'Примечание')
        widths = (50, 100, 130, 70, 80, 100, 200)
        frm, self.tree = self._make_tree(self, cols)
        frm.pack(fill='both', expand=True, padx=PAD_LG, pady=(0, PAD_LG))
        for col, hdr, w in zip(cols, headers, widths):
            self.tree.heading(col, text=hdr)
            self.tree.column(col, width=w)
        self.refresh()

    def _order_from_res(self):
        sel = self.tree.selection()
        if not sel:
            return messagebox.showwarning("Выбор", "Выберите бронь", parent=self)
        rid = int(sel[0])
        uid = self.user['id']
        
        # Находим бронь
        reservations = ReservationModel.get_by_client(uid)
        res = next((r for r in reservations if r['id'] == rid), None)
        if not res:
            return
        
        if res['status'] != 'active':
            return messagebox.showwarning("Бронь", "Бронь неактивна", parent=self)
        
        table_ids_str = res.get('table_ids', '')
        if not table_ids_str:
            return messagebox.showwarning("Бронь", "У брони нет столиков", parent=self)
        
        table_id = int(str(table_ids_str).split(',')[0])
        ClientOrderDialog(self, table_id=table_id, client_id=uid,
                        reservation_id=rid, on_save=self.refresh)

    def _go_home(self):
        root = self.winfo_toplevel()
        if hasattr(root, '_show_page'):
            root._show_page('client_home')

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        uid = self.user.get('id')
        if not uid:
            return
        for r in ReservationModel.get_by_client(uid):
            ts = str(r['reservation_time'])[:5]
            te = str(r['end_time'])[:5] if r.get('end_time') else '—'
            self.tree.insert('', 'end', iid=str(r['id']), values=(
                r['id'], str(r['reservation_date']),
                f"{ts} – {te}",
                r['guests_count'], r.get('table_numbers', ''),
                STATUS_LABELS.get(r['status'], r['status']),
                r.get('notes', '')))

    def _new(self):
        ReservationDialog(self, user=self.user, on_save=self.refresh)

    def _cancel(self):
        sel = self.tree.selection()
        if not sel:
            return messagebox.showwarning("Выбор", "Выберите бронь", parent=self)
        rid = int(sel[0])
        if messagebox.askyesno("Отмена", f"Отменить бронь №{rid}?", parent=self):
            ReservationModel.cancel(rid)
            self.refresh()
            show_toast(self, "Бронь отменена", 'info')

    def _view_orders(self):
        sel = self.tree.selection()
        if not sel:
            return messagebox.showwarning("Выбор", "Выберите бронь", parent=self)
        rid = int(sel[0])
        orders = OrderModel.get_by_reservation(rid)
        if not orders:
            return messagebox.showinfo("Заказы",
                f"По брони №{rid} заказов нет.\n"
                "Заказ можно создать через «Схема зала» → «Создать заказ».", parent=self)
        ClientOrdersListDialog(self, reservation_id=rid, orders=orders)


# ── Просмотр заказов клиента по брони ────────────────────────────────────────
class ClientOrdersListDialog(tk.Toplevel):
    def __init__(self, master, reservation_id, orders):
        super().__init__(master)
        self.title(f"Заказы по брони №{reservation_id}")
        self.configure(bg=BG_DARK)
        self.geometry("720x520")
        self.grab_set()
        self._build(reservation_id, orders)

    # Reservation functionality

    def _build(self, reservation_id, orders):
        OLabel(self, f"Заказы по брони №{reservation_id}",
               color=GOLD, font=FONT_H1, bg=BG_DARK).pack(pady=PAD_LG)
        Divider(self).pack(fill='x', padx=PAD_LG)

        nb = ttk.Notebook(self, style='Oltremare.TNotebook')
        nb.pack(fill='both', expand=True, padx=PAD_LG, pady=PAD)

        for o in orders:
            frame = OFrame(nb, bg=BG_DARK)
            status = STATUS_LABELS.get(o['status'], o['status'])
            nb.add(frame, text=f"  Заказ №{o['id']} ({status})  ")

            info = OCard(frame)
            info.pack(fill='x', padx=PAD, pady=PAD)
            tk.Label(info,
                     text=f"Стол №{o['table_number']}  |  {o['waiter_name']}  |  {status}",
                     bg=BG_CARD, fg=GOLD, font=FONT_H2, pady=8).pack()

            detail = OrderModel.get_order_detail(o['id'])
            cols = ('name', 'qty', 'price', 'total')
            tree = ttk.Treeview(frame, columns=cols, show='headings',
                                style='Oltremare.Treeview', height=9)
            for col, hdr, w in zip(cols, ('Блюдо', 'Кол-во', 'Цена', 'Итого'), (220, 70, 110, 110)):
                tree.heading(col, text=hdr)
                tree.column(col, width=w)
            apply_tree_grid(tree)
            tree.pack(fill='both', expand=True, padx=PAD)

            total = 0
            for item in detail.get('items', []):
                line = item['quantity'] * float(item['final_price'])
                total += line
                tree.insert('', 'end', values=(
                    item['dish_name'], item['quantity'],
                    f"{item['final_price']:.2f} ₽", f"{line:.2f} ₽"))
            OLabel(frame, f"Итого по заказу: {total:.2f} ₽",
                   color=GOLD, font=FONT_H2, bg=BG_DARK).pack(pady=8)

        OButton(self, "Закрыть", command=self.destroy, variant='ghost').pack(pady=PAD)

# ── Просмотр заказа (клиент) ──────────────────────────────────────────────
class ClientOrderDetailDialog(tk.Toplevel):
    def __init__(self, master, order):
        super().__init__(master)
        self.order = order
        self.title(f"Заказ №{order['id']} — Детали")
        self.configure(bg=BG_DARK)
        self.geometry("600x500")
        self.grab_set()
        self._build()

    def _build(self):
        OLabel(self, f"Заказ №{self.order['id']}", color=GOLD, font=FONT_H1, bg=BG_DARK).pack(pady=PAD_LG)
        Divider(self).pack(fill='x', padx=PAD_LG)

        info_frame = OFrame(self, bg=BG_DARK)
        info_frame.pack(fill='x', padx=PAD_LG, pady=10)

        OLabel(info_frame, f"Стол: №{self.order['table_number']}", color=CREAM, font=FONT_BODY, bg=BG_DARK).pack(anchor='w')
        OLabel(info_frame, f"Статус: {STATUS_LABELS.get(self.order['status'], self.order['status'])}", 
               color=STATUS_COLORS.get(self.order['status'], CREAM), font=FONT_BODY, bg=BG_DARK).pack(anchor='w')
        OLabel(info_frame, f"Официант: {self.order['waiter_name']}", color=MUTED, font=FONT_SMALL, bg=BG_DARK).pack(anchor='w')

        placed = str(self.order.get('placed_at', ''))[:16] if self.order.get('placed_at') else '—'
        OLabel(info_frame, f"Оформлен: {placed}", color=MUTED, font=FONT_SMALL, bg=BG_DARK).pack(anchor='w')

        Divider(self).pack(fill='x', padx=PAD_LG, pady=10)

        OLabel(self, "Состав заказа:", color=GOLD, font=FONT_H2, bg=BG_DARK).pack(anchor='w', padx=PAD_LG)

        cols = ('name', 'qty', 'price', 'total')
        headers = ('Блюдо', 'Кол-во', 'Цена', 'Итого')
        widths = (230, 70, 110, 110)
        frm = OFrame(self, bg=BG_DARK)
        frm.pack(fill='both', expand=True, padx=PAD_LG, pady=(0, PAD))

        tree = ttk.Treeview(frm, columns=cols, show='headings', style='Oltremare.Treeview')
        for col, hdr, w in zip(cols, headers, widths):
            tree.heading(col, text=hdr)
            tree.column(col, width=w)

        vsb = ttk.Scrollbar(frm, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side='right', fill='y')
        tree.pack(fill='both', expand=True)

        total = 0
        for item in self.order.get('items', []):
            line = item['quantity'] * float(item['final_price'])
            total += line
            tree.insert('', 'end', values=(
                item['dish_name'],
                item['quantity'],
                f"{item['final_price']:.2f} ₽",
                f"{line:.2f} ₽"
            ))

        total_frame = OFrame(self, bg=BG_DARK)
        total_frame.pack(fill='x', padx=PAD_LG, pady=10)
        OLabel(total_frame, f"ИТОГО: {total:.2f} ₽", color=GOLD, font=FONT_H1, bg=BG_DARK).pack(side='right')

        btns = OFrame(self, bg=BG_DARK)
        btns.pack(fill='x', padx=PAD_LG, pady=PAD)
        OButton(btns, "Закрыть", command=self.destroy, variant='ghost').pack(side='right')


# ── Самостоятельный заказ клиента ────────────────────────────────────────────
class ClientOrderDialog(tk.Toplevel):
    """Клиент делает заказ на месте (от имени своего аккаунта)."""
    def __init__(self, master, table_id, client_id, reservation_id=None, on_save=None):
        super().__init__(master)
        self.table_id = table_id
        self.client_id = client_id
        self.reservation_id = reservation_id
        self.on_save = on_save
        self.order_id = None
        self.title(f"Заказ — Стол №{table_id}")
        self.configure(bg=BG_DARK)
        self.geometry("720x620")
        self.grab_set()
        self._build()
        self._create_order()

    def _build(self):
        top = OFrame(self, bg=BG_DARK)
        top.pack(fill='both', expand=True, padx=PAD, pady=PAD)

        # ── Левая панель: меню ──
        left = OCard(top)
        left.pack(side='left', fill='both', expand=True, padx=(0, 8))
        OLabel(left, "Меню", color=GOLD, font=FONT_H2, bg=BG_CARD).pack(pady=8)
        Divider(left).pack(fill='x')
        self.dish_tree = ttk.Treeview(
            left, columns=('id', 'cat', 'name', 'price', 'disc'),
            show='headings', style='Oltremare.Treeview', height=16)
        for col, hdr, w in zip(
                ('id', 'cat', 'name', 'price', 'disc'),
                ('№', 'Кат.', 'Блюдо', 'Цена', 'Скидка'),
                (40, 90, 170, 90, 70)):
            self.dish_tree.heading(col, text=hdr)
            self.dish_tree.column(col, width=w)
        apply_tree_grid(self.dish_tree)
        self.dish_tree.pack(fill='both', expand=True, padx=8, pady=8)
        self._load_dishes()

        # ── Правая панель: состав заказа ──
        right = OCard(top)
        right.pack(side='left', fill='both', expand=True)
        OLabel(right, "Мой заказ", color=GOLD, font=FONT_H2, bg=BG_CARD).pack(pady=8)
        Divider(right).pack(fill='x')

        qty_row = OFrame(right, bg=BG_CARD)
        qty_row.pack(fill='x', padx=8, pady=8)
        OLabel(qty_row, "Кол-во:", color=MUTED, font=FONT_SMALL, bg=BG_CARD).pack(side='left')
        self.ent_qty = OEntry(qty_row, width=5)
        self.ent_qty.insert(0, '1')
        self.ent_qty.pack(side='left', padx=8, ipady=4)
        OButton(qty_row, "+ Добавить", command=self._add, variant='gold').pack(side='left')

        self.order_tree = ttk.Treeview(
            right, columns=('id', 'name', 'qty', 'total'),
            show='headings', style='Oltremare.Treeview', height=10)
        for col, hdr, w in zip(
                ('id', 'name', 'qty', 'total'),
                ('№', 'Блюдо', 'Кол-во', 'Итого'),
                (40, 170, 70, 100)):
            self.order_tree.heading(col, text=hdr)
            self.order_tree.column(col, width=w)
        self.order_tree.pack(fill='both', expand=True, padx=8, pady=4)
        OButton(right, "✕  Удалить позицию", command=self._remove,
                variant='danger').pack(padx=8, pady=4, fill='x')
        self.lbl_total = OLabel(right, "Итого: 0.00 ₽",
                                 color=GOLD, font=FONT_H1, bg=BG_CARD)
        self.lbl_total.pack(pady=8)

        btns = OFrame(self, bg=BG_DARK)
        btns.pack(fill='x', padx=PAD, pady=PAD)
        OButton(btns, "✔  Отправить заказ", command=self._place,
                variant='gold').pack(side='left', padx=(0, 8))
        OButton(btns, "Закрыть", command=self.destroy, variant='ghost').pack(side='left')

    def _load_dishes(self):
        self.dish_tree.delete(*self.dish_tree.get_children())
        for d in DishModel.get_all(available_only=True):
            disc_val = d.get('discount', 0) or 0
            disc = f"{float(disc_val):.0f}%" if float(disc_val) > 0 else "—"
            self.dish_tree.insert('', 'end', iid=str(d['id']), values=(
                d['id'], d['category_name'], d['name'],
                f"{d['price']:.2f} ₽", disc))

    def _create_order(self):
        try:
            result = OrderModel.create(self.table_id, reservation_id=self.reservation_id, client_id=self.client_id)
            if isinstance(result, dict):
                if result.get('action') == 'confirm':
                    if messagebox.askyesno("Забронированный стол", result['message'], parent=self):
                        self.order_id = OrderModel.create_forced(
                            self.table_id, waiter_id=None, reservation_id=self.reservation_id)
                        self.title(f"Заказ №{self.order_id} — Стол №{self.table_id}")
                    else:
                        self.destroy()
                    return
                elif result.get('action') == 'created':
                    self.order_id = result['order_id']
                    self.title(f"Заказ №{self.order_id} — Стол №{self.table_id}")
                else:
                    raise ValueError("Не удалось создать заказ")
            else:
                self.order_id = result
                self.title(f"Заказ №{self.order_id} — Стол №{self.table_id}")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e), parent=self)
            self.destroy()

    def _add(self):
        sel = self.dish_tree.selection()
        if not sel:
            return messagebox.showwarning("Выбор", "Выберите блюдо", parent=self)
        try:
            qty = int(self.ent_qty.get())
            if qty <= 0:
                raise ValueError("Количество должно быть > 0")
            msg = OrderModel.add_item(self.order_id, int(sel[0]), qty)
            show_toast(self, msg, 'success', 2500)
            self._refresh()
            self._load_dishes()
        except Exception as e:
            messagebox.showerror("Ошибка", str(e), parent=self)

    def _remove(self):
        sel = self.order_tree.selection()
        if not sel:
            return
        try:
            msg = OrderModel.remove_item(int(sel[0]))
            show_toast(self, msg, 'info', 2500)
            self._refresh()
            self._load_dishes()
        except Exception as e:
            messagebox.showerror("Ошибка", str(e), parent=self)

    def _refresh(self):
        self.order_tree.delete(*self.order_tree.get_children())
        if not self.order_id:
            return
        order = OrderModel.get_order_detail(self.order_id)
        total = 0
        for item in order.get('items', []):
            line = item['quantity'] * float(item['final_price'])
            total += line
            self.order_tree.insert('', 'end', iid=str(item['id']), values=(
                item['id'], item['dish_name'], item['quantity'], f"{line:.2f} ₽"))
        self.lbl_total.configure(text=f"Итого: {total:.2f} ₽")

    def _place(self):
        try:
            OrderModel.place_order(self.order_id)
            messagebox.showinfo(
                "Готово",
                f"Заказ №{self.order_id} отправлен!\n"
                "Официант принесёт ваш заказ. Спасибо!", parent=self)
            if self.on_save:
                self.on_save()
            self.destroy()
        except ValueError as e:
            messagebox.showerror("Ошибка", str(e), parent=self)


# ── Главная страница для клиента ──────────────────────────────────────────
class ClientHomeView(BasePage):
    """Главная страница для авторизованного клиента"""
    
    def _build(self):
        container = OFrame(self, bg=BG_DARK)
        container.pack(fill='both', expand=True)
        
        banner = OFrame(container, bg=BG_PANEL)
        banner.pack(fill='x', pady=(0, 30))
        
        tk.Frame(banner, bg=GOLD, height=3).pack(fill='x')
        
        name = self.user.get('full_name', 'Гость')
        tk.Label(banner, text=f"Добро пожаловать, {name}!", 
                font=(FONT_FAMILY, 36, "bold"),
                fg=GOLD, bg=BG_PANEL).pack(pady=(30, 5))
        
        tk.Label(banner, text="Oltremare — итальянская кухня с душой", 
                font=(FONT_SANS, 16), fg=CREAM, bg=BG_PANEL).pack(pady=(0, 10))
        
        tk.Frame(banner, bg=GOLD_DARK, height=2, width=200).pack(pady=10)
        
        tk.Label(banner, text="Двухэтажный ресторан с видом на Саввинскую набережную", 
                font=(FONT_SANS, 12), fg=MUTED, bg=BG_PANEL).pack(pady=5)
        
        tk.Frame(banner, bg=GOLD, height=3).pack(fill='x', pady=(10, 0))

        actions = OFrame(container, bg=BG_DARK)
        actions.pack(fill='x', padx=60, pady=30)
        
        tk.Label(actions, text="Быстрые действия", 
                font=FONT_H1, fg=GOLD, bg=BG_DARK).pack(anchor='w', pady=(0, 20))
        
        grid = OFrame(actions, bg=BG_DARK)
        grid.pack(fill='x')
        
        def go_to(page):
            root = self.winfo_toplevel()
            if hasattr(root, '_show_page'):
                root._show_page(page)
        
        actions_data = [
            ("📅", "Забронировать стол", "Забронируйте столик на удобное время", 
             lambda: ReservationDialog(self, user=self.user, on_save=None)),
            ("🪑", "Схема зала", "Посмотреть доступные столики", 
             lambda: go_to('table_layout')),
            ("🍽️", "Меню", "Посмотреть наше меню", 
             lambda: go_to('menu_view')),
            ("📋", "Мои брони", "Просмотр и управление бронями", 
             lambda: go_to('my_reservations')),
        ]
        
        for i, (icon, title, desc, command) in enumerate(actions_data):
            col = i % 2
            row = i // 2
            
            card = OCard(grid)
            card.grid(row=row, column=col, padx=10, pady=10, sticky='nsew')
            card.bind('<Button-1>', lambda e, cmd=command: cmd())
            
            tk.Label(card, text=icon, font=("Segoe UI", 28), 
                    bg=BG_CARD, fg=GOLD).pack(pady=(15, 5))
            tk.Label(card, text=title, font=FONT_H2, 
                    bg=BG_CARD, fg=CREAM).pack()
            tk.Label(card, text=desc, font=FONT_SMALL, 
                    bg=BG_CARD, fg=MUTED, wraplength=250).pack(pady=(5, 15))
            
            for child in card.winfo_children():
                child.bind('<Button-1>', lambda e, cmd=command: cmd())
        
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)


# ── Меню (клиент / гость) ────────────────────────────────────────────────────
class ClientMenuView(BasePage):
    def _build(self):
        self._page_header("Меню Oltremare")

        # Кнопка "На главную"
        back_frame = OFrame(self, bg=BG_DARK)
        back_frame.pack(fill='x', padx=PAD_LG, pady=(0, PAD))
        OButton(back_frame, "🏠 На главную", 
                command=self._go_home,
                variant='ghost').pack(side='left')

        # Для гостя — баннер с предложением зарегистрироваться
        if self.user.get('role') == 'guest':
            banner = OCard(self)
            banner.pack(fill='x', padx=PAD_LG, pady=(0, PAD))
            bf = OFrame(banner, bg=BG_CARD)
            bf.pack(fill='x', padx=PAD, pady=8)
            OLabel(bf, "Хотите забронировать столик или сделать заказ?",
                   color=GOLD, font=FONT_BODY, bg=BG_CARD).pack(side='left', padx=(0, 12))
            OButton(bf, "Зарегистрироваться", command=self._go_register,
                    variant='gold').pack(side='left')

        ctrl = OFrame(self, bg=BG_DARK)
        ctrl.pack(fill='x', padx=PAD_LG, pady=(0, PAD))
        OLabel(ctrl, "Категория:", bg=BG_DARK).pack(side='left')
        cats = DishModel.get_categories()
        self._cat_vals = ['Все категории'] + [c['name'] for c in cats]
        self._cat_ids  = [None] + [c['id'] for c in cats]
        self.cmb_cat = OCombobox(ctrl, values=self._cat_vals, state='readonly', width=20)
        self.cmb_cat.current(0)
        self.cmb_cat.pack(side='left', padx=8)
        self.cmb_cat.bind('<<ComboboxSelected>>', lambda e: self.refresh())

        cols = ('category', 'name', 'description', 'price', 'discount', 'final')
        headers = ('Категория', 'Блюдо', 'Описание', 'Цена', 'Скидка', 'Итого')
        widths = (110, 180, 250, 90, 70, 110)
        frm, self.tree = self._make_tree(self, cols, heights=20)
        frm.pack(fill='both', expand=True, padx=PAD_LG, pady=(0, PAD_LG))
        for col, hdr, w in zip(cols, headers, widths):
            self.tree.heading(col, text=hdr)
            self.tree.column(col, width=w)
        self.refresh()

    def _go_home(self):
        root = self.winfo_toplevel()
        if hasattr(root, '_show_page'):
            if self.user.get('role') == 'guest':
                root._show_page('home')
            else:
                root._show_page('client_home')

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        cat_id = self._cat_ids[self.cmb_cat.current()]
        for d in DishModel.get_all(available_only=True):
            if cat_id and d['category_id'] != cat_id:
                continue
            disc_val = d.get('discount', 0) or 0
            disc = float(disc_val)
            final = float(d['price']) * (1 - disc / 100)
            self.tree.insert('', 'end', values=(
                d['category_name'], d['name'],
                d.get('description', ''),
                f"{d['price']:.2f} ₽",
                f"{disc:.0f}%" if disc > 0 else "—",
                f"{final:.2f} ₽"))
            apply_tree_grid(self.order_tree)

    def _go_register(self):
        from src.views.login_view import show_register
        show_register(self.winfo_toplevel(), on_success=self._on_registered)

    def _on_registered(self, user):
        show_toast(self, f"Добро пожаловать, {user['full_name']}!", 'success', 3000)
        self.winfo_toplevel()._on_login(user)

# ── Мои заказы (клиент) ─────────────────────────────────────────────────────
# ── Мои заказы (клиент) ─────────────────────────────────────────────────────
class ClientOrdersView(BasePage):
    def _build(self):
        self._page_header("Мои заказы")
        
        back_frame = OFrame(self, bg=BG_DARK)
        back_frame.pack(fill='x', padx=PAD_LG, pady=(0, PAD))
        OButton(back_frame, "🏠 На главную", 
                command=self._go_home,
                variant='ghost').pack(side='left')
        
        tb = OFrame(self, bg=BG_DARK)
        tb.pack(fill='x', padx=PAD_LG, pady=PAD)
        OButton(tb, "🔄 Обновить", command=self.refresh, variant='secondary').pack(side='left', padx=(0, 8))
        OButton(tb, "📋 Просмотр заказа", command=self._view_order, variant='secondary').pack(side='left', padx=(0, 8))
        
        cols = ('id', 'table', 'status', 'placed_at', 'total', 'reservation')
        headers = ('№', 'Стол', 'Статус', 'Оформлен', 'Сумма ₽', 'Бронь №')
        widths = (50, 70, 140, 150, 120, 80)
        
        frm, self.tree = self._make_tree(self, cols, heights=15)
        frm.pack(fill='both', expand=True, padx=PAD_LG, pady=(0, PAD_LG))
        
        for col, hdr, w in zip(cols, headers, widths):
            self.tree.heading(col, text=hdr)
            self.tree.column(col, width=w)
        
        self.refresh()
    
    def _go_home(self):
        root = self.winfo_toplevel()
        if hasattr(root, '_show_page'):
            root._show_page('client_home')
    
    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        uid = self.user.get('id')
        if not uid:
            return
        
        from src.models.models import OrderModel, ReservationModel
        from src.database.db import execute_query
        
        reservations = ReservationModel.get_by_client(uid)
        reservation_ids = [r['id'] for r in reservations]
        all_orders = []
        for rid in reservation_ids:
            orders = OrderModel.get_by_reservation(rid)
            all_orders.extend(orders)
        
        # Заказы клиента (client_id)
        client_orders = execute_query("""
            SELECT o.*, t.number AS table_number, u.full_name AS waiter_name
            FROM orders o
            JOIN tables t ON o.table_id = t.id
            JOIN users u ON o.waiter_id = u.id
            WHERE o.client_id = %s
            ORDER BY o.created_at DESC
        """, (uid,), fetch=True)
        
        all_orders.extend(client_orders)
        
        seen = set()
        unique_orders = []
        for o in all_orders:
            if o['id'] not in seen:
                seen.add(o['id'])
                unique_orders.append(o)
        
        for o in unique_orders:
            total = 0
            detail = OrderModel.get_order_detail(o['id'])
            if detail and detail.get('items'):
                total = sum(i['quantity'] * float(i['final_price']) for i in detail['items'])
            
            color = STATUS_COLORS.get(o['status'], CREAM)
            self.tree.insert('', 'end', iid=str(o['id']), values=(
                o['id'],
                f"№{o['table_number']}",
                STATUS_LABELS.get(o['status'], o['status']),
                str(o.get('placed_at', '') or '')[:16],
                f"{total:.2f}",
                o.get('reservation_id') or '—'
            ))
            self.tree.tag_configure(str(o['id']), foreground=color)
    
    def _view_order(self):
        sel = self.tree.selection()
        if not sel:
            return messagebox.showwarning("Выбор", "Выберите заказ для просмотра", parent=self)
        oid = int(sel[0])
        order = OrderModel.get_order_detail(oid)
        if order:
            ClientOrderDetailDialog(self, order=order)