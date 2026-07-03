"""
Oltremare — Вход / Регистрация (исправлено: RegisterWindow не наследует от Toplevel напрямую)
"""
import tkinter as tk
from tkinter import messagebox
from src.utils.theme import *
from src.models.models import AuthModel


class LoginWindow(tk.Toplevel):
    def __init__(self, master, on_success, on_guest=None):
        super().__init__(master)
        self.on_success = on_success
        self.on_guest   = on_guest
        self.title("Oltremare — Вход")
        self.resizable(False, False)
        self.configure(bg=BG_DARK)
        self.geometry("420x560")
        self._center()
        self._build()
        self.grab_set()

    def _center(self):
        self.update_idletasks()
        sw = self.winfo_screenwidth(); sh = self.winfo_screenheight()
        self.geometry(f"420x560+{(sw-420)//2}+{(sh-560)//2}")

    def _build(self):
        hdr = OFrame(self, bg=BG_PANEL)
        hdr.pack(fill='x')
        tk.Label(hdr, text="Oltremare", font=(FONT_FAMILY, 26, "bold italic"),
                 fg=GOLD, bg=BG_PANEL, pady=22).pack()
        tk.Label(hdr, text="Система управления рестораном",
                 font=FONT_SMALL, fg=MUTED, bg=BG_PANEL).pack()
        Divider(hdr).pack(fill='x', pady=(10,0))

        form = OFrame(self, bg=BG_DARK)
        form.pack(fill='both', expand=True, padx=40, pady=20)

        OLabel(form, "Логин", color=GOLD, font=FONT_SMALL, bg=BG_DARK).pack(anchor='w')
        self.ent_user = OEntry(form)
        self.ent_user.pack(fill='x', pady=(4,14), ipady=7)

        OLabel(form, "Пароль", color=GOLD, font=FONT_SMALL, bg=BG_DARK).pack(anchor='w')
        self.ent_pass = OEntry(form, show="•")
        self.ent_pass.pack(fill='x', pady=(4,20), ipady=7)

        OButton(form, "Войти", command=self._login, variant='gold').pack(fill='x', pady=(0,8))
        Divider(form).pack(fill='x', pady=10)
        OLabel(form, "Нет аккаунта?", color=MUTED, font=FONT_SMALL, bg=BG_DARK).pack()
        OButton(form, "Зарегистрироваться", command=self._open_register,
                variant='secondary').pack(fill='x', pady=4)

        if self.on_guest:
            Divider(form).pack(fill='x', pady=8)
            OButton(form, "Войти как гость (просмотр меню)",
                    command=self._guest, variant='ghost').pack(fill='x')

        hint = OFrame(self, bg=BG_PANEL)
        hint.pack(fill='x', side='bottom')
        tk.Label(hint, text="admin / admin123  ·  kitchen / kitchen123",
                 font=FONT_TINY, fg=MUTED, bg=BG_PANEL, pady=8).pack()

        self.ent_user.focus()
        self.bind('<Return>', lambda e: self._login())

    def _login(self):
        username = self.ent_user.get().strip()
        password = self.ent_pass.get().strip()
        if not username or not password:
            messagebox.showwarning("Ошибка", "Заполните все поля", parent=self)
            return
        try:
            user = AuthModel.login(username, password)
            if user:
                if self.winfo_exists():
                    self.destroy()
                self.on_success(user)
            else:
                messagebox.showerror("Ошибка", "Неверный логин или пароль", parent=self)
                self.ent_pass.delete(0, 'end')
        except Exception as e:
            if self.winfo_exists():
                messagebox.showerror("Ошибка подключения", str(e), parent=self)

    def _open_register(self):
        from src.views.login_view import show_register
        show_register(self.master, on_success=lambda u: (self.destroy(), self.on_success(u)))

    def _guest(self):
        self.destroy()
        if self.on_guest:
            self.on_guest()

# Глобальная функция для вызова из других модулей
def show_register(master, on_success):
    """Открыть окно регистрации (глобальная функция)"""
    win = tk.Toplevel(master)
    win.title("Регистрация")
    win.resizable(False, False)
    win.configure(bg=BG_DARK)
    win.geometry("440x600")
    win.grab_set()

    hdr = OFrame(win, bg=BG_PANEL)
    hdr.pack(fill='x')
    tk.Label(hdr, text="Регистрация", font=FONT_H1, fg=GOLD, bg=BG_PANEL, pady=18).pack()
    Divider(hdr).pack(fill='x')

    form = OFrame(win, bg=BG_DARK)
    form.pack(fill='both', expand=True, padx=40, pady=14)

    fields = [
        ("Полное имя *", 'full_name', False),
        ("Логин *",      'username',  False),
        ("Пароль *",     'password',  True),
        ("Телефон *",    'phone',     False),
        ("Email",        'email',     False),
    ]
    entries = {}
    for label, key, is_pass in fields:
        OLabel(form, label, color=GOLD, font=FONT_SMALL, bg=BG_DARK).pack(anchor='w')
        e = OEntry(form, show="•" if is_pass else "")
        e.pack(fill='x', pady=(4,9), ipady=6)
        entries[key] = e

    OLabel(form, "Формат телефона: +7XXXXXXXXXX или 8XXXXXXXXXX",
           color=MUTED, font=FONT_TINY, bg=BG_DARK).pack(anchor='w', pady=(0,10))

    def do_register():
        from src.models.models import validate_phone
        data = {k: e.get().strip() for k, e in entries.items()}
        if not all([data['full_name'], data['username'], data['password'], data['phone']]):
            messagebox.showwarning("Ошибка", "Заполните обязательные поля (*)", parent=win)
            return
        try:
            validate_phone(data['phone'])
        except ValueError as ex:
            messagebox.showerror("Ошибка", str(ex), parent=win)
            return
        try:
            AuthModel.register(data['username'], data['password'],
                               data['full_name'], data['phone'], data['email'],
                               role_name='client')
            user = AuthModel.login(data['username'], data['password'])
            messagebox.showinfo("Успех", "Аккаунт создан!", parent=win)
            win.destroy()
            on_success(user)
        except ValueError as ex:
            messagebox.showerror("Ошибка", str(ex), parent=win)

    def switch_to_login():
        win.destroy()
        LoginWindow(master, on_success=on_success, on_guest=None)

    OButton(form, "Создать аккаунт", command=do_register, variant='gold').pack(fill='x', pady=(0,6))
    OButton(form, "Уже есть аккаунт? Войти", 
            command=switch_to_login,
            variant='ghost').pack(fill='x', pady=(4, 0))
    OButton(form, "Отмена", command=win.destroy, variant='ghost').pack(fill='x', pady=(4, 0))