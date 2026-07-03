#!/usr/bin/env python3.11
"""
Диагностика подключения к базе данных
"""

import mysql.connector
from mysql.connector import Error
import sys
import traceback

# Импортируем функции из вашего модуля
from src.database.db import get_connection, execute_query, hash_password, init_database


def test_mysql_connection():
    """Тест подключения к MySQL"""
    
    # Конфигурация без указания БД
    config = {
        'host': 'localhost',
        'port': 3306,
        'user': 'root',
        'password': 'root1234',
        'charset': 'utf8mb4',
        'use_unicode': True,
        'connection_timeout': 10
    }
    
    print("=" * 60)
    print("ДИАГНОСТИКА ПОДКЛЮЧЕНИЯ К MYSQL")
    print("=" * 60)
    
    # Шаг 1: Проверка без БД
    print("\n[1] Проверка подключения к MySQL серверу...")
    try:
        conn = mysql.connector.connect(**config)
        print("✅ Успешное подключение к MySQL серверу!")
        cursor = conn.cursor()
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()
        print(f"   Версия MySQL: {version[0]}")
        conn.close()
    except Error as e:
        print(f"❌ Ошибка: {e}")
        print(traceback.format_exc())
        return False
    
    # Шаг 2: Проверка существования БД
    print("\n[2] Проверка базы данных 'oltremare_db'...")
    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        cursor.execute("SHOW DATABASES LIKE 'oltremare_db'")
        result = cursor.fetchone()
        if result:
            print("✅ База данных 'oltremare_db' существует")
        else:
            print("⚠️ База данных 'oltremare_db' не найдена")
            print("   Будет создана при инициализации")
        conn.close()
    except Error as e:
        print(f"❌ Ошибка: {e}")
        return False
    
    # Шаг 3: Проверка подключения к БД
    print("\n[3] Проверка подключения к БД 'oltremare_db'...")
    try:
        db_config = config.copy()
        db_config['database'] = 'oltremare_db'
        conn = mysql.connector.connect(**db_config)
        print("✅ Успешное подключение к базе данных!")
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print(f"   Найдено таблиц: {len(tables)}")
        for table in tables:
            print(f"   - {table[0]}")
        conn.close()
    except Error as e:
        print(f"⚠️ База данных существует, но недоступна: {e}")
        print("   Будет создана при инициализации")
    
    return True


def test_init_database():
    """Тест инициализации базы данных с обработкой ошибок"""
    print("\n" + "=" * 60)
    print("ТЕСТ ИНИЦИАЛИЗАЦИИ БАЗЫ ДАННЫХ")
    print("=" * 60)
    
    try:
        print("\n[4] Попытка инициализации...")
        
        # Запускаем инициализацию
        result = init_database()
        print("✅ База данных успешно инициализирована!")
        print(f"   Результат: {result}")
        return True
        
    except Exception as e:
        print(f"❌ ОШИБКА при инициализации:")
        print(f"   Тип ошибки: {type(e).__name__}")
        print(f"   Сообщение: {e}")
        print("\n   Полный traceback:")
        traceback.print_exc()
        return False


def test_crud_operations():
    """Тест CRUD операций"""
    print("\n" + "=" * 60)
    print("ТЕСТ CRUD ОПЕРАЦИЙ")
    print("=" * 60)
    
    print("\n[5] Тестирование операций...")
    
    # Тест 1: get_connection
    print("   • Проверка get_connection()...")
    try:
        conn = get_connection()
        print("     ✅ Соединение установлено")
        conn.close()
    except Exception as e:
        print(f"     ❌ Ошибка: {e}")
        traceback.print_exc()
        return

    # Тест 2: execute_query для SELECT
    print("   • Проверка execute_query() для SELECT...")
    try:
        result = execute_query("SELECT COUNT(*) as count FROM roles", fetch=True)
        if result and len(result) > 0:
            print(f"     ✅ Запрос выполнен, найдено ролей: {result[0]['count']}")
        else:
            print("     ❌ Пустой результат")
    except Exception as e:
        print(f"     ❌ Ошибка: {e}")
        traceback.print_exc()
        return

    # Тест 3: execute_query для INSERT
    print("   • Проверка execute_query() для INSERT...")
    try:
        # Вставляем тестовую роль
        test_role_name = f"test_role_{id(object())}"  # Уникальное имя
        result = execute_query(
            "INSERT INTO roles (name, description) VALUES (%s, %s)",
            params=(test_role_name, "Тестовая роль")
        )
        print(f"     ✅ INSERT выполнен, ID: {result}")
        
        # Проверяем, что вставилось
        check = execute_query(
            "SELECT * FROM roles WHERE name = %s",
            params=(test_role_name,),
            fetch_one=True
        )
        if check:
            print(f"     ✅ Роль найдена: {check['name']}")
        else:
            print("     ⚠️ Роль не найдена после вставки")
            
        # Удаляем тестовую роль
        execute_query(
            "DELETE FROM roles WHERE name = %s",
            params=(test_role_name,)
        )
        print("     ✅ Тестовая роль удалена")
        
    except Exception as e:
        print(f"     ❌ Ошибка: {e}")
        traceback.print_exc()
        return

    # Тест 4: hash_password
    print("   • Проверка hash_password()...")
    try:
        test_hash = hash_password("test123")
        print(f"     ✅ Хеш создан: {test_hash[:20]}...")
    except Exception as e:
        print(f"     ❌ Ошибка: {e}")
        traceback.print_exc()
        return

    print("\n✅ Все CRUD операции выполнены успешно!")


def main():
    """Главная функция"""
    # Проверка MySQL
    if not test_mysql_connection():
        print("\n❌ Критическая ошибка: не удалось подключиться к MySQL")
        sys.exit(1)
    
    # Проверка инициализации БД
    if not test_init_database():
        print("\n⚠️ Предупреждение: проблемы с инициализацией БД")
        print("   Проверьте права доступа и конфигурацию")
    
    # Проверка CRUD операций
    test_crud_operations()
    
    print("\n" + "=" * 60)
    print("ДИАГНОСТИКА ЗАВЕРШЕНА")
    print("=" * 60)


if __name__ == "__main__":
    main()