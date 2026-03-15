"""Модуль подключения к базе данных."""

from typing import Optional, List, Dict, Any, Generator
from sqlalchemy import create_engine, text, Engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
import logging

from src.config import DatabaseConfig

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Класс для управления подключением к базе данных."""
    
    def __init__(self, config: DatabaseConfig):
        """Инициализация подключения к базе данных.
        
        Args:
            config: Конфигурация базы данных.
        """
        self.config = config
        self._engine: Optional[Engine] = None
        self._session_factory: Optional[sessionmaker] = None
    
    def connect(self) -> None:
        """Устанавливает подключение к базе данных."""
        try:
            connection_string = self.config.get_connection_string()
            self._engine = create_engine(
                connection_string,
                pool_pre_ping=True,
                echo=False
            )
            self._session_factory = sessionmaker(bind=self._engine)
            logger.info(f"Подключено к базе данных: {self.config.db_type}")
        except Exception as e:
            logger.error(f"Ошибка подключения к базе данных: {e}")
            raise
    
    def disconnect(self) -> None:
        """Закрывает подключение к базе данных."""
        if self._engine:
            self._engine.dispose()
            logger.info("Подключение к базе данных закрыто")
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Контекстный менеджер для работы с сессией.
        
        Yields:
            Session: Сессия SQLAlchemy.
        """
        if not self._session_factory:
            raise RuntimeError("База данных не подключена. Вызовите метод connect().")
        
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Выполняет SQL-запрос и возвращает результаты.
        
        Args:
            query: SQL-запрос.
            params: Параметры запроса.
            
        Returns:
            Список словарей с результатами запроса.
        """
        if not self._engine:
            raise RuntimeError("База данных не подключена. Вызовите метод connect().")
        
        try:
            with self._engine.connect() as connection:
                result = connection.execute(text(query), params or {})
                columns = result.keys()
                rows = result.fetchall()
                return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            logger.error(f"Ошибка выполнения запроса: {e}")
            raise
    
    def test_connection(self) -> bool:
        """Проверяет подключение к базе данных.
        
        Returns:
            True если подключение успешно, иначе False.
        """
        try:
            with self._engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Тест подключения не удался: {e}")
            return False
    
    @property
    def engine(self) -> Optional[Engine]:
        """Возвращает движок базы данных."""
        return self._engine
