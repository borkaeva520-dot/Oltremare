"""
Oltremare Restaurant Management System
Database connection and initialization module
"""

import mysql.connector
from mysql.connector import Error
import hashlib

DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'database': 'oltremare_db',
    'user': 'root',
    'password': 'root1234',
    'charset': 'utf8mb4',
    'use_unicode': True,
    'autocommit': False
}


def get_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        raise ConnectionError(f"Ошибка подключения к БД: {e}")


def execute_query(query: str, params=None, fetch=False, fetch_one=False):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query, params or ())
        
        # Определяем тип запроса
        query_type = query.strip().upper().split()[0] if query.strip() else ''
        
        if fetch:
            result = cursor.fetchall()
            return result
        if fetch_one:
            result = cursor.fetchone()
            return result
        
        # Если это SELECT и не указаны fetch параметры - все равно возвращаем данные
        if query_type == 'SELECT':
            result = cursor.fetchall()
            return result
        
        # Для INSERT/UPDATE/DELETE - делаем commit
        conn.commit()
        return cursor.lastrowid
    except Error as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def init_database():
    config = DB_CONFIG.copy()
    db_name = config.pop('database')
    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        cursor.execute(f"USE `{db_name}`")
        conn.commit()
    except Error as e:
        raise ConnectionError(f"Не удалось создать БД: {e}")

    tables_sql = [
        """CREATE TABLE IF NOT EXISTS roles (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(50) NOT NULL UNIQUE,
            description VARCHAR(200)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",

        """CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(100) NOT NULL UNIQUE,
            password_hash VARCHAR(64) NOT NULL,
            full_name VARCHAR(200) NOT NULL,
            phone VARCHAR(20),
            email VARCHAR(150),
            role_id INT NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (role_id) REFERENCES roles(id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",

        """CREATE TABLE IF NOT EXISTS tables (
            id INT AUTO_INCREMENT PRIMARY KEY,
            number INT NOT NULL UNIQUE,
            capacity INT NOT NULL DEFAULT 4,
            location VARCHAR(100),
            status ENUM('free','occupied','reserved','unavailable') DEFAULT 'free'
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",

        """CREATE TABLE IF NOT EXISTS shifts (
            id INT AUTO_INCREMENT PRIMARY KEY,
            waiter_id INT NOT NULL,
            shift_date DATE NOT NULL,
            start_time TIME NOT NULL,
            end_time TIME NOT NULL,
            status ENUM('scheduled','open','closed') DEFAULT 'scheduled',
            opened_at DATETIME,
            closed_at DATETIME,
            FOREIGN KEY (waiter_id) REFERENCES users(id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",

        """CREATE TABLE IF NOT EXISTS shift_tables (
            id INT AUTO_INCREMENT PRIMARY KEY,
            shift_id INT NOT NULL,
            table_id INT NOT NULL,
            FOREIGN KEY (shift_id) REFERENCES shifts(id),
            FOREIGN KEY (table_id) REFERENCES tables(id),
            UNIQUE KEY uq_shift_table (shift_id, table_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",

        """CREATE TABLE IF NOT EXISTS reservations (
            id INT AUTO_INCREMENT PRIMARY KEY,
            client_id INT,
            client_name VARCHAR(200) NOT NULL,
            client_phone VARCHAR(20) NOT NULL,
            reservation_date DATE NOT NULL,
            reservation_time TIME NOT NULL,
            end_time TIME,
            guests_count INT NOT NULL DEFAULT 1,
            status ENUM('active','cancelled','completed') DEFAULT 'active',
            notes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES users(id) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",

        """CREATE TABLE IF NOT EXISTS reservation_tables (
            id INT AUTO_INCREMENT PRIMARY KEY,
            reservation_id INT NOT NULL,
            table_id INT NOT NULL,
            FOREIGN KEY (reservation_id) REFERENCES reservations(id) ON DELETE CASCADE,
            FOREIGN KEY (table_id) REFERENCES tables(id),
            UNIQUE KEY uq_res_table (reservation_id, table_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",

        """CREATE TABLE IF NOT EXISTS dish_categories (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL UNIQUE,
            description TEXT
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",

        """CREATE TABLE IF NOT EXISTS dishes (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(200) NOT NULL,
            category_id INT NOT NULL,
            description TEXT,
            price DECIMAL(10,2) NOT NULL,
            stock_quantity INT NOT NULL DEFAULT 0,
            is_available BOOLEAN DEFAULT TRUE,
            is_stopped BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (category_id) REFERENCES dish_categories(id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",

        """CREATE TABLE IF NOT EXISTS promotions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(200) NOT NULL,
            discount_percent DECIMAL(5,2) NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            dish_id INT,
            category_id INT,
            is_active BOOLEAN DEFAULT TRUE,
            FOREIGN KEY (dish_id) REFERENCES dishes(id) ON DELETE CASCADE,
            FOREIGN KEY (category_id) REFERENCES dish_categories(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",

        """CREATE TABLE IF NOT EXISTS orders (
            id INT AUTO_INCREMENT PRIMARY KEY,
            reservation_id INT,
            table_id INT NOT NULL,
            waiter_id INT NOT NULL,
            status ENUM('composing','placed','cancelled','accepted','ready','delivered','paid') DEFAULT 'composing',
            placed_at DATETIME,
            paid_at DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (reservation_id) REFERENCES reservations(id) ON DELETE SET NULL,
            FOREIGN KEY (table_id) REFERENCES tables(id),
            FOREIGN KEY (waiter_id) REFERENCES users(id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",

        """CREATE TABLE IF NOT EXISTS order_items (
            id INT AUTO_INCREMENT PRIMARY KEY,
            order_id INT NOT NULL,
            dish_id INT NOT NULL,
            quantity INT NOT NULL DEFAULT 1,
            unit_price DECIMAL(10,2) NOT NULL,
            discount_percent DECIMAL(5,2) DEFAULT 0,
            FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
            FOREIGN KEY (dish_id) REFERENCES dishes(id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",

        """CREATE TABLE IF NOT EXISTS bills (
            id INT AUTO_INCREMENT PRIMARY KEY,
            reservation_id INT,
            table_id INT NOT NULL,
            waiter_id INT NOT NULL,
            total_amount DECIMAL(10,2) NOT NULL DEFAULT 0,
            status ENUM('pending','paid','cancelled') DEFAULT 'pending',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            paid_at DATETIME,
            FOREIGN KEY (reservation_id) REFERENCES reservations(id) ON DELETE SET NULL,
            FOREIGN KEY (table_id) REFERENCES tables(id),
            FOREIGN KEY (waiter_id) REFERENCES users(id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",

        """CREATE TABLE IF NOT EXISTS receipts (
            id INT AUTO_INCREMENT PRIMARY KEY,
            bill_id INT NOT NULL UNIQUE,
            receipt_number VARCHAR(50) NOT NULL UNIQUE,
            total_amount DECIMAL(10,2) NOT NULL,
            payment_method ENUM('cash','card') DEFAULT 'card',
            issued_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (bill_id) REFERENCES bills(id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"""
    ]

    try:
        for stmt in tables_sql:
            cursor.execute(stmt)
        conn.commit()
        _insert_initial_data(cursor, conn)
        cursor.close()
        conn.close()
        return True
    except Error as e:
        conn.rollback()
        raise e


def _insert_initial_data(cursor, conn):
    roles = [('admin','Администратор'),('waiter','Официант'),('kitchen','Кухня'),('client','Клиент')]
    cursor.executemany("INSERT IGNORE INTO roles (name, description) VALUES (%s, %s)", roles)

    cursor.execute("""INSERT IGNORE INTO users (username, password_hash, full_name, role_id)
        SELECT 'admin', %s, 'Администратор Oltremare', id FROM roles WHERE name='admin'""",
        (hash_password('admin123'),))
    cursor.execute("""INSERT IGNORE INTO users (username, password_hash, full_name, role_id)
        SELECT 'kitchen', %s, 'Кухня Oltremare', id FROM roles WHERE name='kitchen'""",
        (hash_password('kitchen123'),))

    tables_data = [
        (1,4,'Зал 1'),(2,4,'Зал 1'),(3,2,'Зал 1'),(4,4,'Зал 1'),(5,4,'Зал 2'),
        (6,4,'Зал 2'),(7,2,'Зал 2'),(8,4,'Зал 2'),(9,4,'Терраса'),(10,4,'Терраса'),
    ]
    cursor.executemany("INSERT IGNORE INTO tables (number, capacity, location) VALUES (%s, %s, %s)", tables_data)

    categories = [('Закуски',),('Супы',),('Основные блюда',),('Паста',),('Десерты',),('Напитки',)]
    cursor.executemany("INSERT IGNORE INTO dish_categories (name) VALUES (%s)", categories)
    conn.commit()

    # ИСПРАВЛЕНО: используем отдельный курсор с dictionary=True
    cat_cursor = conn.cursor(dictionary=True)
    cat_cursor.execute("SELECT id, name FROM dish_categories ORDER BY id")
    cats = {r['name']: r['id'] for r in cat_cursor.fetchall()}
    cat_cursor.close()

    # ИСПРАВЛЕНО: проверяем существование блюд
    check_cursor = conn.cursor(dictionary=True)
    check_cursor.execute("SELECT COUNT(*) AS cnt FROM dishes")
    row = check_cursor.fetchone()
    check_cursor.close()
    
    if row and row['cnt'] == 0:
        dishes_sql = [
            ('Брускетта с томатами', cats['Закуски'], 'Классическая итальянская закуска', 450.00, 50),
            ('Карпаччо из говядины', cats['Закуски'], 'Тонко нарезанная говядина с рукколой', 850.00, 30),
            ('Минестроне', cats['Супы'], 'Итальянский овощной суп', 550.00, 40),
            ('Крем-суп из тыквы', cats['Супы'], 'Нежный суп-пюре', 500.00, 35),
            ('Тальята из говядины', cats['Основные блюда'], 'Говядина гриль с розмарином', 1800.00, 20),
            ('Лосось на гриле', cats['Основные блюда'], 'Лосось с соусом из каперсов', 1650.00, 25),
            ('Спагетти Карбонара', cats['Паста'], 'Классическая карбонара', 750.00, 60),
            ('Тальятелле с трюфелем', cats['Паста'], 'Паста с трюфельным соусом', 1200.00, 30),
            ('Тирамису', cats['Десерты'], 'Классический итальянский десерт', 450.00, 40),
            ('Панна котта', cats['Десерты'], 'С ягодным соусом', 380.00, 45),
            ('Вода минеральная', cats['Напитки'], 'Газированная/негазированная 0.5л', 150.00, 100),
            ('Сок свежевыжатый', cats['Напитки'], 'Апельсин/Яблоко', 350.00, 80),
        ]
        cursor.executemany("""INSERT INTO dishes (name, category_id, description, price, stock_quantity)
            VALUES (%s, %s, %s, %s, %s)""", dishes_sql)

    conn.commit()