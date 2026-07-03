"""
Oltremare — Виды администратора 
"""
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox
from datetime import date, datetime
from src.utils.theme import apply_tree_grid

from src.utils.theme import *
from src.database.db import execute_query
from src.models.models import (
    TableModel, ReservationModel, ShiftModel,
    DishModel, AuthModel, StatisticsModel, PromotionModel, BillModel, OrderModel
)

MONTHS_RU = ['','Январь','Февраль','Март','Апрель','Май','Июнь',
             'Июль','Август','Сентябрь','Октябрь','Ноябрь','Декабрь']



# ── Базовый класс страницы ───────────────────────────────────────────────────
class BasePage(OFrame):
    def __init__(self, master, user):
        super().__init__(master, bg=BG_DARK)
        self.user = user
        self._build()

    def _build(self): pass
    def refresh(self): pass

    def _page_header(self, title, subtitle=''):
        h = OFrame(self, bg=BG_DARK)
        h.pack(fill='x', padx=PAD_LG, pady=(PAD_LG, PAD))
        tk.Label(h, text=title, font=FONT_H1, fg=GOLD, bg=BG_DARK).pack(side='left')
        if subtitle:
            tk.Label(h, text=f"— {subtitle}", font=FONT_SMALL, fg=MUTED, bg=BG_DARK).pack(side='left', padx=8)
        Divider(self).pack(fill='x', padx=PAD_LG)

    def _make_tree(self, parent, columns, heights=14):
        frame = OFrame(parent, bg=BG_DARK)
        tree = ttk.Treeview(frame, columns=columns, show='headings',
                            style='Oltremare.Treeview', height=heights)
        vsb = ttk.Scrollbar(frame, orient='vertical', command=tree.yview)
        hsb = ttk.Scrollbar(frame, orient='horizontal', command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side='right', fill='y')
        hsb.pack(side='bottom', fill='x')
        tree.pack(fill='both', expand=True)
        apply_tree_grid(tree)
        return frame, tree


# ── Схема зала ───────────────────────────────────────────────────────────────
class TablesView(BasePage):
    def _build(self):
        self._page_header("Схема зала", "статус столиков")
        ctrl = OFrame(self, bg=BG_DARK)
        ctrl.pack(fill='x', padx=PAD_LG, pady=PAD)

        # Кнопки управления
        OButton(ctrl, "➕ Добавить стол", command=self._add_table, variant='gold').pack(side='left', padx=(0,8))
        OButton(ctrl, "✏️ Редактировать стол", command=self._edit_table, variant='secondary').pack(side='left', padx=(0,8))
        OButton(ctrl, "🗑️ Удалить стол", command=self._delete_table, variant='danger').pack(side='left', padx=(0,8))
        OLabel(ctrl, "Дата:", bg=BG_DARK).pack(side='left')
        self._date_entry = DateEntry(ctrl)
        self._date_entry.pack(side='left', padx=6)
        OLabel(ctrl, "Время:", bg=BG_DARK).pack(side='left', padx=(8,0))
        self._time_cb = TimeCombo(ctrl)
        self._time_cb.pack(side='left', padx=6)
        OButton(ctrl, "Обновить", command=self.refresh, variant='primary').pack(side='left', padx=8)
        

        leg = OFrame(self, bg=BG_DARK)
        leg.pack(fill='x', padx=PAD_LG, pady=(0,PAD))
        for label, color in [("Свободен",SUCCESS),("Забронирован",WARNING),
                              ("Занят",ERROR),("Недоступен",MUTED)]:
            f = OFrame(leg, bg=BG_DARK); f.pack(side='left', padx=8)
            tk.Frame(f, bg=color, width=14, height=14).pack(side='left', padx=4)
            OLabel(f, label, font=FONT_SMALL, bg=BG_DARK).pack(side='left')

        self.canvas_frame = OCard(self)
        self.canvas_frame.pack(fill='both', expand=True, padx=PAD_LG, pady=(0,PAD_LG))
        self.canvas = tk.Canvas(self.canvas_frame, bg=BG_CARD, highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)
        self.canvas.bind('<Configure>', lambda e: self.refresh())
        self.canvas.bind('<Button-1>', self._on_click)  # Добавить в _build
        self.canvas.bind('<Double-Button-1>', self._on_double_click)
        self.canvas.bind('<Button-3>', self._on_right_click)
        
        self._tables_data = []  # ДОБАВЛЯЕМ
        self._selected_table_id = None
        self._rects = []

    def _on_right_click(self, event):
        for r in self._rects:
            if r['x1'] <= event.x <= r['x2'] and r['y1'] <= event.y <= r['y2']:
                table_id = r['table']['id']
                menu = tk.Menu(self, tearoff=0)
                menu.add_command(label="Просмотр стола", command=lambda: TableDetailDialog(self, table_id, self.user, on_update=self.refresh))
                menu.add_command(label="Редактировать стол", command=lambda: TableDialog(self, table=TableModel.get_by_id(table_id), on_save=self.refresh))
                menu.add_command(label="Удалить стол", command=lambda: self._delete_table_by_id(table_id))
                menu.post(event.x_root, event.y_root)
                break

    def _edit_table_by_id(self, table_id):
        table = TableModel.get_by_id(table_id)
        if table:
            TableDialog(self, table=table, on_save=self.refresh)

    def _delete_table_by_id(self, table_id):
        table = TableModel.get_by_id(table_id)
        if table:
            TableDialog(self, table=table, on_save=self.refresh)
    def _on_double_click(self, event):
        """Открыть детали стола по двойному клику"""
        for r in self._rects:
            if r['x1'] <= event.x <= r['x2'] and r['y1'] <= event.y <= r['y2']:
                table_id = r['table']['id']
                TableDetailDialog(self, table_id, self.user, on_update=self.refresh)
                break

    def _on_click(self, event):
        """Выбрать стол по клику"""
        for r in self._rects:
            if r['x1'] <= event.x <= r['x2'] and r['y1'] <= event.y <= r['y2']:
                self._selected_table_id = r['table']['id']
                self.refresh()
                break

    def refresh(self):
        try:
            d = self._date_entry.get_date()
            t_str = self._time_cb.get()
            h, m = map(int, t_str.split(':'))
            dt = datetime(d.year, d.month, d.day, h, m)
        except Exception:
            dt = datetime.now()
        self._tables_data = TableModel.get_layout_status(dt)  # ОБНОВЛЯЕМ ДАННЫЕ
        self._draw(self._tables_data)  # ПЕРЕДАЕМ ИХ В ОТРИСОВКУ

    def _draw(self, tables):
        c = self.canvas
        c.delete('all')
        w = c.winfo_width() or 700
        cols = 5
        pad = 20
        cell_w = (w - pad * 2) // cols
        cell_h = 160
        self._rects = []
        
        for i, t in enumerate(tables):
            col = i % cols
            row = i // cols
            x1 = pad + col * cell_w + 8
            y1 = pad + row * cell_h + 8
            x2 = x1 + cell_w - 16
            y2 = y1 + cell_h - 16
            
            s = t.get('current_status', 'free')
            color = {
                'free': SUCCESS,
                'reserved': WARNING,
                'occupied': ERROR,
                'unavailable': MUTED
            }.get(s, MUTED)
            
            is_sel = (self._selected_table_id == t['id'])
            
            c.create_rectangle(x1, y1, x2, y2, fill=BG_CARD, 
                            outline=GOLD if is_sel else color, 
                            width=3 if is_sel else 2)
            
            cx = (x1 + x2) // 2
            
            # Номер стола
            c.create_text(cx, y1 + 18, text=f"Стол №{t['number']}", font=FONT_H2, fill=GOLD)
            
            # Статус
            c.create_text(cx, y1 + 40, text=STATUS_LABELS.get(s, s), font=FONT_SMALL, fill=color)
            
            # Вместимость
            c.create_text(cx, y1 + 58, text=f"Мест: {t['capacity']}", font=FONT_TINY, fill=MUTED)
            
            # Локация
            c.create_text(cx, y1 + 74, text=t.get('location', ''), font=FONT_TINY, fill=MUTED)
            
            # Если стол занят — показываем имя официанта из заказа
            if s == 'occupied':
                waiter_name = t.get('waiter_name', '')
                if waiter_name:
                    c.create_text(cx, y1 + 92, text=f"👨‍🍳 {waiter_name[:20]}", font=FONT_TINY, fill=CREAM)
                else:
                    c.create_text(cx, y1 + 92, text="👨‍🍳 Официант назначен", font=FONT_TINY, fill=CREAM)
            
            # Если стол свободен — показываем закрепленного официанта из смены
            if s == 'free':
                assigned_waiter = t.get('assigned_waiter', '')
                if assigned_waiter:
                    c.create_text(cx, y1 + 92, text=f"👨‍🍳 {assigned_waiter[:20]}", 
                                font=FONT_TINY, fill=MUTED)
            
            # Если стол забронирован — показываем информацию о брони
            if s == 'reserved':
                client_name = t.get('client_name', '')
                if client_name:
                    c.create_text(cx, y1 + 92, text=f"👤 {client_name[:18]}", font=FONT_TINY, fill=CREAM)
                
                res_time = t.get('reservation_time')
                if res_time:
                    if hasattr(res_time, 'strftime'):
                        time_str = res_time.strftime('%H:%M')
                    else:
                        time_str = str(res_time)[:5] if res_time else ''
                    c.create_text(cx, y1 + 108, text=f"⏰ {time_str}", font=FONT_TINY, fill=WARNING)
                    
                    # Подсветка скорой брони
                    try:
                        now = datetime.now()
                        if hasattr(res_time, 'strftime'):
                            res_dt = datetime.combine(now.date(), res_time)
                        else:
                            res_dt = datetime.combine(now.date(), datetime.strptime(str(res_time)[:5], '%H:%M').time())
                        delta = (res_dt - now).total_seconds() / 60
                        if 0 <= delta <= 60:
                            c.create_rectangle(x1, y1, x2, y2, fill='', outline=ERROR, width=3, dash=(4, 2))
                            if delta <= 30:
                                c.create_text(cx, y1 + 124, text="🔴 СКОРО!", font=FONT_TINY, fill=ERROR)
                    except:
                        pass
            
            self._rects.append({'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2, 'table': t})
    
    def _add_table(self):
        """Добавить новый стол"""
        TableDialog(self, on_save=self.refresh)

    def _edit_table(self):
        """Редактировать выбранный стол"""
        if not hasattr(self, '_selected_table_id') or not self._selected_table_id:
            messagebox.showwarning("Выбор", "Кликните на столик для редактирования", parent=self)
            return
        
        table = TableModel.get_by_id(self._selected_table_id)
        if table:
            TableDialog(self, table=table, on_save=self.refresh)

    def _delete_table(self):
        """Удалить выбранный стол"""
        if not hasattr(self, '_selected_table_id') or not self._selected_table_id:
            messagebox.showwarning("Выбор", "Кликните на столик для удаления", parent=self)
            return
        
        table = TableModel.get_by_id(self._selected_table_id)
        if table:
            TableDeleteDialog(self, table=table, on_save=self.refresh)


# ── Диалог просмотра и управления столом ──────────────────────────────────
# ── Диалог просмотра и управления столом ──────────────────────────────────
# ── Диалог просмотра и управления столом ──────────────────────────────────
class TableDetailDialog(tk.Toplevel):
    def __init__(self, master, table_id, user, on_update=None):
        super().__init__(master)
        self.table_id = table_id
        self.user = user
        self.on_update = on_update
        self.title(f"Управление столом №{table_id}")
        self.configure(bg=BG_DARK)
        self.geometry("850x750")
        self.transient(master)  # ← ЗАМЕНИТЬ self.grab_set()
        self.focus_set()
        self._build()
        self._load_data()

    def _build(self):
        header = OFrame(self, bg=BG_DARK)
        header.pack(fill='x', padx=PAD_LG, pady=PAD_LG)
        tk.Label(header, text=f"Стол №{self.table_id}", font=FONT_H1, fg=GOLD, bg=BG_DARK).pack(side='left')

        btn_frame = OFrame(self, bg=BG_DARK)
        btn_frame.pack(fill='x', padx=PAD_LG, pady=(0, PAD))
        OButton(btn_frame, "🔄 Обновить", command=self._load_data, variant='secondary').pack(side='left', padx=(0,8))
        OButton(btn_frame, "➕ Создать заказ", command=self._create_order, variant='gold').pack(side='left', padx=(0,8))
        OButton(btn_frame, "📅 Добавить бронь", command=self._add_reservation, variant='gold').pack(side='left', padx=(0,8))

        OLabel(self, "Активные заказы на сегодня:", color=GOLD, font=FONT_H2, bg=BG_DARK).pack(anchor='w', padx=PAD_LG)
        cols_orders = ('id', 'waiter', 'status', 'placed_at', 'total')
        frm_orders, self.tree_orders = self._make_tree(self, cols_orders, heights=6)
        frm_orders.pack(fill='x', padx=PAD_LG, pady=(0, PAD))
        for col, hdr, w in zip(cols_orders, ('№', 'Официант', 'Статус', 'Оформлен', 'Сумма ₽'), (50, 150, 120, 150, 100)):
            self.tree_orders.heading(col, text=hdr)
            self.tree_orders.column(col, width=w)

        order_btn_frame = OFrame(self, bg=BG_DARK)
        order_btn_frame.pack(fill='x', padx=PAD_LG, pady=4)
        OButton(order_btn_frame, "📋 Просмотр заказа", command=self._view_order, variant='secondary').pack(side='left', padx=(0,8))
        OButton(order_btn_frame, "✏️ Редактировать заказ", command=self._edit_order, variant='primary').pack(side='left', padx=(0,8))
        OButton(order_btn_frame, "🔄 Переназначить официанта", command=self._reassign_waiter, variant='primary').pack(side='left', padx=(0,8))

        OLabel(self, "Брони на сегодня:", color=GOLD, font=FONT_H2, bg=BG_DARK).pack(anchor='w', padx=PAD_LG)
        cols_res = ('id', 'client', 'phone', 'time', 'guests', 'status')
        frm_res, self.tree_res = self._make_tree(self, cols_res, heights=6)
        frm_res.pack(fill='x', padx=PAD_LG, pady=(0, PAD))
        for col, hdr, w in zip(cols_res, ('№', 'Клиент', 'Телефон', 'Время', 'Гостей', 'Статус'), (50, 150, 120, 100, 70, 100)):
            self.tree_res.heading(col, text=hdr)
            self.tree_res.column(col, width=w)

        res_btn_frame = OFrame(self, bg=BG_DARK)
        res_btn_frame.pack(fill='x', padx=PAD_LG, pady=4)
        OButton(res_btn_frame, "✏️ Редактировать бронь", command=self._edit_reservation, variant='secondary').pack(side='left', padx=(0,8))
        OButton(res_btn_frame, "🗑️ Отменить бронь", command=self._cancel_reservation, variant='danger').pack(side='left', padx=(0,8))

        btns = OFrame(self, bg=BG_DARK)
        btns.pack(fill='x', padx=PAD_LG, pady=PAD)
        OButton(btns, "Закрыть", command=self.destroy, variant='ghost').pack(side='right')

    def _make_tree(self, parent, columns, heights):
        frame = OFrame(parent, bg=BG_DARK)
        tree = ttk.Treeview(frame, columns=columns, show='headings', style='Oltremare.Treeview', height=heights)
        vsb = ttk.Scrollbar(frame, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side='right', fill='y')
        tree.pack(fill='both', expand=True)
        apply_tree_grid(tree)
        return frame, tree

    def _load_data(self):
        self.tree_orders.delete(*self.tree_orders.get_children())
        self.tree_res.delete(*self.tree_res.get_children())

        today = date.today()

        orders = execute_query("""
            SELECT o.*, u.full_name AS waiter_name
            FROM orders o
            JOIN users u ON o.waiter_id = u.id
            WHERE o.table_id = %s AND DATE(o.created_at) = %s
            AND o.status IN ('composing','placed','accepted','cooking','ready','delivered')
            ORDER BY o.created_at DESC
        """, (self.table_id, today), fetch=True)

        for o in orders:
            total = 0
            detail = OrderModel.get_order_detail(o['id'])
            if detail and detail.get('items'):
                total = sum(i['quantity'] * float(i['final_price']) for i in detail['items'])
            self.tree_orders.insert('', 'end', values=(
                o['id'],
                o['waiter_name'],
                STATUS_LABELS.get(o['status'], o['status']),
                str(o.get('placed_at', '') or '')[:16],
                f"{total:.2f}"
            ))

        # Загрузка броней на сегодня с форматированием времени
        reservations = execute_query("""
            SELECT r.*
            FROM reservations r
            JOIN reservation_tables rt ON rt.reservation_id = r.id
            WHERE rt.table_id = %s AND r.reservation_date = %s
            AND r.status = 'active'
            ORDER BY r.reservation_time
        """, (self.table_id, today), fetch=True)

        for r in reservations:
            t_start = str(r['reservation_time'])[:5]
            t_end = str(r['end_time'])[:5] if r.get('end_time') else ''
            time_display = f"{t_start} – {t_end}" if t_end else t_start
            
            self.tree_res.insert('', 'end', values=(
                r['id'],
                r['client_name'],
                r['client_phone'],
                time_display,  # ← Теперь "16:00 – 17:00"
                r['guests_count'],
                STATUS_LABELS.get(r['status'], r['status'])
            ))

        self.update_idletasks()

    def _get_waiter_for_table(self, table_id):
        """Вернуть ID официанта, назначенного на стол сегодня, или None."""
        today = date.today()
        result = execute_query("""
            SELECT DISTINCT s.waiter_id
            FROM shifts s
            JOIN shift_tables st ON st.shift_id = s.id
            WHERE st.table_id = %s AND s.shift_date = %s AND s.status = 'open'
            LIMIT 1
        """, (table_id, today), fetch_one=True)
        return result['waiter_id'] if result else None

    def _create_order(self):
        """Создать заказ для текущего стола с официантом, назначенным на стол."""
        from src.views.waiter_views import OrderDialog

        # 1. Пытаемся найти официанта, закреплённого за столом в активной смене
        waiter_id = self._get_waiter_for_table(self.table_id)

        # 2. Если не найден – предложить выбор из активных официантов
        if not waiter_id:
            active_waiters = AuthModel.get_all_waiters(active_only=True)
            if not active_waiters:
                messagebox.showwarning("Ошибка", "Нет активных официантов для назначения заказа", parent=self)
                return

            # Диалог выбора официанта
            dialog = tk.Toplevel(self)
            dialog.title("Выбор официанта")
            dialog.configure(bg=BG_DARK)
            dialog.geometry("300x300")
            dialog.grab_set()
            tk.Label(dialog, text="Выберите официанта для заказа:", font=FONT_H2, bg=BG_DARK, fg=GOLD).pack(pady=10)
            listbox = tk.Listbox(dialog, bg=BG_INPUT, fg=CREAM, font=FONT_BODY, selectbackground=GOLD_DARK)
            listbox.pack(fill='both', expand=True, padx=20, pady=10)
            for w in active_waiters:
                listbox.insert('end', f"{w['full_name']} (ID: {w['id']})")

            def confirm():
                sel = listbox.curselection()
                if not sel:
                    return
                selected_id = active_waiters[sel[0]]['id']
                dialog.destroy()
                # Открываем диалог заказа с выбранным официантом
                OrderDialog(self, table_id=self.table_id, waiter_id=selected_id, on_save=self._load_data)

            OButton(dialog, "Назначить", command=confirm, variant='gold').pack(pady=10)
            return

        # 3. Если назначенный официант найден – сразу открываем диалог заказа
        OrderDialog(self, table_id=self.table_id, waiter_id=waiter_id, on_save=self._load_data)

    def _add_reservation(self):
        """Открыть диалог бронирования с предустановленным столом"""
        dlg = ReservationDialog(
            self, 
            user=self.user, 
            on_save=self._load_data, 
            preset_table_ids=[self.table_id]
        )
        # Принудительно выбираем стол после открытия диалога
        self.after(100, lambda: self._force_select_table(dlg))

    def _force_select_table(self, dlg):
        """Принудительно выбрать стол в диалоге бронирования"""
        try:
            if dlg.winfo_exists():
                for i, tid in enumerate(dlg._table_ids):
                    if tid == self.table_id:
                        dlg.lb_tables.selection_clear(0, tk.END)
                        dlg.lb_tables.selection_set(i)
                        dlg.lb_tables.see(i)
                        dlg._update_capacity_info()
                        break
        except Exception:
            pass

    def _view_order(self):
        sel = self.tree_orders.selection()
        if not sel:
            messagebox.showwarning("Выбор", "Выберите заказ", parent=self)
            return
        item = self.tree_orders.item(sel[0])
        order_id = int(item['values'][0])
        order = OrderModel.get_order_detail(order_id)
        if order:
            AdminOrderDetailDialog(self, order=order)

    def _edit_order(self):
        sel = self.tree_orders.selection()
        if not sel:
            messagebox.showwarning("Выбор", "Выберите заказ", parent=self)
            return
        item = self.tree_orders.item(sel[0])
        order_id = int(item['values'][0])
        order = OrderModel.get_order_detail(order_id)
        if not order:
            return
        
        current_status = order['status']
        
        if current_status in ('paid', 'cancelled'):
            messagebox.showinfo("Инфо", f"Заказ {STATUS_LABELS.get(current_status, current_status)}, редактирование невозможно", parent=self)
            return
        
        # Открываем диалог редактирования
        from src.views.waiter_views import OrderDialog
        OrderDialog(self, table_id=self.table_id, waiter_id=order['waiter_id'],
                order_id=order_id, on_save=self._load_data)

    def _reassign_waiter(self):
        sel = self.tree_orders.selection()
        if not sel:
            messagebox.showwarning("Выбор", "Выберите заказ", parent=self)
            return
        item = self.tree_orders.item(sel[0])
        order_id = int(item['values'][0])
        
        # Получаем официантов только на активной смене сегодня
        today = date.today()
        active_waiters = execute_query("""
            SELECT DISTINCT u.id, u.full_name 
            FROM shifts s
            JOIN users u ON s.waiter_id = u.id
            WHERE s.shift_date = %s 
            AND s.status = 'open'
            AND u.is_active = TRUE
        """, (today,), fetch=True)
        
        if not active_waiters:
            messagebox.showwarning("Ошибка", "Нет активных официантов на смене сегодня", parent=self)
            return
        
        dialog = tk.Toplevel(self)
        dialog.title("Выбор официанта")
        dialog.configure(bg=BG_DARK)
        dialog.geometry("300x300")
        dialog.grab_set()
        tk.Label(dialog, text="Выберите официанта:", font=FONT_H2, bg=BG_DARK, fg=GOLD).pack(pady=10)
        listbox = tk.Listbox(dialog, bg=BG_INPUT, fg=CREAM, font=FONT_BODY, selectbackground=GOLD_DARK)
        listbox.pack(fill='both', expand=True, padx=20, pady=10)
        for w in active_waiters:
            listbox.insert('end', f"{w['full_name']} (ID: {w['id']})")
        
        def confirm():
            sel_idx = listbox.curselection()
            if not sel_idx:
                return
            new_waiter_id = active_waiters[sel_idx[0]]['id']
            execute_query("UPDATE orders SET waiter_id = %s WHERE id = %s", (new_waiter_id, order_id))
            messagebox.showinfo("Успех", "Официант переназначен", parent=dialog)
            dialog.destroy()
            self._load_data()
        
        OButton(dialog, "Назначить", command=confirm, variant='gold').pack(pady=10)
        
        def confirm():
            sel_idx = listbox.curselection()
            if not sel_idx:
                return
            new_waiter_id = active_waiters[sel_idx[0]]['id']
            execute_query("UPDATE orders SET waiter_id = %s WHERE id = %s", (new_waiter_id, order_id))
            messagebox.showinfo("Успех", "Официант переназначен", parent=dialog)
            dialog.destroy()
            self._load_data()
        
        OButton(dialog, "Назначить", command=confirm, variant='gold').pack(pady=10)
    def _edit_reservation(self):
        sel = self.tree_res.selection()
        if not sel:
            messagebox.showwarning("Выбор", "Выберите бронь", parent=self)
            return
        item = self.tree_res.item(sel[0])
        res_id = int(item['values'][0])
        res_data = execute_query("SELECT * FROM reservations WHERE id = %s", (res_id,), fetch_one=True)
        if res_data:
            # Передаём текущий стол при редактировании
            ReservationDialog(
                self, 
                user=self.user, 
                reservation=res_data, 
                on_save=self._load_data,
                preset_table_ids=[self.table_id]  # ← ДОБАВЛЯЕМ
            )

    def _cancel_reservation(self):
        sel = self.tree_res.selection()
        if not sel:
            messagebox.showwarning("Выбор", "Выберите бронь", parent=self)
            return
        item = self.tree_res.item(sel[0])
        res_id = int(item['values'][0])
        if messagebox.askyesno("Отмена брони", f"Отменить бронь №{res_id}?", parent=self):
            ReservationModel.cancel(res_id)
            self._load_data()
            show_toast(self, "Бронь отменена", 'info')

# ── Диалог подтверждения удаления стола ────────────────────────────────────
class TableDeleteDialog(tk.Toplevel):
    def __init__(self, master, table, on_save=None):
        super().__init__(master)
        self.table = table
        self.on_save = on_save
        self.title(f"Удаление стола №{table['number']}")
        self.configure(bg=BG_DARK)
        self.geometry("400x250")
        self.grab_set()
        self._build()

    def _build(self):
        OLabel(self, "⚠️ Подтверждение удаления", color=ERROR, font=FONT_H1, bg=BG_DARK).pack(pady=PAD_LG)
        Divider(self).pack(fill='x', padx=PAD_LG)
        
        form = OFrame(self, bg=BG_DARK)
        form.pack(fill='both', expand=True, padx=PAD_LG, pady=PAD)
        
        OLabel(form, f"Вы уверены, что хотите удалить стол №{self.table['number']}?", 
               color=CREAM, font=FONT_BODY, bg=BG_DARK).pack(pady=10)
        OLabel(form, f"Вместимость: {self.table['capacity']} мест", 
               color=MUTED, font=FONT_SMALL, bg=BG_DARK).pack()
        OLabel(form, f"Локация: {self.table.get('location', 'не указана')}", 
               color=MUTED, font=FONT_SMALL, bg=BG_DARK).pack()
        OLabel(form, "⚠️ Стол будет удален, если на нем нет активных заказов и броней", 
               color=WARNING, font=FONT_SMALL, bg=BG_DARK).pack(pady=10)

        btns = OFrame(self, bg=BG_DARK)
        btns.pack(fill='x', padx=PAD_LG, pady=PAD)
        OButton(btns, "🗑️ Удалить", command=self._delete, variant='danger').pack(side='left', padx=(0,8))
        OButton(btns, "Отмена", command=self.destroy, variant='ghost').pack(side='left')

    def _delete(self):
        try:
            TableModel.delete(self.table['id'])
            if self.on_save:
                self.on_save()
            show_toast(self.master, f"Стол №{self.table['number']} удален", 'info')
            self.destroy()
        except ValueError as e:
            messagebox.showerror("Ошибка", str(e), parent=self)

# ── Диалог добавления/редактирования стола ──────────────────────────────────
class TableDialog(tk.Toplevel):
    def __init__(self, master, table=None, on_save=None):
        super().__init__(master)
        self.table = table
        self.on_save = on_save
        self.title("Новый стол" if not table else f"Редактировать стол №{table['number']}")
        self.configure(bg=BG_DARK)
        self.geometry("400x400")
        self.grab_set()
        self._build()

    def _build(self):
        OLabel(self, "Данные стола", color=GOLD, font=FONT_H1, bg=BG_DARK).pack(pady=PAD_LG)
        Divider(self).pack(fill='x', padx=PAD_LG)
        
        form = OFrame(self, bg=BG_DARK)
        form.pack(fill='both', expand=True, padx=PAD_LG, pady=PAD)

        OLabel(form, "Номер стола *:", color=GOLD, font=FONT_SMALL, bg=BG_DARK).pack(anchor='w', pady=(8,2))
        self.ent_number = OEntry(form)
        self.ent_number.pack(fill='x', ipady=5)
        
        OLabel(form, "Вместимость * (1-4 места):", color=GOLD, font=FONT_SMALL, bg=BG_DARK).pack(anchor='w', pady=(8,2))
        self.ent_capacity = OEntry(form)
        self.ent_capacity.pack(fill='x', ipady=5)
        
        OLabel(form, "Локация:", color=GOLD, font=FONT_SMALL, bg=BG_DARK).pack(anchor='w', pady=(8,2))
        locations = ['Зал 1', 'Зал 2', 'Зал 3', 'Терраса', 'VIP-зал', 'Барная стойка', 'Летняя веранда']
        self.cmb_location = OCombobox(form, values=locations, state='readonly')
        self.cmb_location.pack(fill='x', ipady=5)
        self.cmb_location.set('Зал 1')

        if self.table:
            self.ent_number.insert(0, str(self.table['number']))
            self.ent_capacity.insert(0, str(self.table['capacity']))
            current_location = self.table.get('location', 'Зал 1')
            if current_location in locations:
                self.cmb_location.set(current_location)
            else:
                self.cmb_location.set('Зал 1')
            self.ent_number.config(state='readonly')  # Номер нельзя менять при редактировании

        btns = OFrame(self, bg=BG_DARK)
        btns.pack(fill='x', padx=PAD_LG, pady=PAD)
        OButton(btns, "Сохранить", command=self._save, variant='gold').pack(side='left', padx=(0,8))
        OButton(btns, "Отмена", command=self.destroy, variant='ghost').pack(side='left')

    def _save(self):
        try:
            number = int(self.ent_number.get().strip())
            capacity = int(self.ent_capacity.get().strip())
            location = self.cmb_location.get().strip()
            if number < 1:
                raise ValueError("Номер стола должен быть положительным числом")
            if capacity < 1:
                raise ValueError("Вместимость должна быть минимум 1 место")
            if capacity > 4:
                raise ValueError("Вместимость не может превышать 4 места!")
            if not location:
                location = 'Зал 1'
            if self.table:
                TableModel.update(self.table['id'], number, capacity, location)
                msg = f"Стол №{number} обновлен"
            else:
                TableModel.create(number, capacity, location)
                msg = f"Стол №{number} создан"
            if self.on_save:
                self.on_save()
            show_toast(self.master, msg, 'success')
            self.destroy()
        except ValueError as e:
            messagebox.showerror("Ошибка", str(e), parent=self)


# ── Брони ────────────────────────────────────────────────────────────────────
class ReservationsView(BasePage):
    def _build(self):
        self._page_header("Бронирование")
        # !! Кнопки в отдельном фрейме с явным паком
        tb = OFrame(self, bg=BG_DARK)
        tb.pack(fill='x', padx=PAD_LG, pady=PAD)
        OButton(tb, "+ Новая бронь", command=self._new,
                variant='gold').pack(side='left', padx=(0,8))
        OButton(tb, "Редактировать", command=self._edit,
                variant='secondary').pack(side='left', padx=(0,8))
        OButton(tb, "Отменить", command=self._cancel,
                variant='danger').pack(side='left')

        cols = ('id','client','phone','date','time_range','guests','tables','status','notes')
        headers = ('№','Клиент','Телефон','Дата','Время','Гостей','Столики','Статус','Примечание')
        widths = (50,150,120,100,130,60,80,100,160)
        frm, self.tree = self._make_tree(self, cols)
        frm.pack(fill='both', expand=True, padx=PAD_LG, pady=(0,PAD_LG))
        for col,hdr,w in zip(cols,headers,widths):
            self.tree.heading(col, text=hdr); self.tree.column(col, width=w, minwidth=40)
        self.refresh()

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        for r in ReservationModel.get_all():
            t_start = str(r['reservation_time'])[:5]
            t_end = str(r['end_time'])[:5] if r.get('end_time') else ''
            
            if t_end:
                time_display = f"{t_start} – {t_end}"
            else:
                time_display = t_start
            
            self.tree.insert('','end', iid=str(r['id']), values=(
                r['id'], r['client_name'], r['client_phone'],
                str(r['reservation_date']), time_display,
                r['guests_count'], r.get('table_numbers',''),
                STATUS_LABELS.get(r['status'],r['status']),
                r.get('notes','')))

    def _new(self):
        ReservationDialog(self, user=self.user, on_save=self.refresh)

    def _cancel(self):
        sel = self.tree.selection()
        if not sel: return messagebox.showwarning("Выбор","Выберите бронь",parent=self)
        rid = int(sel[0])
        if messagebox.askyesno("Отмена брони", f"Отменить бронь №{rid}?", parent=self):
            ReservationModel.cancel(rid); self.refresh()
            show_toast(self, "Бронь отменена", 'info')

    def _edit(self):
        sel = self.tree.selection()
        if not sel: return messagebox.showwarning("Выбор","Выберите бронь",parent=self)
        rid = int(sel[0])
        res = next((r for r in ReservationModel.get_all() if r['id']==rid), None)
        if res: ReservationDialog(self, user=self.user, reservation=res, on_save=self.refresh)


class ReservationDialog(tk.Toplevel):
    def __init__(self, master, user, reservation=None, on_save=None, preset_table_ids=None):
        super().__init__(master)
        self.user = user
        self.reservation = reservation
        self.on_save = on_save
        self.preset_table_ids = preset_table_ids
        self._table_capacities = {}
        self.title("Новая бронь" if not reservation else f"Бронь №{reservation['id']}")
        self.configure(bg=BG_DARK)
        self.geometry("600x870")
        self.transient(master)
        self.lift()          # ← ДОБАВИТЬ
        self.focus_force()   # ← ДОБАВИТЬ (вместо focus_set)
        self._build()

    def _build(self):
        OLabel(self, "Бронирование столика", color=GOLD, font=FONT_H1, bg=BG_DARK).pack(pady=PAD_LG)
        Divider(self).pack(fill='x', padx=PAD_LG)
        form = OFrame(self, bg=BG_DARK)
        form.pack(fill='both', expand=True, padx=PAD_LG, pady=PAD)

        def lbl(t): OLabel(form, t, color=GOLD, font=FONT_SMALL, bg=BG_DARK).pack(anchor='w', pady=(8,2))

        lbl("Имя клиента *"); self.ent_name = OEntry(form); self.ent_name.pack(fill='x', ipady=5)
        lbl("Телефон * (+7XXXXXXXXXX)"); self.ent_phone = OEntry(form); self.ent_phone.pack(fill='x', ipady=5)
        lbl("Количество гостей *")
        self.ent_guests = OEntry(form)
        self.ent_guests.pack(fill='x', ipady=5)
        self.ent_guests.bind('<KeyRelease>', lambda e: self._update_capacity_info())

        self.capacity_label = OLabel(form, "Выберите столики", 
                                    color=MUTED, font=FONT_SMALL, bg=BG_DARK)
        self.capacity_label.pack(anchor='w', pady=(4, 8))
        
        # Дата
        dr = OFrame(form, bg=BG_DARK); dr.pack(fill='x', pady=(8,2))
        OLabel(dr, "Дата *", color=GOLD, font=FONT_SMALL, bg=BG_DARK).pack(side='left')
        self.date_entry = DateEntry(dr); self.date_entry.pack(side='left', padx=8)
        self.date_entry.bind('<<DateSelected>>', lambda e: self._check_date())

        # Время
        tr = OFrame(form, bg=BG_DARK); tr.pack(fill='x', pady=(8,2))
        OLabel(tr, "Начало *", color=GOLD, font=FONT_SMALL, bg=BG_DARK).pack(side='left')
        self.time_start = TimeCombo(tr); self.time_start.pack(side='left', padx=8)
        OLabel(tr, "Окончание", color=GOLD, font=FONT_SMALL, bg=BG_DARK).pack(side='left', padx=(16,0))
        self.time_end = TimeCombo(tr); self.time_end.pack(side='left', padx=8)

        lbl("Примечание"); self.ent_notes = OEntry(form); self.ent_notes.pack(fill='x', ipady=5)

        # Столы - схема
        OLabel(form, "Выберите столики (кликните по столу для выбора/снятия):",
            color=GOLD, font=FONT_SMALL, bg=BG_DARK).pack(anchor='w', pady=(8,2))
        
        self.tables_frame = OCard(form)
        self.tables_frame.pack(fill='both', expand=True, pady=(0,10))
        self.tables_canvas = tk.Canvas(self.tables_frame, bg=BG_CARD, highlightthickness=0)
        self.tables_canvas.pack(fill='both', expand=True)
        self.tables_canvas.bind('<Configure>', lambda e: self._draw_tables())
        self.tables_canvas.bind('<Button-1>', self._on_table_click)
        
        self._selected_tables = []
        self._all_tables = TableModel.get_all()
        
        # Информация о выбранных столах
        self.selected_info = OLabel(form, "Выбрано столов: 0", 
                                    color=MUTED, font=FONT_SMALL, bg=BG_DARK)
        self.selected_info.pack(anchor='w', pady=(4,0))
        
        # Кнопки управления столами
        btn_frame = OFrame(form, bg=BG_DARK)
        btn_frame.pack(fill='x', pady=8)
        OButton(btn_frame, "Выбрать все", command=self._select_all_tables, 
                variant='secondary').pack(side='left', padx=(0,8))
        OButton(btn_frame, "Снять все", command=self._clear_all_tables, 
                variant='danger').pack(side='left')

        # Если есть предустановленные столы
        if self.preset_table_ids:
            self._selected_tables = self.preset_table_ids.copy()

        if self.reservation:
            r = self.reservation
            self.ent_name.insert(0, r['client_name'])
            self.ent_phone.insert(0, r['client_phone'])
            self.ent_guests.insert(0, str(r['guests_count']))
            self.date_entry.set_date(r['reservation_date'])
            self.time_start.set(str(r['reservation_time'])[:5])
            if r.get('end_time'): self.time_end.set(str(r['end_time'])[:5])
            self.ent_notes.insert(0, r.get('notes',''))
            
            # Если редактируем, выбираем уже назначенные столы
            if r.get('table_ids'):
                self._selected_tables = [int(x) for x in str(r['table_ids']).split(',') if x]
        else:
            self.ent_guests.insert(0,'2')

        btns = OFrame(self, bg=BG_DARK); btns.pack(fill='x', padx=PAD_LG, pady=PAD)
        OButton(btns, "Сохранить", command=self._save, variant='gold').pack(side='left', padx=(0,8))
        OButton(btns, "Отмена", command=self.destroy, variant='ghost').pack(side='left')
        
        self._draw_tables()
        self._update_capacity_info()

    def _draw_tables(self):
        """Нарисовать схему столов с возможностью выбора"""
        c = self.tables_canvas
        c.delete('all')
        w = c.winfo_width() or 500
        cols = 4
        pad = 15
        cell_w = (w - pad * 2) // cols
        cell_h = 95
        
        self._rects = []
        self._table_capacities = {}
        
        for i, t in enumerate(self._all_tables):
            col = i % cols
            row = i // cols
            x1 = pad + col * cell_w + 6
            y1 = pad + row * cell_h + 6
            x2 = x1 + cell_w - 12
            y2 = y1 + cell_h - 12
            
            is_selected = t['id'] in self._selected_tables
            self._table_capacities[t['id']] = t['capacity']
            
            c.create_rectangle(x1, y1, x2, y2, fill=GOLD_DARK if is_selected else BG_CARD, 
                            outline=GOLD if is_selected else BORDER, 
                            width=3 if is_selected else 1)
            
            cx = (x1 + x2) // 2
            c.create_text(cx, y1 + 18, text=f"Стол №{t['number']}", font=FONT_H2, fill=GOLD if is_selected else CREAM)
            c.create_text(cx, y1 + 40, text=f"Мест: {t['capacity']}", font=FONT_SMALL, fill=MUTED)
            c.create_text(cx, y1 + 58, text=t.get('location', ''), font=FONT_TINY, fill=MUTED)
            
            if is_selected:
                c.create_text(cx, y1 + 76, text="✓", font=FONT_H1, fill=SUCCESS)
            
            self._rects.append({'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2, 'table': t})
        
        self.selected_info.configure(text=f"Выбрано столов: {len(self._selected_tables)}")
        self._update_capacity_info()

    def _on_table_click(self, event):
        """Обработка клика по столу для выбора/снятия"""
        for r in self._rects:
            if r['x1'] <= event.x <= r['x2'] and r['y1'] <= event.y <= r['y2']:
                table_id = r['table']['id']
                if table_id in self._selected_tables:
                    self._selected_tables.remove(table_id)
                else:
                    self._selected_tables.append(table_id)
                self._draw_tables()
                break

    def _select_all_tables(self):
        """Выбрать все столы"""
        self._selected_tables = [t['id'] for t in self._all_tables]
        self._draw_tables()

    def _clear_all_tables(self):
        """Снять все столы"""
        self._selected_tables = []
        self._draw_tables()


    def _on_time_change(self):
        """Сохранить выбранные столы при изменении времени"""
        # Просто обновляем информацию о вместимости
        self._update_capacity_info()
        # Сохраняем выбранные столы в атрибут
        if hasattr(self, '_selected_tables'):
            selected = self.lb_tables.curselection()
            self._selected_tables = list(selected)

    def _update_capacity_info(self, event=None):
        """Обновить информацию о вместимости выбранных столов"""
        try:
            guests_text = self.ent_guests.get().strip()
            guests = int(guests_text) if guests_text else 0
            
            if self._selected_tables:
                total_capacity = sum(self._table_capacities.get(tid, 0) for tid in self._selected_tables)
                
                if guests > 0:
                    if total_capacity < guests:
                        self.capacity_label.configure(
                            text=f"⚠️ Не хватает мест: выбрано {total_capacity}, нужно {guests}",
                            fg=ERROR)
                    else:
                        self.capacity_label.configure(
                            text=f"✓ Достаточно мест: выбрано {total_capacity} для {guests} гостей",
                            fg=SUCCESS)
                else:
                    self.capacity_label.configure(
                        text=f"Выбрано мест: {total_capacity} (укажите количество гостей)",
                        fg=MUTED)
            else:
                self.capacity_label.configure(text="Выберите столики", fg=MUTED)
        except ValueError:
            pass

    def _check_date(self, event=None):
        """Проверить выбранную дату и показать предупреждение"""
        try:
            selected_date = self.date_entry.get_date()
            today = date.today()
            
            if selected_date < today:
                self.capacity_label.configure(
                    text=f"⚠️ Дата {selected_date.strftime('%d.%m.%Y')} уже прошла!",
                    fg=ERROR
                )
            elif selected_date == today:
                self.capacity_label.configure(
                    text=f"📅 Сегодня {selected_date.strftime('%d.%m.%Y')} (проверьте время)",
                    fg=WARNING
                )
            else:
                self.capacity_label.configure(
                    text=f"📅 Дата {selected_date.strftime('%d.%m.%Y')} - доступно",
                    fg=SUCCESS
                )
        except:
            pass

    def _save(self):
        try:
            name = self.ent_name.get().strip()
            phone = self.ent_phone.get().strip()
            guests = int(self.ent_guests.get().strip())
            notes = self.ent_notes.get().strip()
            res_date = self.date_entry.get_date()
            res_time = self.time_start.get()
            end_time = self.time_end.get() or None

            today = date.today()
            if res_date < today:
                raise ValueError(f"Дата брони не может быть в прошлом!\nСегодня: {today.strftime('%d.%m.%Y')}")
            
            if res_date == today:
                now = datetime.now().time()
                current_time = datetime.strptime(res_time, '%H:%M').time()
                if current_time < now:
                    raise ValueError(f"Время брони не может быть в прошлом!\nСейчас: {now.strftime('%H:%M')}")
            
            if not name or not phone:
                raise ValueError("Заполните обязательные поля")
            if guests <= 0:
                raise ValueError("Количество гостей должно быть больше 0")
            
            if not self._selected_tables:
                raise ValueError("Выберите хотя бы один столик")
            
            table_ids = self._selected_tables

            # Проверка конфликтов
            if self.reservation:
                conflicts = ReservationModel._check_conflict(
                    table_ids, res_date, res_time, end_time, 
                    exclude_reservation_id=self.reservation['id']
                )
            else:
                conflicts = ReservationModel._check_conflict(table_ids, res_date, res_time, end_time)

            if conflicts:
                conflict_info = []
                for c in conflicts:
                    tables = c.get('tables', '')
                    start = str(c['reservation_time'])[:5]
                    end = str(c['end_time'])[:5] if c.get('end_time') else '—'
                    conflict_info.append(f"Бронь №{c['id']} ({c['client_name']}) на столе {tables}, {start}-{end}")
                raise ValueError(
                    f"Обнаружены пересечения с другими бронями:\n" + "\n".join(conflict_info)
                )
            
            # Проверка вместимости
            total_capacity = sum(self._table_capacities.get(tid, 0) for tid in table_ids)
            if total_capacity < guests:
                raise ValueError(f"Недостаточно мест: выбрано {total_capacity}, требуется {guests}")
            
            if self.reservation:
                ReservationModel.update(
                    reservation_id=self.reservation['id'],
                    client_name=name,
                    res_date=res_date,
                    res_time=res_time,
                    end_time=end_time,
                    guests_count=guests,
                    table_ids=table_ids,
                    notes=notes,
                    client_phone=phone if phone else None
                )
                msg = f"Бронь №{self.reservation['id']} обновлена"
            else:
                rid = ReservationModel.create(name, phone, res_date, res_time, guests,
                    table_ids, notes, client_id=self.user.get('id'), end_time=end_time)
                msg = f"Бронь №{rid} создана"
            
            if self.on_save:
                self.on_save()
            show_toast(self.master, msg, 'success')
            self.destroy()
            
        except (ValueError, Exception) as e:
            messagebox.showerror("Ошибка", str(e), parent=self)


# ── Смены ────────────────────────────────────────────────────────────────────
# ── Смены ────────────────────────────────────────────────────────────────────

class ShiftsView(BasePage):
    def _build(self):
        self._page_header("График смен")
        
        # Панель управления с фильтром по дате
        ctrl = OFrame(self, bg=BG_DARK)
        ctrl.pack(fill='x', padx=PAD_LG, pady=PAD)
        
        OLabel(ctrl, "Дата:", bg=BG_DARK).pack(side='left')
        self.date_filter = DateEntry(ctrl)
        self.date_filter.pack(side='left', padx=6)
        self.date_filter.set_date(date.today())
        
        OButton(ctrl, "🔍 Показать", command=self.refresh, variant='primary').pack(side='left', padx=8)
        
        # Кнопки действий
        tb = OFrame(self, bg=BG_DARK)
        tb.pack(fill='x', padx=PAD_LG, pady=PAD)
        OButton(tb, "+ Создать смену", command=self._new, variant='gold').pack(side='left', padx=(0,8))
        OButton(tb, "✏️ Редактировать смену", command=self._edit, variant='secondary').pack(side='left', padx=(0,8))
        OButton(tb, "❌ Закрыть смену", command=self._close_shift, variant='danger').pack(side='left')
        OButton(tb, "🔄 Перераспределить столы на дату", command=self._redistribute_tables, variant='secondary').pack(side='left', padx=(0,8))

        cols = ('id','waiter','date','start','end','tables','status')
        headers = ('№','Официант','Дата','Начало','Конец','Столики','Статус')
        widths = (50,180,100,80,80,130,110)
        frm, self.tree = self._make_tree(self, cols)
        frm.pack(fill='both', expand=True, padx=PAD_LG, pady=(0,PAD_LG))
        for col,hdr,w in zip(cols,headers,widths):
            self.tree.heading(col, text=hdr)
            self.tree.column(col, width=w)
        
        # Двойной клик для редактирования
        self.tree.bind('<Double-Button-1>', lambda e: self._edit())
        self.refresh()

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        
        # Получаем все смены
        shifts = ShiftModel.get_all()
        
        # Фильтруем по дате если выбрана
        try:
            filter_date = self.date_filter.get_date()
            if filter_date:
                shifts = [s for s in shifts if s['shift_date'] == filter_date]
        except:
            pass
        
        for s in shifts:
            self.tree.insert('','end', iid=str(s['id']), values=(
                s['id'], s['waiter_name'], str(s['shift_date']),
                str(s['start_time'])[:5], str(s['end_time'])[:5],
                s.get('table_numbers','—'), STATUS_LABELS.get(s['status'],s['status'])))

    def _new(self):
        ShiftDialog(self, on_save=self.refresh)

    def _edit(self):
        """Редактировать выбранную смену"""
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Выбор", "Выберите смену для редактирования", parent=self)
            return
        
        shift_id = int(sel[0])
        # Получаем полные данные смены
        shift = execute_query("""
            SELECT s.*, u.full_name AS waiter_name,
                GROUP_CONCAT(DISTINCT t.id ORDER BY t.id) AS table_ids,
                GROUP_CONCAT(DISTINCT t.number ORDER BY t.number) AS table_numbers
            FROM shifts s 
            JOIN users u ON s.waiter_id = u.id
            LEFT JOIN shift_tables st ON st.shift_id = s.id
            LEFT JOIN tables t ON st.table_id = t.id
            WHERE s.id = %s
            GROUP BY s.id
        """, (shift_id,), fetch_one=True)
        
        if shift:
            # Предупреждение для открытых смен
            if shift['status'] == 'open':
                if not messagebox.askyesno("Редактирование", 
                        "Смена уже открыта. Изменение времени или столиков может повлиять на активные заказы.\n\n"
                        "Продолжить?", parent=self):
                    return
            
            # Предупреждение для закрытых смен
            if shift['status'] == 'closed':
                if not messagebox.askyesno("Редактирование", 
                        "Смена уже закрыта. Изменение повлияет на статистику и отчеты.\n\n"
                        "Продолжить?", parent=self):
                    return
            
            ShiftEditDialog(self, shift=shift, on_save=self.refresh)

    def _close_shift(self):
        """Закрыть выбранную смену"""
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Выбор", "Выберите смену для закрытия", parent=self)
            return
        
        shift_id = int(sel[0])
        shift = execute_query("""
            SELECT s.*, u.full_name AS waiter_name 
            FROM shifts s 
            JOIN users u ON s.waiter_id = u.id 
            WHERE s.id=%s
        """, (shift_id,), fetch_one=True)
        
        if not shift:
            messagebox.showerror("Ошибка", "Смена не найдена", parent=self)
            return
        
        if shift['status'] == 'closed':
            messagebox.showinfo("Инфо", "Смена уже закрыта", parent=self)
            return
        
        if shift['status'] != 'open':
            messagebox.showwarning("Ошибка", "Можно закрыть только открытую смену", parent=self)
            return
        
        if messagebox.askyesno("Закрытие смены", 
                f"Закрыть смену №{shift_id}?\n\n"
                f"Официант: {shift['waiter_name']}\n"
                f"Дата: {shift['shift_date']}\n"
                f"Время: {shift['start_time']} - {shift['end_time']}", 
                parent=self):
            ShiftModel.close_shift(shift_id, shift['waiter_id'])
            self.refresh()
            show_toast(self, f"Смена №{shift_id} закрыта", 'success')

    def _redistribute_tables(self):
        try:
            filter_date = self.date_filter.get_date()
        except:
            filter_date = date.today()
        result = ShiftModel.distribute_free_tables_among_all_shifts(filter_date)
        messagebox.showinfo("Результат", result, parent=self)
        self.refresh()


class ShiftDialog(tk.Toplevel):
    def __init__(self, master, on_save=None):
        super().__init__(master)
        self.on_save = on_save
        self.title("Новая смена")
        self.configure(bg=BG_DARK)
        self.geometry("700x780")
        self.grab_set()
        self.transient(master)
        self._selected_tables = []
        self._build()

    def _build(self):
        OLabel(self,"Создать смену",color=GOLD,font=FONT_H1,bg=BG_DARK).pack(pady=PAD_LG)
        Divider(self).pack(fill='x',padx=PAD_LG)
        
        form = OFrame(self,bg=BG_DARK)
        form.pack(fill='both',expand=True,padx=PAD_LG,pady=PAD)

        # Официант
        OLabel(form,"Официант *:",color=GOLD,font=FONT_SMALL,bg=BG_DARK).pack(anchor='w',pady=(8,2))
        waiters = AuthModel.get_all_waiters()
        self._waiter_ids = [w['id'] for w in waiters]
        waiter_names = [w['full_name'] for w in waiters]
        if not waiter_names:
            waiter_names = ['— нет официантов —']
        self.cmb_waiter = OCombobox(form, values=waiter_names, state='readonly')
        self.cmb_waiter.pack(fill='x')
        if waiters:
            self.cmb_waiter.current(0)

        # Дата
        OLabel(form,"Дата смены *:",color=GOLD,font=FONT_SMALL,bg=BG_DARK).pack(anchor='w',pady=(8,2))
        self.date_entry = DateEntry(form)
        self.date_entry.pack(anchor='w')
        self.date_entry.set_date(date.today())

        # Время
        tr = OFrame(form,bg=BG_DARK)
        tr.pack(fill='x',pady=(8,2))
        OLabel(tr,"Начало *:",color=GOLD,font=FONT_SMALL,bg=BG_DARK).pack(side='left')
        self.cb_start = TimeCombo(tr)
        self.cb_start.set('09:00')
        self.cb_start.pack(side='left',padx=8)
        OLabel(tr,"Конец *:",color=GOLD,font=FONT_SMALL,bg=BG_DARK).pack(side='left',padx=(16,0))
        self.cb_end = TimeCombo(tr)
        self.cb_end.set('21:00')
        self.cb_end.pack(side='left',padx=8)

        # Столы - схема
        OLabel(form,"Выберите столики (кликните по столу для выбора/снятия):",
               color=GOLD,font=FONT_SMALL,bg=BG_DARK).pack(anchor='w',pady=(8,2))
        
        # Фрейм для схемы столов
        self.tables_frame = OCard(form)
        self.tables_frame.pack(fill='both', expand=True, pady=(0,10))
        self.tables_canvas = tk.Canvas(self.tables_frame, bg=BG_CARD, highlightthickness=0)
        self.tables_canvas.pack(fill='both', expand=True)
        self.tables_canvas.bind('<Configure>', lambda e: self._draw_tables())
        self.tables_canvas.bind('<Button-1>', self._on_table_click)
        
        # Информация о выбранных столах
        self.info_label = OLabel(form, "Выбрано столов: 0", 
                                  color=MUTED, font=FONT_SMALL, bg=BG_DARK)
        self.info_label.pack(anchor='w', pady=(4,0))
        
        # Кнопки управления столами
        btn_frame = OFrame(form, bg=BG_DARK)
        btn_frame.pack(fill='x', pady=8)
        OButton(btn_frame, "Выбрать все", command=self._select_all_tables, 
                variant='secondary').pack(side='left', padx=(0,8))
        OButton(btn_frame, "Снять все", command=self._clear_all_tables, 
                variant='danger').pack(side='left')

        btns = OFrame(self,bg=BG_DARK)
        btns.pack(fill='x',padx=PAD_LG,pady=PAD)
        OButton(btns,"Создать",command=self._save,variant='gold').pack(side='left',padx=(0,8))
        OButton(btns,"Отмена",command=self.destroy,variant='ghost').pack(side='left')
        
        self._draw_tables()

    def _draw_tables(self):
        """Нарисовать схему столов с возможностью выбора"""
        c = self.tables_canvas
        c.delete('all')
        w = c.winfo_width() or 600
        cols = 5
        pad = 20
        cell_w = (w - pad * 2) // cols
        cell_h = 100
        
        self._rects = []
        self._all_tables = TableModel.get_all()
        
        for i, t in enumerate(self._all_tables):
            col = i % cols
            row = i // cols
            x1 = pad + col * cell_w + 8
            y1 = pad + row * cell_h + 8
            x2 = x1 + cell_w - 16
            y2 = y1 + cell_h - 16
            
            is_selected = t['id'] in self._selected_tables
            
            c.create_rectangle(x1, y1, x2, y2, fill=GOLD_DARK if is_selected else BG_CARD, 
                            outline=GOLD if is_selected else BORDER, 
                            width=3 if is_selected else 1)
            
            cx = (x1 + x2) // 2
            c.create_text(cx, y1 + 20, text=f"Стол №{t['number']}", font=FONT_H2, fill=GOLD if is_selected else CREAM)
            c.create_text(cx, y1 + 45, text=f"Мест: {t['capacity']}", font=FONT_SMALL, fill=MUTED)
            c.create_text(cx, y1 + 65, text=t.get('location', ''), font=FONT_TINY, fill=MUTED)
            
            if is_selected:
                c.create_text(cx, y1 + 82, text="✓", font=FONT_H1, fill=SUCCESS)
            
            self._rects.append({'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2, 'table': t})
        
        self.info_label.configure(text=f"Выбрано столов: {len(self._selected_tables)}")

    def _on_table_click(self, event):
        """Обработка клика по столу для выбора/снятия"""
        for r in self._rects:
            if r['x1'] <= event.x <= r['x2'] and r['y1'] <= event.y <= r['y2']:
                table_id = r['table']['id']
                if table_id in self._selected_tables:
                    self._selected_tables.remove(table_id)
                else:
                    self._selected_tables.append(table_id)
                self._draw_tables()
                break

    def _select_all_tables(self):
        """Выбрать все столы"""
        self._selected_tables = [t['id'] for t in self._all_tables]
        self._draw_tables()

    def _clear_all_tables(self):
        """Снять все столы"""
        self._selected_tables = []
        self._draw_tables()

    def _save(self):
        try:
            idx = self.cmb_waiter.current()
            if idx < 0 or not self._waiter_ids:
                raise ValueError("Выберите официанта")
            waiter_id = self._waiter_ids[idx]
            
            shift_date = self.date_entry.get_date()
            start = self.cb_start.get()
            end = self.cb_end.get()
            
            # Проверка времени
            def normalize_time(t):
                parts = t.split(':')
                if len(parts) == 2:
                    h = parts[0].zfill(2)
                    return f"{h}:{parts[1]}"
                return t
        
            start_normalized = normalize_time(start)
            end_normalized = normalize_time(end)
            
            from datetime import datetime as dt
            start_time = dt.strptime(start_normalized, '%H:%M').time()
            end_time = dt.strptime(end_normalized, '%H:%M').time()
            
            if start_time >= end_time:
                raise ValueError(f"Время начала ({start}) должно быть раньше времени окончания ({end})")
            
            # Проверка даты
            today = date.today()
            if shift_date < today:
                if not messagebox.askyesno("Дата в прошлом", 
                        f"Вы выбрали дату {shift_date.strftime('%d.%m.%Y')}, которая уже прошла.\n\n"
                        "Создать смену на прошедшую дату?", parent=self):
                    return
            
            if shift_date == today:
                now = datetime.now().time()
                if start_time < now:
                    if not messagebox.askyesno("Время в прошлом", 
                            f"Время начала {start} уже прошло (сейчас {now.strftime('%H:%M')}).\n\n"
                            "Создать смену на прошедшее время?", parent=self):
                        return
            
            if not self._selected_tables:
                raise ValueError("Выберите хотя бы один столик")
            # Проверка конфликтов с другими сменами
            conflicts = ShiftModel.check_table_conflict(
                self._selected_tables, shift_date, start, end
            )
            if conflicts:
                conflict_info = []
                for c in conflicts:
                    conflict_info.append(
                        f"Смена №{c['id']} (официант {c['waiter_name']}) "
                        f"столы {c['tables']}, {str(c['start_time'])[:5]}-{str(c['end_time'])[:5]}"
                    )
                raise ValueError(
                    "Обнаружены пересечения с другими сменами:\n" + "\n".join(conflict_info)
                )
            
            sid = ShiftModel.create(waiter_id, shift_date, start, end)
            if self._selected_tables:
                ShiftModel.assign_tables(sid, self._selected_tables)
            
            if self.on_save:
                self.on_save()
            show_toast(self.master, f"Смена №{sid} создана", 'success')
            self.destroy()
            
        except (ValueError, Exception) as e:
            messagebox.showerror("Ошибка", str(e), parent=self)


class ShiftEditDialog(tk.Toplevel):
    """Диалог редактирования смены"""
    def __init__(self, master, shift, on_save=None):
        super().__init__(master)
        self.shift = shift
        self.on_save = on_save
        self.title(f"Редактирование смены №{shift['id']}")
        self.configure(bg=BG_DARK)
        self.geometry("580x820")
        self.grab_set()
        self._build()

    def _build(self):
        OLabel(self, f"Редактирование смены №{self.shift['id']}", 
            color=GOLD, font=FONT_H1, bg=BG_DARK).pack(pady=PAD_LG)
        Divider(self).pack(fill='x', padx=PAD_LG)
        
        form = OFrame(self, bg=BG_DARK)
        form.pack(fill='both', expand=True, padx=PAD_LG, pady=PAD)

        # Информация о текущем состоянии
        info_frame = OFrame(form, bg=BG_DARK)
        info_frame.pack(fill='x', pady=(0, 10))
        
        status_text = {
            'scheduled': '⏳ Запланирована',
            'open': '🟢 Открыта',
            'closed': '🔴 Закрыта'
        }.get(self.shift['status'], self.shift['status'])
        
        status_color = {
            'scheduled': WARNING,
            'open': SUCCESS,
            'closed': ERROR
        }.get(self.shift['status'], CREAM)
        
        OLabel(info_frame, f"Статус: {status_text}", 
            color=status_color, font=FONT_SMALL, bg=BG_DARK).pack(anchor='w')
        OLabel(info_frame, f"Официант: {self.shift['waiter_name']}", 
            color=CREAM, font=FONT_SMALL, bg=BG_DARK).pack(anchor='w')
        OLabel(info_frame, f"Дата: {self.shift['shift_date']}", 
            color=MUTED, font=FONT_SMALL, bg=BG_DARK).pack(anchor='w')
        
        if self.shift['status'] == 'open':
            OLabel(info_frame, "⚠️ Смена открыта — изменение может повлиять на активные заказы", 
                color=WARNING, font=FONT_SMALL, bg=BG_DARK).pack(anchor='w', pady=(4,0))
        elif self.shift['status'] == 'closed':
            OLabel(info_frame, "⚠️ Смена закрыта — изменение повлияет на статистику", 
                color=ERROR, font=FONT_SMALL, bg=BG_DARK).pack(anchor='w', pady=(4,0))
        
        Divider(form).pack(fill='x', pady=10)

        # Выбор статуса
        status_frame = OFrame(form, bg=BG_DARK)
        status_frame.pack(fill='x', pady=(0, 10))

        OLabel(status_frame, "Статус смены:", color=GOLD, font=FONT_SMALL, bg=BG_DARK).pack(anchor='w', pady=(0,4))

        # Список доступных статусов для выбора
        status_options = [
            ('scheduled', '⏳ Запланирована'),
            ('open', '🟢 Открыта'),
            ('closed', '🔴 Закрыта')
        ]

        self.status_var = tk.StringVar(value=self.shift['status'])
        self.cmb_status = OCombobox(status_frame, values=[v for _, v in status_options], state='readonly')
        self.cmb_status.pack(fill='x', ipady=5)

        # Устанавливаем текущий статус
        for i, (val, label) in enumerate(status_options):
            if val == self.shift['status']:
                self.cmb_status.current(i)
                break

        # Предупреждение при смене статуса
        self.cmb_status.bind('<<ComboboxSelected>>', self._on_status_change)

        Divider(form).pack(fill='x', pady=10)

        # Поля для редактирования
        OLabel(form,"Дата смены *:",color=GOLD,font=FONT_SMALL,bg=BG_DARK).pack(anchor='w',pady=(8,2))
        self.date_entry = DateEntry(form)
        self.date_entry.pack(anchor='w')
        self.date_entry.set_date(self.shift['shift_date'])

        tr = OFrame(form,bg=BG_DARK)
        tr.pack(fill='x',pady=(8,2))
        OLabel(tr,"Начало *:",color=GOLD,font=FONT_SMALL,bg=BG_DARK).pack(side='left')
        self.cb_start = TimeCombo(tr)
        self.cb_start.set(str(self.shift['start_time'])[:5])
        self.cb_start.pack(side='left',padx=8)
        OLabel(tr,"Конец *:",color=GOLD,font=FONT_SMALL,bg=BG_DARK).pack(side='left',padx=(16,0))
        self.cb_end = TimeCombo(tr)
        self.cb_end.set(str(self.shift['end_time'])[:5])
        self.cb_end.pack(side='left',padx=8)

        # Столы - схема
        OLabel(form,"Выберите столики (кликните по столу для выбора/снятия):",
            color=GOLD,font=FONT_SMALL,bg=BG_DARK).pack(anchor='w',pady=(8,2))
        
        # Фрейм для схемы столов
        self.tables_frame = OCard(form)
        self.tables_frame.pack(fill='both', expand=True, pady=(0,10))
        self.tables_canvas = tk.Canvas(self.tables_frame, bg=BG_CARD, highlightthickness=0)
        self.tables_canvas.pack(fill='both', expand=True)
        self.tables_canvas.bind('<Configure>', lambda e: self._draw_tables())
        self.tables_canvas.bind('<Button-1>', self._on_table_click)
        
        # Получаем ID столов, назначенных на эту смену
        self._assigned_table_ids = []
        if self.shift.get('table_ids'):
            self._assigned_table_ids = [int(x) for x in self.shift['table_ids'].split(',') if x]
        self._selected_tables = self._assigned_table_ids.copy()
        
        # Информация о выбранных столах
        self.info_label = OLabel(form, f"Выбрано столов: {len(self._selected_tables)}", 
                                color=MUTED, font=FONT_SMALL, bg=BG_DARK)
        self.info_label.pack(anchor='w', pady=(4,0))
        
        # Кнопки управления столами
        btn_frame = OFrame(form, bg=BG_DARK)
        btn_frame.pack(fill='x', pady=8)
        OButton(btn_frame, "Выбрать все", command=self._select_all_tables, 
                variant='secondary').pack(side='left', padx=(0,8))
        OButton(btn_frame, "Снять все", command=self._clear_all_tables, 
                variant='danger').pack(side='left')

        btns = OFrame(self,bg=BG_DARK)
        btns.pack(fill='x',padx=PAD_LG,pady=PAD)
        OButton(btns,"Сохранить изменения",command=self._save,variant='gold').pack(side='left',padx=(0,8))
        OButton(btns,"Отмена",command=self.destroy,variant='ghost').pack(side='left')
        
        self._draw_tables()

    def _on_status_change(self, event=None):
        """Обработка изменения статуса"""
        selected = self.cmb_status.get()
        status_map = {
            '⏳ Запланирована': 'scheduled',
            '🟢 Открыта': 'open',
            '🔴 Закрыта': 'closed'
        }
        new_status = status_map.get(selected, 'scheduled')
        current_status = self.shift['status']
        
        # Если статус не меняется
        if new_status == current_status:
            return
        
        # Предупреждения при смене статуса
        if new_status == 'open' and current_status == 'scheduled':
            if not messagebox.askyesno("Открыть смену", 
                    "Вы уверены, что хотите открыть смену?\n\n"
                    "После открытия смены официант сможет начать работу.", parent=self):
                # Возвращаем предыдущий статус
                for i, (val, label) in enumerate([
                    ('scheduled', '⏳ Запланирована'),
                    ('open', '🟢 Открыта'),
                    ('closed', '🔴 Закрыта')
                ]):
                    if val == current_status:
                        self.cmb_status.current(i)
                        break
                return
        
        if new_status == 'closed' and current_status != 'closed':
            if not messagebox.askyesno("Закрыть смену", 
                    "Вы уверены, что хотите закрыть смену?\n\n"
                    "Смену можно будет только редактировать, но официант не сможет её открыть.", parent=self):
                # Возвращаем предыдущий статус
                for i, (val, label) in enumerate([
                    ('scheduled', '⏳ Запланирована'),
                    ('open', '🟢 Открыта'),
                    ('closed', '🔴 Закрыта')
                ]):
                    if val == current_status:
                        self.cmb_status.current(i)
                        break
                return
        
        # Если статус меняется на scheduled - предупреждение
        if new_status == 'scheduled' and current_status == 'open':
            if not messagebox.askyesno("Перевести в запланирована", 
                    "Вы уверены, что хотите перевести открытую смену в статус «Запланирована»?\n\n"
                    "Официант не сможет работать по этой смене.", parent=self):
                # Возвращаем предыдущий статус
                for i, (val, label) in enumerate([
                    ('scheduled', '⏳ Запланирована'),
                    ('open', '🟢 Открыта'),
                    ('closed', '🔴 Закрыта')
                ]):
                    if val == current_status:
                        self.cmb_status.current(i)
                        break
                return

    def _update_selection_info(self, event=None):
        """Обновить информацию о количестве выбранных столов"""
        sel = self.lb_tables.curselection()
        count = len(sel)
        if count == 0:
            self.info_label.configure(text="⚠️ Не выбрано ни одного стола", fg=ERROR)
        else:
            self.info_label.configure(text=f"✓ Выбрано столов: {count}", fg=SUCCESS)

    def _draw_tables(self):
        """Нарисовать схему столов с возможностью выбора"""
        c = self.tables_canvas
        c.delete('all')
        w = c.winfo_width() or 600
        cols = 5
        pad = 20
        cell_w = (w - pad * 2) // cols
        cell_h = 100
        
        self._rects = []
        self._all_tables = TableModel.get_all()
        
        for i, t in enumerate(self._all_tables):
            col = i % cols
            row = i // cols
            x1 = pad + col * cell_w + 8
            y1 = pad + row * cell_h + 8
            x2 = x1 + cell_w - 16
            y2 = y1 + cell_h - 16
            
            is_selected = t['id'] in self._selected_tables
            
            c.create_rectangle(x1, y1, x2, y2, fill=GOLD_DARK if is_selected else BG_CARD, 
                            outline=GOLD if is_selected else BORDER, 
                            width=3 if is_selected else 1)
            
            cx = (x1 + x2) // 2
            c.create_text(cx, y1 + 20, text=f"Стол №{t['number']}", font=FONT_H2, fill=GOLD if is_selected else CREAM)
            c.create_text(cx, y1 + 45, text=f"Мест: {t['capacity']}", font=FONT_SMALL, fill=MUTED)
            c.create_text(cx, y1 + 65, text=t.get('location', ''), font=FONT_TINY, fill=MUTED)
            
            if is_selected:
                c.create_text(cx, y1 + 82, text="✓", font=FONT_H1, fill=SUCCESS)
            
            self._rects.append({'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2, 'table': t})
        
        self.info_label.configure(text=f"Выбрано столов: {len(self._selected_tables)}")

    def _on_table_click(self, event):
        """Обработка клика по столу для выбора/снятия"""
        for r in self._rects:
            if r['x1'] <= event.x <= r['x2'] and r['y1'] <= event.y <= r['y2']:
                table_id = r['table']['id']
                if table_id in self._selected_tables:
                    self._selected_tables.remove(table_id)
                else:
                    self._selected_tables.append(table_id)
                self._draw_tables()
                break

    def _select_all_tables(self):
        """Выбрать все столы"""
        self._selected_tables = [t['id'] for t in self._all_tables]
        self._draw_tables()

    def _clear_all_tables(self):
        """Снять все столы"""
        self._selected_tables = []
        self._draw_tables()

    def _save(self):
        try:
            shift_date = self.date_entry.get_date()
            start = self.cb_start.get()
            end = self.cb_end.get()
            
            # Получаем выбранный статус
            status_text = self.cmb_status.get()
            status_map = {
                '⏳ Запланирована': 'scheduled',
                '🟢 Открыта': 'open',
                '🔴 Закрыта': 'closed'
            }
            new_status = status_map.get(status_text, 'scheduled')
            
            # Проверка времени
            def normalize_time(t):
                parts = t.split(':')
                if len(parts) == 2:
                    h = parts[0].zfill(2)
                    return f"{h}:{parts[1]}"
                return t
        
            start_normalized = normalize_time(start)
            end_normalized = normalize_time(end)
            
            from datetime import datetime as dt
            start_time = dt.strptime(start_normalized, '%H:%M').time()
            end_time = dt.strptime(end_normalized, '%H:%M').time()
            
            if start_time >= end_time:
                raise ValueError(f"Время начала ({start}) должно быть раньше времени окончания ({end})")
            
            # Проверка даты
            today = date.today()
            if shift_date < today:
                if not messagebox.askyesno("Дата в прошлом", 
                        f"Вы выбрали дату {shift_date.strftime('%d.%m.%Y')}, которая уже прошла.\n\n"
                        "Изменить смену на прошедшую дату?", parent=self):
                    return
            
            if shift_date == today:
                now = datetime.now().time()
                if start_time < now:
                    if not messagebox.askyesno("Время в прошлом", 
                            f"Время начала {start} уже прошло (сейчас {now.strftime('%H:%M')}).\n\n"
                            "Изменить смену на прошедшее время?", parent=self):
                        return
            
            if not self._selected_tables:
                raise ValueError("Выберите хотя бы один столик")
            # Проверка конфликтов с другими сменами (исключая текущую)
            conflicts = ShiftModel.check_table_conflict(
                self._selected_tables, shift_date, start, end, exclude_shift_id=self.shift['id']
            )
            if conflicts:
                conflict_info = []
                for c in conflicts:
                    conflict_info.append(
                        f"Смена №{c['id']} (официант {c['waiter_name']}) "
                        f"столы {c['tables']}, {str(c['start_time'])[:5]}-{str(c['end_time'])[:5]}"
                    )
                raise ValueError(
                    "Обнаружены пересечения с другими сменами:\n" + "\n".join(conflict_info)
                )
            
            # Обновляем смену (включая статус)
            execute_query("""
                UPDATE shifts 
                SET shift_date = %s, start_time = %s, end_time = %s, status = %s
                WHERE id = %s
            """, (shift_date, start, end, new_status, self.shift['id']))
            
            # Обновляем столики
            ShiftModel.assign_tables(self.shift['id'], self._selected_tables)
            
            if self.on_save:
                self.on_save()
            
            show_toast(self.master, f"Смена №{self.shift['id']} обновлена", 'success')
            self.destroy()
            
        except (ValueError, Exception) as e:
            messagebox.showerror("Ошибка", str(e), parent=self)
# ── Заказы (администратор) ──────────────────────────────────────────────────
class AdminOrdersView(BasePage):
    def _build(self):
        self._page_header("Управление заказами", "просмотр и редактирование")
        
        # Панель фильтров
        filter_frame = OFrame(self, bg=BG_DARK)
        filter_frame.pack(fill='x', padx=PAD_LG, pady=(0, PAD))
        
        OLabel(filter_frame, "Статус:", bg=BG_DARK).pack(side='left')
        self.status_filter = OCombobox(filter_frame, values=[
            'Все', 'Составление', 'Оформлен', 'Отменён', 'Принят', 
            'Готовится', 'Готов', 'Выдан', 'Оплачен'
        ], state='readonly', width=15)
        self.status_filter.current(0)
        self.status_filter.pack(side='left', padx=8)
        
        OButton(filter_frame, "🔍 Применить фильтр", command=self.refresh, 
                variant='primary').pack(side='left', padx=(0, 8))
        OButton(filter_frame, "🔄 Обновить", command=self.refresh, 
                variant='secondary').pack(side='left')
        
            # Панель выбора даты (НОВАЯ)
        date_frame = OFrame(self, bg=BG_DARK)
        date_frame.pack(fill='x', padx=PAD_LG, pady=(4, PAD))
        
        OLabel(date_frame, "Дата:", bg=BG_DARK).pack(side='left')
        self.date_entry = DateEntry(date_frame)
        self.date_entry.pack(side='left', padx=6)
        self.date_entry.set_date(date.today())  # по умолчанию сегодня
        self.selected_date = date.today()       # сохраняем для фильтрации
        
        OButton(date_frame, "Показать", command=self._apply_date_filter, variant='primary').pack(side='left', padx=4)
        OButton(date_frame, "Все даты", command=self._show_all_orders, variant='secondary').pack(side='left', padx=4)
        OButton(date_frame, "Обновить", command=self.refresh, variant='secondary').pack(side='left', padx=4)
        
        # Кнопки действий - ДОБАВЛЯЕМ "Создать заказ"
        tb = OFrame(self, bg=BG_DARK)
        tb.pack(fill='x', padx=PAD_LG, pady=PAD)
        OButton(tb, "➕ Создать заказ", command=self._create_order, 
                variant='gold').pack(side='left', padx=(0,8))
        OButton(tb, "📋 Просмотр заказа", command=self._view_order, 
                variant='secondary').pack(side='left', padx=(0,8))
        OButton(tb, "✏️ Редактировать статус", command=self._edit_status, 
                variant='primary').pack(side='left', padx=(0,8))
        OButton(tb, "✏️ Редактировать заказ", command=self._edit_order,  # ← ДОБАВИТЬ
                variant='primary').pack(side='left', padx=(0,8))
        OButton(tb, "❌ Отменить заказ", command=self._cancel_order, 
                variant='danger').pack(side='left')

        # Таблица заказов
        cols = ('id', 'table', 'waiter', 'status', 'placed_at', 'created_at', 'total')
        headers = ('№', 'Стол', 'Официант', 'Статус', 'Оформлен', 'Создан', 'Сумма ₽')
        widths = (60, 80, 160, 140, 150, 150, 120)
        
        frm, self.tree = self._make_tree(self, cols, heights=18)
        frm.pack(fill='both', expand=True, padx=PAD_LG, pady=(0, PAD_LG))
        
        for col, hdr, w in zip(cols, headers, widths):
            self.tree.heading(col, text=hdr)
            self.tree.column(col, width=w, minwidth=50)
        
        self.refresh()

    def _apply_date_filter(self):
        """Применить фильтр по выбранной дате"""
        try:
            self.selected_date = self.date_entry.get_date()
        except:
            self.selected_date = None
        self.refresh()

    def _show_all_orders(self):
        """Показать заказы за все даты"""
        self.selected_date = None
        self.refresh()
    def _create_order(self):
        """Создать новый заказ"""
        # Получаем список столов
        tables = TableModel.get_all()
        if not tables:
            messagebox.showwarning("Внимание", "Нет доступных столов для создания заказа", parent=self)
            return
        
        # Получаем список официантов
        waiters = AuthModel.get_all_waiters()
        if not waiters:
            messagebox.showwarning("Внимание", "Нет активных официантов", parent=self)
            return
        
        # Открываем диалог создания заказа
        AdminOrderCreateDialog(self, tables=tables, waiters=waiters, on_save=self.refresh)

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        
        # Формируем условия WHERE
        conditions = []
        params = []
        
        # Фильтр по дате
        if self.selected_date is not None:
            conditions.append("DATE(o.created_at) = %s")
            params.append(self.selected_date)
        
        # Фильтр по статусу
        status_filter = self.status_filter.get()
        if status_filter != 'Все':
            status_map = {
                'Составление': 'composing',
                'Оформлен': 'placed',
                'Отменён': 'cancelled',
                'Принят': 'accepted',
                'Готовится': 'cooking',
                'Готов': 'ready',
                'Выдан': 'delivered',
                'Оплачен': 'paid'
            }
            filter_key = status_map.get(status_filter)
            if filter_key:
                conditions.append("o.status = %s")
                params.append(filter_key)
        
        # Строим запрос
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        query = f"""
            SELECT o.*, t.number AS table_number, u.full_name AS waiter_name
            FROM orders o
            JOIN tables t ON o.table_id = t.id
            JOIN users u ON o.waiter_id = u.id
            WHERE {where_clause}
            ORDER BY o.created_at DESC
        """
        orders = execute_query(query, tuple(params), fetch=True)
        
        for o in orders:
            color = STATUS_COLORS.get(o['status'], CREAM)
            iid = str(o['id'])
            
            total = 0
            detail = OrderModel.get_order_detail(o['id'])
            if detail and detail.get('items'):
                total = sum(i['quantity'] * float(i['final_price']) for i in detail['items'])
            
            self.tree.insert('', 'end', iid=iid, tags=(iid,), values=(
                o['id'],
                f"№{o['table_number']}",
                o['waiter_name'],
                STATUS_LABELS.get(o['status'], o['status']),
                str(o.get('placed_at', '') or '')[:16],
                str(o['created_at'])[:16],
                f"{total:.2f}"
            ))
            self.tree.tag_configure(iid, foreground=color)

    def _view_order(self):
        """Просмотр деталей заказа"""
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Выбор", "Выберите заказ для просмотра", parent=self)
            return
        oid = int(sel[0])
        order = OrderModel.get_order_detail(oid)
        if order:
            AdminOrderDetailDialog(self, order=order)

    def _edit_status(self):
        """Изменить статус заказа"""
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Выбор", "Выберите заказ", parent=self)
            return
        oid = int(sel[0])
        order = OrderModel.get_order_detail(oid)
        if order:
            AdminOrderStatusDialog(self, order=order, on_save=self.refresh, is_admin=True)

    def _cancel_order(self):
        """Отменить заказ"""
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Выбор", "Выберите заказ", parent=self)
            return
        oid = int(sel[0])
        order = OrderModel.get_order_detail(oid)
        if not order:
            return
            
        if order['status'] in ('cancelled', 'paid'):
            messagebox.showinfo("Инфо", f"Заказ №{oid} уже {STATUS_LABELS.get(order['status'], order['status'])}", parent=self)
            return
            
        if messagebox.askyesno("Отмена заказа", 
                f"Отменить заказ №{oid}?\n\n"
                f"Стол: №{order['table_number']}\n"
                f"Официант: {order['waiter_name']}\n"
                f"Статус: {STATUS_LABELS.get(order['status'], order['status'])}", 
                parent=self):
            try:
                OrderModel.cancel_order(oid)
                self.refresh()
                show_toast(self, f"Заказ №{oid} отменен", 'info')
            except Exception as e:
                messagebox.showerror("Ошибка", str(e), parent=self)
    def _edit_order(self):
        """Редактировать заказ (администратор)"""
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Выбор", "Выберите заказ", parent=self)
            return
        oid = int(sel[0])
        order = OrderModel.get_order_detail(oid)
        if not order:
            return
        
        current_status = order['status']
        
        if current_status in ('paid', 'cancelled'):
            messagebox.showinfo("Инфо", f"Заказ {STATUS_LABELS.get(current_status, current_status)}, редактирование невозможно", parent=self)
            return
        
        from src.views.waiter_views import OrderDialog
        OrderDialog(self, table_id=order['table_id'], waiter_id=order['waiter_id'],
                    order_id=oid, on_save=self.refresh)

# ── Диалог создания заказа (администратор) ──────────────────────────────────
class AdminOrderCreateDialog(tk.Toplevel):
    def __init__(self, master, tables, waiters, on_save=None):
        super().__init__(master)
        self.tables = tables
        self.waiters = waiters
        self.on_save = on_save
        self.order_id = None
        self.title("Создание заказа")
        self.configure(bg=BG_DARK)
        self.geometry("500x420")
        self.grab_set()
        self._build()

    def _build(self):
        OLabel(self, "Создание нового заказа", color=GOLD, font=FONT_H1, 
            bg=BG_DARK).pack(pady=PAD_LG)
        Divider(self).pack(fill='x', padx=PAD_LG)
        
        form = OFrame(self, bg=BG_DARK)
        form.pack(fill='both', expand=True, padx=PAD_LG, pady=PAD)

        # Выбор официанта
        OLabel(form, "Официант *:", color=GOLD, font=FONT_SMALL, bg=BG_DARK).pack(anchor='w', pady=(8,2))
        self._waiter_ids = [w['id'] for w in self.waiters]
        waiter_names = [f"{w['full_name']} ({w.get('username', '')})" for w in self.waiters]
        self.cmb_waiter = OCombobox(form, values=waiter_names, state='readonly')
        self.cmb_waiter.pack(fill='x', ipady=5)
        if waiter_names:
            self.cmb_waiter.current(0)

        # Выбор стола - схема
        OLabel(form, "Выберите столик (кликните по столу для выбора):",
            color=GOLD, font=FONT_SMALL, bg=BG_DARK).pack(anchor='w', pady=(8,2))
        
        self.tables_frame = OCard(form)
        self.tables_frame.pack(fill='both', expand=True, pady=(0,10))
        self.tables_canvas = tk.Canvas(self.tables_frame, bg=BG_CARD, highlightthickness=0)
        self.tables_canvas.pack(fill='both', expand=True)
        self.tables_canvas.bind('<Configure>', lambda e: self._draw_tables())
        self.tables_canvas.bind('<Button-1>', self._on_table_click)
        
        self._selected_table_id = None
        self._all_tables = self.tables

        # Информация о выбранном столе
        self.selected_info = OLabel(form, "Стол не выбран", 
                                    color=MUTED, font=FONT_SMALL, bg=BG_DARK)
        self.selected_info.pack(anchor='w', pady=(4,0))

        # Информационная метка
        self.info_label = OLabel(form, "Заказ будет создан в статусе «Составление»", 
                                color=MUTED, font=FONT_SMALL, bg=BG_DARK)
        self.info_label.pack(pady=10)

        btns = OFrame(self, bg=BG_DARK)
        btns.pack(fill='x', padx=PAD_LG, pady=PAD)
        OButton(btns, "Создать заказ", command=self._create, 
                variant='gold').pack(side='left', padx=(0,8))
        OButton(btns, "Отмена", command=self.destroy, variant='ghost').pack(side='left')
        
        self._draw_tables()

    def _draw_tables(self):
        """Нарисовать схему столов с возможностью выбора"""
        c = self.tables_canvas
        c.delete('all')
        w = c.winfo_width() or 500
        cols = 4
        pad = 15
        cell_w = (w - pad * 2) // cols
        cell_h = 95
        
        self._rects = []
        
        for i, t in enumerate(self._all_tables):
            col = i % cols
            row = i // cols
            x1 = pad + col * cell_w + 6
            y1 = pad + row * cell_h + 6
            x2 = x1 + cell_w - 12
            y2 = y1 + cell_h - 12
            
            is_selected = (self._selected_table_id == t['id'])
            
            c.create_rectangle(x1, y1, x2, y2, fill=GOLD_DARK if is_selected else BG_CARD, 
                            outline=GOLD if is_selected else BORDER, 
                            width=3 if is_selected else 1)
            
            cx = (x1 + x2) // 2
            c.create_text(cx, y1 + 18, text=f"Стол №{t['number']}", font=FONT_H2, fill=GOLD if is_selected else CREAM)
            c.create_text(cx, y1 + 40, text=f"Мест: {t['capacity']}", font=FONT_SMALL, fill=MUTED)
            c.create_text(cx, y1 + 58, text=t.get('location', ''), font=FONT_TINY, fill=MUTED)
            
            if is_selected:
                c.create_text(cx, y1 + 76, text="✓", font=FONT_H1, fill=SUCCESS)
            
            self._rects.append({'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2, 'table': t})
        
        if self._selected_table_id:
            table = next((t for t in self._all_tables if t['id'] == self._selected_table_id), None)
            if table:
                self.selected_info.configure(
                    text=f"Выбран: Стол №{table['number']} ({table['location']}, {table['capacity']} мест)",
                    fg=SUCCESS)
            else:
                self.selected_info.configure(text="Стол не выбран", fg=MUTED)
        else:
            self.selected_info.configure(text="Стол не выбран", fg=MUTED)

    def _on_table_click(self, event):
        """Обработка клика по столу для выбора"""
        for r in self._rects:
            if r['x1'] <= event.x <= r['x2'] and r['y1'] <= event.y <= r['y2']:
                table_id = r['table']['id']
                if self._selected_table_id == table_id:
                    self._selected_table_id = None
                else:
                    self._selected_table_id = table_id
                self._draw_tables()
                break

    def _create(self):
        try:
            waiter_idx = self.cmb_waiter.current()
            
            if waiter_idx < 0:
                raise ValueError("Выберите официанта")
            if not self._selected_table_id:
                raise ValueError("Выберите стол на схеме")
            
            waiter_id = self._waiter_ids[waiter_idx]
            table_id = self._selected_table_id
            
            # Проверяем, нет ли уже активного заказа на этом столе
            result = OrderModel.create(table_id, waiter_id)
            
            if isinstance(result, dict) and result.get('action') == 'confirm':
                if messagebox.askyesno("Забронированный стол", result['message'], parent=self):
                    order_id = OrderModel.create_forced(table_id, waiter_id)
                    msg = f"Заказ №{order_id} создан на забронированный стол!"
                else:
                    return
            elif isinstance(result, dict) and result.get('action') == 'created':
                order_id = result['order_id']
                msg = f"Заказ №{order_id} создан успешно!"
            else:
                order_id = result if isinstance(result, int) else None
                msg = f"Заказ №{order_id} создан успешно!"
            
            if self.on_save:
                self.on_save()
            
            show_toast(self.master, msg, 'success')
            
            if messagebox.askyesno("Добавить блюда", 
                    f"Заказ №{order_id} создан. Хотите добавить блюда в заказ?", 
                    parent=self):
                self.destroy()
                from src.views.waiter_views import OrderDialog
                OrderDialog(self.master, table_id=table_id, waiter_id=waiter_id, 
                        order_id=order_id, on_save=self.on_save)
            else:
                self.destroy()
            
        except Exception as e:
            messagebox.showerror("Ошибка", str(e), parent=self)

# ── Диалог просмотра заказа ──────────────────────────────────────────────────
class AdminOrderDetailDialog(tk.Toplevel):
    def __init__(self, master, order):
        super().__init__(master)
        self.order = order
        self.title(f"Заказ №{order['id']} — Стол №{order['table_number']}")
        self.configure(bg=BG_DARK)
        self.geometry("740x670")
        self.grab_set()
        self._build()

    def _build(self):
        info = OCard(self)
        info.pack(fill='x', padx=PAD, pady=PAD)
        
        status = STATUS_LABELS.get(self.order['status'], self.order['status'])
        color = STATUS_COLORS.get(self.order['status'], CREAM)
        
        tk.Label(info, bg=BG_CARD, fg=GOLD, font=FONT_H2,
                 text=f"Заказ №{self.order['id']}  |  Стол №{self.order['table_number']}").pack(pady=8)
        
        info_frame = OFrame(info, bg=BG_CARD)
        info_frame.pack(fill='x', padx=10, pady=5)
        
        OLabel(info_frame, f"Официант: {self.order['waiter_name']}", 
               color=CREAM, font=FONT_SMALL, bg=BG_CARD).pack(side='left', padx=10)
        OLabel(info_frame, f"Статус: {status}", 
               color=color, font=FONT_SMALL, bg=BG_CARD).pack(side='left', padx=10)
        
        created = str(self.order.get('created_at', ''))[:16]
        placed = str(self.order.get('placed_at', ''))[:16] if self.order.get('placed_at') else '—'
        OLabel(info_frame, f"Создан: {created}", 
               color=MUTED, font=FONT_TINY, bg=BG_CARD).pack(side='right', padx=10)
        OLabel(info_frame, f"Оформлен: {placed}", 
               color=MUTED, font=FONT_TINY, bg=BG_CARD).pack(side='right', padx=10)

        # Таблица с блюдами
        OLabel(self, "Состав заказа:", color=GOLD, font=FONT_H2, 
               bg=BG_DARK).pack(anchor='w', padx=PAD_LG, pady=(PAD, 4))
        
        cols = ('name', 'qty', 'price', 'discount', 'total')
        headers = ('Блюдо', 'Кол-во', 'Цена', 'Скидка', 'Итого')
        widths = (230, 70, 100, 80, 110)
        
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
        apply_tree_grid(tree)

        total = 0
        for item in self.order.get('items', []):
            line = item['quantity'] * float(item['final_price'])
            total += line
            tree.insert('', 'end', values=(
                item['dish_name'],
                item['quantity'],
                f"{item['unit_price']:.2f} ₽",
                f"{item['discount_percent']:.0f}%",
                f"{line:.2f} ₽"
            ))

        total_frame = OFrame(self, bg=BG_DARK)
        total_frame.pack(fill='x', padx=PAD_LG, pady=(0, PAD))
        
        OLabel(total_frame, f"ИТОГО: {total:.2f} ₽", 
               color=GOLD, font=FONT_H1, bg=BG_DARK).pack(side='right')

        # Кнопки
        btns = OFrame(self, bg=BG_DARK)
        btns.pack(fill='x', padx=PAD_LG, pady=PAD)
        
        # Кнопка "Изменить статус" для всех статусов, кроме оплачен и отменен
        if self.order['status'] not in ('paid', 'cancelled'):
            OButton(btns, "✏️ Изменить статус", command=self._edit_status, 
                    variant='primary').pack(side='left', padx=(0, 8))
        
        # Кнопка "Редактировать заказ" только для статуса "Составление"
        if self.order['status'] == 'composing':
            OButton(btns, "✏️ Редактировать заказ", command=self._edit_order, 
                    variant='gold').pack(side='left', padx=(0, 8))
        
        OButton(btns, "Закрыть", command=self.destroy, variant='ghost').pack(side='right')

    def _edit_status(self):
        """Изменить статус заказа"""
        AdminOrderStatusDialog(self, order=self.order, on_save=self._on_status_changed, is_admin=True)

    def _on_status_changed(self):
        """Обновить данные после изменения статуса"""
        self.order = OrderModel.get_order_detail(self.order['id'])
        for widget in self.winfo_children():
            widget.destroy()
        self._build()

    def _edit_order(self):
        """Редактировать заказ (только для статуса Составление)"""
        from src.views.waiter_views import OrderDialog
        OrderDialog(self, table_id=self.order['table_id'], waiter_id=self.order['waiter_id'],
                    order_id=self.order['id'], on_save=self._on_status_changed)

# ── Диалог изменения статуса заказа ─────────────────────────────────────────
class AdminOrderStatusDialog(tk.Toplevel):
    def __init__(self, master, order, on_save=None, is_admin=True):
        super().__init__(master)
        self.order = order
        self.on_save = on_save
        self.is_admin = is_admin  # True - администратор, False - официант
        self.title(f"Изменить статус заказа №{order['id']}")
        self.configure(bg=BG_DARK)
        self.geometry("400x380")
        self.grab_set()
        self._build()

    def _build(self):
        OLabel(self, f"Заказ №{self.order['id']}", color=GOLD, font=FONT_H1, 
            bg=BG_DARK).pack(pady=PAD_LG)
        Divider(self).pack(fill='x', padx=PAD_LG)
        
        form = OFrame(self, bg=BG_DARK)
        form.pack(fill='both', expand=True, padx=PAD_LG, pady=PAD)

        # Информация о заказе
        info_frame = OFrame(form, bg=BG_DARK)
        info_frame.pack(fill='x', pady=5)
        
        current_status = STATUS_LABELS.get(self.order['status'], self.order['status'])
        OLabel(info_frame, f"Текущий статус: {current_status}", 
            color=STATUS_COLORS.get(self.order['status'], CREAM), 
            font=FONT_BODY, bg=BG_DARK).pack(anchor='w')
        
        OLabel(info_frame, f"Стол: №{self.order['table_number']}", 
            color=MUTED, font=FONT_SMALL, bg=BG_DARK).pack(anchor='w')
        OLabel(info_frame, f"Официант: {self.order['waiter_name']}", 
            color=MUTED, font=FONT_SMALL, bg=BG_DARK).pack(anchor='w')

        Divider(form).pack(fill='x', pady=10)

        # Выбор нового статуса
        OLabel(form, "Новый статус:", color=GOLD, font=FONT_SMALL, 
            bg=BG_DARK).pack(anchor='w', pady=(8,2))
        
        # Список всех доступных статусов
        all_statuses = [
            ('composing', 'Составление'),
            ('placed', 'Оформлен'),
            ('accepted', 'Принят'),
            ('cooking', 'Готовится'),
            ('ready', 'Готов'),
            ('delivered', 'Выдан'),
            ('paid', 'Оплачен'),
            ('cancelled', 'Отменён')
        ]
        
        # Если заказ уже оплачен или отменен, нельзя менять статус
        if self.order['status'] in ('paid', 'cancelled'):
            OLabel(form, "❌ Заказ уже оплачен или отменен, изменение статуса невозможно", 
                color=ERROR, font=FONT_SMALL, bg=BG_DARK).pack(pady=10)
            self.cmb_status = None
        else:
            current = self.order['status']
            
            status_options = []
            
            if self.is_admin:
                # АДМИНИСТРАТОР: может менять на любой статус
                # Показываем все статусы кроме текущего
                for k, v in all_statuses:
                    if k != current:
                        status_options.append((k, v))
            else:
                # ОФИЦИАНТ: может менять по цепочке + отмена, НО НЕ МОЖЕТ ОПЛАТИТЬ
                allowed = []
                if current == 'composing':
                    allowed = ['placed', 'cancelled']
                elif current == 'placed':
                    allowed = ['accepted', 'cancelled']
                elif current == 'accepted':
                    allowed = ['cooking', 'cancelled']
                elif current == 'cooking':
                    allowed = ['ready']
                elif current == 'ready':
                    allowed = ['delivered']
                elif current == 'delivered':
                    allowed = []  # ← ОФИЦИАНТ НЕ МОЖЕТ ОПЛАТИТЬ! Только администратор.
                else:
                    allowed = []
                
                status_options = [(k, v) for k, v in all_statuses if k in allowed]
            
            if not status_options:
                OLabel(form, "❌ Нет доступных статусов для изменения", 
                    color=ERROR, font=FONT_SMALL, bg=BG_DARK).pack(pady=10)
                self.cmb_status = None
            else:
                self.cmb_status = OCombobox(form, 
                    values=[v for _, v in status_options], 
                    state='readonly', width=20)
                self.cmb_status.pack(fill='x', ipady=5)
                self.cmb_status.current(0)

        btns = OFrame(self, bg=BG_DARK)
        btns.pack(fill='x', padx=PAD_LG, pady=PAD)
        
        if self.cmb_status is not None:
            OButton(btns, "Сохранить", command=self._save, 
                    variant='gold').pack(side='left', padx=(0,8))
        OButton(btns, "Отмена", command=self.destroy, variant='ghost').pack(side='left')

    def _save(self):
        try:
            selected_text = self.cmb_status.get()
            status_map = {
                'Составление': 'composing',
                'Оформлен': 'placed',
                'Принят': 'accepted',
                'Готовится': 'cooking',
                'Готов': 'ready',
                'Выдан': 'delivered',
                'Оплачен': 'paid',
                'Отменён': 'cancelled'
            }
            new_status = status_map.get(selected_text)
            
            if not new_status:
                raise ValueError("Выберите корректный статус")
            
            OrderModel.update_status(self.order['id'], new_status)
            
            if self.on_save:
                self.on_save()
            
            show_toast(self.master, f"Статус заказа №{self.order['id']} изменен на «{selected_text}»", 'success')
            self.destroy()
            
        except Exception as e:
            messagebox.showerror("Ошибка", str(e), parent=self)


# ── Меню / склад ─────────────────────────────────────────────────────────────
class MenuView(BasePage):
    def _build(self):
        self._page_header("Меню и склад")
        tb = OFrame(self,bg=BG_DARK); tb.pack(fill='x',padx=PAD_LG,pady=PAD)
        OButton(tb,"+ Добавить блюдо",command=self._new,variant='gold').pack(side='left',padx=(0,8))
        OButton(tb,"Редактировать",command=self._edit,variant='secondary').pack(side='left')
        flt = OFrame(self, bg=BG_DARK)
        flt.pack(fill='x', padx=PAD_LG, pady=(0, PAD))
        OLabel(flt, "Категория:", bg=BG_DARK, font=FONT_SMALL).pack(side='left')
        cats = DishModel.get_categories()
        self._cat_vals = ['Все категории'] + [c['name'] for c in cats]
        self._cat_ids  = [None] + [c['id'] for c in cats]
        self._cmb_cat  = OCombobox(flt, values=self._cat_vals, state='readonly', width=20)
        self._cmb_cat.current(0)
        self._cmb_cat.pack(side='left', padx=8)
        self._cmb_cat.bind('<<ComboboxSelected>>', lambda e: self.refresh())

        cols = ('id','category','name','price','stock','stopped')
        headers = ('№','Категория','Название','Цена (₽)','Склад','Стоп-лист')
        widths = (50,130,220,90,80,90)
        frm, self.tree = self._make_tree(self, cols)
        frm.pack(fill='both',expand=True,padx=PAD_LG,pady=(0,PAD_LG))
        for col,hdr,w in zip(cols,headers,widths):
            self.tree.heading(col,text=hdr); self.tree.column(col,width=w)
        self.refresh()

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        cat_id = self._cat_ids[self._cmb_cat.current()] if hasattr(self, '_cmb_cat') else None
        dishes = DishModel.get_all()
        dishes.sort(key=lambda d: (d.get('category_name', ''), d.get('name', '')))  # сортировка
        for d in dishes:
            if cat_id and d['category_id'] != cat_id:
                continue
            stopped = "⛔ Да" if d.get('is_stopped') else "✓ Нет"
            color = ERROR if d.get('is_stopped') else (SUCCESS if d['stock_quantity'] > 0 else WARNING)
            iid = str(d['id'])
            self.tree.insert('', 'end', iid=iid, tags=(iid,), values=(
                d['id'], d['category_name'], d['name'],
                f"{d['price']:.2f}", d['stock_quantity'], stopped))
            self.tree.tag_configure(iid, foreground=color)

    def _new(self): DishDialog(self,on_save=self.refresh)
    def _edit(self):
        sel = self.tree.selection()
        if not sel: return messagebox.showwarning("Выбор","Выберите блюдо",parent=self)
        did = int(sel[0])
        dish = next((d for d in DishModel.get_all() if d['id']==did), None)
        if dish: DishDialog(self,dish=dish,on_save=self.refresh)


class DishDialog(tk.Toplevel):
    def __init__(self,master,dish=None,on_save=None):
        super().__init__(master); self.dish=dish; self.on_save=on_save
        self.title("Блюдо" if not dish else f"Редактировать: {dish['name']}")
        self.configure(bg=BG_DARK); self.geometry("440x650"); self.grab_set(); self._build()

    def _build(self):
        OLabel(self,"Данные блюда",color=GOLD,font=FONT_H1,bg=BG_DARK).pack(pady=PAD_LG)
        Divider(self).pack(fill='x',padx=PAD_LG)
        form = OFrame(self,bg=BG_DARK); form.pack(fill='both',expand=True,padx=PAD_LG,pady=PAD)

        for lbl_t, attr in [("Название *:","ent_name"),("Описание:","ent_desc"),
                             ("Цена (₽) *:","ent_price"),("Остаток *:","ent_stock")]:
            OLabel(form,lbl_t,color=GOLD,font=FONT_SMALL,bg=BG_DARK).pack(anchor='w',pady=(8,2))
            e = OEntry(form); e.pack(fill='x',ipady=5); setattr(self,attr,e)

        OLabel(form,"Категория *:",color=GOLD,font=FONT_SMALL,bg=BG_DARK).pack(anchor='w',pady=(8,2))
        cats = DishModel.get_categories()
        self._cat_ids = [c['id'] for c in cats]
        self.cmb_cat = OCombobox(form,values=[c['name'] for c in cats],state='readonly')
        self.cmb_cat.pack(fill='x')

        self.var_stopped = tk.BooleanVar()
        tk.Checkbutton(form,text="В стоп-листе",variable=self.var_stopped,
                       bg=BG_DARK,fg=CREAM,selectcolor=BG_INPUT,
                       activebackground=BG_DARK,font=FONT_BODY).pack(anchor='w',pady=(10,0))

        if self.dish:
            d = self.dish
            self.ent_name.insert(0,d['name']); self.ent_desc.insert(0,d.get('description',''))
            self.ent_price.insert(0,str(d['price'])); self.ent_stock.insert(0,str(d['stock_quantity']))
            if d['category_id'] in self._cat_ids:
                self.cmb_cat.current(self._cat_ids.index(d['category_id']))
            self.var_stopped.set(bool(d.get('is_stopped')))
        else:
            if cats: self.cmb_cat.current(0)

        btns = OFrame(self,bg=BG_DARK); btns.pack(fill='x',padx=PAD_LG,pady=PAD)
        OButton(btns,"Сохранить",command=self._save,variant='gold').pack(side='left',padx=(0,8))
        OButton(btns,"Отмена",command=self.destroy,variant='ghost').pack(side='left')

    def _save(self):
        try:
            name = self.ent_name.get().strip()
            if not name: raise ValueError("Введите название")
            idx = self.cmb_cat.current()
            if idx < 0: raise ValueError("Выберите категорию")
            cat_id = self._cat_ids[idx]
            desc   = self.ent_desc.get().strip()
            price  = float(self.ent_price.get().strip())
            stock  = int(self.ent_stock.get().strip())
            if self.dish:
                DishModel.update(self.dish['id'],name,cat_id,desc,price,stock)
                if bool(self.var_stopped.get()) != bool(self.dish.get('is_stopped')):
                    DishModel.toggle_stop(self.dish['id'])
                msg = f"Блюдо «{name}» обновлено"
            else:
                DishModel.create(name,cat_id,desc,price,stock)
                msg = f"Блюдо «{name}» добавлено"
            if self.on_save: self.on_save()
            show_toast(self.master,msg,'success'); self.destroy()
        except (ValueError,Exception) as e:
            messagebox.showerror("Ошибка",str(e),parent=self)


# ── Пользователи ─────────────────────────────────────────────────────────────
class UsersView(BasePage):
    def _build(self):
        self._page_header("Пользователи")
        tb = OFrame(self,bg=BG_DARK); tb.pack(fill='x',padx=PAD_LG,pady=PAD)
        OButton(tb, "✏️ Редактировать", command=self._edit, variant='secondary').pack(side='left', padx=(0,8))
        OButton(tb,"+ Добавить",command=self._new,variant='gold').pack(side='left',padx=(0,8))
        OButton(tb,"Деактивировать / Активировать",command=self._toggle,variant='danger').pack(side='left')
        cols = ('id','username','full_name','role','phone','active')
        headers = ('№','Логин','ФИО','Роль','Телефон','Активен')
        widths = (50,120,200,110,120,80)
        frm, self.tree = self._make_tree(self,cols)
        frm.pack(fill='both',expand=True,padx=PAD_LG,pady=(0,PAD_LG))
        for col,hdr,w in zip(cols,headers,widths):
            self.tree.heading(col,text=hdr); self.tree.column(col,width=w)
        self.refresh()

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        rm = {'admin':'Администратор','waiter':'Официант','kitchen':'Кухня','client':'Клиент'}
        for u in AuthModel.get_all_users():
            self.tree.insert('','end',iid=str(u['id']),values=(
                u['id'],u['username'],u['full_name'],
                rm.get(u['role'],u['role']),u.get('phone',''),
                "Да" if u['is_active'] else "Нет"))

    def _new(self): UserDialog(self,on_save=self.refresh)
    def _toggle(self):
        sel = self.tree.selection()
        if not sel: return messagebox.showwarning("Выбор","Выберите пользователя",parent=self)
        uid = int(sel[0])
        u = next((x for x in AuthModel.get_all_users() if x['id']==uid),None)
        if u: AuthModel.toggle_user_active(uid, not u['is_active']); self.refresh()

    def _edit(self):
        """Редактировать выбранного пользователя"""
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Выбор", "Выберите пользователя для редактирования", parent=self)
            return
        
        user_id = int(sel[0])
        users = AuthModel.get_all_users()
        user = next((u for u in users if u['id'] == user_id), None)
        
        if user:
            UserDialog(self, user=user, on_save=self.refresh)


class UserDialog(tk.Toplevel):
    def __init__(self, master, user=None, on_save=None):
        super().__init__(master)
        self.user = user  # None - новый пользователь, dict - существующий
        self.on_save = on_save
        self.title("Новый пользователь" if not user else f"Редактировать: {user['full_name']}")
        self.configure(bg=BG_DARK)
        self.geometry("420x650")
        self.grab_set()
        self._build()

    def _build(self):
        OLabel(self, "Новый пользователь" if not self.user else "Редактирование пользователя", 
               color=GOLD, font=FONT_H1, bg=BG_DARK).pack(pady=PAD_LG)
        Divider(self).pack(fill='x', padx=PAD_LG)
        
        form = OFrame(self, bg=BG_DARK)
        form.pack(fill='both', expand=True, padx=PAD_LG, pady=PAD)
        
        fields = [
            ("ФИО *", 'full_name', False),
            ("Логин *", 'username', False),
            ("Пароль", 'password', True),  # Пароль необязателен при редактировании
            ("Телефон", 'phone', False),
            ("Email", 'email', False)
        ]
        
        self.entries = {}
        for lbl, key, is_pass in fields:
            OLabel(form, lbl, color=GOLD, font=FONT_SMALL, bg=BG_DARK).pack(anchor='w', pady=(6,2))
            
            if key == 'password' and self.user:
                OLabel(form, "(оставьте пустым, чтобы не менять)", 
                       color=MUTED, font=FONT_TINY, bg=BG_DARK).pack(anchor='w')
            
            e = OEntry(form, show="•" if is_pass else "")
            e.pack(fill='x', ipady=5)
            
            if self.user and key in self.user and key != 'password':
                e.insert(0, str(self.user.get(key, '')))
            
            self.entries[key] = e
        
        OLabel(form, "Роль *:", color=GOLD, font=FONT_SMALL, bg=BG_DARK).pack(anchor='w', pady=(6,2))
        self._roles = ['admin', 'waiter', 'kitchen', 'client']
        role_names = ['Администратор', 'Официант', 'Кухня', 'Клиент']
        
        self.cmb_role = OCombobox(form, values=role_names, state='readonly')
        self.cmb_role.pack(fill='x', ipady=5)
        
        if self.user:
            role_map = {'admin': 0, 'waiter': 1, 'kitchen': 2, 'client': 3}
            current_role = self.user.get('role', 'client')
            self.cmb_role.current(role_map.get(current_role, 3))
            self.cmb_role.config(state='disabled')  # Роль нельзя менять при редактировании
        else:
            self.cmb_role.current(1)
        
        if self.user:
            self.var_active = tk.BooleanVar(value=bool(self.user.get('is_active', True)))
            tk.Checkbutton(form, text="Активен", variable=self.var_active,
                          bg=BG_DARK, fg=CREAM, selectcolor=BG_INPUT,
                          activebackground=BG_DARK, font=FONT_BODY).pack(anchor='w', pady=(10,0))
        
        btns = OFrame(self, bg=BG_DARK)
        btns.pack(fill='x', padx=PAD_LG, pady=PAD)
        OButton(btns, "Сохранить", command=self._save, variant='gold').pack(side='left', padx=(0,8))
        OButton(btns, "Отмена", command=self.destroy, variant='ghost').pack(side='left')

    def _save(self):
        try:
            data = {k: e.get().strip() for k, e in self.entries.items()}
            
            if not self.user:
                if not all([data['full_name'], data['username'], data['password']]):
                    raise ValueError("Заполните обязательные поля (*)")
            else:
                if not data['full_name'] or not data['username']:
                    raise ValueError("ФИО и Логин обязательны для заполнения")
            
            role_idx = self.cmb_role.current()
            if role_idx < 0:
                raise ValueError("Выберите роль")
            role = self._roles[role_idx]
            
            if self.user:
                # РЕДАКТИРОВАНИЕ
                user_id = self.user['id']
                AuthModel.update_user(user_id, data['username'], data['full_name'], data['phone'], data['email'])
                
                if data['password']:
                    AuthModel.update_password(user_id, data['password'])
                
                if hasattr(self, 'var_active'):
                    AuthModel.toggle_user_active(user_id, self.var_active.get())
                
                msg = f"Пользователь «{data['full_name']}» обновлен"
            else:
                # СОЗДАНИЕ
                if not data['password']:
                    raise ValueError("Пароль обязателен при создании пользователя")
                AuthModel.create_user(data['username'], data['password'], data['full_name'], data['phone'], data['email'], role)
                msg = f"Пользователь «{data['full_name']}» создан"
            
            if self.on_save:
                self.on_save()
            show_toast(self.master, msg, 'success')
            self.destroy()
            
        except (ValueError, Exception) as e:
            messagebox.showerror("Ошибка", str(e), parent=self)


# ── Акции ────────────────────────────────────────────────────────────────────
class PromotionsView(BasePage):
    def _build(self):
        self._page_header("Акции и скидки")
        tb = OFrame(self,bg=BG_DARK); tb.pack(fill='x',padx=PAD_LG,pady=PAD)
        OButton(tb,"+ Новая акция",command=self._new,variant='gold').pack(side='left',padx=(0,8))
        OButton(tb,"Деактивировать",command=self._deactivate,variant='danger').pack(side='left')
        cols = ('id','name','discount','dish','category','start','end')
        headers = ('№','Название','Скидка %','Блюдо','Категория','С','По')
        widths = (50,200,80,150,130,100,100)
        frm, self.tree = self._make_tree(self,cols)
        frm.pack(fill='both',expand=True,padx=PAD_LG,pady=(0,PAD_LG))
        for col,hdr,w in zip(cols,headers,widths):
            self.tree.heading(col,text=hdr); self.tree.column(col,width=w)
        self.refresh()

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        for p in PromotionModel.get_active():
            self.tree.insert('','end',iid=str(p['id']),values=(
                p['id'],p['name'],f"{p['discount_percent']}%",
                p.get('dish_name','—'),p.get('category_name','—'),
                str(p['start_date']),str(p['end_date'])))

    def _new(self): PromoDialog(self,on_save=self.refresh)
    def _deactivate(self):
        sel = self.tree.selection()
        if not sel: return
        PromotionModel.deactivate(int(sel[0])); self.refresh()
        show_toast(self,"Акция деактивирована",'info')


class PromoDialog(tk.Toplevel):
    def __init__(self,master,on_save=None):
        super().__init__(master); self.on_save=on_save
        self.title("Новая акция"); self.configure(bg=BG_DARK)
        self.geometry("460x540"); self.grab_set(); self._build()

    def _build(self):
        OLabel(self,"Создать акцию",color=GOLD,font=FONT_H1,bg=BG_DARK).pack(pady=PAD_LG)
        Divider(self).pack(fill='x',padx=PAD_LG)
        form = OFrame(self,bg=BG_DARK); form.pack(fill='both',expand=True,padx=PAD_LG,pady=PAD)

        OLabel(form,"Название акции *:",color=GOLD,font=FONT_SMALL,bg=BG_DARK).pack(anchor='w',pady=(8,2))
        self.ent_name = OEntry(form); self.ent_name.pack(fill='x',ipady=5)
        OLabel(form,"Скидка % *:",color=GOLD,font=FONT_SMALL,bg=BG_DARK).pack(anchor='w',pady=(8,2))
        self.ent_disc = OEntry(form); self.ent_disc.insert(0,'10'); self.ent_disc.pack(fill='x',ipady=5)

        # Даты — активные DateEntry
        dr = OFrame(form,bg=BG_DARK); dr.pack(fill='x',pady=(10,2))
        OLabel(dr,"Начало *:",color=GOLD,font=FONT_SMALL,bg=BG_DARK).pack(side='left')
        self.date_start = DateEntry(dr); self.date_start.pack(side='left',padx=8)
        OLabel(dr,"По *:",color=GOLD,font=FONT_SMALL,bg=BG_DARK).pack(side='left',padx=(16,0))
        self.date_end = DateEntry(dr); self.date_end.pack(side='left',padx=8)

        OLabel(form,"Применить к блюду (опц.):",color=GOLD,font=FONT_SMALL,bg=BG_DARK).pack(anchor='w',pady=(8,2))
        dishes = DishModel.get_all()
        self._dish_ids = [None]+[d['id'] for d in dishes]
        self.cmb_dish = OCombobox(form,values=['— не выбрано —']+[d['name'] for d in dishes],state='readonly')
        self.cmb_dish.current(0); self.cmb_dish.pack(fill='x')

        # После создания self.cmb_dish и перед self.cmb_cat
        OLabel(form, "Фильтр по категории:", color=GOLD, font=FONT_SMALL, bg=BG_DARK).pack(anchor='w', pady=(8,2))
        cats = DishModel.get_categories()
        self._filter_cat_ids = [None] + [c['id'] for c in cats]
        self._filter_cat_vals = ['Все категории'] + [c['name'] for c in cats]
        self.cmb_filter_cat = OCombobox(form, values=self._filter_cat_vals, state='readonly')
        self.cmb_filter_cat.current(0)
        self.cmb_filter_cat.pack(fill='x', ipady=5)
        self.cmb_filter_cat.bind('<<ComboboxSelected>>', lambda e: self._update_dish_list())

        OLabel(form,"Или к категории (опц.):",color=GOLD,font=FONT_SMALL,bg=BG_DARK).pack(anchor='w',pady=(8,2))
        cats = DishModel.get_categories()
        self._cat_ids = [None]+[c['id'] for c in cats]
        self.cmb_cat = OCombobox(form,values=['— не выбрано —']+[c['name'] for c in cats],state='readonly')
        self.cmb_cat.current(0); self.cmb_cat.pack(fill='x')

        btns = OFrame(self,bg=BG_DARK); btns.pack(fill='x',padx=PAD_LG,pady=PAD)
        OButton(btns,"Создать",command=self._save,variant='gold').pack(side='left',padx=(0,8))
        OButton(btns,"Отмена",command=self.destroy,variant='ghost').pack(side='left')
        self._update_dish_list()


    def _update_dish_list(self):
        cat_id = self._filter_cat_ids[self.cmb_filter_cat.current()]
        dishes = DishModel.get_all()
        if cat_id:
            dishes = [d for d in dishes if d['category_id'] == cat_id]
        dishes.sort(key=lambda d: d['name'])
        self._dish_ids = [None] + [d['id'] for d in dishes]
        dish_names = ['— не выбрано —'] + [d['name'] for d in dishes]
        self.cmb_dish['values'] = dish_names
        self.cmb_dish.current(0)

    def _save(self):
        try:
            name  = self.ent_name.get().strip()
            disc  = float(self.ent_disc.get().strip())
            start = self.date_start.get_date()
            end   = self.date_end.get_date()
            dish_id = self._dish_ids[self.cmb_dish.current()]
            cat_id  = self._cat_ids[self.cmb_cat.current()]
            PromotionModel.create(name,disc,start,end,dish_id,cat_id)
            if self.on_save: self.on_save()
            show_toast(self.master,"Акция создана",'success'); self.destroy()
        except (ValueError,Exception) as e:
            messagebox.showerror("Ошибка",str(e),parent=self)


# ── Статистика ────────────────────────────────────────────────────────────────
class StatisticsView(BasePage):

    def _tab_availability(self, nb):
        """Вкладка: Список свободных и занятых столов на дату"""
        frame = OFrame(nb, bg=BG_DARK)
        nb.add(frame, text="  Занятость столов  ")
        
        # Панель управления
        ctrl = OFrame(frame, bg=BG_DARK)
        ctrl.pack(fill='x', padx=PAD, pady=PAD)
        
        OLabel(ctrl, "Дата:", color=GOLD, font=FONT_SMALL, bg=BG_DARK).pack(side='left')
        self.avail_date = DateEntry(ctrl)
        self.avail_date.pack(side='left', padx=8)
        
        OButton(ctrl, "Показать", variant='gold', 
                command=self._load_availability).pack(side='left', padx=8)
        
        # Легенда
        leg = OFrame(frame, bg=BG_DARK)
        leg.pack(fill='x', padx=PAD, pady=(0, PAD))
        for lbl, color in [("Свободен", SUCCESS), ("Забронирован", WARNING)]:
            f = OFrame(leg, bg=BG_DARK)
            f.pack(side='left', padx=10)
            tk.Frame(f, bg=color, width=14, height=14).pack(side='left', padx=4)
            OLabel(f, lbl, font=FONT_SMALL, bg=BG_DARK).pack(side='left')
        
        # Таблица
        cols = ('table', 'status', 'client', 'time_start', 'time_end', 'guests', 'reservation')
        headers = ('Стол', 'Статус', 'Клиент', 'Начало', 'Окончание', 'Гостей', 'Бронь №')
        widths = (80, 120, 180, 100, 100, 70, 80)
        
        frm, self.avail_tree = self._make_tree(frame, cols, heights=20)
        frm.pack(fill='both', expand=True, padx=PAD, pady=(0, PAD))
        
        for col, hdr, w in zip(cols, headers, widths):
            self.avail_tree.heading(col, text=hdr)
            self.avail_tree.column(col, width=w, minwidth=50)
        
        # По умолчанию показываем сегодня
        self.avail_date.set_date(date.today())
        self._load_availability()

    def _load_availability(self):
        """Загрузить список занятости столов"""
        try:
            check_date = self.avail_date.get_date()
            self.avail_tree.delete(*self.avail_tree.get_children())
            
            data = StatisticsModel.table_availability_list(check_date)
            
            for item in data:
                # Определяем цвет для статуса
                if item['status'] == 'Свободен':
                    color = SUCCESS
                else:
                    color = WARNING
                
                iid = f"row_{item['table_number']}_{item['reservation_id'] or 'free'}"
                self.avail_tree.insert('', 'end', iid=iid, tags=(iid,), values=(
                    f"№{item['table_number']}",
                    item['status'],
                    item['client_name'] or '—',
                    item['time_start'],
                    item['time_end'],
                    item['guests_count'] or '—',
                    item['reservation_id'] or '—'
                ))
                self.avail_tree.tag_configure(iid, foreground=color)
                
        except Exception as e:
            messagebox.showerror("Ошибка", str(e), parent=self)
    def _build(self):
        self._page_header("Статистика")
        nb = ttk.Notebook(self, style='Oltremare.TNotebook')
        nb.pack(fill='both', expand=True, padx=PAD_LG, pady=PAD)
        self._tab_sales(nb); self._tab_waiters(nb)
        self._tab_reservations(nb); self._tab_hourly(nb); self._tab_receipts(nb)
        self._tab_availability(nb)

    def _month_selector(self, parent, prefix, def_year, def_month):
        f = OFrame(parent, bg=BG_DARK); f.pack(side='left', padx=4)
        OLabel(f,"Год:",bg=BG_DARK,font=FONT_SMALL).pack(side='left')
        yv = tk.StringVar(value=str(def_year))
        OEntry(f, textvariable=yv, width=5).pack(side='left', padx=4, ipady=3)
        OLabel(f,"Мес.:",bg=BG_DARK,font=FONT_SMALL).pack(side='left',padx=(6,0))
        mcb = OCombobox(f, values=MONTHS_RU[1:], state='readonly', width=11)
        mcb.current(def_month-1); mcb.pack(side='left', padx=4)
        setattr(self, f'{prefix}_year', yv)
        setattr(self, f'{prefix}_mcb',  mcb)

    def _get_ym(self, prefix):
        y = int(getattr(self, f'{prefix}_year').get())
        m = MONTHS_RU.index(getattr(self, f'{prefix}_mcb').get())
        return y, m

    def _tab_sales(self, nb):
        frame = OFrame(nb, bg=BG_DARK); nb.add(frame, text="  Продажи блюд  ")
        ctrl = OFrame(frame, bg=BG_DARK); ctrl.pack(fill='x', padx=PAD, pady=PAD)
        now = date.today(); pm = now.month-1 or 12; py = now.year if now.month>1 else now.year-1
        OLabel(ctrl,"Период 1:",color=GOLD,font=FONT_SMALL,bg=BG_DARK).pack(side='left',padx=(0,4))
        self._month_selector(ctrl,'s1',py,pm)
        OLabel(ctrl,"Период 2:",color=GOLD,font=FONT_SMALL,bg=BG_DARK).pack(side='left',padx=(12,4))
        self._month_selector(ctrl,'s2',now.year,now.month)
        cols = ('cat','dish','qty1','qty2','diff')
        frm = OFrame(frame,bg=BG_DARK); frm.pack(fill='both',expand=True,padx=PAD,pady=(0,PAD))
        tree = ttk.Treeview(frm,columns=cols,show='headings',style='Oltremare.Treeview')
        for col,hdr,w in zip(cols,('Категория','Блюдо','Кол-во п.1','Кол-во п.2','Динамика'),(130,180,130,130,100)):
            tree.heading(col,text=hdr); tree.column(col,width=w)
        apply_tree_grid(tree)
        vsb = ttk.Scrollbar(frm,orient='vertical',command=tree.yview)
        tree.configure(yscrollcommand=vsb.set); vsb.pack(side='right',fill='y'); tree.pack(fill='both',expand=True)
        OButton(ctrl,"Показать",variant='gold',command=lambda:self._load_sales(tree)).pack(side='left',padx=8)

    def _load_sales(self, tree):
        try:
            y1,m1=self._get_ym('s1'); y2,m2=self._get_ym('s2')
            tree.delete(*tree.get_children())
            for r in StatisticsModel.dish_sales_two_months(y1,m1,y2,m2):
                diff = (r['qty2'] or 0)-(r['qty1'] or 0)
                tree.insert('','end',values=(r['category'],r['dish_name'],
                    r['qty1'] or 0,r['qty2'] or 0,f"+{diff}" if diff>0 else str(diff)))
        except Exception as e: messagebox.showerror("Ошибка",str(e),parent=self)

    def _tab_waiters(self, nb):
        frame = OFrame(nb,bg=BG_DARK); nb.add(frame,text="  Официанты  ")
        ctrl = OFrame(frame,bg=BG_DARK); ctrl.pack(fill='x',padx=PAD,pady=PAD)
        now = date.today(); pm = now.month-1 or 12; py = now.year if now.month>1 else now.year-1
        OLabel(ctrl,"Период 1:",color=GOLD,font=FONT_SMALL,bg=BG_DARK).pack(side='left',padx=(0,4))
        self._month_selector(ctrl,'w1',py,pm)
        OLabel(ctrl,"Период 2:",color=GOLD,font=FONT_SMALL,bg=BG_DARK).pack(side='left',padx=(12,4))
        self._month_selector(ctrl,'w2',now.year,now.month)
        cols = ('name','o1','o2','b1','b2','r1','r2')
        hdrs = ('ФИО','Заказов (п.1)','Заказов (п.2)','Чеков (п.1)','Чеков (п.2)','Выручка (п.1)','Выручка (п.2)')
        frm = OFrame(frame,bg=BG_DARK); frm.pack(fill='both',expand=True,padx=PAD,pady=(0,PAD))
        tree = ttk.Treeview(frm,columns=cols,show='headings',style='Oltremare.Treeview')
        for col,hdr in zip(cols,hdrs): tree.heading(col,text=hdr); tree.column(col,width=115)
        apply_tree_grid(tree)
        vsb = ttk.Scrollbar(frm,orient='vertical',command=tree.yview)
        tree.configure(yscrollcommand=vsb.set); vsb.pack(side='right',fill='y'); tree.pack(fill='both',expand=True)
        OButton(ctrl,"Показать",variant='gold',command=lambda:self._load_waiters(tree)).pack(side='left',padx=8)

    def _load_waiters(self,tree):
        try:
            y1,m1=self._get_ym('w1'); y2,m2=self._get_ym('w2')
            tree.delete(*tree.get_children())
            for r in StatisticsModel.waiter_stats_two_months(y1,m1,y2,m2):
                tree.insert('','end',values=(r['full_name'],r['orders1'],r['orders2'],
                    r['paid_bills1'],r['paid_bills2'],f"{r['revenue1']:.2f}",f"{r['revenue2']:.2f}"))
        except Exception as e: messagebox.showerror("Ошибка",str(e),parent=self)

    def _tab_reservations(self,nb):
        frame = OFrame(nb,bg=BG_DARK); nb.add(frame,text="  Брони по столам  ")
        ctrl = OFrame(frame,bg=BG_DARK); ctrl.pack(fill='x',padx=PAD,pady=PAD)
        now = date.today()
        OLabel(ctrl,"Период:",color=GOLD,font=FONT_SMALL,bg=BG_DARK).pack(side='left',padx=(0,4))
        self._month_selector(ctrl,'r1',now.year,now.month)
        frm = OFrame(frame,bg=BG_DARK); frm.pack(fill='both',expand=True,padx=PAD,pady=(0,PAD))
        tree = ttk.Treeview(frm,columns=('num','cnt'),show='headings',style='Oltremare.Treeview')
        tree.heading('num',text='Стол'); tree.column('num',width=200)
        tree.heading('cnt',text='Броней'); tree.column('cnt',width=200)
        vsb = ttk.Scrollbar(frm,orient='vertical',command=tree.yview)
        apply_tree_grid(tree)
        tree.configure(yscrollcommand=vsb.set); vsb.pack(side='right',fill='y'); tree.pack(fill='both',expand=True)
        OButton(ctrl,"Показать",variant='gold',
                command=lambda:self._load_res(tree)).pack(side='left',padx=8)

    def _load_res(self,tree):
        try:
            y,m = self._get_ym('r1')
            tree.delete(*tree.get_children())
            for r in StatisticsModel.table_reservations(y,m):
                tree.insert('','end',values=(f"№{r['number']}",r['reservation_count']))
        except Exception as e: messagebox.showerror("Ошибка",str(e),parent=self)

    def _tab_hourly(self,nb):
        frame = OFrame(nb,bg=BG_DARK); nb.add(frame,text="  Занятость по часам  ")
        ctrl = OFrame(frame,bg=BG_DARK); ctrl.pack(fill='x',padx=PAD,pady=PAD)
        OLabel(ctrl,"Дата:",color=GOLD,bg=BG_DARK,font=FONT_SMALL).pack(side='left')
        self.h_date = DateEntry(ctrl); self.h_date.pack(side='left',padx=8)
        OButton(ctrl,"Показать",variant='gold',command=self._load_hourly).pack(side='left',padx=8)
        # Легенда
        for lbl,color in [("Бронь",WARNING),("Заказ",ERROR)]:
            f = OFrame(ctrl,bg=BG_DARK); f.pack(side='left',padx=8)
            tk.Frame(f,bg=color,width=12,height=12).pack(side='left',padx=4)
            OLabel(f,lbl,font=FONT_SMALL,bg=BG_DARK).pack(side='left')
        self.h_cf = OCard(frame)
        self.h_cf.pack(fill='both',expand=True,padx=PAD,pady=(0,PAD))
        self.h_canvas = tk.Canvas(self.h_cf,bg=BG_CARD,highlightthickness=0)
        self.h_canvas.pack(fill='both',expand=True)

    def _load_hourly(self):
        try:
            dt = self.h_date.get_date()
            result,hours,table_nums = StatisticsModel.hourly_table_occupancy(dt)
            c = self.h_canvas; c.delete('all')
            cell_w=52; cell_h=30; off_x=80; off_y=44
            for j,h in enumerate(hours):
                c.create_text(off_x+j*cell_w+cell_w//2,20,text=f"{h}:00",font=FONT_TINY,fill=MUTED)
            for i,t in enumerate(table_nums):
                c.create_text(40,off_y+i*cell_h+cell_h//2,text=f"Стол {t}",font=FONT_TINY,fill=CREAM)
                for j,h in enumerate(hours):
                    val = result.get(t,{}).get(h,'')
                    x1=off_x+j*cell_w; y1=off_y+i*cell_h
                    x2=x1+cell_w-2;    y2=y1+cell_h-2
                    fill = WARNING if val=='Бронь' else (ERROR if val=='Заказ' else BG_CARD)
                    c.create_rectangle(x1,y1,x2,y2,fill=fill,outline=BORDER)
                    if val:
                        c.create_text((x1+x2)//2,(y1+y2)//2,text=val[:5],font=FONT_TINY,
                                      fill=BG_DARK if fill!=BG_CARD else MUTED)
        except Exception as e: messagebox.showerror("Ошибка",str(e),parent=self)

    def _tab_receipts(self,nb):
        frame = OFrame(nb,bg=BG_DARK); nb.add(frame,text="  Чеки  ")
        tb = OFrame(frame,bg=BG_DARK); tb.pack(fill='x',padx=PAD,pady=PAD)
        OButton(tb,"Обновить",command=lambda:self._load_receipts(tree),variant='secondary').pack(side='left',padx=(0,8))
        OButton(tb,"Просмотр чека",command=lambda:self._view_receipt(tree),variant='gold').pack(side='left')
        cols = ('id','num','table','waiter','amount','method','issued')
        hdrs = ('№','Номер чека','Стол','Официант','Сумма ₽','Способ','Дата/время')
        widths = (50,180,70,160,100,80,150)
        frm = OFrame(frame,bg=BG_DARK); frm.pack(fill='both',expand=True,padx=PAD,pady=(0,PAD))
        tree = ttk.Treeview(frm,columns=cols,show='headings',style='Oltremare.Treeview')
        for col,hdr,w in zip(cols,hdrs,widths):
            tree.heading(col,text=hdr); tree.column(col,width=w)
        vsb = ttk.Scrollbar(frm,orient='vertical',command=tree.yview)
        apply_tree_grid(tree)
        tree.configure(yscrollcommand=vsb.set); vsb.pack(side='right',fill='y'); tree.pack(fill='both',expand=True)
        self._receipts_tree = tree
        self._load_receipts(tree)

    def _load_receipts(self,tree):
        tree.delete(*tree.get_children())
        for r in BillModel.get_all_receipts():
            method = 'Карта' if r['payment_method']=='card' else 'Наличные'
            tree.insert('','end',iid=str(r['id']),values=(
                r['id'],r['receipt_number'],f"№{r['table_number']}",
                r['waiter_name'],f"{r['total_amount']:.2f}",method,str(r['issued_at'])[:16]))

    def _view_receipt(self,tree):
        sel = tree.selection()
        if not sel: return messagebox.showwarning("Выбор","Выберите чек",parent=self)
        rid = int(sel[0])
        r = next((x for x in BillModel.get_all_receipts() if x['id']==rid),None)
        if r:
            m = 'Карта' if r['payment_method']=='card' else 'Наличные'
            messagebox.showinfo("Чек",
                f"ЧЕК ОПЛАТЫ\n{'─'*35}\n"
                f"Номер:    {r['receipt_number']}\n"
                f"Стол:     №{r['table_number']}\n"
                f"Официант: {r['waiter_name']}\n"
                f"Сумма:    {r['total_amount']:.2f} ₽\n"
                f"Оплата:   {m}\n"
                f"Выдан:    {str(r['issued_at'])[:16]}\n"
                f"{'─'*35}\nСпасибо за посещение Oltremare!", parent=self)
