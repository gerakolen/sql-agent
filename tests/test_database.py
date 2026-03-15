"""Тестовый скрипт для проверки работы с базой данных без LLM."""

import sys
from src.config import Config
from src.database.connection import DatabaseConnection
from src.database.schema import DatabaseSchema
from src.validators.sql_validator import SQLValidator

def main():
    print("🧪 Тестирование модулей без LLM...\n")
    
    # Загружаем конфигурацию
    config = Config.from_env()
    print(f"✓ Конфигурация загружена")
    print(f"  - База данных: {config.database.db_type}")
    
    # Подключаемся к базе данных
    print("\n📊 Подключение к базе данных...")
    db_connection = DatabaseConnection(config.database)
    db_connection.connect()
    print(f"✓ Подключение установлено")
    
    # Проверяем подключение
    if db_connection.test_connection():
        print("✓ Тест подключения пройден")
    else:
        print("✗ Тест подключения не удался")
        sys.exit(1)
    
    # Тестируем чтение схемы
    print("\n📋 Чтение схемы базы данных...")
    schema = DatabaseSchema(db_connection.engine)
    tables = schema.get_table_names()
    print(f"✓ Найдено таблиц: {len(tables)}")
    for table in tables:
        print(f"  - {table}")
    
    # Тестируем получение информации о таблице
    print("\n📋 Информация о таблице 'customers':")
    table_info = schema.get_table_info("customers")
    print(f"  Колонок: {len(table_info['columns'])}")
    for col in table_info['columns']:
        pk = " (PK)" if col['primary_key'] else ""
        print(f"  - {col['name']}: {col['type']}{pk}")
    
    # Тестируем выполнение SQL-запроса
    print("\n🔍 Выполнение тестового SQL-запроса...")
    query = "SELECT * FROM customers LIMIT 3"
    results = db_connection.execute_query(query)
    print(f"✓ Запрос выполнен, получено {len(results)} строк")
    for row in results:
        print(f"  - {row['name']}: {row['email']}")
    
    # Тестируем валидацию SQL
    print("\n🛡️ Тестирование валидации SQL...")
    validator = SQLValidator(max_results=100)
    
    # Валидный запрос
    is_valid, result = validator.validate("SELECT * FROM customers")
    print(f"✓ Валидный запрос: {is_valid}")
    
    # Невалидный запрос (DROP)
    is_valid, error = validator.validate("DROP TABLE customers")
    print(f"✓ DROP запрос заблокирован: {not is_valid}")
    print(f"  Ошибка: {error}")
    
    # Тестируем добавление LIMIT
    is_valid, query_with_limit = validator.validate("SELECT * FROM customers")
    print(f"✓ LIMIT добавлен: {'LIMIT' in query_with_limit}")
    
    # Закрываем подключение
    db_connection.disconnect()
    print("\n✓ Подключение закрыто")
    print("\n✅ Все тесты пройдены успешно!")

if __name__ == "__main__":
    main()
