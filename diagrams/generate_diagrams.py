"""
Генератор диаграмм для проекта Oltremare
- UML Use Case диаграмма
- ER диаграмма
- Блок-схема процесса заказа
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Ellipse
import matplotlib.patheffects as pe
import numpy as np

# Цвета в стиле Oltremare
BG      = '#0F0F1A'
DARK    = '#1A1A2E'
GOLD    = '#C9A96E'
CREAM   = '#F5F0E8'
BLUE    = '#2E4057'
GREEN   = '#4CAF82'
RED     = '#C94F4F'
GRAY    = '#888888'
WHITE   = '#FFFFFF'

# ─────────────────────────────────────────────────────────────
# 1. UML Use Case Diagram
# ─────────────────────────────────────────────────────────────
def draw_actor(ax, x, y, label, color=CREAM):
    # Голова
    circle = plt.Circle((x, y+0.35), 0.12, color=color, zorder=5)
    ax.add_patch(circle)
    # Тело
    ax.plot([x, x], [y+0.23, y-0.10], color=color, lw=2, zorder=5)
    # Руки
    ax.plot([x-0.18, x+0.18], [y+0.08, y+0.08], color=color, lw=2, zorder=5)
    # Ноги
    ax.plot([x, x-0.15], [y-0.10, y-0.35], color=color, lw=2, zorder=5)
    ax.plot([x, x+0.15], [y-0.10, y-0.35], color=color, lw=2, zorder=5)
    ax.text(x, y-0.50, label, ha='center', va='top', fontsize=8,
            color=color, fontweight='bold', zorder=6)

def use_case_ellipse(ax, x, y, w, h, text, color=BLUE, textcolor=CREAM):
    ell = Ellipse((x, y), w, h, color=color, zorder=4, alpha=0.9)
    ax.add_patch(ell)
    ax.text(x, y, text, ha='center', va='center', fontsize=7,
            color=textcolor, zorder=5, wrap=True,
            multialignment='center')

def draw_arrow(ax, x1, y1, x2, y2, color=GRAY):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color=color, lw=1.2))

fig, ax = plt.subplots(figsize=(20, 14))
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)
ax.set_xlim(0, 20)
ax.set_ylim(0, 14)
ax.axis('off')
ax.set_title('UML-диаграмма вариантов использования\nСистема управления рестораном «Oltremare»',
             color=GOLD, fontsize=14, fontweight='bold', pad=15)

# Граница системы
sys_rect = FancyBboxPatch((2.5, 0.5), 15, 12.5, boxstyle="round,pad=0.1",
                           edgecolor=GOLD, facecolor='#12122A', linewidth=2, zorder=1)
ax.add_patch(sys_rect)
ax.text(10, 13.1, 'Система «Oltremare»', ha='center', color=GOLD, fontsize=10, style='italic')

# Акторы
actors = [
    (0.9, 11.5, 'Клиент'),
    (0.9, 7.5,  'Официант'),
    (0.9, 3.5,  'Кухня'),
    (19.1, 9.0, 'Администратор'),
]
for (ax_, ay, lbl) in actors:
    draw_actor(ax, ax_, ay, lbl, GOLD)

# Use cases — Клиент
client_cases = [
    (5.5, 12.0, 'Зарегистрироваться /\nВойти в систему'),
    (5.5, 10.5, 'Забронировать\nстолик'),
    (5.5, 9.0,  'Отменить\nбронь'),
    (5.5, 7.5,  'Просмотреть\nсхему столиков'),
]
for (cx, cy, txt) in client_cases:
    use_case_ellipse(ax, cx, cy, 3.0, 0.8, txt)

# Стрелки клиента вручную
for (cx, cy, txt) in client_cases:
    ax.annotate('', xy=(cx-1.5, cy), xytext=(1.3, 11.5),
                arrowprops=dict(arrowstyle='->', color=GRAY, lw=1))

# Use cases — Официант
waiter_cases = [
    (9.5, 12.0, 'Открыть / закрыть\nсмену'),
    (9.5, 10.5, 'Создать заказ'),
    (9.5, 9.0,  'Добавить блюдо\nв заказ'),
    (9.5, 7.5,  'Удалить блюдо\nиз заказа'),
    (9.5, 6.0,  'Оформить заказ'),
    (9.5, 4.5,  'Сформировать\nсчёт'),
    (9.5, 3.0,  'Провести оплату\n/ выдать чек'),
]
for (cx, cy, txt) in waiter_cases:
    use_case_ellipse(ax, cx, cy, 3.0, 0.8, txt, color='#1E3A5F')
    ax.annotate('', xy=(cx-1.5, cy), xytext=(1.3, 7.5),
                arrowprops=dict(arrowstyle='->', color=GRAY, lw=1))

# Use cases — Кухня
kitchen_cases = [
    (14.0, 6.0, 'Просмотреть\nзаказы'),
    (14.0, 4.5, 'Изменить статус\nзаказа'),
    (14.0, 3.0, 'Отметить заказ\nготовым'),
]
for (cx, cy, txt) in kitchen_cases:
    use_case_ellipse(ax, cx, cy, 3.0, 0.8, txt, color='#1A3A2A')
    ax.annotate('', xy=(cx+1.5, cy), xytext=(18.7, 3.5),
                arrowprops=dict(arrowstyle='->', color=GRAY, lw=1))

# Use cases — Администратор
admin_cases = [
    (14.0, 12.0, 'Управление\nпользователями'),
    (14.0, 10.5, 'Формировать\nграфик смен'),
    (14.0, 9.0,  'Управление\nменю и ценами'),
    (14.0, 7.5,  'Управление\nакциями'),
    (14.0, 1.5,  'Просматривать\nстатистику'),
]
for (cx, cy, txt) in admin_cases:
    use_case_ellipse(ax, cx, cy, 3.0, 0.8, txt, color='#3A2040')
    ax.annotate('', xy=(cx+1.5, cy), xytext=(18.7, 9.0),
                arrowprops=dict(arrowstyle='->', color=GRAY, lw=1))

# Общие use cases
use_case_ellipse(ax, 5.5, 1.5, 3.0, 0.8, 'Зарегистрироваться /\nВойти в систему', color='#2A2A4A')

# Легенда
legend_elements = [
    mpatches.Patch(facecolor='#1E3A5F', label='Официант'),
    mpatches.Patch(facecolor='#1A3A2A', label='Кухня'),
    mpatches.Patch(facecolor='#3A2040', label='Администратор'),
    mpatches.Patch(facecolor=BLUE,      label='Клиент'),
]
ax.legend(handles=legend_elements, loc='lower right', facecolor=DARK,
          labelcolor=CREAM, fontsize=8, framealpha=0.8)

plt.tight_layout()
plt.savefig('/home/claude/oltremare/diagrams/uml_use_case.png', dpi=150, bbox_inches='tight',
            facecolor=BG)
plt.close()
print("UML Use Case saved")


# ─────────────────────────────────────────────────────────────
# 2. ER Diagram
# ─────────────────────────────────────────────────────────────
def er_table(ax, x, y, name, fields, width=3.2, color=BLUE):
    row_h = 0.28
    total_h = row_h * (len(fields) + 1)
    # Header
    header = FancyBboxPatch((x, y - row_h), width, row_h,
                             boxstyle="round,pad=0.02", facecolor=GOLD,
                             edgecolor=GOLD, linewidth=1, zorder=3)
    ax.add_patch(header)
    ax.text(x + width/2, y - row_h/2, name, ha='center', va='center',
            fontsize=8, fontweight='bold', color=DARK, zorder=4)
    # Fields
    for i, (fname, ftype) in enumerate(fields):
        row_y = y - row_h*(i+2)
        bg_color = '#1E2A3A' if i % 2 == 0 else '#162030'
        rect = FancyBboxPatch((x, row_y), width, row_h,
                               boxstyle="square,pad=0", facecolor=bg_color,
                               edgecolor='#333355', linewidth=0.5, zorder=3)
        ax.add_patch(rect)
        is_pk = fname.startswith('PK ')
        is_fk = fname.startswith('FK ')
        fc = GOLD if is_pk else ('#A0C8FF' if is_fk else CREAM)
        ax.text(x + 0.1, row_y + row_h/2, fname, ha='left', va='center',
                fontsize=6.5, color=fc, zorder=4)
        ax.text(x + width - 0.1, row_y + row_h/2, ftype, ha='right', va='center',
                fontsize=6, color=GRAY, zorder=4)
    return (x + width/2, y - row_h/2), (x + width/2, y - total_h + row_h/2)

def er_line(ax, p1, p2, color=GRAY):
    ax.annotate('', xy=p2, xytext=p1,
                arrowprops=dict(arrowstyle='->', color=color, lw=1.0,
                                connectionstyle='arc3,rad=0.1'))

fig2, ax2 = plt.subplots(figsize=(24, 18))
fig2.patch.set_facecolor(BG)
ax2.set_facecolor(BG)
ax2.set_xlim(0, 24)
ax2.set_ylim(0, 18)
ax2.axis('off')
ax2.set_title('ER-диаграмма базы данных\nСистема управления рестораном «Oltremare»',
              color=GOLD, fontsize=14, fontweight='bold', pad=10)

tables_data = [
    # (x, y, name, [(field, type), ...])
    (0.2, 17.5, 'users', [
        ('PK id', 'INT'),
        ('login', 'VARCHAR(64)'),
        ('password_hash','VARCHAR(255)'),
        ('role', 'ENUM'),
        ('full_name', 'VARCHAR(150)'),
        ('phone', 'VARCHAR(20)'),
        ('is_active', 'TINYINT'),
    ]),
    (4.0, 17.5, 'tables', [
        ('PK id', 'INT'),
        ('number', 'INT'),
        ('capacity', 'INT'),
        ('floor', 'TINYINT'),
        ('pos_x / pos_y', 'INT'),
        ('status', 'ENUM'),
    ]),
    (7.8, 17.5, 'shifts', [
        ('PK id', 'INT'),
        ('FK waiter_id', 'INT'),
        ('shift_date', 'DATE'),
        ('start_time', 'TIME'),
        ('end_time', 'TIME'),
        ('status', 'ENUM'),
    ]),
    (11.6, 17.5, 'shift_tables', [
        ('PK id', 'INT'),
        ('FK shift_id', 'INT'),
        ('FK table_id', 'INT'),
    ]),
    (0.2, 12.0, 'reservations', [
        ('PK id', 'INT'),
        ('client_name', 'VARCHAR(150)'),
        ('phone', 'VARCHAR(20)'),
        ('res_date', 'DATE'),
        ('time_start', 'TIME'),
        ('time_end', 'TIME'),
        ('guests_count', 'INT'),
        ('status', 'ENUM'),
    ]),
    (4.0, 12.0, 'reservation_tables', [
        ('PK id', 'INT'),
        ('FK reservation_id', 'INT'),
        ('FK table_id', 'INT'),
    ]),
    (7.8, 12.0, 'menu_categories', [
        ('PK id', 'INT'),
        ('name', 'VARCHAR(100)'),
        ('sort_order', 'INT'),
    ]),
    (11.6, 12.0, 'menu_items', [
        ('PK id', 'INT'),
        ('FK category_id', 'INT'),
        ('name', 'VARCHAR(200)'),
        ('price', 'DECIMAL'),
        ('stock_qty', 'INT'),
        ('is_available', 'TINYINT'),
    ]),
    (15.4, 12.0, 'promotions', [
        ('PK id', 'INT'),
        ('name', 'VARCHAR(200)'),
        ('discount_pct', 'DECIMAL'),
        ('date_start', 'DATE'),
        ('date_end', 'DATE'),
        ('is_active', 'TINYINT'),
    ]),
    (19.2, 12.0, 'promotion_items', [
        ('PK id', 'INT'),
        ('FK promotion_id', 'INT'),
        ('FK menu_item_id', 'INT'),
        ('FK category_id', 'INT'),
    ]),
    (0.2, 6.0, 'orders', [
        ('PK id', 'INT'),
        ('FK reservation_id', 'INT'),
        ('FK table_id', 'INT'),
        ('FK waiter_id', 'INT'),
        ('status', 'ENUM'),
        ('placed_at', 'DATETIME'),
        ('total_amount', 'DECIMAL'),
        ('created_at', 'DATETIME'),
    ]),
    (4.0, 6.0, 'order_items', [
        ('PK id', 'INT'),
        ('FK order_id', 'INT'),
        ('FK menu_item_id', 'INT'),
        ('quantity', 'INT'),
        ('price_at_order', 'DECIMAL'),
        ('discount_pct', 'DECIMAL'),
    ]),
    (7.8, 6.0, 'bills', [
        ('PK id', 'INT'),
        ('FK reservation_id', 'INT'),
        ('total_amount', 'DECIMAL'),
        ('discount_amount', 'DECIMAL'),
        ('status', 'ENUM'),
        ('created_at', 'DATETIME'),
    ]),
    (11.6, 6.0, 'receipts', [
        ('PK id', 'INT'),
        ('FK bill_id', 'INT'),
        ('FK waiter_id', 'INT'),
        ('paid_amount', 'DECIMAL'),
        ('paid_at', 'DATETIME'),
    ]),
]

# Рисуем таблицы, сохраняем координаты
table_coords = {}
for (x, y, name, fields) in tables_data:
    top, bot = er_table(ax2, x, y, name, fields)
    table_coords[name] = {'top': top, 'bot': bot, 'x': x, 'y': y,
                          'left': (x, y - 0.28/2),
                          'right': (x + 3.2, y - 0.28/2)}

# Связи (упрощённо — линии между центрами)
relations = [
    ('shifts', 'users', GOLD),
    ('shifts', 'shift_tables', GREEN),
    ('tables', 'shift_tables', GREEN),
    ('reservations', 'reservation_tables', GREEN),
    ('tables', 'reservation_tables', GREEN),
    ('menu_categories', 'menu_items', GOLD),
    ('promotions', 'promotion_items', GOLD),
    ('menu_items', 'promotion_items', GOLD),
    ('reservations', 'orders', BLUE),
    ('tables', 'orders', BLUE),
    ('users', 'orders', BLUE),
    ('orders', 'order_items', GREEN),
    ('menu_items', 'order_items', GREEN),
    ('reservations', 'bills', '#A0A0FF'),
    ('bills', 'receipts', '#A0A0FF'),
    ('users', 'receipts', '#A0A0FF'),
]

for (t1, t2, color) in relations:
    p1 = table_coords[t1]['bot']
    p2 = table_coords[t2]['top']
    ax2.annotate('', xy=p2, xytext=p1,
                arrowprops=dict(arrowstyle='->', color=color, lw=1.2,
                                connectionstyle='arc3,rad=0.05'))

plt.tight_layout()
plt.savefig('/home/claude/oltremare/diagrams/er_diagram.png', dpi=150, bbox_inches='tight',
            facecolor=BG)
plt.close()
print("ER Diagram saved")


# ─────────────────────────────────────────────────────────────
# 3. Блок-схема: процесс добавления блюда в заказ
# ─────────────────────────────────────────────────────────────
def flowbox(ax, x, y, w, h, text, shape='rect', color=BLUE, tcolor=CREAM, fs=8):
    if shape == 'oval':
        ell = Ellipse((x, y), w, h, facecolor=color, edgecolor=GOLD, linewidth=1.5, zorder=3)
        ax.add_patch(ell)
    elif shape == 'diamond':
        dx, dy = w/2, h/2
        diamond = plt.Polygon([[x,y+dy],[x+dx,y],[x,y-dy],[x-dx,y]],
                               facecolor=color, edgecolor=GOLD, linewidth=1.5, zorder=3)
        ax.add_patch(diamond)
    else:
        rect = FancyBboxPatch((x-w/2, y-h/2), w, h,
                               boxstyle="round,pad=0.05",
                               facecolor=color, edgecolor=GOLD, linewidth=1.5, zorder=3)
        ax.add_patch(rect)
    ax.text(x, y, text, ha='center', va='center', fontsize=fs,
            color=tcolor, zorder=4, multialignment='center')

def flow_arrow(ax, x1, y1, x2, y2, label='', color=GRAY):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color=color, lw=1.5))
    if label:
        mx, my = (x1+x2)/2 + 0.15, (y1+y2)/2
        ax.text(mx, my, label, fontsize=7, color=GOLD)

fig3, ax3 = plt.subplots(figsize=(10, 18))
fig3.patch.set_facecolor(BG)
ax3.set_facecolor(BG)
ax3.set_xlim(0, 10)
ax3.set_ylim(0, 18)
ax3.axis('off')
ax3.set_title('Блок-схема: добавление блюда в заказ\nСистема «Oltremare»',
              color=GOLD, fontsize=12, fontweight='bold', pad=10)

steps = [
    (5, 17.2, 3.5, 0.6, 'НАЧАЛО', 'oval', GREEN),
    (5, 16.0, 4.0, 0.6, 'Официант выбирает блюдо\nи количество порций', 'rect', BLUE),
    (5, 14.6, 4.0, 0.8, 'Статус заказа\n= «Составление»?', 'diamond', '#3A2040'),
    (5, 13.2, 4.0, 0.6, 'Запрос к БД:\nсток блюда на складе', 'rect', BLUE),
    (5, 11.8, 4.0, 0.8, 'stock_qty >=\nзапрошенное кол-во?', 'diamond', '#3A2040'),
    (5, 10.4, 4.5, 0.6, 'Найти активную скидку\n(акция на блюдо/категорию)', 'rect', BLUE),
    (5, 9.0, 4.5, 0.6, 'INSERT order_items\n(цена + скидка)', 'rect', '#1A3A2A'),
    (5, 7.6, 4.5, 0.6, 'UPDATE menu_items:\nstock_qty -= количество\n(триггер)', 'rect', '#1A3A2A'),
    (5, 6.2, 4.5, 0.6, 'UPDATE orders:\ntotal_amount пересчитан\n(триггер)', 'rect', '#1A3A2A'),
    (5, 4.8, 4.5, 0.6, 'Вывод сообщения:\n«Блюдо N добавлено в Заказ M»', 'rect', '#2A3A1A'),
    (5, 3.4, 3.5, 0.6, 'КОНЕЦ', 'oval', GREEN),
]

# Ошибки (выносы)
errors = [
    (8.2, 14.6, 2.2, 0.6, 'Ошибка:\nЗаказ нельзя изменить', 'rect', RED),
    (8.2, 11.8, 2.5, 0.7, 'Ошибка:\n«Доступно X порций»\nДобавление отменено', 'rect', RED),
]

for (x, y, w, h, txt, shape, color) in steps:
    flowbox(ax3, x, y, w, h, txt, shape, color)

for (x, y, w, h, txt, shape, color) in errors:
    flowbox(ax3, x, y, w, h, txt, shape, color)

# Стрелки основного потока
for i in range(len(steps)-1):
    _, y1 = steps[i][0], steps[i][1]
    _, y2 = steps[i+1][0], steps[i+1][1]
    flow_arrow(ax3, 5, y1-0.3, 5, y2+0.3)

# Ответ «Нет» → ошибки
flow_arrow(ax3, 6.5, 14.6, 7.1, 14.6, 'Нет')
flow_arrow(ax3, 6.5, 11.8, 7.1, 11.8, 'Нет')

# Ответ «Да» подписи
ax3.text(4.3, 13.95, 'Да', fontsize=7, color=GOLD)
ax3.text(4.3, 12.55, 'Да', fontsize=7, color=GOLD)

plt.tight_layout()
plt.savefig('/home/claude/oltremare/diagrams/flowchart.png', dpi=150, bbox_inches='tight',
            facecolor=BG)
plt.close()
print("Flowchart saved")
print("All diagrams generated!")
