"""
Oltremare — Виды кухни (исправленная версия)
"""
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox

from src.utils.theme import *
from src.models.models import OrderModel, DishModel
from src.views.admin_views import BasePage


# ── Заказы (кухня) ───────────────────────────────────────────────────────────
class KitchenOrdersView(BasePage):
    def _build(self):
        self._page_header("Кухня — Заказы", "управление статусами")

        tb = OFrame(self, bg=BG_DARK)
        tb.pack(fill='x', padx=PAD_LG, pady=PAD)
        OButton(tb, "Обновить", command=self.refresh, variant='secondary').pack(side='left', padx=(0, 8))
        OButton(tb, "▶ Принять в готовку", command=lambda: self._set_status('accepted'),
                variant='primary').pack(side='left', padx=(0, 8))
        OButton(tb, "🔪 В процессе", command=lambda: self._set_status('cooking'),
                variant='primary').pack(side='left', padx=(0, 8))
        OButton(tb, "✔ Готово к выдаче", command=lambda: self._set_status('ready'),
                variant='success').pack(side='left', padx=(0, 8))
        OButton(tb, "↗ Выдан официанту", command=lambda: self._set_status('delivered'),
                variant='gold').pack(side='left')

        # Легенда
        leg = OFrame(self, bg=BG_DARK)
        leg.pack(fill='x', padx=PAD_LG, pady=(0, PAD))
        for sk in ('placed', 'accepted', 'cooking', 'ready', 'delivered'):
            f = OFrame(leg, bg=BG_DARK)
            f.pack(side='left', padx=10)
            tk.Frame(f, bg=STATUS_COLORS.get(sk, MUTED), width=12, height=12).pack(side='left', padx=4)
            OLabel(f, STATUS_LABELS.get(sk, sk), font=FONT_SMALL, bg=BG_DARK).pack(side='left')

        # СОЗДАЕМ TREEVIEW
        cols = ('id', 'table', 'waiter', 'status', 'placed_at', 'items')
        headers = ('№', 'Стол', 'Официант', 'Статус', 'Оформлен', 'Состав заказа')
        widths = (50, 70, 160, 150, 150, 360)
        
        frm, self.tree = self._make_tree(self, cols, heights=16)  # ИСПРАВЛЕНО
        frm.pack(fill='both', expand=True, padx=PAD_LG, pady=(0, PAD_LG))
        
        for col, hdr, w in zip(cols, headers, widths):
            self.tree.heading(col, text=hdr)
            self.tree.column(col, width=w)
            
        self.refresh()

    def refresh(self):
        if not hasattr(self, 'tree'):
            return
        self.tree.delete(*self.tree.get_children())
        for o in OrderModel.get_all():
            if o['status'] not in ('placed', 'accepted', 'cooking', 'ready', 'delivered'):
                continue
            detail = OrderModel.get_order_detail(o['id'])
            items_str = ', '.join(
                f"{i['dish_name']} x{i['quantity']}"
                for i in detail.get('items', [])) if detail else ''
            color = STATUS_COLORS.get(o['status'], CREAM)
            iid = str(o['id'])
            self.tree.insert('', 'end', iid=iid, tags=(iid,), values=(
                o['id'], f"№{o['table_number']}", o['waiter_name'],
                STATUS_LABELS.get(o['status'], o['status']),
                str(o.get('placed_at', '') or '')[:16],
                items_str))
            self.tree.tag_configure(iid, foreground=color)

    def _set_status(self, new_status):
        if not hasattr(self, 'tree'):
            return
        sel = self.tree.selection()
        if not sel:
            return messagebox.showwarning("Выбор", "Выберите заказ", parent=self)
        oid = int(sel[0])
        try:
            OrderModel.update_status(oid, new_status)
            self.refresh()
            show_toast(self, f"Заказ №{oid}: {STATUS_LABELS.get(new_status, new_status)}", 'success')
        except Exception as e:
            messagebox.showerror("Ошибка", str(e), parent=self)


# ── Склад / Стоп-лист ────────────────────────────────────────────────────────
class StockView(BasePage):
    def _build(self):
        self._page_header("Склад и стоп-лист")

        tb = OFrame(self, bg=BG_DARK)
        tb.pack(fill='x', padx=PAD_LG, pady=PAD)
        OButton(tb, "Обновить", command=self.refresh, variant='secondary').pack(side='left', padx=(0, 8))
        OButton(tb, "Изменить остаток", command=self._edit_stock,
                variant='primary').pack(side='left', padx=(0, 8))
        OButton(tb, "⛔ Стоп / ✓ Снять стоп", command=self._toggle_stop,
                variant='danger').pack(side='left')

        # Стоп-лист баннер
        self.stop_banner = OCard(self)
        self.stop_banner.pack(fill='x', padx=PAD_LG, pady=(0, PAD))
        self.lbl_stop = tk.Label(self.stop_banner, text="",
                                  font=FONT_BODY, fg=ERROR, bg=BG_CARD,
                                  wraplength=900, justify='left', pady=6)
        self.lbl_stop.pack(anchor='w', padx=PAD)

        cols = ('id', 'category', 'name', 'stock', 'price', 'stopped')
        headers = ('№', 'Категория', 'Блюдо', 'Остаток', 'Цена ₽', 'Стоп-лист')
        widths = (50, 130, 220, 90, 90, 90)
        
        frm, self.tree = self._make_tree(self, cols, heights=16)  # ИСПРАВЛЕНО
        frm.pack(fill='both', expand=True, padx=PAD_LG, pady=(0, PAD_LG))
        
        for col, hdr, w in zip(cols, headers, widths):
            self.tree.heading(col, text=hdr)
            self.tree.column(col, width=w)
        self.refresh()

    def refresh(self):
        if not hasattr(self, 'tree'):
            return
        self.tree.delete(*self.tree.get_children())
        dishes = DishModel.get_all()
        stopped_names = []
        for d in dishes:
            stopped = d.get('is_stopped', False)
            if stopped:
                stopped_names.append(d['name'])
            stop_label = "⛔ Стоп" if stopped else "✓ Доступно"
            color = ERROR if stopped else (SUCCESS if d['stock_quantity'] > 0 else WARNING)
            iid = str(d['id'])
            self.tree.insert('', 'end', iid=iid, tags=(iid,), values=(
                d['id'], d['category_name'], d['name'],
                d['stock_quantity'], f"{d['price']:.2f}", stop_label))
            self.tree.tag_configure(iid, foreground=color)
        if stopped_names:
            self.lbl_stop.configure(
                text="⛔ СТОП-ЛИСТ: " + ", ".join(stopped_names))
        else:
            self.lbl_stop.configure(text="✅ Стоп-лист пуст")

    def _edit_stock(self):
        if not hasattr(self, 'tree'):
            return
        sel = self.tree.selection()
        if not sel:
            return messagebox.showwarning("Выбор", "Выберите блюдо", parent=self)
        did = int(sel[0])
        dishes = DishModel.get_all()
        dish = next((d for d in dishes if d['id'] == did), None)
        if dish:
            StockEditDialog(self, dish=dish, on_save=self.refresh)

    def _toggle_stop(self):
        if not hasattr(self, 'tree'):
            return
        sel = self.tree.selection()
        if not sel:
            return messagebox.showwarning("Выбор", "Выберите блюдо", parent=self)
        did = int(sel[0])
        dishes = DishModel.get_all()
        dish = next((d for d in dishes if d['id'] == did), None)
        if dish:
            was_stopped = bool(dish.get('is_stopped'))
            DishModel.toggle_stop(did)
            action = "убрано из" if was_stopped else "добавлено в"
            show_toast(self, f"Блюдо «{dish['name']}» {action} стоп-листа",
                       'info' if was_stopped else 'warning')
            self.refresh()


class StockEditDialog(tk.Toplevel):
    def __init__(self, master, dish, on_save=None):
        super().__init__(master)
        self.dish = dish
        self.on_save = on_save
        self.title(f"Склад: {dish['name']}")
        self.configure(bg=BG_DARK)
        self.geometry("360x280")
        self.grab_set()
        self._build()

    def _build(self):
        OLabel(self, self.dish['name'], color=GOLD, font=FONT_H1, bg=BG_DARK).pack(pady=PAD_LG)
        Divider(self).pack(fill='x', padx=PAD_LG)
        form = OFrame(self, bg=BG_DARK)
        form.pack(fill='both', expand=True, padx=PAD_LG, pady=PAD)
        OLabel(form, f"Текущий остаток: {self.dish['stock_quantity']} порц.",
               color=MUTED, font=FONT_BODY, bg=BG_DARK).pack(anchor='w', pady=8)
        OLabel(form, "Новый остаток:", color=GOLD, font=FONT_SMALL, bg=BG_DARK).pack(anchor='w')
        self.ent_stock = OEntry(form)
        self.ent_stock.insert(0, str(self.dish['stock_quantity']))
        self.ent_stock.pack(fill='x', ipady=6)
        self.ent_stock.select_range(0, 'end')
        btns = OFrame(self, bg=BG_DARK)
        btns.pack(fill='x', padx=PAD_LG, pady=PAD)
        OButton(btns, "Сохранить", command=self._save, variant='gold').pack(side='left', padx=(0, 8))
        OButton(btns, "Отмена", command=self.destroy, variant='ghost').pack(side='left')

    def _save(self):
        try:
            qty = int(self.ent_stock.get().strip())
            if qty < 0:
                raise ValueError("Остаток не может быть отрицательным")
            DishModel.update_stock(self.dish['id'], qty)
            if self.on_save:
                self.on_save()
            show_toast(self.master, f"Остаток обновлён: {qty} порц.", 'success')
            self.destroy()
        except ValueError as e:
            messagebox.showerror("Ошибка", str(e), parent=self)