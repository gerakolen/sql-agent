"""Тестовый скрипт для проверки работы SQL-агента."""

import sys
from src.config import Config
from src.database.connection import DatabaseConnection
from src.agents.sql_agent import SQLAgent

def main():
    print("🧪 Тестирование SQL-агента...\n")
    
    # Загружаем конфигурацию
    config = Config.from_env()
    print(f"✓ Конфигурация загружена")
    print(f"  - База данных: {config.database.db_type}")
    print(f"  - Модель: {config.llm.model}")
    
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
    
    # Создаём агента
    print("\n🤖 Инициализация SQL-агента...")
    agent = SQLAgent(config, db_connection)
    print("✓ Агент инициализирован")
    
    # Тестовый запрос
    test_question = "Покажи всех клиентов"
    print(f"\n❓ Тестовый вопрос: {test_question}")
    print("🔄 Обработка...")
    
    result = agent.query(test_question)
    
    if result["success"]:
        print("\n✓ Запрос выполнен успешно")
        print(f"\n💬 Ответ:\n{result['answer']}")
    else:
        print(f"\n✗ Ошибка: {result['error']}")
    
    # Закрываем подключение
    db_connection.disconnect()
    print("\n✓ Подключение закрыто")

if __name__ == "__main__":
    main()
