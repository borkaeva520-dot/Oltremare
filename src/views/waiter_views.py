"""
Oltremare — Виды официанта (исправленная версия)
"""
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox
from datetime import date, datetime
from src.utils.theme import apply_tree_grid

from src.utils.theme import *
from src.database.db import execute_query
from src.models.models import (
    ShiftModel, TableModel, OrderModel,
    DishModel, BillModel, ReservationModel
)
from src.views.admin_views import BasePage, ReservationDialog


class WaiterTableDetailDialog(tk.Toplevel):
    """Диалог просмотра стола для официанта"""
    def __init__(self, master, table_id, user, on_update=None):
        super().__init__(master)
        self.table_id = table_id
        self.user = user
        self.on_update = on_update
        self.title(f"Просмотр стола №{table_id}")
        self.configure(bg=BG_DARK)
        self.geometry("700x750")
        self.transient(master)
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

        btns = OFrame(self, bg=BG_DARK)
        btns.pack(fill='x', padx=PAD_LG, pady=PAD)
        OButton(btns, "Закрыть", command=self.destroy, variant='ghost').pack(side='right')

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

        # Загрузка броней на сегодня
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
                time_display,
                r['guests_count'],
                STATUS_LABELS.get(r['status'], r['status'])
            ))

        self.update_idletasks()
# Order management module
    def _create_order(self):
        """Создать заказ для текущего стола"""
        # Сначала пытаемся взять официанта, назначенного на стол
        assigned_waiter = self._get_waiter_for_table(self.table_id)
        uid = assigned_waiter if assigned_waiter else self.user['id']
        shift = ShiftModel.get_today_open(uid)
        if not shift:
            messagebox.showwarning("Смена", "Сначала откройте смену!", parent=self)
            return
        
        result = OrderModel.create(self.table_id, uid)
        
        if isinstance(result, dict):
            if result.get('action') == 'confirm':
                if messagebox.askyesno("Забронированный стол", result['message'], parent=self):
                    reservation_id = result['reservation']['id']
                    order_id = OrderModel.create_forced(self.table_id, uid, reservation_id)
                    OrderDialog(self, table_id=self.table_id, waiter_id=uid,
                              reservation_id=reservation_id, order_id=order_id, on_save=self._load_data)
                return
            elif result.get('action') == 'created':
                order_id = result['order_id']
                OrderDialog(self, table_id=self.table_id, waiter_id=uid,
                          order_id=order_id, on_save=self._load_data)

    def _view_order(self):
        sel = self.tree_orders.selection()
        if not sel:
            messagebox.showwarning("Выбор", "Выберите заказ", parent=self)
            return
        item = self.tree_orders.item(sel[0])
        order_id = int(item['values'][0])
        order = OrderModel.get_order_detail(order_id)
        if order:
            OrderDetailDialog(self, order=order, waiter_id=self.user['id'], on_save=self._load_data)

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
        
        # Открываем диалог редактирования для всех статусов кроме paid/cancelled
        OrderDialog(self, table_id=self.table_id, waiter_id=order['waiter_id'],
                    order_id=order_id, on_save=self._load_data)

    def _edit_reservation(self):
        sel = self.tree_res.selection()
        if not sel:
            messagebox.showwarning("Выбор", "Выберите бронь", parent=self)
            return
        item = self.tree_res.item(sel[0])
        res_id = int(item['values'][0])
        res_data = execute_query("SELECT * FROM reservations WHERE id = %s", (res_id,), fetch_one=True)
        if res_data:
            from src.views.admin_views import ReservationDialog
            ReservationDialog(
                self, 
                user=self.user, 
                reservation=res_data, 
                on_save=self._load_data,
                preset_table_ids=[self.table_id]
            )

# ── Смена ────────────────────────────────────────────────────────────────────
class WaiterShiftView(BasePage):
    def _build(self):
        self._page_header("Моя смена")
        self.info_card = OCard(self)
        self.info_card.pack(fill='x', padx=PAD_LG, pady=PAD)
        self.lbl_shift = tk.Label(self.info_card, text="Загрузка...",
                                   font=FONT_H2, fg=CREAM, bg=BG_CARD, pady=16, wraplength=700)
        self.lbl_shift.pack()

        btns = OFrame(self, bg=BG_DARK)
        btns.pack(padx=PAD_LG, pady=PAD)
        OButton(btns, "▶  Открыть смену", command=self._open_shift,
                variant='success').pack(side='left', padx=(0, 12))
        OButton(btns, "■  Закрыть смену", command=self._close_shift,
                variant='danger').pack(side='left')

        OLabel(self, "История смен:", color=GOLD, font=FONT_H2,
               bg=BG_DARK).pack(anchor='w', padx=PAD_LG, pady=(PAD, 4))
        cols = ('id', 'date', 'start', 'end', 'tables', 'status')
        headers = ('№', 'Дата', 'Начало', 'Конец', 'Столики', 'Статус')
        widths = (50, 100, 80, 80, 120, 110)
        frm, self.tree = self._make_tree(self, cols, heights=10)
        frm.pack(fill='both', expand=True, padx=PAD_LG, pady=(0, PAD_LG))
        for col, hdr, w in zip(cols, headers, widths):
            self.tree.heading(col, text=hdr)
            self.tree.column(col, width=w)
        self.refresh()

    def refresh(self):
        uid = self.user['id']
        shift = ShiftModel.get_today_open(uid)
        if shift:
            tables = shift.get('table_numbers', '—')
            self.lbl_shift.configure(
                text=f"✅ Активная смена №{shift['id']}   |   Столики: {tables}\n"
                     f"Начало: {str(shift['start_time'])[:5]}  |  Открыта: {str(shift['opened_at'])[:16]}",
                fg=SUCCESS)
        else:
            self.lbl_shift.configure(
                text="Активной смены нет. Откройте смену для начала работы.", fg=MUTED)
        self.tree.delete(*self.tree.get_children())
        for s in ShiftModel.get_for_waiter(uid):
            self.tree.insert('', 'end', values=(
                s['id'], str(s['shift_date']),
                str(s['start_time'])[:5], str(s['end_time'])[:5],
                s.get('table_numbers', '—'),
                STATUS_LABELS.get(s['status'], s['status'])))

    def _open_shift(self):
        uid = self.user['id']
        shifts = ShiftModel.get_for_waiter(uid)
        today = date.today()
        scheduled = [s for s in shifts
                     if str(s['shift_date']) == str(today) and s['status'] == 'scheduled']
        if not scheduled:
            messagebox.showinfo("Смена",
                "Нет запланированных смен на сегодня.\nОбратитесь к администратору.", parent=self)
            return
        shift = scheduled[0]
        ShiftModel.open_shift(shift['id'], uid)

        tables = ShiftModel.get_tables_for_shift(shift['id'])
        if not tables:
            result = ShiftModel.distribute_free_tables_among_all_shifts(today)
            if "Нет свободных столов" in result:
                messagebox.showwarning("Внимание",
                    "У вашей смены нет назначенных столов, и свободных столов на сегодня нет.\n"
                    "Обратитесь к администратору.", parent=self)
            else:
                show_toast(self, f"Смена открыта! {result}", 'success')
        else:
            show_toast(self, "Смена открыта!", 'success')

        self.refresh()

    def _close_shift(self):
        uid = self.user['id']
        shift = ShiftModel.get_today_open(uid)
        if not shift:
            messagebox.showinfo("Смена", "Нет открытой смены", parent=self)
            return
        if messagebox.askyesno("Закрыть смену", "Закрыть текущую смену?", parent=self):
            ShiftModel.close_shift(shift['id'], uid)
            self.refresh()
            show_toast(self, "Смена закрыта", 'info')


# ── Схема зала (официант) ────────────────────────────────────────────────────
class TablesLayoutView(BasePage):
    def _build(self):
        self._page_header("Схема зала", "выберите столик")
        ctrl = OFrame(self, bg=BG_DARK)
        ctrl.pack(fill='x', padx=PAD_LG, pady=PAD)
        OButton(ctrl, "Обновить", command=self.refresh, variant='secondary').pack(side='left', padx=(0, 8))
        OButton(ctrl, "Создать заказ для стола", command=self._create_order,
                variant='gold').pack(side='left')

        leg = OFrame(self, bg=BG_DARK)
        leg.pack(fill='x', padx=PAD_LG, pady=(0, PAD))
        for lbl, color in [("Свободен", SUCCESS), ("Забронирован", WARNING),
                            ("Занят (заказ)", ERROR), ("Недоступен", MUTED)]:
            f = OFrame(leg, bg=BG_DARK)
            f.pack(side='left', padx=8)
            tk.Frame(f, bg=color, width=14, height=14).pack(side='left', padx=4)
            OLabel(f, lbl, font=FONT_SMALL, bg=BG_DARK).pack(side='left')

        self.canvas_frame = OCard(self)
        self.canvas_frame.pack(fill='both', expand=True, padx=PAD_LG, pady=(0, PAD_LG))
        self.canvas = tk.Canvas(self.canvas_frame, bg=BG_CARD, highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)
        self.canvas.bind('<Configure>', lambda e: self.refresh())
        self.canvas.bind('<Button-1>', self._on_click)
        self.canvas.bind('<Double-Button-1>', self._on_double_click)
        self._selected_table_id = None
        self._rects = []
        self._tables_data = []

    def _on_double_click(self, event):
        """Обработка двойного клика по столу - открыть детали стола"""
        for r in self._rects:
            if r['x1'] <= event.x <= r['x2'] and r['y1'] <= event.y <= r['y2']:
                table_id = r['table']['id']
                # Открываем окно просмотра стола
                WaiterTableDetailDialog(self, table_id, self.user, on_update=self.refresh)
                break
    def refresh(self):
        self._tables_data = TableModel.get_layout_status()
        self._draw(self._tables_data)

    def _draw(self, tables):
        c = self.canvas
        c.delete('all')
        w = c.winfo_width() or 700
        cols = 5
        pad = 20
        cell_w = (w - pad * 2) // cols
        cell_h = 145
        self._rects = []
        
        # Получаем назначения официантов на столы из смены текущего официанта
        uid = self.user['id']
        today = date.today()
        shift_assignments = execute_query("""
            SELECT DISTINCT st.table_id
            FROM shift_tables st
            JOIN shifts s ON st.shift_id = s.id
            WHERE s.waiter_id = %s AND s.shift_date = %s AND s.status = 'open'
        """, (uid, today), fetch=True)
        
        my_tables = [a['table_id'] for a in shift_assignments]
        
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
            is_my_table = t['id'] in my_tables 
            
            # Если стол свободен и закреплен за официантом - выделяем другим цветом
            outline_color = GOLD if is_sel else color
            if is_my_table and not is_sel:
                outline_color = INFO
            
            c.create_rectangle(x1, y1, x2, y2, fill=BG_CARD, 
                            outline=outline_color, 
                            width=3 if is_sel or is_my_table else 2)
            
            cx = (x1 + x2) // 2
            
            c.create_text(cx, y1 + 20, text=f"Стол №{t['number']}", font=FONT_H2, fill=GOLD)
            c.create_text(cx, y1 + 42, text=STATUS_LABELS.get(s, s), font=FONT_SMALL, fill=color)
            c.create_text(cx, y1 + 60, text=f"Мест: {t['capacity']}", font=FONT_TINY, fill=MUTED)
            c.create_text(cx, y1 + 76, text=t.get('location', ''), font=FONT_TINY, fill=MUTED)


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
            
            # Информация о брони
            if s == 'reserved' and t.get('client_name'):
                c.create_text(cx, y1 + 92, text=t['client_name'][:18], font=FONT_TINY, fill=CREAM)
                
                if t.get('reservation_time'):
                    res_time = t['reservation_time']
                    if hasattr(res_time, 'strftime'):
                        time_str = res_time.strftime('%H:%M')
                    else:
                        time_str = str(res_time)[:5] if res_time else ''
                    c.create_text(cx, y1 + 108, text=f"⏰ {time_str}", font=FONT_TINY, fill=WARNING)

                if t.get('reservation_time'):
                    try:
                        from datetime import datetime, timedelta
                        now = datetime.now()
                        if hasattr(t['reservation_time'], 'strftime'):
                            res_dt = datetime.combine(now.date(), t['reservation_time'])
                        else:
                            res_dt = datetime.combine(now.date(), datetime.strptime(str(t['reservation_time'])[:5], '%H:%M').time())
                        delta = (res_dt - now).total_seconds() / 60
                        if 0 <= delta <= 60:
                            c.create_rectangle(x1, y1, x2, y2, fill='', outline=ERROR, width=3, dash=(4, 2))
                            if delta <= 30:
                                c.create_text(cx, y1 + 124, text="🔴 СКОРО!", font=FONT_TINY, fill=ERROR)
                    except:
                        pass
            
            self._rects.append({'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2, 'table': t})

    def _on_click(self, event):
        for r in self._rects:
            if r['x1'] <= event.x <= r['x2'] and r['y1'] <= event.y <= r['y2']:
                self._selected_table_id = r['table']['id']
                self._draw(self._tables_data)  # Перерисовываем с выделением
                break

    def _create_order(self):
        if not self._selected_table_id:
            messagebox.showwarning("Выбор", "Кликните на столик для выбора", parent=self)
            return
        
        uid = self.user['id']
        shift = ShiftModel.get_today_open(uid)
        if not shift:
            messagebox.showwarning("Смена", "Сначала откройте смену!", parent=self)
            return
        
        # Проверяем, есть ли уже заказ на этом столе
        existing_orders = OrderModel.get_by_table(self._selected_table_id, active_only=True)
        
        # Проверяем статусы существующих заказов
        allowed_statuses = ['composing', 'placed', 'accepted']
        
        if existing_orders:
            # Проверяем, можно ли редактировать существующий заказ
            for o in existing_orders:
                if o['status'] in allowed_statuses:
                    # Открываем существующий заказ для редактирования
                    OrderDialog(self, table_id=self._selected_table_id, waiter_id=uid,
                            order_id=o['id'], on_save=self.refresh)
                    return
        
        # Если нет активного заказа или он в другом статусе - создаем новый
        result = OrderModel.create(self._selected_table_id, uid)
        
        if isinstance(result, dict):
            if result.get('action') == 'confirm':
                # Показываем предупреждение о брони
                if messagebox.askyesno("Забронированный стол", result['message'], parent=self):
                    # Пользователь подтвердил - создаем заказ
                    reservation_id = result['reservation']['id']
                    order_id = OrderModel.create_forced(self._selected_table_id, uid, reservation_id)
                    # Открываем диалог заказа
                    OrderDialog(self, table_id=self._selected_table_id, 
                            waiter_id=uid, reservation_id=reservation_id,
                            order_id=order_id, on_save=self.refresh)
                return
            
            elif result.get('action') == 'created':
                order_id = result['order_id']
                # Открываем диалог заказа
                OrderDialog(self, table_id=self._selected_table_id, 
                        waiter_id=uid, order_id=order_id, on_save=self.refresh)


# ── Заказы (официант) ────────────────────────────────────────────────────────
class OrdersView(BasePage):
    def _build(self):
        self._page_header("Заказы")
        tb = OFrame(self, bg=BG_DARK)
        tb.pack(fill='x', padx=PAD_LG, pady=PAD)
        OButton(tb, "Обновить", command=self.refresh, variant='secondary').pack(side='left', padx=(0, 8))
        OButton(tb, "Открыть / изменить", command=self._open_order, variant='primary').pack(side='left', padx=(0, 8))
        OButton(tb, "✏️ Изменить статус", command=self._edit_status, variant='primary').pack(side='left', padx=(0, 8))
        OButton(tb, "Оформить счёт и оплату", command=self._create_bill, variant='gold').pack(side='left', padx=(0, 8))
        OButton(tb, "Отменить заказ", command=self._cancel_order, variant='danger').pack(side='left')

        cols = ('id', 'table', 'waiter', 'status', 'placed_at', 'created_at')
        headers = ('№', 'Стол', 'Официант', 'Статус', 'Оформлен', 'Создан')
        widths = (50, 70, 160, 150, 150, 150)
        frm, self.tree = self._make_tree(self, cols)
        frm.pack(fill='both', expand=True, padx=PAD_LG, pady=(0, PAD_LG))
        for col, hdr, w in zip(cols, headers, widths):
            self.tree.heading(col, text=hdr)
            self.tree.column(col, width=w)
        self.refresh()

    def _edit_status(self):
        """Изменить статус заказа (официант)"""
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Выбор", "Выберите заказ", parent=self)
            return
        
        oid = int(sel[0])
        order = OrderModel.get_order_detail(oid)
        if not order:
            messagebox.showerror("Ошибка", "Заказ не найден", parent=self)
            return
        
        # Используем тот же диалог, но с is_admin=False
        from src.views.admin_views import AdminOrderStatusDialog
        AdminOrderStatusDialog(self, order=order, on_save=self.refresh, is_admin=False)

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        for o in OrderModel.get_all():
            # Добавляем 'cooking' в список статусов для отображения
            color = STATUS_COLORS.get(o['status'], CREAM)
            iid = str(o['id'])
            self.tree.insert('', 'end', iid=iid, tags=(iid,), values=(
                o['id'], f"№{o['table_number']}", o['waiter_name'],
                STATUS_LABELS.get(o['status'], o['status']),
                str(o.get('placed_at', '') or '')[:16],
                str(o['created_at'])[:16]))
            self.tree.tag_configure(iid, foreground=color)

    def _open_order(self):
        sel = self.tree.selection()
        if not sel:
            return messagebox.showwarning("Выбор", "Выберите заказ", parent=self)
        oid = int(sel[0])
        order = OrderModel.get_order_detail(oid)
        if not order:
            return
        
        current_status = order['status']
        
        # Разрешаем редактирование для всех статусов, кроме оплачен и отменен
        if current_status in ('paid', 'cancelled'):
            OrderDetailDialog(self, order=order, waiter_id=self.user['id'], on_save=self.refresh)
            return
        
        # Для всех остальных статусов - открываем редактирование
        OrderDialog(self, table_id=order['table_id'], waiter_id=self.user['id'],
                    order_id=oid, on_save=self.refresh)

    def _cancel_order(self):
        sel = self.tree.selection()
        if not sel:
            return
        oid = int(sel[0])
        if messagebox.askyesno("Отмена", f"Отменить заказ №{oid}?", parent=self):
            try:
                OrderModel.cancel_order(oid)
                self.refresh()
                show_toast(self, "Заказ отменён", 'info')
            except ValueError as e:
                messagebox.showerror("Ошибка", str(e), parent=self)

    def _create_bill(self):
        sel = self.tree.selection()
        if not sel:
            return messagebox.showwarning("Выбор", "Выберите заказ", parent=self)
        oid = int(sel[0])
        order = OrderModel.get_order_detail(oid)
        if not order:
            return
        try:
            bill_id, total = BillModel.create_bill(
                order['table_id'], self.user['id'], order.get('reservation_id'))
            if total == 0:
                messagebox.showwarning("Счёт", "Сумма заказов равна 0. Проверьте состав заказов.", parent=self)
                return
            if not messagebox.askyesno("Счёт",
                    f"Счёт №{bill_id} — Стол №{order['table_number']}\n"
                    f"Итого: {total:.2f} ₽\n\nПровести оплату?", parent=self):
                return
            # Выбор способа оплаты
            PayDialog(self, bill_id=bill_id, total=total, on_paid=self._on_paid)
        except Exception as e:
            messagebox.showerror("Ошибка", str(e), parent=self)

    def _on_paid(self, receipt_num):
        self.refresh()
        show_toast(self, f"Оплата принята. Чек: {receipt_num}", 'success', 3500)

class WaiterOrderStatusDialog(tk.Toplevel):
    """Диалог изменения статуса заказа для официанта"""
    def __init__(self, master, order, on_save=None):
        super().__init__(master)
        self.order = order
        self.on_save = on_save
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

        Divider(form).pack(fill='x', pady=10)

        # Выбор нового статуса
        OLabel(form, "Новый статус:", color=GOLD, font=FONT_SMALL, 
               bg=BG_DARK).pack(anchor='w', pady=(8,2))
        
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
        
        if self.order['status'] in ('paid', 'cancelled'):
            OLabel(form, "❌ Заказ уже оплачен или отменен", 
                   color=ERROR, font=FONT_SMALL, bg=BG_DARK).pack(pady=10)
            self.cmb_status = None
        else:
            current = self.order['status']
            
            # Для официанта доступны все переходы
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
                allowed = ['paid']  # ← Разрешаем оплату
            else:
                allowed = []
            
            status_options = [(k, v) for k, v in all_statuses if k in allowed]
            
            if not status_options:
                OLabel(form, "❌ Нет доступных статусов", 
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


class PayDialog(tk.Toplevel):
    """Диалог выбора способа оплаты."""
    def __init__(self, master, bill_id, total, on_paid=None):
        super().__init__(master)
        self.bill_id = bill_id
        self.total = total
        self.on_paid = on_paid
        self.title("Оплата")
        self.configure(bg=BG_DARK)
        self.geometry("360x300")
        self.resizable(False, False)
        self.grab_set()
        self._build()

    def _build(self):
        OLabel(self, "Способ оплаты", color=GOLD, font=FONT_H1, bg=BG_DARK).pack(pady=PAD_LG)
        Divider(self).pack(fill='x', padx=PAD_LG)
        OLabel(self, f"Итого к оплате: {self.total:.2f} ₽",
               color=CREAM, font=FONT_H2, bg=BG_DARK).pack(pady=PAD_LG)
        self.method_var = tk.StringVar(value='card')
        rf = OFrame(self, bg=BG_DARK)
        rf.pack(pady=PAD)
        for text, val in [("💳 Банковская карта", 'card'), ("💵 Наличные", 'cash')]:
            tk.Radiobutton(rf, text=text, variable=self.method_var, value=val,
                           bg=BG_DARK, fg=CREAM, selectcolor=BG_INPUT,
                           activebackground=BG_DARK, font=FONT_BODY,
                           cursor='hand2').pack(anchor='w', pady=4)
        btns = OFrame(self, bg=BG_DARK)
        btns.pack(fill='x', padx=PAD_LG, pady=PAD)
        OButton(btns, "Оплатить", command=self._pay, variant='gold').pack(side='left', padx=(0, 8))
        OButton(btns, "Отмена", command=self.destroy, variant='ghost').pack(side='left')

    def _pay(self):
        try:
            receipt_num = BillModel.pay_bill(self.bill_id, self.method_var.get())
            self.destroy()
            if self.on_paid:
                self.on_paid(receipt_num)
        except Exception as e:
            messagebox.showerror("Ошибка", str(e), parent=self)


# ── Диалог создания нового заказа ────────────────────────────────────────────
class OrderDialog(tk.Toplevel):
    def __init__(self, master, table_id, waiter_id, reservation_id=None, order_id=None, on_save=None):  # ДОБАВЛЯЕМ order_id
        super().__init__(master)
        self.table_id = table_id
        self.waiter_id = waiter_id
        self.reservation_id = reservation_id
        self.order_id = order_id  # Теперь может быть передан извне
        self.on_save = on_save
        self.configure(bg=BG_DARK)
        self.geometry("780x700")
        self.grab_set()
        self._build()
        
        # Если заказ уже создан - загружаем его, иначе создаем новый
        if self.order_id:
            self.title(f"Заказ №{self.order_id} — Стол №{self.table_id}")
            self._refresh_order()
        else:
            self._create_order()

    def _build(self):
        # ВЕСЬ КОД _build ОСТАЕТСЯ БЕЗ ИЗМЕНЕНИЙ
        top = OFrame(self, bg=BG_DARK)
        top.pack(fill='both', expand=True, padx=PAD, pady=PAD)

        # ── Левая панель: меню ──
        left = OCard(top)
        left.pack(side='left', fill='both', expand=True, padx=(0, 8))
        OLabel(left, "Меню", color=GOLD, font=FONT_H2, bg=BG_CARD).pack(pady=8)
        Divider(left).pack(fill='x')

        self.dish_tree = ttk.Treeview(
            left, columns=('id', 'cat', 'name', 'price', 'stock', 'disc'),
            show='headings', style='Oltremare.Treeview', height=18)
        for col, hdr, w in zip(
                ('id', 'cat', 'name', 'price', 'stock', 'disc'),
                ('№', 'Кат.', 'Блюдо', 'Цена', 'Остаток', 'Скидка'),
                (40, 80, 160, 80, 70, 60)):
            self.dish_tree.heading(col, text=hdr)
            self.dish_tree.column(col, width=w)
        apply_tree_grid(self.dish_tree)
        self.dish_tree.pack(fill='both', expand=True, padx=8, pady=8)
        self._load_dishes()

        # ── Правая панель: состав ──
        right = OCard(top)
        right.pack(side='left', fill='both', expand=True)
        OLabel(right, "Состав заказа", color=GOLD, font=FONT_H2, bg=BG_CARD).pack(pady=8)
        Divider(right).pack(fill='x')

        # Фильтр по категории
        flt = OFrame(left, bg=BG_CARD)
        flt.pack(fill='x', padx=8, pady=(6,2))
        OLabel(flt, "Категория:", color=MUTED, font=FONT_SMALL, bg=BG_CARD).pack(side='left')
        _cats = DishModel.get_categories()
        self._dish_cat_vals = ['Все'] + [c['name'] for c in _cats]
        self._dish_cat_ids  = [None]  + [c['id']   for c in _cats]
        self._dish_cat_cb   = OCombobox(flt, values=self._dish_cat_vals, state='readonly', width=16)
        self._dish_cat_cb.current(0)
        self._dish_cat_cb.pack(side='left', padx=6)
        self._dish_cat_cb.bind('<<ComboboxSelected>>', lambda e: self._load_dishes())

        # Добавляем информацию о статусе
        self.status_label = OLabel(right, "Статус: загрузка...", 
                                color=MUTED, font=FONT_SMALL, bg=BG_CARD)
        self.status_label.pack(anchor='w', padx=8, pady=4)

        qty_row = OFrame(right, bg=BG_CARD)
        qty_row.pack(fill='x', padx=8, pady=8)
        OLabel(qty_row, "Кол-во:", color=MUTED, font=FONT_SMALL, bg=BG_CARD).pack(side='left')
        self.ent_qty = OEntry(qty_row, width=5)
        self.ent_qty.insert(0, '1')
        self.ent_qty.pack(side='left', padx=8, ipady=4)
        OButton(qty_row, "+ Добавить", command=self._add_item,
                variant='gold').pack(side='left')

        self.order_tree = ttk.Treeview(
            right, columns=('id', 'name', 'qty', 'price', 'total'),
            show='headings', style='Oltremare.Treeview', height=10)
        for col, hdr, w in zip(
                ('id', 'name', 'qty', 'price', 'total'),
                ('№', 'Блюдо', 'Кол-во', 'Цена', 'Итого'),
                (40, 160, 60, 80, 90)):
            self.order_tree.heading(col, text=hdr)
            self.order_tree.column(col, width=w)
        apply_tree_grid(self.order_tree)
        self.order_tree.pack(fill='both', expand=True, padx=8, pady=4)

        OButton(right, "✕  Удалить позицию", command=self._remove_item,
                variant='danger').pack(padx=8, pady=4, fill='x')

        self.lbl_total = OLabel(right, "Итого: 0.00 ₽", color=GOLD,
                                 font=FONT_H1, bg=BG_CARD)
        self.lbl_total.pack(pady=8)

        btns = OFrame(self, bg=BG_DARK)
        btns.pack(fill='x', padx=PAD, pady=PAD)

        # Создаем две кнопки и показываем нужную
        self.btn_place_order = OButton(btns, "✔  Оформить заказ", command=self._place_order,
                                    variant='gold')
        self.btn_save_changes = OButton(btns, "💾 Сохранить изменения", command=self._save_changes,
                                        variant='primary')

        # По умолчанию показываем кнопку оформления
        self.btn_place_order.pack(side='left', padx=(0, 8))
        self.btn_save_changes.pack_forget()

        OButton(btns, "Закрыть", command=self.destroy, variant='ghost').pack(side='left')

    def _load_dishes(self):
        self.dish_tree.delete(*self.dish_tree.get_children())
        cat_id = None
        if hasattr(self, '_dish_cat_ids') and hasattr(self, '_dish_cat_cb'):
            cat_id = self._dish_cat_ids[self._dish_cat_cb.current()]
        dishes = DishModel.get_all(available_only=True)
        dishes.sort(key=lambda d: (d.get('category_name', ''), d.get('name', '')))  # сортировка
        for d in dishes:
            if cat_id and d.get('category_id') != cat_id:
                continue
            disc_val = d.get('discount', 0) or 0
            disc = f"{float(disc_val):.0f}%" if float(disc_val) > 0 else "—"
            stop = " ⛔" if d.get('is_stopped') else ""
            self.dish_tree.insert('', 'end', iid=str(d['id']), values=(
                d['id'], d['category_name'], d['name'] + stop,
                f"{d['price']:.2f} ₽", d['stock_quantity'], disc))
        apply_tree_grid(self.dish_tree)  # если уже вызывается, можно оставить

    def _create_order(self):
        """Создать новый заказ (только если order_id не передан)"""
        try:
            # Используем create_forced, т.к. проверка уже пройдена в TablesLayoutView
            self.order_id = OrderModel.create_forced(
                self.table_id, self.waiter_id, self.reservation_id)
            self.title(f"Заказ №{self.order_id} — Стол №{self.table_id}")
            self._refresh_order()
        except Exception as e:
            messagebox.showerror("Ошибка", str(e), parent=self)
            self.destroy()

    def _add_item(self):
        if not self.order_id:
            return
        sel = self.dish_tree.selection()
        if not sel:
            return messagebox.showwarning("Выбор", "Выберите блюдо из меню", parent=self)
        dish_id = int(sel[0])
        try:
            qty = int(self.ent_qty.get().strip())
            if qty <= 0:
                raise ValueError("Количество должно быть > 0")
            
            # Проверяем статус заказа
            order = execute_query("SELECT status FROM orders WHERE id=%s", (self.order_id,), fetch_one=True)
            if not order:
                raise ValueError("Заказ не найден")
            
            # Разрешаем редактирование для статусов: composing, placed, accepted, cooking, ready
            if order['status'] in ('paid', 'cancelled'):
                raise ValueError(f"Нельзя редактировать заказ в статусе «{STATUS_LABELS.get(order['status'], order['status'])}»")
            
            msg = OrderModel.add_item(self.order_id, dish_id, qty)
            show_toast(self, msg, 'success', 3000)
            self._refresh_order()
            self._load_dishes()
        except (ValueError, Exception) as e:
            messagebox.showerror("Ошибка", str(e), parent=self)

    def _remove_item(self):
        sel = self.order_tree.selection()
        if not sel:
            return
        try:
            item_id = int(sel[0])
            
            # Проверяем статус заказа
            item = execute_query("""SELECT o.status FROM order_items oi
                JOIN orders o ON oi.order_id = o.id
                WHERE oi.id = %s""", (item_id,), fetch_one=True)
            if item and item['status'] in ('paid', 'cancelled'):
                raise ValueError(f"Нельзя редактировать заказ в статусе «{STATUS_LABELS.get(item['status'], item['status'])}»")
            
            msg = OrderModel.remove_item(item_id)
            show_toast(self, msg, 'info', 3000)
            self._refresh_order()
            self._load_dishes()
        except Exception as e:
            messagebox.showerror("Ошибка", str(e), parent=self)

    def _refresh_order(self):
        self.order_tree.delete(*self.order_tree.get_children())
        if not self.order_id:
            return
        order = OrderModel.get_order_detail(self.order_id)
        if not order:
            return
        
        total = 0
        for item in order.get('items', []):
            line_total = item['quantity'] * float(item['final_price'])
            total += line_total
            self.order_tree.insert('', 'end', iid=str(item['id']), values=(
                item['id'], item['dish_name'], item['quantity'],
                f"{item['final_price']:.2f} ₽", f"{line_total:.2f} ₽"))
        
        self.lbl_total.configure(text=f"Итого: {total:.2f} ₽")
        
        # Обновляем статус
        status_text = STATUS_LABELS.get(order['status'], order['status'])
        color = STATUS_COLORS.get(order['status'], CREAM)
        self.status_label.configure(text=f"Статус: {status_text}", fg=color)
        
        # Меняем кнопку в зависимости от статуса
        # Показываем нужную кнопку в зависимости от статуса
        if order['status'] == 'composing':
            self.btn_place_order.pack(side='left', padx=(0, 8))
            self.btn_save_changes.pack_forget()
        else:
            self.btn_save_changes.pack(side='left', padx=(0, 8))
            self.btn_place_order.pack_forget()

    def _place_order(self):
        if not self.order_id:
            return
        try:
            order = execute_query("SELECT status FROM orders WHERE id=%s", (self.order_id,), fetch_one=True)
            if not order:
                raise ValueError("Заказ не найден")
            
            if order['status'] in ('paid', 'cancelled'):
                raise ValueError(f"Заказ уже {STATUS_LABELS.get(order['status'], order['status'])}")
            
            # Если заказ уже оформлен (не composing) - просто сохраняем
            if order['status'] != 'composing':
                self._save_changes()
                return
            
            # Если заказ в статусе composing - оформляем
            OrderModel.place_order(self.order_id)
            order = OrderModel.get_order_detail(self.order_id)
            items_count = sum(i['quantity'] for i in order.get('items', []))
            total = sum(i['quantity'] * float(i['final_price']) for i in order.get('items', []))
            placed = str(order.get('placed_at', ''))[:16]
            res_id = order.get('reservation_id')
            msg = (f"{'В список заказов по Брони №' + str(res_id) + chr(10) if res_id else ''}"
                f"Заказ №{self.order_id} успешно оформлен!\n\n"
                f"Стол №{order['table_number']}\n"
                f"Принял: {order['waiter_name']}\n"
                f"Дата и время: {placed}\n"
                f"Количество блюд: {items_count} порц.\n"
                f"Сумма заказа: {total:.2f} ₽")
            messagebox.showinfo("Заказ оформлен", msg, parent=self)
            if self.on_save:
                self.on_save()
            self.destroy()
        except ValueError as e:
            messagebox.showerror("Ошибка", str(e), parent=self)

    def _save_changes(self):
        """Сохранить изменения (для уже оформленных заказов)"""
        self._refresh_order()
        show_toast(self, "Изменения сохранены", 'success')
        if self.on_save:
            self.on_save()
        self.destroy()


# ── Просмотр существующего заказа ────────────────────────────────────────────
class OrderDetailDialog(tk.Toplevel):
    def __init__(self, master, order, waiter_id, on_save=None):
        super().__init__(master)
        self.order = order
        self.waiter_id = waiter_id
        self.on_save = on_save
        self.title(f"Заказ №{order['id']} — Стол №{order['table_number']}")
        self.configure(bg=BG_DARK)
        self.geometry("620x570")
        self.grab_set()
        self._build()

    def _build(self):
        info = OCard(self)
        info.pack(fill='x', padx=PAD, pady=PAD)
        status = STATUS_LABELS.get(self.order['status'], self.order['status'])
        tk.Label(info, bg=BG_CARD, fg=GOLD, font=FONT_H2,
                text=f"Заказ №{self.order['id']}  |  {status}  |  {self.order['waiter_name']}").pack(pady=10)

        cols = ('name', 'qty', 'price', 'discount', 'total')
        headers = ('Блюдо', 'Кол-во', 'Цена', 'Скидка', 'Итого')
        widths = (180, 70, 90, 70, 90)
        frm = OFrame(self, bg=BG_DARK)
        frm.pack(fill='both', expand=True, padx=PAD, pady=(0, PAD))
        tree = ttk.Treeview(frm, columns=cols, show='headings', style='Oltremare.Treeview')
        for col, hdr, w in zip(cols, headers, widths):
            tree.heading(col, text=hdr)
            tree.column(col, width=w)
        apply_tree_grid(tree)
        vsb = ttk.Scrollbar(frm, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side='right', fill='y')
        tree.pack(fill='both', expand=True)

        total = 0
        for item in self.order.get('items', []):
            line = item['quantity'] * float(item['final_price'])
            total += line
            tree.insert('', 'end', values=(
                item['dish_name'], item['quantity'],
                f"{item['unit_price']:.2f} ₽",
                f"{item['discount_percent']:.0f}%",
                f"{line:.2f} ₽"))

        OLabel(self, f"ИТОГО: {total:.2f} ₽", color=GOLD, font=FONT_H1, bg=BG_DARK).pack(pady=8)

        btns = OFrame(self, bg=BG_DARK)
        btns.pack(fill='x', padx=PAD, pady=PAD)
        
        # Кнопка "Изменить статус" доступна для всех статусов, кроме оплачен и отменен
        if self.order['status'] not in ('paid', 'cancelled'):
            OButton(btns, "✏️ Изменить статус", command=self._edit_status, 
                    variant='primary').pack(side='left', padx=(0, 8))
        
        if self.order['status'] == 'composing':
            OButton(btns, "Оформить", command=self._place, variant='gold').pack(side='left', padx=(0, 8))
        
        OButton(btns, "Закрыть", command=self.destroy, variant='ghost').pack(side='left')

    def _place(self):
        try:
            OrderModel.place_order(self.order['id'])
            if self.on_save:
                self.on_save()
            show_toast(self.master, "Заказ оформлен", 'success')
            self.destroy()
        except Exception as e:
            messagebox.showerror("Ошибка", str(e), parent=self)

    def _edit_status(self):
        """Изменить статус заказа"""
        from src.views.admin_views import AdminOrderStatusDialog
        AdminOrderStatusDialog(self, order=self.order, on_save=self._on_status_changed, is_admin=False)

    def _on_status_changed(self):
        """Обновить данные после изменения статуса"""
        # Обновляем данные заказа
        self.order = OrderModel.get_order_detail(self.order['id'])
        # Обновляем интерфейс - перестраиваем окно
        for widget in self.winfo_children():
            widget.destroy()
        self._build()
        if self.on_save:
            self.on_save()


# ── Брони (официант) ─────────────────────────────────────────────────────────
class WaiterReservationsView(BasePage):
    def _build(self):
        self._page_header("Брони на сегодня")
        tb = OFrame(self, bg=BG_DARK)
        tb.pack(fill='x', padx=PAD_LG, pady=PAD)
        OButton(tb, "+ Новая бронь", command=self._new, variant='gold').pack(side='left', padx=(0, 8))
        OButton(tb, "✏️ Редактировать", command=self._edit, variant='secondary').pack(side='left', padx=(0, 8))
        OButton(tb, "Обновить", command=self.refresh, variant='secondary').pack(side='left', padx=(0, 8))
        OButton(tb, "Создать заказ по брони", command=self._order_from_res, variant='primary').pack(side='left')

        cols = ('id', 'client', 'phone', 'date', 'time_range', 'guests', 'tables', 'notes')
        headers = ('№', 'Клиент', 'Телефон', 'Дата', 'Время', 'Гостей', 'Столики', 'Примечание')
        widths = (50, 150, 120, 100, 130, 70, 80, 180)
        frm, self.tree = self._make_tree(self, cols)
        frm.pack(fill='both', expand=True, padx=PAD_LG, pady=(0, PAD_LG))
        for col, hdr, w in zip(cols, headers, widths):
            self.tree.heading(col, text=hdr)
            self.tree.column(col, width=w)
        self.refresh()

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        for r in ReservationModel.get_by_date(date.today()):
            t_start = str(r['reservation_time'])[:5]
            t_end = str(r['end_time'])[:5] if r.get('end_time') else ''
            
            # Форматируем время в виде "16:00 – 20:00"
            if t_end:
                time_display = f"{t_start} – {t_end}"
            else:
                time_display = t_start
            
            self.tree.insert('', 'end', iid=str(r['id']), values=(
                r['id'], r['client_name'], r['client_phone'],
                str(r['reservation_date']),
                time_display,  # ← Теперь показывает "16:00 – 17:00"
                r['guests_count'], r.get('table_numbers', ''),
                r.get('notes', '')))

    def _new(self):
        ReservationDialog(self, user=self.user, on_save=self.refresh)

    def _edit(self):  # ← ДОБАВЛЕН МЕТОД
        """Редактировать выбранную бронь"""
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Выбор", "Выберите бронь для редактирования", parent=self)
            return
        rid = int(sel[0])
        rows = ReservationModel.get_by_date(date.today())
        res = next((r for r in rows if r['id'] == rid), None)
        if res:
            ReservationDialog(self, user=self.user, reservation=res, on_save=self.refresh)

    def _order_from_res(self):
        sel = self.tree.selection()
        if not sel:
            return messagebox.showwarning("Выбор", "Выберите бронь", parent=self)
        rid = int(sel[0])
        uid = self.user['id']
        shift = ShiftModel.get_today_open(uid)
        if not shift:
            return messagebox.showwarning("Смена", "Сначала откройте смену!", parent=self)
        # Берём первый стол из брони
        rows = ReservationModel.get_by_date(date.today())
        res = next((r for r in rows if r['id'] == rid), None)
        if not res:
            return
        table_ids_str = res.get('table_ids', '')
        if not table_ids_str:
            return messagebox.showwarning("Бронь", "У брони нет прикреплённых столиков", parent=self)
        table_id = int(str(table_ids_str).split(',')[0])
        OrderDialog(self, table_id=table_id, waiter_id=uid,
                    reservation_id=rid, on_save=self.refresh)
