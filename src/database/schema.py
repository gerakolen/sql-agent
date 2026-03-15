"""Модуль для работы со схемой базы данных."""

from typing import List, Dict, Any, Optional
from sqlalchemy import inspect, Engine
import logging

logger = logging.getLogger(__name__)


class DatabaseSchema:
    """Класс для работы со схемой базы данных."""
    
    def __init__(self, engine: Engine):
        """Инициализация схемы базы данных.
        
        Args:
            engine: Движок SQLAlchemy.
        """
        self.engine = engine
        self._inspector = inspect(engine)
        self._schema: Optional[Dict[str, Any]] = None
    
    def get_schema(self) -> Dict[str, Any]:
        """Возвращает схему базы данных.
        
        Returns:
            Словарь с информацией о таблицах, колонках и связях.
        """
        if self._schema is None:
            self._schema = self._load_schema()
        return self._schema
    
    def _load_schema(self) -> Dict[str, Any]:
        """Загружает схему базы данных.
        
        Returns:
            Словарь с информацией о таблицах, колонках и связях.
        """
        schema = {
            "tables": {},
            "foreign_keys": []
        }
        
        try:
            table_names = self._inspector.get_table_names()
            
            for table_name in table_names:
                columns = self._inspector.get_columns(table_name)
                primary_keys = self._inspector.get_pk_constraint(table_name).get("constrained_columns", [])
                foreign_keys = self._inspector.get_foreign_keys(table_name)
                
                schema["tables"][table_name] = {
                    "columns": [
                        {
                            "name": col["name"],
                            "type": str(col["type"]),
                            "nullable": col.get("nullable", True),
                            "default": col.get("default"),
                            "primary_key": col["name"] in primary_keys
                        }
                        for col in columns
                    ],
                    "primary_keys": primary_keys
                }
                
                for fk in foreign_keys:
                    schema["foreign_keys"].append({
                        "table": table_name,
                        "columns": fk["constrained_columns"],
                        "referred_table": fk["referred_table"],
                        "referred_columns": fk["referred_columns"]
                    })
            
            logger.info(f"Схема базы данных загружена: {len(table_names)} таблиц")
            return schema
            
        except Exception as e:
            logger.error(f"Ошибка загрузки схемы: {e}")
            raise
    
    def get_table_names(self) -> List[str]:
        """Возвращает список имён таблиц.
        
        Returns:
            Список имён таблиц.
        """
        return self._inspector.get_table_names()
    
    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """Возвращает информацию о таблице.
        
        Args:
            table_name: Имя таблицы.
            
        Returns:
            Словарь с информацией о таблице.
        """
        schema = self.get_schema()
        if table_name not in schema["tables"]:
            raise ValueError(f"Таблица '{table_name}' не найдена")
        return schema["tables"][table_name]
    
    def get_schema_for_llm(self) -> str:
        """Возвращает схему в формате, подходящем для LLM.
        
        Returns:
            Строковое представление схемы.
        """
        schema = self.get_schema()
        result = []
        
        for table_name, table_info in schema["tables"].items():
            result.append(f"Таблица: {table_name}")
            result.append("Колонки:")
            for col in table_info["columns"]:
                pk = " (PRIMARY KEY)" if col["primary_key"] else ""
                nullable = " NULL" if col["nullable"] else " NOT NULL"
                result.append(f"  - {col['name']}: {col['type']}{nullable}{pk}")
            result.append("")
        
        if schema["foreign_keys"]:
            result.append("Внешние ключи:")
            for fk in schema["foreign_keys"]:
                result.append(
                    f"  {fk['table']}.{', '.join(fk['columns'])} -> "
                    f"{fk['referred_table']}.{', '.join(fk['referred_columns'])}"
                )
        
        return "\n".join(result)
    
    def get_sample_rows(self, table_name: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Возвращает примеры строк из таблицы.
        
        Args:
            table_name: Имя таблицы.
            limit: Количество строк.
            
        Returns:
            Список словарей с примерами данных.
        """
        from sqlalchemy import text
        
        try:
            with self.engine.connect() as conn:
                query = text(f"SELECT * FROM {table_name} LIMIT {limit}")
                result = conn.execute(query)
                columns = result.keys()
                rows = result.fetchall()
                return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            logger.warning(f"Не удалось получить примеры строк из {table_name}: {e}")
            return []
