"""
Oltremare — модели бизнес-логики (финальная версия)
"""
import re
import itertools
from datetime import datetime, date, time, timedelta
from src.database.db import execute_query, hash_password
from src.utils.theme import STATUS_LABELS

# ─── AUTH ────────────────────────────────────────────────────────────────────

class AuthModel:
    @staticmethod
    def login(username: str, password: str):
        pwd_hash = hash_password(password)
        return execute_query("""
            SELECT u.id, u.username, u.full_name, u.phone, u.email,
                   u.is_active, r.name AS role
            FROM users u JOIN roles r ON u.role_id = r.id
            WHERE u.username=%s AND u.password_hash=%s AND u.is_active=TRUE
        """, (username, pwd_hash), fetch_one=True)
    
    @staticmethod
    def update_user(user_id, username, full_name, phone, email):
        """Обновить данные пользователя"""
        existing = execute_query(
            "SELECT id FROM users WHERE username=%s AND id!=%s",
            (username, user_id), fetch_one=True
        )
        if existing:
            raise ValueError(f"Логин «{username}» уже используется")
        
        execute_query("""
            UPDATE users 
            SET username=%s, full_name=%s, phone=%s, email=%s
            WHERE id=%s
        """, (username, full_name, phone, email, user_id))

    @staticmethod
    def update_password(user_id, new_password):
        """Обновить пароль пользователя"""
        execute_query("""
            UPDATE users 
            SET password_hash=%s
            WHERE id=%s
        """, (hash_password(new_password), user_id))

    @staticmethod
    def get_user_by_id(user_id):
        """Получить пользователя по ID"""
        return execute_query("""
            SELECT u.id, u.username, u.full_name, u.phone, u.email,
                r.name AS role, u.is_active
            FROM users u 
            JOIN roles r ON u.role_id=r.id 
            WHERE u.id=%s
        """, (user_id,), fetch_one=True)

    @staticmethod
    def register(username, password, full_name, phone, email, role_name='client'):
        role = execute_query("SELECT id FROM roles WHERE name=%s", (role_name,), fetch_one=True)
        if not role:
            raise ValueError("Роль не найдена")
        try:
            return execute_query("""
                INSERT INTO users (username, password_hash, full_name, phone, email, role_id)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (username, hash_password(password), full_name, phone, email, role['id']))
        except Exception:
            raise ValueError("Пользователь с таким логином уже существует")

    @staticmethod
    def get_all_waiters():
        return execute_query("""
            SELECT u.id, u.full_name, u.username, u.phone
            FROM users u JOIN roles r ON u.role_id=r.id
            WHERE r.name='waiter' AND u.is_active=TRUE ORDER BY u.full_name
        """, fetch=True)

    @staticmethod
    def create_user(username, password, full_name, phone, email, role_name):
        return AuthModel.register(username, password, full_name, phone, email, role_name)

    @staticmethod
    def get_all_users():
        return execute_query("""
            SELECT u.id, u.username, u.full_name, u.phone, u.email,
                   r.name AS role, u.is_active
            FROM users u JOIN roles r ON u.role_id=r.id ORDER BY r.name, u.full_name
        """, fetch=True)

    @staticmethod
    def toggle_user_active(user_id: int, is_active: bool):
        execute_query("UPDATE users SET is_active=%s WHERE id=%s", (is_active, user_id))


# ─── TABLES ──────────────────────────────────────────────────────────────────

class TableModel:
    @staticmethod
    def get_all():
        """Получить все столики."""
        return execute_query("SELECT * FROM tables ORDER BY number", fetch=True)

    @staticmethod
    def create(number, capacity, location=''):
        """Создать новый стол с проверкой вместимости"""
        if capacity > 4:
            raise ValueError(f"Вместимость стола не может превышать 4 места (запрошено: {capacity})")
        if capacity < 1:
            raise ValueError(f"Вместимость стола должна быть минимум 1 место (запрошено: {capacity})")
        if number < 1:
            raise ValueError(f"Номер стола должен быть положительным числом")
        
        existing = execute_query("SELECT id FROM tables WHERE number=%s", (number,), fetch_one=True)
        if existing:
            raise ValueError(f"Стол с номером {number} уже существует")
        
        return execute_query("""
            INSERT INTO tables (number, capacity, location, status) 
            VALUES (%s, %s, %s, 'free')
        """, (number, capacity, location))

    @staticmethod
    def update(table_id, number, capacity, location=''):
        """Обновить данные стола с проверкой вместимости"""
        if capacity > 4:
            raise ValueError(f"Вместимость стола не может превышать 4 места (запрошено: {capacity})")
        if capacity < 1:
            raise ValueError(f"Вместимость стола должна быть минимум 1 место (запрошено: {capacity})")
        if number < 1:
            raise ValueError(f"Номер стола должен быть положительным числом")
        
        existing = execute_query(
            "SELECT id FROM tables WHERE number=%s AND id!=%s", 
            (number, table_id), fetch_one=True
        )
        if existing:
            raise ValueError(f"Стол с номером {number} уже существует")
        
        execute_query("""
            UPDATE tables SET number=%s, capacity=%s, location=%s 
            WHERE id=%s
        """, (number, capacity, location, table_id))
    @staticmethod
    def delete(table_id):
        """Удалить стол (только если нет активных заказов и броней)"""
        # Проверяем, есть ли активные заказы на этом столе
        active_orders = execute_query("""
            SELECT COUNT(*) AS cnt FROM orders 
            WHERE table_id=%s AND status IN ('composing','placed','accepted','cooking','ready','delivered')
        """, (table_id,), fetch_one=True)
        
        if active_orders and active_orders['cnt'] > 0:
            raise ValueError(f"Нельзя удалить стол: на нем есть активные заказы ({active_orders['cnt']} шт.)")
        
        # Проверяем, есть ли активные брони на этом столе
        active_reservations = execute_query("""
            SELECT COUNT(*) AS cnt FROM reservation_tables rt
            JOIN reservations r ON rt.reservation_id = r.id
            WHERE rt.table_id=%s AND r.status='active' AND r.reservation_date >= CURDATE()
        """, (table_id,), fetch_one=True)
        
        if active_reservations and active_reservations['cnt'] > 0:
            raise ValueError(f"Нельзя удалить стол: на нем есть активные брони ({active_reservations['cnt']} шт.)")
        
        # Удаляем связи со сменами
        execute_query("DELETE FROM shift_tables WHERE table_id=%s", (table_id,))
        # Удаляем связи с бронями (только неактивные)
        execute_query("""
            DELETE FROM reservation_tables 
            WHERE table_id=%s AND reservation_id NOT IN (
                SELECT id FROM reservations WHERE status='active' AND reservation_date >= CURDATE()
            )
        """, (table_id,))
        # Удаляем стол
        execute_query("DELETE FROM tables WHERE id=%s", (table_id,))

    @staticmethod
    def get_by_id(table_id):
        """Получить стол по ID"""
        return execute_query("SELECT * FROM tables WHERE id=%s", (table_id,), fetch_one=True)

    
    @staticmethod
    def get_layout_status(check_datetime=None):
        if check_datetime is None:
            check_datetime = datetime.now()
        chk_date = check_datetime.date()
        chk_time_str = check_datetime.strftime('%H:%M:%S')

        tables = execute_query("SELECT id, number, capacity, location, status FROM tables ORDER BY number", fetch=True)

        orders = execute_query("""
            SELECT DISTINCT o.table_id, u.full_name AS waiter_name
            FROM orders o
            JOIN users u ON o.waiter_id = u.id
            WHERE o.status IN ('composing','placed','accepted','cooking','ready','delivered')
            AND DATE(o.created_at) = %s
        """, (chk_date,), fetch=True)
        occupied_tables = {o['table_id']: o['waiter_name'] for o in orders}

        shift_assignments = execute_query("""
            SELECT DISTINCT st.table_id, u.full_name AS waiter_name
            FROM shift_tables st
            JOIN shifts s ON st.shift_id = s.id
            JOIN users u ON s.waiter_id = u.id
            WHERE s.shift_date = %s AND s.status = 'open'
        """, (chk_date,), fetch=True)
        assigned_tables = {a['table_id']: a['waiter_name'] for a in shift_assignments}

        reservations = execute_query("""
            SELECT DISTINCT 
                rt.table_id, 
                r.id, 
                r.client_name, 
                r.guests_count,
                r.reservation_time,
                r.end_time
            FROM reservation_tables rt
            JOIN reservations r ON rt.reservation_id = r.id
            WHERE r.reservation_date = %s
            AND r.status = 'active'
            AND (
                r.reservation_time <= %s
                AND (r.end_time IS NULL OR r.end_time > %s)
                OR
                r.reservation_time > %s
                AND r.reservation_time <= ADDTIME(%s, '01:00:00')
            )
        """, (chk_date, chk_time_str, chk_time_str, chk_time_str, chk_time_str), fetch=True)

        reserved_info = {}
        for res in reservations:
            if res['table_id'] not in reserved_info:
                reserved_info[res['table_id']] = {
                    'reservation_id': res['id'],
                    'client_name': res['client_name'],
                    'guests_count': res['guests_count'],
                    'reservation_time': res['reservation_time'],
                    'end_time': res['end_time']
                }

        result = []
        for t in tables:
            row = {
                'id': t['id'],
                'number': t['number'],
                'capacity': t['capacity'],
                'location': t['location'],
                'current_status': 'free',
                'reservation_id': None,
                'client_name': None,
                'guests_count': None,
                'reservation_time': None,
                'waiter_name': None,
                'assigned_waiter': None
            }
            if t['status'] == 'unavailable':
                row['current_status'] = 'unavailable'
            elif t['id'] in occupied_tables:
                row['current_status'] = 'occupied'
                row['waiter_name'] = occupied_tables[t['id']]
            elif t['id'] in reserved_info:
                row['current_status'] = 'reserved'
                row['reservation_id'] = reserved_info[t['id']]['reservation_id']
                row['client_name'] = reserved_info[t['id']]['client_name']
                row['guests_count'] = reserved_info[t['id']]['guests_count']
                row['reservation_time'] = reserved_info[t['id']]['reservation_time']
            elif t['id'] in assigned_tables:
                row['assigned_waiter'] = assigned_tables[t['id']]
            result.append(row)
        return result
    @staticmethod
    def update_status(table_id: int, status: str):
        execute_query("UPDATE tables SET status=%s WHERE id=%s", (status, table_id))


# ─── SHIFTS ──────────────────────────────────────────────────────────────────

class ShiftModel:

    @staticmethod
    def get_active_waiter():
        """Найти первого официанта с открытой сменой сегодня"""
        today = date.today()
        result = execute_query("""
            SELECT DISTINCT u.id, u.full_name 
            FROM shifts s
            JOIN users u ON s.waiter_id = u.id
            WHERE s.shift_date = %s 
            AND s.status = 'open'
            AND u.is_active = TRUE
            LIMIT 1
        """, (today,), fetch_one=True)
        return result
    @staticmethod
    def create(waiter_id, shift_date, start_time, end_time):
        return execute_query("""
            INSERT INTO shifts (waiter_id, shift_date, start_time, end_time)
            VALUES (%s, %s, %s, %s)
        """, (waiter_id, shift_date, start_time, end_time))

    @staticmethod
    def assign_tables(shift_id, table_ids: list):
        execute_query("DELETE FROM shift_tables WHERE shift_id=%s", (shift_id,))
        for tid in table_ids:
            execute_query("INSERT IGNORE INTO shift_tables (shift_id, table_id) VALUES (%s,%s)", (shift_id, tid))

    @staticmethod
    def open_shift(shift_id, waiter_id):
        execute_query("""UPDATE shifts SET status='open', opened_at=NOW()
            WHERE id=%s AND waiter_id=%s AND status='scheduled'""", (shift_id, waiter_id))

    @staticmethod
    def close_shift(shift_id, waiter_id):
        execute_query("""UPDATE shifts SET status='closed', closed_at=NOW()
            WHERE id=%s AND waiter_id=%s AND status='open'""", (shift_id, waiter_id))

    @staticmethod
    def auto_close_expired():
        """Автоматически закрыть смены, которые закончились > 30 мин назад."""
        execute_query("""
            UPDATE shifts SET status='closed', closed_at=NOW()
            WHERE status='open'
              AND shift_date < CURDATE()
              AND TIMESTAMPDIFF(MINUTE, CONCAT(shift_date,' ',end_time), NOW()) > 30
        """)

    @staticmethod
    def get_for_waiter(waiter_id):
        return execute_query("""
            SELECT s.*, GROUP_CONCAT(t.number ORDER BY t.number) AS table_numbers
            FROM shifts s
            LEFT JOIN shift_tables st ON st.shift_id=s.id
            LEFT JOIN tables t ON st.table_id=t.id
            WHERE s.waiter_id=%s GROUP BY s.id ORDER BY s.shift_date DESC
        """, (waiter_id,), fetch=True)

    @staticmethod
    def get_all():
        """Получить все смены"""
        return execute_query("""
            SELECT s.*, u.full_name AS waiter_name,
                GROUP_CONCAT(DISTINCT t.number ORDER BY t.number) AS table_numbers
            FROM shifts s 
            JOIN users u ON s.waiter_id = u.id
            LEFT JOIN shift_tables st ON st.shift_id = s.id
            LEFT JOIN tables t ON st.table_id = t.id
            GROUP BY s.id 
            ORDER BY s.shift_date DESC
        """, fetch=True)

    @staticmethod
    def get_today_open(waiter_id):
        """Открытая смена сегодня (с учётом автозакрытия)."""
        ShiftModel.auto_close_expired()
        return execute_query("""
            SELECT s.*, GROUP_CONCAT(t.number ORDER BY t.number) AS table_numbers
            FROM shifts s
            LEFT JOIN shift_tables st ON st.shift_id=s.id
            LEFT JOIN tables t ON st.table_id=t.id
            WHERE s.waiter_id=%s AND s.shift_date=%s AND s.status='open'
            GROUP BY s.id LIMIT 1
        """, (waiter_id, date.today()), fetch_one=True)

    @staticmethod
    def get_today_scheduled(waiter_id):
        """Запланированные смены на сегодня."""
        return execute_query("""
            SELECT s.*, GROUP_CONCAT(t.number ORDER BY t.number) AS table_numbers
            FROM shifts s
            LEFT JOIN shift_tables st ON st.shift_id=s.id
            LEFT JOIN tables t ON st.table_id=t.id
            WHERE s.waiter_id=%s AND s.shift_date=%s AND s.status='scheduled'
            GROUP BY s.id
        """, (waiter_id, date.today()), fetch=True)
    
    @staticmethod
    def get_shifts_for_date(shift_date):
        """Получить все смены на указанную дату (статусы scheduled или open)."""
        return execute_query("""
            SELECT s.id, s.waiter_id, s.shift_date, s.start_time, s.end_time, s.status,
                   u.full_name AS waiter_name
            FROM shifts s
            JOIN users u ON s.waiter_id = u.id
            WHERE s.shift_date = %s AND s.status IN ('scheduled', 'open')
            ORDER BY s.waiter_id
        """, (shift_date,), fetch=True)

    # ─── Автоматическое распределение столов ──────────────────────────────

    @staticmethod
    def get_shifts_for_date(shift_date):
        """Получить все смены на указанную дату (статусы scheduled или open)."""
        return execute_query("""
            SELECT s.id, s.waiter_id, s.shift_date, s.start_time, s.end_time, s.status,
                   u.full_name AS waiter_name
            FROM shifts s
            JOIN users u ON s.waiter_id = u.id
            WHERE s.shift_date = %s AND s.status IN ('scheduled', 'open')
            ORDER BY s.waiter_id
        """, (shift_date,), fetch=True)

    @staticmethod
    def get_tables_for_shift(shift_id):
        """Получить ID столов, назначенных на конкретную смену."""
        return execute_query("""
            SELECT table_id FROM shift_tables WHERE shift_id = %s
        """, (shift_id,), fetch=True)

    @staticmethod
    def get_occupied_table_ids_for_date(shift_date, exclude_shift_id=None):
        """
        Получить ID столов, занятых любой сменой на указанную дату (кроме исключённой).
        """
        query = """
            SELECT DISTINCT st.table_id
            FROM shift_tables st
            JOIN shifts s ON st.shift_id = s.id
            WHERE s.shift_date = %s AND s.status IN ('scheduled', 'open')
        """
        params = [shift_date]
        if exclude_shift_id:
            query += " AND s.id != %s"
            params.append(exclude_shift_id)
        return [row['table_id'] for row in execute_query(query, tuple(params), fetch=True)]

    @staticmethod
    def get_free_tables(shift_date, start_time, end_time, exclude_shift_id=None):
        """
        Возвращает список свободных столов в указанный период.
        Учитывает только открытые и запланированные смены (не закрытые).
        """
        all_tables = execute_query("SELECT id, number, capacity, location FROM tables ORDER BY number", fetch=True)
        occupied = ShiftModel.get_occupied_table_ids_for_date(shift_date, exclude_shift_id)
        return [t for t in all_tables if t['id'] not in occupied]

    @staticmethod
    def check_table_conflict(table_ids, shift_date, start_time, end_time, exclude_shift_id=None):
        """
        Проверяет, есть ли конфликты для указанных столов в указанный период.
        Возвращает список конфликтующих смен.
        """
        if not table_ids:
            return []
        placeholders = ','.join(['%s'] * len(table_ids))
        query = f"""
            SELECT DISTINCT s.id, s.shift_date, s.start_time, s.end_time, u.full_name AS waiter_name,
                   GROUP_CONCAT(t.number ORDER BY t.number) AS tables
            FROM shifts s
            JOIN shift_tables st ON st.shift_id = s.id
            JOIN tables t ON st.table_id = t.id
            JOIN users u ON s.waiter_id = u.id
            WHERE s.shift_date = %s
              AND s.status IN ('scheduled', 'open')
              AND st.table_id IN ({placeholders})
              AND (
                  (s.start_time < %s AND s.end_time > %s) OR
                  (s.start_time < %s AND s.end_time > %s) OR
                  (s.start_time >= %s AND s.start_time < %s)
              )
        """
        params = [shift_date] + table_ids + [end_time, start_time, end_time, start_time, start_time, end_time]
        if exclude_shift_id:
            query += " AND s.id != %s"
            params.append(exclude_shift_id)
        query += " GROUP BY s.id"
        return execute_query(query, tuple(params), fetch=True)

    @staticmethod
    def distribute_free_tables_among_all_shifts(shift_date):
        """
        Распределить свободные столы (не занятые ни одной сменой) равномерно
        между всеми официантами, у которых есть смена на эту дату.
        Столы добавляются к существующим наборам столов (не удаляются).
        Возвращает строку с результатом.
        """
        import itertools

        shifts = ShiftModel.get_shifts_for_date(shift_date)
        if not shifts:
            return "Нет смен на эту дату."

        occupied_table_ids = ShiftModel.get_occupied_table_ids_for_date(shift_date)
        all_tables = execute_query("SELECT id, number, capacity, location FROM tables ORDER BY number", fetch=True)
        all_table_ids = [t['id'] for t in all_tables]
        free_table_ids = [tid for tid in all_table_ids if tid not in occupied_table_ids]
        if not free_table_ids:
            return "Нет свободных столов для распределения."

        shifts_by_waiter = {}
        for s in shifts:
            wid = s['waiter_id']
            if wid not in shifts_by_waiter:
                shifts_by_waiter[wid] = []
            shifts_by_waiter[wid].append(s)

        waiter_table_count = {}
        for wid, shifts_list in shifts_by_waiter.items():
            count = 0
            for sh in shifts_list:
                tables = ShiftModel.get_tables_for_shift(sh['id'])
                count += len(tables)
            waiter_table_count[wid] = count

        waiter_order = sorted(waiter_table_count.keys(), key=lambda wid: waiter_table_count[wid])
        waiter_cycle = itertools.cycle(waiter_order)

        shift_additions = {s['id']: [] for s in shifts}

        for table_id in free_table_ids:
            waiter_id = next(waiter_cycle)
            shifts_of_waiter = shifts_by_waiter.get(waiter_id, [])
            if not shifts_of_waiter:
                continue
            best_shift = None
            min_count = float('inf')
            for sh in shifts_of_waiter:
                current_tables = ShiftModel.get_tables_for_shift(sh['id'])
                current_count = len(current_tables) + len(shift_additions.get(sh['id'], []))
                if current_count < min_count:
                    min_count = current_count
                    best_shift = sh['id']
            if best_shift is not None:
                shift_additions[best_shift].append(table_id)

        total_added = 0
        for shift_id, table_ids in shift_additions.items():
            if table_ids:
                for tid in table_ids:
                    execute_query(
                        "INSERT IGNORE INTO shift_tables (shift_id, table_id) VALUES (%s, %s)",
                        (shift_id, tid)
                    )
                total_added += len(table_ids)

        return f"Распределено {total_added} свободных столов между {len(shifts)} сменами."

# ─── PHONE VALIDATION ────────────────────────────────────────────────────────

def validate_phone(phone: str) -> str:
    digits = re.sub(r'\D', '', phone)
    if digits.startswith('8'):
        digits = '7' + digits[1:]
    if not (10 <= len(digits) <= 12):
        raise ValueError(f"Некорректный номер телефона: «{phone}».\nДолжно быть 10–12 цифр.")
    return '+' + digits




# ─── RESERVATIONS ────────────────────────────────────────────────────────────

class ReservationModel:
    
    @staticmethod
    def _check_conflict(table_ids, res_date, res_time, end_time, exclude_reservation_id=None):
        """
        Проверить, нет ли конфликтов броней на выбранные столы.
        Возвращает список конфликтующих броней.
        """
        if not table_ids:
            return []
        
        # Если end_time не указан, устанавливаем через 2 часа
        if not end_time:
            from datetime import datetime as dt
            base_hour = dt.strptime(res_time, '%H:%M').hour
            base_min = dt.strptime(res_time, '%H:%M').minute
            end_hour = (base_hour + 2) % 24
            end_time = f"{end_hour:02d}:{base_min:02d}"
        
        placeholders = ','.join(['%s'] * len(table_ids))
        
        query = f"""
            SELECT r.id, r.client_name, r.reservation_time, r.end_time,
                GROUP_CONCAT(DISTINCT t.number ORDER BY t.number) AS tables
            FROM reservations r
            JOIN reservation_tables rt ON rt.reservation_id = r.id
            JOIN tables t ON rt.table_id = t.id
            WHERE r.reservation_date = %s
            AND r.status = 'active'
            AND rt.table_id IN ({placeholders})
            AND (
                -- Пересечение: начало новой брони внутри существующей
                (r.reservation_time <= %s AND (r.end_time IS NULL OR r.end_time > %s))
                OR
                -- Пересечение: конец новой брони внутри существующей
                (r.reservation_time < %s AND (r.end_time IS NULL OR r.end_time >= %s))
            )
        """
        
        params = [res_date] + table_ids + [res_time, res_time, res_time, res_time]
        
        if exclude_reservation_id:
            query += " AND r.id != %s"
            params.append(exclude_reservation_id)
        
        query += " GROUP BY r.id"
        
        return execute_query(query, tuple(params), fetch=True)
    
    @staticmethod
    def _get_tables_with_active_orders(table_ids, res_date):
        """
        Возвращает список ID столов, на которых есть активные заказы на указанную дату.
        Активные заказы – статусы не 'cancelled' и не 'paid'.
        """
        if not table_ids:
            return []
        placeholders = ','.join(['%s'] * len(table_ids))
        query = f"""
            SELECT DISTINCT table_id
            FROM orders
            WHERE table_id IN ({placeholders})
            AND DATE(created_at) = %s
            AND status NOT IN ('cancelled', 'paid')
        """
        params = table_ids + [res_date]
        rows = execute_query(query, tuple(params), fetch=True)
        return [row['table_id'] for row in rows]
    
    @staticmethod
    def create(client_name, client_phone, res_date, res_time, guests_count,
            table_ids: list, notes='', client_id=None, end_time=None):
        phone = validate_phone(client_phone)
        
        # Убираем дубликаты столов
        table_ids = list(set(table_ids))
        
        if not table_ids:
            raise ValueError("Выберите хотя бы один столик")
        
        # Проверяем вместимость
        if table_ids:
            ph = ','.join(['%s'] * len(table_ids))
            cap = execute_query(f"SELECT SUM(capacity) AS cap FROM tables WHERE id IN ({ph})",
                                tuple(table_ids), fetch_one=True)
            if cap and cap['cap'] and int(cap['cap']) < guests_count:
                raise ValueError(f"Недостаточно мест: доступно {cap['cap']}, запрошено {guests_count}")
        
        # Проверяем конфликты броней
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
        
        # Проверка активных заказов на выбранных столах
        active_order_tables = ReservationModel._get_tables_with_active_orders(table_ids, res_date)
        if active_order_tables:
            now = datetime.now()
            if res_date == now.date():
                res_datetime = datetime.combine(res_date, datetime.strptime(res_time, '%H:%M').time())
                delta = (res_datetime - now).total_seconds() / 60
                if delta < 60:
                    tables_str = ', '.join(str(t) for t in active_order_tables)
                    raise ValueError(f"Стол {tables_str} заняты активными заказами, до начала брони менее часа. Бронирование невозможно.")
            # Если дата не сегодня или delta >= 60, пропускаем (разрешаем)
        
        rid = execute_query("""
            INSERT INTO reservations
            (client_id, client_name, client_phone, reservation_date,
            reservation_time, end_time, guests_count, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (client_id, client_name, phone, res_date, res_time, end_time, guests_count, notes))
        
        for tid in table_ids:
            execute_query(
                "INSERT INTO reservation_tables (reservation_id, table_id) VALUES (%s,%s)",
                (rid, tid)
            )
        
        return rid

    @staticmethod
    def cancel(reservation_id: int):
        execute_query("UPDATE reservations SET status='cancelled' WHERE id=%s", (reservation_id,))

    @staticmethod
    def update(reservation_id, client_name, res_date, res_time, end_time, guests_count,
            table_ids, notes, client_phone=None):
        # Убираем дубликаты столов
        table_ids = list(set(table_ids))

        # === ПРОВЕРКА КОНФЛИКТОВ С ДРУГИМИ БРОНЯМИ (исключаем текущую) ===
        conflicts = ReservationModel._check_conflict(
            table_ids, res_date, res_time, end_time,
            exclude_reservation_id=reservation_id
        )
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

        # === ПРОВЕРКА АКТИВНЫХ ЗАКАЗОВ (новая) ===
        active_order_tables = ReservationModel._get_tables_with_active_orders(table_ids, res_date)
        if active_order_tables:
            now = datetime.now()
            if res_date == now.date():
                res_datetime = datetime.combine(res_date, datetime.strptime(res_time, '%H:%M').time())
                delta = (res_datetime - now).total_seconds() / 60
                if delta < 60:
                    tables_str = ', '.join(str(t) for t in active_order_tables)
                    raise ValueError(f"Стол {tables_str} заняты активными заказами, до начала брони менее часа. Бронирование невозможно.")

        # Обновление данных брони
        if client_phone:
            client_phone = validate_phone(client_phone)
            execute_query("""UPDATE reservations SET 
                client_name=%s,
                reservation_date=%s, 
                reservation_time=%s,
                end_time=%s, 
                guests_count=%s, 
                notes=%s, 
                client_phone=%s 
                WHERE id=%s""",
                (client_name, res_date, res_time, end_time, guests_count, notes, client_phone, reservation_id))
        else:
            execute_query("""UPDATE reservations SET 
                client_name=%s,
                reservation_date=%s, 
                reservation_time=%s,
                end_time=%s, 
                guests_count=%s, 
                notes=%s 
                WHERE id=%s""",
                (client_name, res_date, res_time, end_time, guests_count, notes, reservation_id))

        # Обновление связей со столами
        execute_query("DELETE FROM reservation_tables WHERE reservation_id=%s", (reservation_id,))
        for tid in table_ids:
            execute_query(
                "INSERT INTO reservation_tables (reservation_id, table_id) VALUES (%s,%s)",
                (reservation_id, tid)
            )

    @staticmethod
    def get_all(status=None):
        """Получить все брони"""
        where = "WHERE r.status = %s" if status else ""
        params = (status,) if status else ()
        return execute_query(f"""
            SELECT 
                r.*,
                GROUP_CONCAT(DISTINCT t.number ORDER BY t.number SEPARATOR ', ') AS table_numbers,
                GROUP_CONCAT(DISTINCT t.id ORDER BY t.number SEPARATOR ',') AS table_ids
            FROM reservations r
            LEFT JOIN reservation_tables rt ON rt.reservation_id = r.id
            LEFT JOIN tables t ON rt.table_id = t.id
            {where}
            GROUP BY r.id
            ORDER BY r.reservation_date DESC, r.reservation_time
        """, params if params else None, fetch=True)

    @staticmethod
    def get_by_date(res_date: date):
        """Получить брони на дату"""
        return execute_query("""
            SELECT 
                r.*,
                GROUP_CONCAT(DISTINCT t.number ORDER BY t.number SEPARATOR ', ') AS table_numbers,
                GROUP_CONCAT(DISTINCT t.id ORDER BY t.number SEPARATOR ',') AS table_ids
            FROM reservations r
            LEFT JOIN reservation_tables rt ON rt.reservation_id = r.id
            LEFT JOIN tables t ON rt.table_id = t.id
            WHERE r.reservation_date = %s AND r.status = 'active'
            GROUP BY r.id
            ORDER BY r.reservation_time
        """, (res_date,), fetch=True)

    @staticmethod
    def get_by_client(client_id):
        """Получить брони клиента"""
        return execute_query("""
            SELECT 
                r.*,
                GROUP_CONCAT(DISTINCT t.number ORDER BY t.number SEPARATOR ', ') AS table_numbers,
                GROUP_CONCAT(DISTINCT t.id ORDER BY t.number SEPARATOR ',') AS table_ids
            FROM reservations r
            LEFT JOIN reservation_tables rt ON rt.reservation_id = r.id
            LEFT JOIN tables t ON rt.table_id = t.id
            WHERE r.client_id = %s
            GROUP BY r.id
            ORDER BY r.reservation_date DESC
        """, (client_id,), fetch=True)


# ─── DISHES ──────────────────────────────────────────────────────────────────

class DishModel:
    @staticmethod
    def get_all(available_only=False, category_id=None, include_stopped=False):
        """Получить все блюда с полем discount из акций."""
        conditions = []
        params = []
        if available_only:
            conditions.append("d.is_available=TRUE")
            conditions.append("d.stock_quantity > 0")
            if not include_stopped:
                conditions.append("(d.is_stopped=FALSE OR d.is_stopped IS NULL)")
        if category_id:
            conditions.append("d.category_id=%s")
            params.append(category_id)
        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        return execute_query(f"""
            SELECT d.*, c.name AS category_name,
                   COALESCE((
                     SELECT p.discount_percent FROM promotions p
                     WHERE p.is_active=TRUE AND p.end_date>=CURDATE()
                       AND (p.dish_id=d.id OR p.category_id=d.category_id)
                     LIMIT 1
                   ), 0) AS discount
            FROM dishes d
            LEFT JOIN dish_categories c ON d.category_id=c.id
            {where}
            ORDER BY c.name, d.name
        """, params if params else None, fetch=True)

    @staticmethod
    def get_categories():
        return execute_query("SELECT * FROM dish_categories ORDER BY name", fetch=True)

    @staticmethod
    def check_stock(dish_id: int, quantity: int):
        row = execute_query("SELECT stock_quantity, name, is_stopped FROM dishes WHERE id=%s",
                            (dish_id,), fetch_one=True)
        if not row:
            raise ValueError("Блюдо не найдено")
        if row.get('is_stopped'):
            raise ValueError(f"Блюдо «{row['name']}» в стоп-листе.")
        if row['stock_quantity'] < quantity:
            raise ValueError(
                f"Блюдо «{row['name']}» доступно только {row['stock_quantity']} порц. "
                f"Запрошено: {quantity}.")
        return row

    @staticmethod
    def decrease_stock(dish_id: int, quantity: int):
        execute_query("UPDATE dishes SET stock_quantity=stock_quantity-%s WHERE id=%s", (quantity, dish_id))

    @staticmethod
    def increase_stock(dish_id: int, quantity: int):
        execute_query("UPDATE dishes SET stock_quantity=stock_quantity+%s WHERE id=%s", (quantity, dish_id))

    @staticmethod
    def update_stock(dish_id: int, quantity: int):
        execute_query("UPDATE dishes SET stock_quantity=%s WHERE id=%s", (quantity, dish_id))

    @staticmethod
    def toggle_stop(dish_id: int):
        execute_query("UPDATE dishes SET is_stopped=NOT is_stopped WHERE id=%s", (dish_id,))

    @staticmethod
    def create(name, category_id, description, price, stock_quantity=0):
        return execute_query("""INSERT INTO dishes (name,category_id,description,price,stock_quantity)
            VALUES (%s,%s,%s,%s,%s)""", (name, category_id, description, price, stock_quantity))

    @staticmethod
    def update(dish_id, name, category_id, description, price, stock_quantity, is_available=True):
        execute_query("""UPDATE dishes SET name=%s,category_id=%s,description=%s,
            price=%s,stock_quantity=%s,is_available=%s WHERE id=%s""",
            (name, category_id, description, price, stock_quantity, is_available, dish_id))


# ─── ORDERS ──────────────────────────────────────────────────────────────────

class OrderModel:

    @staticmethod
    def get_reservation_info(table_id):
        today = date.today()
        now_str = datetime.now().strftime('%H:%M:%S')
        query = """
            SELECT r.id, r.client_name, r.reservation_time, r.end_time, 
                r.guests_count, GROUP_CONCAT(t.number) AS tables
            FROM reservations r
            JOIN reservation_tables rt ON rt.reservation_id = r.id
            JOIN tables t ON rt.table_id = t.id
            WHERE rt.table_id = %s 
            AND r.reservation_date = %s
            AND r.status = 'active'
            AND (
                r.reservation_time <= %s
                AND (r.end_time IS NULL OR r.end_time >= %s)
                OR
                r.reservation_time > %s
                AND r.reservation_time <= ADDTIME(%s, '01:00:00')
            )
            GROUP BY r.id
            LIMIT 1
        """
        params = (table_id, today, now_str, now_str, now_str, now_str)
        return execute_query(query, params, fetch_one=True)
    
    @staticmethod
    def get_minutes_until_next_reservation(table_id):
        today = date.today()
        now = datetime.now()
        reservation = execute_query("""
            SELECT r.reservation_time
            FROM reservations r
            JOIN reservation_tables rt ON rt.reservation_id = r.id
            WHERE rt.table_id = %s AND r.reservation_date = %s AND r.status = 'active'
            AND r.reservation_time > TIME(%s)
            ORDER BY r.reservation_time LIMIT 1
        """, (table_id, today, now.strftime('%H:%M:%S')), fetch_one=True)
        if not reservation:
            return None
        res_time = reservation['reservation_time']
        # Приводим к времени
        if isinstance(res_time, str):
            res_time = datetime.strptime(res_time, '%H:%M:%S').time()
        elif isinstance(res_time, timedelta):
            res_time = (datetime.min + res_time).time()
        res_datetime = datetime.combine(today, res_time)
        delta = (res_datetime - now).total_seconds() / 60
        return delta

    @staticmethod
    def create(table_id, waiter_id=None, reservation_id=None, client_id=None):
        """Создать заказ с проверкой на бронь и дублирование"""
        existing = execute_query("""SELECT id FROM orders 
            WHERE table_id=%s AND status IN ('composing','placed','accepted','cooking','ready','delivered')
            LIMIT 1""", (table_id,), fetch_one=True)
        
        if existing:
            raise ValueError(f"На этом столе уже есть активный заказ №{existing['id']}")
        
        # Проверка, не начнётся ли бронь через < 30 минут
        delta = OrderModel.get_minutes_until_next_reservation(table_id)
        if delta is not None and delta < 30:
            raise ValueError("На этом столе через менее 30 минут начинается бронь. Заказ невозможен.")
        
        # Если waiter_id не передан (клиент), ищем активного официанта
        if waiter_id is None:
            active_waiter = ShiftModel.get_active_waiter()
            if not active_waiter:
                raise ValueError("Нет активных официантов на смене. Заказ не может быть создан.")
            waiter_id = active_waiter['id']
        
        reservation = OrderModel.get_reservation_info(table_id)
        if reservation:
            start_time = str(reservation['reservation_time'])[:5]
            end_time = str(reservation['end_time'])[:5] if reservation.get('end_time') else '—'
            msg = (f"⚠️ ВНИМАНИЕ: Стол забронирован!\n\n"
                f"Клиент: {reservation['client_name']}\n"
                f"Время: {start_time} - {end_time}\n"
                f"Гостей: {reservation['guests_count']}\n"
                f"Бронь №{reservation['id']}\n\n"
                f"Продолжить создание заказа на забронированный стол?")
            
            return {
                'action': 'confirm',
                'message': msg,
                'reservation': reservation
            }
        
        oid = execute_query("""INSERT INTO orders (table_id, waiter_id, reservation_id, status, client_id)
            VALUES (%s, %s, %s, 'composing', %s)""", (table_id, waiter_id, reservation_id, client_id))
        TableModel.update_status(table_id, 'occupied')
        return {'action': 'created', 'order_id': oid}

    @staticmethod
    def create_forced(table_id, waiter_id=None, reservation_id=None, client_id=None):
        """Принудительное создание заказа (после подтверждения брони)"""
        if waiter_id is None:
            active_waiter = ShiftModel.get_active_waiter()
            if not active_waiter:
                raise ValueError("Нет активных официантов на смене. Заказ не может быть создан.")
            waiter_id = active_waiter['id']
        
        oid = execute_query("""INSERT INTO orders (table_id, waiter_id, reservation_id, status, client_id)
            VALUES (%s, %s, %s, 'composing', %s)""", (table_id, waiter_id, reservation_id, client_id))
        TableModel.update_status(table_id, 'occupied')
        return oid

    @staticmethod
    def add_item(order_id, dish_id, quantity):
        order = execute_query("SELECT status FROM orders WHERE id=%s", (order_id,), fetch_one=True)
        if not order:
            raise ValueError("Заказ не найден")
        # Разрешаем редактирование для всех статусов, кроме оплачен и отменён
        if order['status'] in ('paid', 'cancelled'):
            raise ValueError(f"Нельзя редактировать заказ в статусе «{STATUS_LABELS.get(order['status'], order['status'])}»")
        
        dish = DishModel.check_stock(dish_id, quantity)
        dish_full = execute_query("""
            SELECT d.price, d.name,
                COALESCE((SELECT p.discount_percent FROM promotions p
                    WHERE p.is_active=TRUE AND p.end_date>=CURDATE()
                    AND (p.dish_id=d.id OR p.category_id=d.category_id) LIMIT 1),0) AS discount
            FROM dishes d WHERE d.id=%s
        """, (dish_id,), fetch_one=True)
        unit_price = float(dish_full['price'])
        discount = float(dish_full['discount'])
        execute_query("""INSERT INTO order_items (order_id,dish_id,quantity,unit_price,discount_percent)
            VALUES (%s,%s,%s,%s,%s)""", (order_id, dish_id, quantity, unit_price, discount))
        DishModel.decrease_stock(dish_id, quantity)
        return f"Блюдо «{dish['name']}» × {quantity} порц. добавлено в Заказ №{order_id}"

    @staticmethod
    def remove_item(order_item_id):
        item = execute_query("""SELECT oi.*, o.status AS order_status, d.name
            FROM order_items oi
            JOIN orders o ON oi.order_id = o.id
            JOIN dishes d ON oi.dish_id = d.id
            WHERE oi.id=%s""", (order_item_id,), fetch_one=True)
        if not item:
            raise ValueError("Позиция не найдена")
        # Разрешаем удаление для всех статусов, кроме оплачен и отменён
        if item['order_status'] in ('paid', 'cancelled'):
            raise ValueError(f"Нельзя редактировать заказ в статусе «{STATUS_LABELS.get(item['order_status'], item['order_status'])}»")
        
        DishModel.increase_stock(item['dish_id'], item['quantity'])
        execute_query("DELETE FROM order_items WHERE id=%s", (order_item_id,))
        return f"Блюдо «{item['name']}» × {item['quantity']} порц. удалено из Заказа №{item['order_id']}"

    @staticmethod
    def place_order(order_id):
        order = execute_query("SELECT * FROM orders WHERE id=%s", (order_id,), fetch_one=True)
        if not order or order['status'] != 'composing':
            raise ValueError("Невозможно оформить заказ")
        cnt = execute_query("SELECT COUNT(*) AS cnt FROM order_items WHERE order_id=%s",
                            (order_id,), fetch_one=True)
        if not cnt or cnt['cnt'] == 0:
            raise ValueError("Заказ пуст — добавьте блюда")
        execute_query("UPDATE orders SET status='placed', placed_at=NOW() WHERE id=%s", (order_id,))

    @staticmethod
    def cancel_order(order_id):
        order = execute_query("SELECT status,table_id FROM orders WHERE id=%s", (order_id,), fetch_one=True)
        if not order: raise ValueError("Заказ не найден")
        if order['status'] not in ('composing', 'placed'):
            raise ValueError("Заказ нельзя отменить (уже принят кухней)")
        items = execute_query("SELECT dish_id,quantity FROM order_items WHERE order_id=%s",
                              (order_id,), fetch=True)
        for item in items:
            DishModel.increase_stock(item['dish_id'], item['quantity'])
        execute_query("UPDATE orders SET status='cancelled' WHERE id=%s", (order_id,))
        active = execute_query("""SELECT COUNT(*) AS cnt FROM orders
            WHERE table_id=%s AND status IN ('composing','placed','accepted','ready','delivered')""",
            (order['table_id'],), fetch_one=True)
        if active and active['cnt'] == 0:
            TableModel.update_status(order['table_id'], 'free')

    @staticmethod
    def update_status(order_id, new_status):
        valid = ('composing','placed','cancelled','accepted','cooking','ready','delivered','paid')
        if new_status not in valid: 
            raise ValueError("Недопустимый статус")
        
        order = execute_query("SELECT status, table_id FROM orders WHERE id=%s", (order_id,), fetch_one=True)
        if not order:
            raise ValueError("Заказ не найден")
        
        current = order['status']
        
        # Определяем допустимые переходы
        allowed_transitions = {
            'composing': ['placed', 'cancelled'],
            'placed': ['accepted', 'cancelled'],
            'accepted': ['cooking', 'cancelled'],
            'cooking': ['ready'],
            'ready': ['delivered'],
            'delivered': ['paid'],  # ← РАЗРЕШАЕМ ПЕРЕХОД К ОПЛАТЕ
            'paid': [],
            'cancelled': []
        }
        
        if new_status not in allowed_transitions.get(current, []):
            raise ValueError(f"Недопустимый переход из статуса «{STATUS_LABELS.get(current, current)}» "
                            f"в статус «{STATUS_LABELS.get(new_status, new_status)}»")
        
        extra = ", paid_at=NOW()" if new_status == 'paid' else ""
        execute_query(f"UPDATE orders SET status=%s{extra} WHERE id=%s", (new_status, order_id))
        
        if new_status == 'paid':
            if order:
                active = execute_query("""SELECT COUNT(*) AS cnt FROM orders
                    WHERE table_id=%s AND status IN ('composing','placed','accepted','ready','delivered')""",
                    (order['table_id'],), fetch_one=True)
                if active and active['cnt'] == 0:
                    TableModel.update_status(order['table_id'], 'free')

    @staticmethod
    def get_order_detail(order_id):
        order = execute_query("""
            SELECT o.*, t.number AS table_number, u.full_name AS waiter_name
            FROM orders o JOIN tables t ON o.table_id=t.id JOIN users u ON o.waiter_id=u.id
            WHERE o.id=%s
        """, (order_id,), fetch_one=True)
        if order:
            order['items'] = execute_query("""
                SELECT oi.*, d.name AS dish_name,
                       ROUND(oi.unit_price*(1-oi.discount_percent/100),2) AS final_price
                FROM order_items oi JOIN dishes d ON oi.dish_id=d.id WHERE oi.order_id=%s
            """, (order_id,), fetch=True)
        return order

    @staticmethod
    def get_by_table(table_id, active_only=True):
        where = "AND o.status NOT IN ('cancelled','paid')" if active_only else ""
        return execute_query(f"""SELECT o.*, u.full_name AS waiter_name
            FROM orders o JOIN users u ON o.waiter_id=u.id
            WHERE o.table_id=%s {where} ORDER BY o.created_at DESC""", (table_id,), fetch=True)

    @staticmethod
    def get_all(status=None):
        where = "WHERE o.status=%s" if status else ""
        params = (status,) if status else ()
        return execute_query(f"""SELECT o.*, t.number AS table_number, u.full_name AS waiter_name
            FROM orders o JOIN tables t ON o.table_id=t.id JOIN users u ON o.waiter_id=u.id
            {where} ORDER BY o.created_at DESC""", params, fetch=True)

    @staticmethod
    def get_by_reservation(reservation_id):
        return execute_query("""SELECT o.*, t.number AS table_number, u.full_name AS waiter_name
            FROM orders o JOIN tables t ON o.table_id=t.id JOIN users u ON o.waiter_id=u.id
            WHERE o.reservation_id=%s ORDER BY o.created_at DESC""", (reservation_id,), fetch=True)


# ─── BILLS & RECEIPTS ────────────────────────────────────────────────────────

class BillModel:
    @staticmethod
    def check_all_delivered(table_id):
        not_ready = execute_query("""SELECT COUNT(*) AS cnt FROM orders
            WHERE table_id=%s AND status IN ('composing','placed','accepted','ready')""",
            (table_id,), fetch_one=True)
        return not_ready and not_ready['cnt'] == 0

    @staticmethod
    def create_bill(table_id, waiter_id, reservation_id=None):
        if not BillModel.check_all_delivered(table_id):
            raise ValueError("Нельзя оформить счёт: не все заказы выданы кухней (статус «Выдан»).")
        orders = execute_query("SELECT id FROM orders WHERE table_id=%s AND status='delivered'",
                               (table_id,), fetch=True)
        if not orders:
            raise ValueError("Нет заказов в статусе «Выдан» для этого стола.")
        total = 0
        for o in orders:
            s = execute_query("""SELECT COALESCE(SUM(oi.quantity*oi.unit_price*(1-oi.discount_percent/100)),0) AS s
                FROM order_items oi WHERE oi.order_id=%s""", (o['id'],), fetch_one=True)
            if s: total += float(s['s'])
        bill_id = execute_query("""INSERT INTO bills (reservation_id,table_id,waiter_id,total_amount)
            VALUES (%s,%s,%s,%s)""", (reservation_id, table_id, waiter_id, round(total, 2)))
        return bill_id, round(total, 2)

    @staticmethod
    def pay_bill(bill_id, payment_method='card'):
        execute_query("UPDATE bills SET status='paid', paid_at=NOW() WHERE id=%s", (bill_id,))
        bill = execute_query("SELECT * FROM bills WHERE id=%s", (bill_id,), fetch_one=True)
        receipt_num = f"OLT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{bill_id}"
        execute_query("""INSERT INTO receipts (bill_id,receipt_number,total_amount,payment_method)
            VALUES (%s,%s,%s,%s)""", (bill_id, receipt_num, bill['total_amount'], payment_method))
        execute_query("""UPDATE orders SET status='paid', paid_at=NOW()
            WHERE table_id=%s AND status='delivered'""", (bill['table_id'],))
        TableModel.update_status(bill['table_id'], 'free')
        return receipt_num

    @staticmethod
    def get_receipt(bill_id):
        return execute_query("""SELECT r.*, b.table_id, b.paid_at, t.number AS table_number,
            u.full_name AS waiter_name
            FROM receipts r JOIN bills b ON r.bill_id=b.id
            JOIN tables t ON b.table_id=t.id JOIN users u ON b.waiter_id=u.id
            WHERE r.bill_id=%s""", (bill_id,), fetch_one=True)

    @staticmethod
    def get_all_receipts():
        return execute_query("""SELECT r.*, t.number AS table_number, u.full_name AS waiter_name,
            b.paid_at AS bill_paid_at
            FROM receipts r JOIN bills b ON r.bill_id=b.id
            JOIN tables t ON b.table_id=t.id JOIN users u ON b.waiter_id=u.id
            ORDER BY r.issued_at DESC""", fetch=True)


# ─── PROMOTIONS ──────────────────────────────────────────────────────────────

class PromotionModel:
    @staticmethod
    def create(name, discount_percent, start_date, end_date, dish_id=None, category_id=None):
        return execute_query("""INSERT INTO promotions
            (name,discount_percent,start_date,end_date,dish_id,category_id)
            VALUES (%s,%s,%s,%s,%s,%s)""",
            (name, discount_percent, start_date, end_date, dish_id, category_id))

    @staticmethod
    def get_active():
        return execute_query("""SELECT p.*, d.name AS dish_name, c.name AS category_name
            FROM promotions p LEFT JOIN dishes d ON p.dish_id=d.id
            LEFT JOIN dish_categories c ON p.category_id=c.id
            WHERE p.is_active=TRUE AND p.end_date>=CURDATE() ORDER BY p.end_date""", fetch=True)

    @staticmethod
    def deactivate(promo_id):
        execute_query("UPDATE promotions SET is_active=FALSE WHERE id=%s", (promo_id,))


# ─── STATISTICS ──────────────────────────────────────────────────────────────

class StatisticsModel:

    @staticmethod
    def table_availability_list(check_date: date):
        """
        Получить список свободных и занятых столов на дату.
        Возвращает: список словарей с полями:
        - table_number: номер стола
        - status: 'Свободен' или 'Забронирован'
        - reservation_id: ID брони (если есть)
        - client_name: имя клиента (если есть)
        - time_start: время начала брони
        - time_end: время окончания брони
        """
        # Получаем все столы
        tables = execute_query("SELECT id, number, capacity, location FROM tables ORDER BY number", fetch=True)
        
        # Получаем все активные брони на выбранную дату
        reservations = execute_query("""
            SELECT 
                r.id AS reservation_id,
                r.client_name,
                r.reservation_time,
                r.end_time,
                r.guests_count,
                rt.table_id
            FROM reservations r
            JOIN reservation_tables rt ON rt.reservation_id = r.id
            WHERE r.reservation_date = %s 
            AND r.status = 'active'
            ORDER BY r.reservation_time, rt.table_id
        """, (check_date,), fetch=True)
        
        # Группируем брони по столам
        reservations_by_table = {}
        for res in reservations:
            table_id = res['table_id']
            if table_id not in reservations_by_table:
                reservations_by_table[table_id] = []
            reservations_by_table[table_id].append(res)
        
        # Формируем результат
        result = []
        for t in tables:
            table_id = t['id']
            if table_id in reservations_by_table and reservations_by_table[table_id]:
                # Стол занят (забронирован)
                for res in reservations_by_table[table_id]:
                    result.append({
                        'table_number': t['number'],
                        'status': 'Забронирован',
                        'reservation_id': res['reservation_id'],
                        'client_name': res['client_name'],
                        'time_start': str(res['reservation_time'])[:5],
                        'time_end': str(res['end_time'])[:5] if res.get('end_time') else '—',
                        'guests_count': res['guests_count']
                    })
            else:
                # Стол свободен
                result.append({
                    'table_number': t['number'],
                    'status': 'Свободен',
                    'reservation_id': None,
                    'client_name': None,
                    'time_start': '—',
                    'time_end': '—',
                    'guests_count': None
                })
        
        return result
    @staticmethod
    def dish_sales_two_months(year1, month1, year2, month2):
        return execute_query("""
            SELECT c.name AS category, d.name AS dish_name,
                   SUM(CASE WHEN YEAR(o.placed_at)=%s AND MONTH(o.placed_at)=%s THEN oi.quantity ELSE 0 END) AS qty1,
                   SUM(CASE WHEN YEAR(o.placed_at)=%s AND MONTH(o.placed_at)=%s THEN oi.quantity ELSE 0 END) AS qty2
            FROM order_items oi JOIN orders o ON oi.order_id=o.id
            JOIN dishes d ON oi.dish_id=d.id JOIN dish_categories c ON d.category_id=c.id
            WHERE o.status NOT IN ('cancelled','composing')
            GROUP BY c.name, d.name ORDER BY c.name, d.name
        """, (year1,month1,year2,month2), fetch=True)

    @staticmethod
    def table_reservations(year, month):
        return execute_query("""
            SELECT t.number, COUNT(r.id) AS reservation_count
            FROM tables t LEFT JOIN reservation_tables rt ON rt.table_id=t.id
            LEFT JOIN reservations r ON rt.reservation_id=r.id
              AND YEAR(r.reservation_date)=%s AND MONTH(r.reservation_date)=%s AND r.status='active'
            GROUP BY t.id, t.number ORDER BY t.number
        """, (year, month), fetch=True)

    @staticmethod
    def waiter_stats_two_months(year1, month1, year2, month2):
        return execute_query("""
            SELECT u.full_name,
                   SUM(CASE WHEN YEAR(o.placed_at)=%s AND MONTH(o.placed_at)=%s THEN 1 ELSE 0 END) AS orders1,
                   SUM(CASE WHEN YEAR(o.placed_at)=%s AND MONTH(o.placed_at)=%s THEN 1 ELSE 0 END) AS orders2,
                   SUM(CASE WHEN YEAR(b.paid_at)=%s AND MONTH(b.paid_at)=%s THEN 1 ELSE 0 END) AS paid_bills1,
                   SUM(CASE WHEN YEAR(b.paid_at)=%s AND MONTH(b.paid_at)=%s THEN 1 ELSE 0 END) AS paid_bills2,
                   SUM(CASE WHEN YEAR(b.paid_at)=%s AND MONTH(b.paid_at)=%s THEN b.total_amount ELSE 0 END) AS revenue1,
                   SUM(CASE WHEN YEAR(b.paid_at)=%s AND MONTH(b.paid_at)=%s THEN b.total_amount ELSE 0 END) AS revenue2
            FROM users u JOIN roles r ON u.role_id=r.id AND r.name='waiter'
            LEFT JOIN orders o ON o.waiter_id=u.id
            LEFT JOIN bills b ON b.waiter_id=u.id AND b.status='paid'
            GROUP BY u.id, u.full_name ORDER BY u.full_name
        """, (year1,month1,year2,month2, year1,month1,year2,month2, year1,month1,year2,month2), fetch=True)

    @staticmethod
    def hourly_table_occupancy(check_date: date):
        hours = list(range(9, 24))
        tables = execute_query("SELECT id, number FROM tables ORDER BY number", fetch=True)
        reservations = execute_query("""
            SELECT rt.table_id, r.reservation_time, r.end_time
            FROM reservations r JOIN reservation_tables rt ON rt.reservation_id=r.id
            WHERE r.reservation_date=%s AND r.status='active'
        """, (check_date,), fetch=True)
        orders = execute_query("""
            SELECT table_id, created_at, paid_at, status
            FROM orders WHERE DATE(created_at)=%s AND status!='cancelled'
        """, (check_date,), fetch=True)
        result = {}
        for t in tables:
            result[t['number']] = {}
            for h in hours:
                cell = ''
                for res in reservations:
                    if res['table_id'] != t['id']: continue
                    rt = res['reservation_time']
                    re_end = res['end_time']
                    sh = int(rt.total_seconds()//3600) if hasattr(rt,'total_seconds') else rt.hour
                    eh = int(re_end.total_seconds()//3600) if re_end and hasattr(re_end,'total_seconds') \
                         else (re_end.hour if re_end else sh+2)
                    if sh <= h < eh:
                        cell = 'Бронь'; break
                if not cell:
                    for o in orders:
                        if o['table_id'] != t['id']: continue
                        ca = o['created_at']
                        pa = o['paid_at']
                        start_h = ca.hour if ca else 0
                        end_h = pa.hour if pa else 23
                        if start_h <= h <= end_h:
                            cell = 'Заказ'; break
                result[t['number']][h] = cell
        return result, hours, [t['number'] for t in tables]
