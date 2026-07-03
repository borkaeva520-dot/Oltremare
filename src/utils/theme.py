"""
Oltremare — тема, стили, виджеты (финальная версия)
Кнопки с тёмным фоном, цифры в календаре видны, DateEntry активен.
"""
import tkinter as tk
import tkinter.ttk as ttk
import calendar
from datetime import date as _date

BG_DARK    = "#1A1714"
BG_PANEL   = "#2A2420"
BG_CARD    = "#332E29"
BG_INPUT   = "#3D3630"
BG_HOVER   = "#4A433C"

CREAM      = "#F5EFE6"
GOLD       = "#C9A96E"
GOLD_LIGHT = "#E8C99A"
GOLD_DARK  = "#9E7A45"
MUTED      = "#9A8F84"
BORDER     = "#4A433C"

SUCCESS    = "#6B9E6B"
WARNING    = "#C9A96E"
ERROR      = "#B05555"
INFO       = "#5580B0"

BTN_NAV_FG = "#D4C5B0"

STATUS_COLORS = {
    "free":"#6B9E6B","occupied":"#B05555","reserved":"#C9A96E","unavailable":"#666666",
    "composing":"#5580B0","placed":"#C9A96E","cancelled":"#B05555","accepted":"#8B6BB0","cooking":"#E8A045",
    "ready":"#6B9E9E","delivered":"#6B9E6B","paid":"#6B9E6B",
    "pending":"#C9A96E","active":"#6B9E6B","scheduled":"#5580B0","open":"#6B9E6B","closed":"#9A8F84",
}
STATUS_LABELS = {
    "free":"Свободен","occupied":"Занят","reserved":"Забронирован","unavailable":"Недоступен",
    "composing":"Составление","placed":"Оформлен","cancelled":"Отменён","accepted":"Принят","cooking":"Готовится",
    "ready":"Готов","delivered":"Выдан","paid":"Оплачен",
    "pending":"Ожидает оплаты","active":"Активна","scheduled":"Запланирована",
    "open":"Открыта","closed":"Закрыта",
}

FONT_FAMILY = "Georgia"
FONT_SANS   = "Helvetica Neue"
FONT_TITLE  = (FONT_FAMILY, 22, "bold")
FONT_H1     = (FONT_SANS, 15, "bold")
FONT_H2     = (FONT_SANS, 13, "bold")
FONT_BODY   = (FONT_SANS, 14)
FONT_SMALL  = (FONT_SANS, 12)
FONT_TINY   = (FONT_SANS, 12)
FONT_NAV = (FONT_SANS, 13, "bold")

PAD    = 12
PAD_SM = 12
PAD_LG = 20
SIDEBAR_W = 220


def configure_ttk_styles():
    style = ttk.Style()
    try: style.theme_use('clam')
    except Exception: pass
    style.configure('.', background=BG_DARK, foreground=CREAM,
        fieldbackground=BG_INPUT, font=FONT_BODY, bordercolor=BORDER,
        troughcolor=BG_PANEL, selectbackground=GOLD_DARK, selectforeground=CREAM)
    style.configure('Oltremare.Treeview', background=BG_CARD, foreground=CREAM,
        fieldbackground=BG_CARD, rowheight=28, font=FONT_BODY)
    style.configure('Oltremare.Treeview.Heading', background=BG_PANEL,
        foreground=GOLD, font=FONT_H2, relief='flat')
    style.map('Oltremare.Treeview',
        background=[('selected', GOLD_DARK)], foreground=[('selected', CREAM)])
    style.configure('TCombobox', background=BG_INPUT, foreground=CREAM,
        fieldbackground=BG_INPUT, selectbackground=GOLD_DARK, arrowcolor=GOLD)
    style.map('TCombobox',
        fieldbackground=[('readonly', BG_INPUT)], foreground=[('readonly', CREAM)],
        selectbackground=[('readonly', GOLD_DARK)])
    style.configure('Oltremare.TNotebook', background=BG_DARK, tabmargins=[2,5,2,0])
    style.configure('Oltremare.TNotebook.Tab', background=BG_PANEL, foreground=MUTED,
        padding=[14,6], font=FONT_BODY)
    style.map('Oltremare.TNotebook.Tab',
        background=[('selected', BG_DARK)], foreground=[('selected', GOLD)])
    style.configure('Vertical.TScrollbar', background=BG_PANEL,
        troughcolor=BG_DARK, arrowcolor=GOLD)
    style.configure('Horizontal.TScrollbar', background=BG_PANEL,
        troughcolor=BG_DARK, arrowcolor=GOLD)


# ── Базовые виджеты ──────────────────────────────────────────────────────────

class OFrame(tk.Frame):
    def __init__(self, master, bg=None, **kw):
        super().__init__(master, bg=bg or BG_DARK, **kw)

class OCard(tk.Frame):
    def __init__(self, master, **kw):
        super().__init__(master, bg=BG_CARD,
            highlightthickness=1, highlightbackground=BORDER, **kw)

class OLabel(tk.Label):
    def __init__(self, master, text='', color=None, font=None, bg=None, **kw):
        super().__init__(master, text=text, fg=color or CREAM,
            bg=bg or BG_DARK, font=font or FONT_BODY, **kw)

class OButton(tk.Button):
    """Кнопка — всегда тёмный фон, светлый контрастный текст."""
    _COLORS = {
        'primary':   ("#3A6A9E", "#03338D"),
        'secondary': ("#3A3A3A", "#3A3A3A"),
        'danger':    ("#750000", "#750000"),
        'success':   ("#077207", "#077207"),
        'ghost':     (BG_PANEL, GOLD),
        'gold':      (GOLD_DARK, "#1A1714"),
        'info':      ("#1E5F8A", CREAM),
    }
    _HOVER = {
        'primary':   "#4A5A8A",
        'secondary': "#5A5A5A",
        'danger':    "#7B0000",
        'success':   "#3A7A3A",
        'ghost':     BG_HOVER,
        'gold':      GOLD,
        'info':      "#2E4A7F",
    }
    def __init__(self, master, text='', command=None, variant='primary', width=None, **kw):
        bg, fg = self._COLORS.get(variant, self._COLORS['primary'])
        hover  = self._HOVER.get(variant, BG_HOVER)
        opts = dict(text=text, command=command, bg=bg, fg=fg, font=FONT_BODY,
            relief='flat', cursor='hand2', padx=PAD, pady=6,
            activebackground=hover, activeforeground=fg,
            borderwidth=0)
        if width: opts['width'] = width
        opts.update(kw)
        super().__init__(master, **opts)
        self._bg = bg; self._hover_bg = hover
        self.bind('<Enter>', lambda e: self.configure(bg=self._hover_bg))
        self.bind('<Leave>', lambda e: self.configure(bg=self._bg))

class OEntry(tk.Entry):
    def __init__(self, master, **kw):
        super().__init__(master, bg=BG_INPUT, fg=CREAM, insertbackground=GOLD,
            relief='flat', font=FONT_BODY, highlightthickness=1,
            highlightbackground=BORDER, highlightcolor=GOLD, **kw)

class OText(tk.Text):
    def __init__(self, master, **kw):
        super().__init__(master, bg=BG_INPUT, fg=CREAM, insertbackground=GOLD,
            relief='flat', font=FONT_BODY, highlightthickness=1,
            highlightbackground=BORDER, highlightcolor=GOLD,
            selectbackground=GOLD_DARK, **kw)

class OCombobox(ttk.Combobox):
    def __init__(self, master, **kw):
        super().__init__(master, font=FONT_BODY, **kw)

class Divider(tk.Frame):
    def __init__(self, master, **kw):
        super().__init__(master, bg=BORDER, height=1, **kw)


def show_toast(parent, message: str, kind='info', duration=2800):
    colors = {'info': INFO, 'success': SUCCESS, 'error': ERROR, 'warning': WARNING}
    bg = colors.get(kind, INFO)
    try:
        toast = tk.Toplevel(parent)
        toast.overrideredirect(True)
        toast.attributes('-topmost', True)
        toast.configure(bg=bg)
        tk.Label(toast, text=message, bg=bg, fg=CREAM, font=FONT_BODY,
            padx=20, pady=10, wraplength=420, justify='center').pack()
        parent.update_idletasks()
        pw = parent.winfo_width(); ph = parent.winfo_height()
        px = parent.winfo_rootx(); py = parent.winfo_rooty()
        toast.update_idletasks()
        tw = toast.winfo_width(); th = toast.winfo_height()
        toast.geometry(f"+{px+(pw-tw)//2}+{py+ph-th-70}")
        toast.after(duration, lambda: toast.destroy() if toast.winfo_exists() else None)
    except Exception:
        pass


# ── Календарь ────────────────────────────────────────────────────────────────

class DatePicker(tk.Frame):
    """Мини-календарь. Цифры — CREAM на тёмном фоне."""
    def __init__(self, master, initial_date=None, **kw):
        super().__init__(master, bg=BG_PANEL,
                         highlightthickness=2, highlightbackground=GOLD, **kw)
        self._date = initial_date or _date.today()
        self._year  = self._date.year
        self._month = self._date.month
        self._build()

    def _build(self):
        for w in self.winfo_children():
            w.destroy()

        # Заголовок месяц/год
        hdr = tk.Frame(self, bg=BG_PANEL)
        hdr.pack(fill='x', padx=6, pady=6)
        tk.Button(hdr, text='◀', bg=BG_CARD, fg=GOLD_LIGHT, relief='flat',
                font=FONT_BODY, cursor='hand2', padx=4,
                command=self._prev_month).pack(side='left')
        tk.Label(hdr, text=f"{calendar.month_abbr[self._month]} {self._year}",
                bg=BG_PANEL, fg=GOLD_LIGHT, font=FONT_H2, width=12).pack(side='left', expand=True)
        tk.Button(hdr, text='▶', bg=BG_CARD, fg=GOLD_LIGHT, relief='flat',
                font=FONT_BODY, cursor='hand2', padx=4,
                command=self._next_month).pack(side='right')

        # Дни недели (с использованием grid)
        dow_frame = tk.Frame(self, bg=BG_PANEL)
        dow_frame.pack(fill='x', padx=6)
        for i, d in enumerate(['Пн','Вт','Ср','Чт','Пт','Сб','Вс']):
            lbl = tk.Label(dow_frame, text=d, bg=BG_PANEL, fg=GOLD,
                        font=FONT_SMALL, anchor='center')
            lbl.grid(row=0, column=i, sticky='nsew')
            dow_frame.columnconfigure(i, weight=1)

        Divider(self).pack(fill='x', padx=6, pady=2)

        # Сетка дней
        cal = calendar.monthcalendar(self._year, self._month)
        for row in cal:
            row_frame = tk.Frame(self, bg=BG_PANEL)
            row_frame.pack(fill='x', padx=6, pady=1)
            for col, day in enumerate(row):
                if day == 0:
                    lbl = tk.Label(row_frame, text='', bg=BG_PANEL, font=FONT_SMALL)
                    lbl.grid(row=0, column=col, sticky='nsew')
                else:
                    d = _date(self._year, self._month, day)
                    is_sel   = (d == self._date)
                    is_today = (d == _date.today())
                    if is_sel:
                        bg, fg = GOLD, "#1A1714"
                    elif is_today:
                        bg, fg = BG_HOVER, GOLD_LIGHT
                    else:
                        bg, fg = BG_CARD, GOLD
                    btn = tk.Button(row_frame, text=str(day), bg=bg, fg=fg,
                                    relief='flat', cursor='hand2',
                                    font=FONT_BODY, pady=2,
                                    activebackground=GOLD_DARK, activeforeground=CREAM,
                                    command=lambda dd=d: self._select(dd))
                    btn.grid(row=0, column=col, sticky='nsew')
                row_frame.columnconfigure(col, weight=1)

        tk.Frame(self, bg=BG_PANEL, height=4).pack()

    def _prev_month(self):
        if self._month == 1: 
            self._month = 12
            self._year -= 1
        else: 
            self._month -= 1
        self._build()

    def _next_month(self):
        if self._month == 12: 
            self._month = 1
            self._year += 1
        else: 
            self._month += 1
        self._build()

    def _select(self, d):
        self._date = d
        self._build()
        self.event_generate('<<DateSelected>>')

    def get_date(self): 
        return self._date

    def set_date(self, d):
        self._date = d
        self._year = d.year
        self._month = d.month
        self._build()


class DateEntry(tk.Frame):
    """Поле ввода даты с кнопкой-календарём."""
    def __init__(self, master, initial_date=None, **kw):
        super().__init__(master, bg=BG_DARK, **kw)
        self._date = initial_date or _date.today()
        self._popup = None
        self.var = tk.StringVar(value=self._date.strftime('%d.%m.%Y'))
        
        self._entry = OEntry(self, textvariable=self.var, width=11)
        self._entry.pack(side='left', ipady=5)
        self._entry.bind('<Button-1>', self._toggle_popup)
        self._entry.bind('<Key>', lambda e: 'break')
        
        self._btn = tk.Button(self, text='📅', bg=BG_CARD, fg=GOLD,
                              relief='flat', cursor='hand2',
                              font=FONT_BODY, padx=4, pady=3,
                              activebackground=BG_HOVER, activeforeground=GOLD,
                              command=self._toggle_popup)
        self._btn.pack(side='left', padx=(2, 0))

    def _toggle_popup(self, event=None):
        """Открыть/закрыть календарь"""
        if self._popup and self._popup.winfo_exists():
            self._close_popup()
            return
        
        # Создаем окно календаря
        self._popup = tk.Toplevel(self)
        self._popup.overrideredirect(True)
        self._popup.attributes('-topmost', True)
        self._popup.configure(bg=BG_PANEL)
        
        # Позиционируем под полем ввода
        self.update_idletasks()
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height() + 4
        self._popup.geometry(f"+{x}+{y}")
        
        # Создаем календарь
        picker = DatePicker(self._popup, initial_date=self._date)
        picker.pack(padx=4, pady=4)
        picker.bind('<<DateSelected>>', lambda e: self._on_select(picker))
        
        # Захватываем фокус
        self._popup.grab_set()
        self._popup.focus_set()
        
        # Закрываем по Escape
        self._popup.bind('<Escape>', lambda e: self._close_popup())
        
        # Закрываем при клике вне календаря
        self._popup.bind('<FocusOut>', lambda e: self.after(100, self._close_popup))

    def _on_select(self, picker):
        """Выбрана дата"""
        self._date = picker.get_date()
        self.var.set(self._date.strftime('%d.%m.%Y'))
        self._close_popup()
        self.event_generate('<<DateSelected>>')

    def _close_popup(self):
        """Закрыть календарь и вернуть фокус"""
        try:
            if self._popup and self._popup.winfo_exists():
                self._popup.grab_release()
                self._popup.destroy()
        except Exception:
            pass
        self._popup = None
        self._entry.focus_set()

    def get_date(self):
        try:
            from datetime import datetime as _dt
            return _dt.strptime(self.var.get(), '%d.%m.%Y').date()
        except ValueError:
            return self._date

    def set_date(self, d):
        self._date = d
        self.var.set(d.strftime('%d.%m.%Y'))

def apply_tree_grid(tree):
    """Добавить визуальную сетку: чередующиеся строки + разделители колонок."""
    # Чередование строк (чётные темнее)
    tree.tag_configure('odd',  background=BG_CARD)
    tree.tag_configure('even', background="#2E2923")

    def _retag(*_):
        for i, iid in enumerate(tree.get_children()):
            tag = 'even' if i % 2 == 0 else 'odd'
            cur = list(tree.item(iid, 'tags'))
            cur = [t for t in cur if t not in ('odd','even')]
            cur.append(tag)
            tree.item(iid, tags=cur)

    tree.bind('<<TreeviewSelect>>', _retag, add='+')
    tree.bind('<Map>', _retag, add='+')
    # Вызываем сразу
    try:
        _retag()
    except Exception:
        pass
    return tree


class TimeCombo(ttk.Combobox):
    """Выпадающий список времени 09:00–23:00 шаг 30 мин."""
    def __init__(self, master, **kw):
        times = []
        for h in range(9, 24):
            times.append(f"{h:02d}:00")
            if h < 23: times.append(f"{h:02d}:30")
        super().__init__(master, values=times, state='readonly',
                         font=FONT_BODY, width=7, **kw)
        self.set('19:00')

    def get_time_str(self): return self.get()