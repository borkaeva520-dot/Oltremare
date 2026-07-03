-- ============================================================
-- База данных: Система управления рестораном «Oltremare»
-- СУБД: MySQL 8.0+ / MariaDB 10.6+
-- Кодировка: UTF-8
-- ============================================================

CREATE DATABASE IF NOT EXISTS oltremare CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE oltremare;

-- ------------------------------------------------------------
-- 1. Пользователи (роли: admin, waiter, kitchen, client)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    login         VARCHAR(64) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role          ENUM('admin','waiter','kitchen','client') NOT NULL DEFAULT 'client',
    full_name     VARCHAR(150) NOT NULL,
    phone         VARCHAR(20),
    email         VARCHAR(120),
    is_active     TINYINT(1) NOT NULL DEFAULT 1,
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_users_role (role)
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- 2. Столики
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tables (
    id       INT AUTO_INCREMENT PRIMARY KEY,
    number   INT NOT NULL UNIQUE,
    capacity INT NOT NULL DEFAULT 4 CHECK (capacity BETWEEN 1 AND 4),
    floor    TINYINT NOT NULL DEFAULT 1,
    pos_x    INT NOT NULL DEFAULT 0,   -- позиция на схеме (px)
    pos_y    INT NOT NULL DEFAULT 0,
    status   ENUM('free','reserved','occupied','unavailable') NOT NULL DEFAULT 'free',
    INDEX idx_tables_status (status)
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- 3. Смены официантов
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS shifts (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    waiter_id    INT NOT NULL,
    shift_date   DATE NOT NULL,
    start_time   TIME NOT NULL DEFAULT '09:00:00',
    end_time     TIME NOT NULL DEFAULT '21:00:00',
    opened_at    DATETIME,
    closed_at    DATETIME,
    status       ENUM('scheduled','open','closed') NOT NULL DEFAULT 'scheduled',
    FOREIGN KEY (waiter_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_shifts_waiter (waiter_id),
    INDEX idx_shifts_date (shift_date)
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- 4. Столики в смене (M:N — смена <-> столик)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS shift_tables (
    id       INT AUTO_INCREMENT PRIMARY KEY,
    shift_id INT NOT NULL,
    table_id INT NOT NULL,
    UNIQUE KEY uq_shift_table (shift_id, table_id),
    FOREIGN KEY (shift_id)  REFERENCES shifts(id) ON DELETE CASCADE,
    FOREIGN KEY (table_id)  REFERENCES tables(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- 5. Брони
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS reservations (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    client_name   VARCHAR(150) NOT NULL,
    phone         VARCHAR(20)  NOT NULL,
    email         VARCHAR(120),
    res_date      DATE NOT NULL,
    time_start    TIME NOT NULL,
    time_end      TIME NOT NULL,
    guests_count  INT NOT NULL DEFAULT 1,
    comment       TEXT,
    status        ENUM('pending','confirmed','cancelled','completed') NOT NULL DEFAULT 'confirmed',
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_res_date (res_date),
    INDEX idx_res_status (status)
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- 6. Столики в брони (M:N — бронь <-> столик)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS reservation_tables (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    reservation_id INT NOT NULL,
    table_id       INT NOT NULL,
    UNIQUE KEY uq_res_table (reservation_id, table_id),
    FOREIGN KEY (reservation_id) REFERENCES reservations(id) ON DELETE CASCADE,
    FOREIGN KEY (table_id)       REFERENCES tables(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- 7. Категории меню
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS menu_categories (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    name       VARCHAR(100) NOT NULL UNIQUE,
    sort_order INT NOT NULL DEFAULT 0
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- 8. Блюда меню
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS menu_items (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    category_id  INT NOT NULL,
    name         VARCHAR(200) NOT NULL,
    description  TEXT,
    price        DECIMAL(10,2) NOT NULL CHECK (price >= 0),
    stock_qty    INT NOT NULL DEFAULT 0 CHECK (stock_qty >= 0),
    is_available TINYINT(1) NOT NULL DEFAULT 1,
    FOREIGN KEY (category_id) REFERENCES menu_categories(id),
    INDEX idx_items_category (category_id)
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- 9. Акции / скидки
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS promotions (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    name         VARCHAR(200) NOT NULL,
    description  TEXT,
    discount_pct DECIMAL(5,2) NOT NULL CHECK (discount_pct BETWEEN 0 AND 100),
    date_start   DATE NOT NULL,
    date_end     DATE NOT NULL,
    is_active    TINYINT(1) NOT NULL DEFAULT 1,
    CHECK (date_end >= date_start)
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- 10. Блюда / категории в акции
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS promotion_items (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    promotion_id   INT NOT NULL,
    menu_item_id   INT,               -- NULL => вся категория
    category_id    INT,               -- NULL => конкретное блюдо
    FOREIGN KEY (promotion_id) REFERENCES promotions(id) ON DELETE CASCADE,
    FOREIGN KEY (menu_item_id) REFERENCES menu_items(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id)  REFERENCES menu_categories(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- 11. Заказы
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS orders (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    reservation_id INT,
    table_id       INT NOT NULL,
    waiter_id      INT NOT NULL,
    status         ENUM('draft','placed','accepted','cooking','ready','delivered','cancelled') NOT NULL DEFAULT 'draft',
    placed_at      DATETIME,
    delivered_at   DATETIME,
    total_amount   DECIMAL(10,2) NOT NULL DEFAULT 0,
    created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (reservation_id) REFERENCES reservations(id) ON DELETE SET NULL,
    FOREIGN KEY (table_id)       REFERENCES tables(id),
    FOREIGN KEY (waiter_id)      REFERENCES users(id),
    INDEX idx_orders_status   (status),
    INDEX idx_orders_waiter   (waiter_id),
    INDEX idx_orders_table    (table_id),
    INDEX idx_orders_res      (reservation_id)
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- 12. Блюда в заказе
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS order_items (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    order_id       INT NOT NULL,
    menu_item_id   INT NOT NULL,
    quantity       INT NOT NULL DEFAULT 1 CHECK (quantity > 0),
    price_at_order DECIMAL(10,2) NOT NULL,
    discount_pct   DECIMAL(5,2) NOT NULL DEFAULT 0,
    FOREIGN KEY (order_id)     REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (menu_item_id) REFERENCES menu_items(id),
    INDEX idx_oi_order (order_id)
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- 13. Счета
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS bills (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    reservation_id  INT,
    total_amount    DECIMAL(10,2) NOT NULL DEFAULT 0,
    discount_amount DECIMAL(10,2) NOT NULL DEFAULT 0,
    status          ENUM('open','paid','cancelled') NOT NULL DEFAULT 'open',
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (reservation_id) REFERENCES reservations(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- 14. Чеки
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS receipts (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    bill_id     INT NOT NULL,
    waiter_id   INT NOT NULL,
    paid_amount DECIMAL(10,2) NOT NULL,
    paid_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bill_id)   REFERENCES bills(id),
    FOREIGN KEY (waiter_id) REFERENCES users(id)
) ENGINE=InnoDB;

-- ============================================================
-- ТРИГГЕРЫ
-- ============================================================

DELIMITER $$

-- Уменьшаем остаток на складе при добавлении блюда в заказ
CREATE TRIGGER trg_order_item_insert
AFTER INSERT ON order_items
FOR EACH ROW
BEGIN
    UPDATE menu_items
    SET stock_qty = stock_qty - NEW.quantity
    WHERE id = NEW.menu_item_id;
END$$

-- Восстанавливаем остаток при удалении блюда из заказа
CREATE TRIGGER trg_order_item_delete
AFTER DELETE ON order_items
FOR EACH ROW
BEGIN
    UPDATE menu_items
    SET stock_qty = stock_qty + OLD.quantity
    WHERE id = OLD.menu_item_id;
END$$

-- Обновляем total_amount заказа при изменении order_items
CREATE TRIGGER trg_update_order_total_ins
AFTER INSERT ON order_items
FOR EACH ROW
BEGIN
    UPDATE orders
    SET total_amount = (
        SELECT COALESCE(SUM(quantity * price_at_order * (1 - discount_pct/100)), 0)
        FROM order_items WHERE order_id = NEW.order_id
    )
    WHERE id = NEW.order_id;
END$$

CREATE TRIGGER trg_update_order_total_del
AFTER DELETE ON order_items
FOR EACH ROW
BEGIN
    UPDATE orders
    SET total_amount = (
        SELECT COALESCE(SUM(quantity * price_at_order * (1 - discount_pct/100)), 0)
        FROM order_items WHERE order_id = OLD.order_id
    )
    WHERE id = OLD.order_id;
END$$

DELIMITER ;

-- ============================================================
-- ХРАНИМЫЕ ПРОЦЕДУРЫ
-- ============================================================

DELIMITER $$

-- Процедура: добавить блюдо в заказ с проверкой склада
CREATE PROCEDURE sp_add_order_item(
    IN p_order_id    INT,
    IN p_item_id     INT,
    IN p_quantity    INT,
    OUT p_result     VARCHAR(500)
)
BEGIN
    DECLARE v_stock    INT DEFAULT 0;
    DECLARE v_price    DECIMAL(10,2) DEFAULT 0;
    DECLARE v_name     VARCHAR(200) DEFAULT '';
    DECLARE v_discount DECIMAL(5,2) DEFAULT 0;
    DECLARE v_status   VARCHAR(20) DEFAULT '';

    -- Проверяем статус заказа
    SELECT status INTO v_status FROM orders WHERE id = p_order_id;
    IF v_status != 'draft' THEN
        SET p_result = 'ОШИБКА: Заказ уже оформлен. Редактирование невозможно.';
        LEAVE sp_add_order_item;
    END IF;

    -- Получаем данные блюда
    SELECT name, price, stock_qty INTO v_name, v_price, v_stock
    FROM menu_items WHERE id = p_item_id;

    -- Проверяем наличие
    IF v_stock < p_quantity THEN
        SET p_result = CONCAT('ОШИБКА: Недостаточно порций «', v_name,
            '». Доступно: ', v_stock, ' порций.');
        LEAVE sp_add_order_item;
    END IF;

    -- Ищем активную скидку
    SELECT COALESCE(MAX(pr.discount_pct), 0) INTO v_discount
    FROM promotions pr
    JOIN promotion_items pi ON pi.promotion_id = pr.id
    WHERE pr.is_active = 1
      AND CURDATE() BETWEEN pr.date_start AND pr.date_end
      AND (pi.menu_item_id = p_item_id OR pi.category_id = (
            SELECT category_id FROM menu_items WHERE id = p_item_id));

    INSERT INTO order_items (order_id, menu_item_id, quantity, price_at_order, discount_pct)
    VALUES (p_order_id, p_item_id, p_quantity, v_price, v_discount);

    SET p_result = CONCAT('Блюдо «', v_name, '» в количестве ', p_quantity,
        ' порций успешно добавлено в Заказ №', p_order_id);
END$$

-- Процедура: статистика продаж за два месяца
CREATE PROCEDURE sp_sales_stats(
    IN p_year1  INT, IN p_month1 INT,
    IN p_year2  INT, IN p_month2 INT
)
BEGIN
    SELECT
        mc.name                           AS category,
        mi.name                           AS dish,
        COALESCE(SUM(CASE WHEN YEAR(o.created_at)=p_year1 AND MONTH(o.created_at)=p_month1
                          THEN oi.quantity END), 0) AS qty_month1,
        COALESCE(SUM(CASE WHEN YEAR(o.created_at)=p_year2 AND MONTH(o.created_at)=p_month2
                          THEN oi.quantity END), 0) AS qty_month2,
        COALESCE(SUM(CASE WHEN YEAR(o.created_at)=p_year2 AND MONTH(o.created_at)=p_month2
                          THEN oi.quantity END), 0)
        - COALESCE(SUM(CASE WHEN YEAR(o.created_at)=p_year1 AND MONTH(o.created_at)=p_month1
                          THEN oi.quantity END), 0) AS dynamics
    FROM order_items oi
    JOIN menu_items mi  ON mi.id = oi.menu_item_id
    JOIN menu_categories mc ON mc.id = mi.category_id
    JOIN orders o ON o.id = oi.order_id
    WHERE o.status = 'delivered'
      AND ((YEAR(o.created_at)=p_year1 AND MONTH(o.created_at)=p_month1)
        OR (YEAR(o.created_at)=p_year2 AND MONTH(o.created_at)=p_month2))
    GROUP BY mc.name, mi.name
    ORDER BY mc.name, mi.name;
END$$

-- Процедура: занятость столиков по часам на дату
CREATE PROCEDURE sp_table_hourly(IN p_date DATE)
BEGIN
    SELECT
        t.number AS table_number,
        h.hour_val,
        CASE WHEN r.id IS NOT NULL THEN CONCAT('Бронь №', r.id) ELSE '' END AS status
    FROM tables t
    CROSS JOIN (
        SELECT  9 AS hour_val UNION SELECT 10 UNION SELECT 11 UNION SELECT 12
        UNION SELECT 13 UNION SELECT 14 UNION SELECT 15 UNION SELECT 16
        UNION SELECT 17 UNION SELECT 18 UNION SELECT 19 UNION SELECT 20
        UNION SELECT 21 UNION SELECT 22
    ) h
    LEFT JOIN reservation_tables rt ON rt.table_id = t.id
    LEFT JOIN reservations r
        ON r.id = rt.reservation_id
        AND r.res_date = p_date
        AND r.status IN ('confirmed','pending')
        AND HOUR(r.time_start) <= h.hour_val
        AND HOUR(r.time_end)    > h.hour_val
    ORDER BY t.number, h.hour_val;
END$$

DELIMITER ;

-- ============================================================
-- НАЧАЛЬНЫЕ ДАННЫЕ
-- ============================================================

-- Администратор (пароль: admin123 — хранится в виде хеша в приложении, здесь placeholder)
INSERT INTO users (login, password_hash, role, full_name, phone) VALUES
('admin', '$2b$12$PLACEHOLDER_ADMIN_HASH', 'admin', 'Администратор Системы', '+7-999-000-0001'),
('waiter1', '$2b$12$PLACEHOLDER_W1_HASH',  'waiter', 'Иванов Иван Иванович',   '+7-999-000-0002'),
('waiter2', '$2b$12$PLACEHOLDER_W2_HASH',  'waiter', 'Петрова Мария Сергеевна','+7-999-000-0003'),
('kitchen1','$2b$12$PLACEHOLDER_K1_HASH',  'kitchen','Кухня Основная',         NULL);

-- Столики (10 столиков, 2 этажа)
INSERT INTO tables (number, capacity, floor, pos_x, pos_y) VALUES
(1,4,1,50,50),  (2,4,1,200,50),  (3,2,1,350,50),
(4,4,1,50,200), (5,4,1,200,200), (6,2,1,350,200),
(7,4,2,50,50),  (8,4,2,200,50),  (9,2,2,350,50),
(10,4,2,50,200);

-- Категории меню
INSERT INTO menu_categories (name, sort_order) VALUES
('Завтраки',1),('Закуски',2),('Супы',3),('Паста',4),
('Пицца',5),('Горячее',6),('Десерты',7),('Напитки',8);

-- Блюда
INSERT INTO menu_items (category_id, name, price, stock_qty, description) VALUES
(1,'Яичница с трюфелем',890,20,'Три яйца, трюфельное масло, зелень'),
(1,'Каша овсяная с ягодами',450,30,'Фермерские ягоды, мёд'),
(2,'Брускетта с томатами',590,25,'Хлеб чиабатта, помидоры черри, базилик'),
(2,'Карпаччо из говядины',1290,15,'Тонкие ломтики говядины, руккола, пармезан'),
(3,'Минестроне',680,20,'Итальянский овощной суп'),
(4,'Паста Карбонара',990,30,'Спагетти, гуанчале, яйцо, пармезан'),
(4,'Паста Болоньезе',950,30,'Тальятелле, говяжий фарш, томаты'),
(4,'Трюфельная паста',1490,20,'Паппарделле, трюфель, пармезан'),
(5,'Маргарита',750,25,'Томатный соус, моцарелла, базилик'),
(5,'Четыре сыра',990,20,'Моцарелла, горгонзола, пармезан, рикотта'),
(6,'Дорадо на гриле',1890,15,'Морской окунь, лимон, оливковое масло'),
(6,'Телятина Оссобуко',2190,10,'Тушёная телячья рулька, гремолата, ризотто'),
(7,'Тирамису',590,30,'Классический итальянский десерт'),
(7,'Панна-котта',550,25,'Ванильный крем, ягодный соус'),
(8,'Эспрессо',250,100,'Двойной эспрессо'),
(8,'Капучино',350,100,'Эспрессо, вспененное молоко');

-- Пример акции
INSERT INTO promotions (name, description, discount_pct, date_start, date_end, is_active) VALUES
('Скидка на десерты', '15% на все десерты в июне', 15.00, '2026-06-01', '2026-06-30', 1);

-- Привязка акции к категории «Десерты» (id=7)
INSERT INTO promotion_items (promotion_id, category_id) VALUES (1, 7);

-- ============================================================
-- ПОЛЕЗНЫЕ ПРЕДСТАВЛЕНИЯ (VIEWS)
-- ============================================================

CREATE VIEW v_free_tables AS
SELECT t.id, t.number, t.capacity, t.floor
FROM tables t
WHERE t.status = 'free'
  AND t.id NOT IN (
      SELECT rt.table_id
      FROM reservation_tables rt
      JOIN reservations r ON r.id = rt.reservation_id
      WHERE r.status IN ('confirmed','pending')
        AND r.res_date = CURDATE()
        AND r.time_start <= CURTIME()
        AND r.time_end   >= CURTIME()
  );

CREATE VIEW v_active_orders AS
SELECT o.id, o.table_id, t.number AS table_number,
       u.full_name AS waiter, o.status, o.total_amount, o.created_at
FROM orders o
JOIN tables t ON t.id = o.table_id
JOIN users  u ON u.id = o.waiter_id
WHERE o.status NOT IN ('delivered','cancelled');
