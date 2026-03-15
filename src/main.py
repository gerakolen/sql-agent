"""Text-to-SQL AI Assistant - Основной файл приложения."""

import sys
import logging
import argparse
from typing import Optional
from pathlib import Path

# Добавляем родительскую директорию в путь для импортов
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import Config
from src.database.connection import DatabaseConnection
from src.agents.sql_agent import SQLAgent
from src.utils.formatters import ResultFormatter

# Настройка логирования (по умолчанию только WARNING и ERROR)
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TextToSQLAssistant:
    """Основной класс приложения."""
    
    def __init__(self, config: Optional[Config] = None, verbose: bool = False, show_tools: bool = False, show_sql: bool = False, show_logs: bool = False):
        """Инициализация приложения.
        
        Args:
            config: Конфигурация приложения. Если None, загружается из переменных окружения.
            verbose: Показывать все сообщения.
            show_tools: Показывать сообщения инструментов.
            show_sql: Показывать SQL-запросы.
            show_logs: Показывать логи приложения.
        """
        self.config = config or Config.from_env()
        self.db_connection: Optional[DatabaseConnection] = None
        self.agent: Optional[SQLAgent] = None
        self.formatter = ResultFormatter()
        self.verbose = verbose
        self.show_tools = show_tools
        self.show_sql = show_sql
        self.show_logs = show_logs
        
        # Настраиваем уровень логирования
        if show_logs:
            logging.getLogger().setLevel(logging.INFO)
        else:
            logging.getLogger().setLevel(logging.WARNING)
    
    def initialize(self) -> bool:
        """Инициализирует подключение к базе данных и агента.
        
        Returns:
            True если инициализация прошла успешно, иначе False.
        """
        try:
            # Подключение к базе данных
            logger.info("Подключение к базе данных...")
            self.db_connection = DatabaseConnection(self.config.database)
            self.db_connection.connect()
            
            # Проверка подключения
            if not self.db_connection.test_connection():
                logger.error("Не удалось проверить подключение к базе данных")
                return False
            
            logger.info("Подключение к базе данных установлено успешно")
            
            # Инициализация агента
            logger.info("Инициализация SQL-агента...")
            self.agent = SQLAgent(self.config, self.db_connection)
            logger.info("SQL-агент инициализирован успешно")
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при инициализации: {e}")
            return False
    
    def run_interactive(self) -> None:
        """Запускает интерактивный режим работы."""
        print("\n" + "=" * 60)
        print("🤖 Text-to-SQL AI Assistant")
        print("=" * 60)
        print(f"База данных: {self.config.database.db_type}")
        print(f"Модель: {self.config.llm.model}")
        print("=" * 60)
        print("\nВведите ваш вопрос на естественном языке.")
        print("Для выхода введите 'exit' или 'quit'.\n")
        
        while True:
            try:
                # Получаем вопрос от пользователя
                question = input("❓ Ваш вопрос: ").strip()
                
                # Проверка на выход
                if question.lower() in ["exit", "quit", "выход", "выйти"]:
                    print("\n👋 До свидания!")
                    break
                
                if not question:
                    print("⚠️  Пожалуйста, введите вопрос.")
                    continue
                
                # Выполняем запрос
                print("\n🔄 Обработка запроса...")
                
                try:
                    for message in self.agent.query_with_stream(question, verbose=self.verbose, show_tools=self.show_tools, show_sql=self.show_sql):
                        message.pretty_print()
                    print()
                except Exception as e:
                    print(f"\n{self.formatter.format_error(str(e))}\n")
                
            except KeyboardInterrupt:
                print("\n\n👋 До свидания!")
                break
            except Exception as e:
                logger.error(f"Ошибка при обработке запроса: {e}")
                print(f"\n{self.formatter.format_error(str(e))}\n")
    
    def run_single_query(self, question: str) -> None:
        """Выполняет один запрос и выводит результат.
        
        Args:
            question: Вопрос пользователя.
        """
        print(f"\n🔄 Обработка запроса: {question}")
        
        try:
            for message in self.agent.query_with_stream(question, verbose=self.verbose, show_tools=self.show_tools, show_sql=self.show_sql):
                message.pretty_print()
        except Exception as e:
            print(f"\n{self.formatter.format_error(str(e))}\n")
    
    def shutdown(self) -> None:
        """Завершает работу приложения."""
        if self.db_connection:
            self.db_connection.disconnect()
        logger.info("Приложение завершено")


def main():
    """Точка входа в приложение."""
    # Парсинг аргументов командной строки
    parser = argparse.ArgumentParser(description='Text-to-SQL AI Assistant')
    parser.add_argument('question', nargs='?', help='Вопрос на естественном языке')
    parser.add_argument('--verbose', '-v', action='store_true', help='Показывать все сообщения')
    parser.add_argument('--tools', '-t', action='store_true', help='Показывать сообщения инструментов')
    parser.add_argument('--sql', '-s', action='store_true', help='Показывать SQL-запросы')
    parser.add_argument('--logs', '-l', action='store_true', help='Показывать логи приложения')
    
    args = parser.parse_args()
    
    # Загружаем конфигурацию
    config = Config.from_env()
    
    # Создаём и инициализируем приложение
    app = TextToSQLAssistant(config, verbose=args.verbose, show_tools=args.tools, show_sql=args.sql, show_logs=args.logs)
    
    if not app.initialize():
        print("❌ Не удалось инициализировать приложение.")
        sys.exit(1)
    
    # Проверяем аргументы командной строки
    if args.question:
        # Режим одного запроса
        app.run_single_query(args.question)
    else:
        # Интерактивный режим
        app.run_interactive()
    
    # Завершаем работу
    app.shutdown()


if __name__ == "__main__":
    main()
