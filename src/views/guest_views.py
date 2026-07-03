"""
Oltremare — Виды для гостя (приветственная страница)
"""
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox

from src.utils.theme import *
from src.models.models import DishModel
from src.views.admin_views import BasePage
from src.views.login_view import show_register


# ── Приветственная страница для гостя ──────────────────────────────────────
class GuestHomeView(BasePage):
    """Приветственная страница как на сайте ресторана"""
    
    def _build(self):
        # Основной контейнер с прокруткой
        container = OFrame(self, bg=BG_DARK)
        container.pack(fill='both', expand=True)
        
        # Создаем Canvas для прокрутки
        self.canvas = tk.Canvas(container, bg=BG_DARK, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient='vertical', command=self.canvas.yview)
        
        # Фрейм для контента
        self.scrollable_frame = OFrame(self.canvas, bg=BG_DARK)
        
        # Настройка прокрутки
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw", width=self.canvas.winfo_width())
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        # Расположение
        self.canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Привязываем колесико мыши для прокрутки
        self._bind_mousewheel()
        
        # При изменении размера canvas обновляем ширину контента
        self.canvas.bind('<Configure>', self._on_canvas_configure)
        
        self._build_content()

    def _on_canvas_configure(self, event):
        """Обновить ширину контента при изменении размера окна"""
        self.canvas.itemconfig(1, width=event.width)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _bind_mousewheel(self):
        """Привязать прокрутку колесиком мыши"""
        def on_mousewheel(event):
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        def on_mousewheel_mac(event):
            self.canvas.yview_scroll(int(-1 * event.delta), "units")
        
        # Для Windows/Linux
        self.canvas.bind_all("<MouseWheel>", on_mousewheel)
        # Для MacOS
        self.canvas.bind_all("<Button-4>", lambda e: self.canvas.yview_scroll(-1, "units"))
        self.canvas.bind_all("<Button-5>", lambda e: self.canvas.yview_scroll(1, "units"))

    def _unbind_mousewheel(self):
        """Отвязать прокрутку (для предотвращения конфликтов)"""
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")

    def destroy(self):
        """Переопределяем destroy для отвязки событий"""
        self._unbind_mousewheel()
        super().destroy()

    def _build_content(self):
        """Построить контент страницы"""
        # Очищаем
        for w in self.scrollable_frame.winfo_children():
            w.destroy()

        # ── Верхний баннер ──
        banner = OFrame(self.scrollable_frame, bg=BG_PANEL)
        banner.pack(fill='x', pady=(0, 40))
        
        # Декоративная линия
        tk.Frame(banner, bg=GOLD, height=3).pack(fill='x')
        
        # Логотип
        tk.Label(banner, text="Oltremare", 
                font=(FONT_FAMILY, 48, "bold italic"),
                fg=GOLD, bg=BG_PANEL).pack(pady=(40, 5))
        
        tk.Label(banner, text="Итальянская кухня с душой", 
                font=(FONT_SANS, 16), fg=CREAM, bg=BG_PANEL).pack(pady=(0, 10))
        
        tk.Frame(banner, bg=GOLD_DARK, height=2, width=200).pack(pady=10)
        
        tk.Label(banner, text="Двухэтажный ресторан с видом на Саввинскую набережную", 
                font=(FONT_SANS, 12), fg=MUTED, bg=BG_PANEL).pack(pady=5)
        
        # Кнопка "Забронировать"
        btn_frame = OFrame(banner, bg=BG_PANEL)
        btn_frame.pack(pady=25)
        
        OButton(btn_frame, "🍽️ Забронировать столик", 
                command=self._prompt_register,
                variant='gold').pack(pady=10, padx=20, ipadx=30, ipady=8)
        
        tk.Label(banner, text="Нажимая на кнопку «Забронировать», вы соглашаетесь с Политикой конфиденциальности",
                font=FONT_TINY, fg=MUTED, bg=BG_PANEL, wraplength=500).pack(pady=(0, 30))
        
        tk.Frame(banner, bg=GOLD, height=3).pack(fill='x')

        # ── О ресторане ──
        about = OFrame(self.scrollable_frame, bg=BG_DARK)
        about.pack(fill='x', padx=60, pady=40)
        
        tk.Label(about, text="О ресторане", 
                font=FONT_H1, fg=GOLD, bg=BG_DARK).pack(anchor='w', pady=(0, 15))
        
        tk.Label(about, 
                text="«Со страстью и самоотдачей — мы готовим по простым рецептам, "
                     "которые обогащаем опытом и нашей души»",
                font=(FONT_SANS, 14), fg=CREAM, bg=BG_DARK, wraplength=800,
                justify='left').pack(anchor='w')
        
        tk.Label(about, 
                text=f"\n— Бренд-шеф Эмануэле Поллини",
                font=(FONT_SANS, 12, "italic"), fg=MUTED, bg=BG_DARK).pack(anchor='w')

        # ── Меню (краткий обзор) ──
        menu_preview = OFrame(self.scrollable_frame, bg=BG_DARK)
        menu_preview.pack(fill='x', padx=60, pady=40)
        
        tk.Label(menu_preview, text="Наше меню", 
                font=FONT_H1, fg=GOLD, bg=BG_DARK).pack(anchor='w', pady=(0, 15))
        
        # Показываем несколько категорий с блюдами
        categories = DishModel.get_categories()[:4]
        menu_grid = OFrame(menu_preview, bg=BG_DARK)
        menu_grid.pack(fill='x')
        
        for i, cat in enumerate(categories):
            col = i % 2
            row = i // 2
            
            card = OCard(menu_grid)
            card.grid(row=row, column=col, padx=10, pady=10, sticky='nsew')
            
            tk.Label(card, text=cat['name'], font=FONT_H2, 
                    bg=BG_CARD, fg=GOLD).pack(pady=(15, 5))
            
            dishes = DishModel.get_all(available_only=True, category_id=cat['id'])[:3]
            for d in dishes:
                tk.Label(card, text=f"• {d['name']}", font=FONT_SMALL, 
                        bg=BG_CARD, fg=CREAM).pack(anchor='w', padx=15, pady=2)
            
            if len(dishes) == 0:
                tk.Label(card, text="Скоро появится", font=FONT_SMALL, 
                        bg=BG_CARD, fg=MUTED).pack(pady=10)
        
        menu_grid.columnconfigure(0, weight=1)
        menu_grid.columnconfigure(1, weight=1)

        # Кнопка "Полное меню"
        OButton(menu_preview, "🍽️ Смотреть полное меню", 
                command=self._go_to_menu,
                variant='secondary').pack(pady=20)

        # ── Нижний колонтитул ──
        footer = OFrame(self.scrollable_frame, bg=BG_PANEL)
        footer.pack(fill='x', pady=(40, 0))
        
        tk.Frame(footer, bg=GOLD, height=2).pack(fill='x')
        
        footer_inner = OFrame(footer, bg=BG_PANEL)
        footer_inner.pack(fill='x', padx=60, pady=20)
        
        tk.Label(footer_inner, text="© 2026 Oltremare. Все права защищены.", 
                font=FONT_TINY, fg=MUTED, bg=BG_PANEL).pack(side='left')
        
        tk.Label(footer_inner, text="Ресторан итальянской кухни", 
                font=FONT_TINY, fg=MUTED, bg=BG_PANEL).pack(side='right')

    def _prompt_register(self):
        """Предложить зарегистрироваться для бронирования"""
        if messagebox.askyesno("Регистрация",
                "Для бронирования столика и заказов нужен аккаунт.\n\n"
                "Зарегистрироваться сейчас?",
                parent=self):
            from src.views.login_view import show_register
            show_register(self.winfo_toplevel(), on_success=self._on_registered)

    def _on_registered(self, user):
        """После регистрации обновляем интерфейс"""
        show_toast(self, f"Добро пожаловать, {user['full_name']}!", 'success', 3000)
        self.winfo_toplevel()._on_login(user)

    def _go_to_menu(self):
        """Перейти на страницу меню"""
        root = self.winfo_toplevel()
        if hasattr(root, '_show_page'):
            root._show_page('menu_view')