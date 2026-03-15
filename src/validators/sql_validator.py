"""Модуль валидации SQL-запросов."""

import re
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class SQLValidator:
    """Валидатор SQL-запросов для обеспечения безопасности."""
    
    # Запрещённые ключевые слова (операции модификации данных)
    FORBIDDEN_KEYWORDS = [
        "DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE", 
        "TRUNCATE", "GRANT", "REVOKE", "EXEC", "EXECUTE"
    ]
    
    # Разрешённые ключевые слова для SELECT-запросов
    ALLOWED_KEYWORDS = [
        "SELECT", "FROM", "WHERE", "JOIN", "LEFT", "RIGHT", "INNER", "OUTER",
        "ON", "AND", "OR", "NOT", "IN", "IS", "NULL", "LIKE", "BETWEEN",
        "GROUP", "BY", "HAVING", "ORDER", "ASC", "DESC", "LIMIT", "OFFSET",
        "DISTINCT", "COUNT", "SUM", "AVG", "MIN", "MAX", "CASE", "WHEN",
        "THEN", "ELSE", "END", "AS", "WITH", "UNION", "ALL", "EXISTS"
    ]
    
    def __init__(self, max_results: int = 100):
        """Инициализация валидатора.
        
        Args:
            max_results: Максимальное количество возвращаемых строк.
        """
        self.max_results = max_results
    
    def validate(self, query: str) -> Tuple[bool, Optional[str]]:
        """Валидирует SQL-запрос.
        
        Args:
            query: SQL-запрос для валидации.
            
        Returns:
            Кортеж (is_valid, error_message).
        """
        query = query.strip()
        
        # Проверка на пустой запрос
        if not query:
            return False, "Пустой запрос"
        
        # Проверка на запрещённые ключевые слова
        for keyword in self.FORBIDDEN_KEYWORDS:
            pattern = r"\b" + keyword + r"\b"
            if re.search(pattern, query, re.IGNORECASE):
                return False, f"Запрещённое ключевое слово: {keyword}"
        
        # Проверка на наличие SELECT
        if not re.search(r"\bSELECT\b", query, re.IGNORECASE):
            return False, "Запрос должен начинаться с SELECT"
        
        # Проверка на наличие LIMIT
        if not re.search(r"\bLIMIT\b", query, re.IGNORECASE):
            query = self._add_limit(query)
        
        # Проверка на подозрительные паттерны
        suspicious_patterns = [
            r";\s*\w+",  # Несколько запросов
            r"--",       # SQL-комментарии
            r"/\*",      # Многострочные комментарии
            r"\bxp_",    # Расширенные хранимые процедуры
            r"\bsp_",    # Системные хранимые процедуры
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return False, f"Обнаружен подозрительный паттерн: {pattern}"
        
        return True, query
    
    def _add_limit(self, query: str) -> str:
        """Добавляет LIMIT к запросу, если его нет.
        
        Args:
            query: SQL-запрос.
            
        Returns:
            Запрос с добавленным LIMIT.
        """
        # Проверяем, есть ли уже LIMIT
        if re.search(r"\bLIMIT\b", query, re.IGNORECASE):
            return query
        
        # Добавляем LIMIT в конец запроса
        return f"{query} LIMIT {self.max_results}"
    
    def sanitize_query(self, query: str) -> str:
        """Очищает запрос от потенциально опасных элементов.
        
        Args:
            query: SQL-запрос.
            
        Returns:
            Очищенный запрос.
        """
        # Удаляем комментарии
        query = re.sub(r"--.*$", "", query, flags=re.MULTILINE)
        query = re.sub(r"/\*.*?\*/", "", query, flags=re.DOTALL)
        
        # Удаляем лишние пробелы
        query = re.sub(r"\s+", " ", query).strip()
        
        return query
    
    def check_table_names(self, query: str, allowed_tables: List[str]) -> Tuple[bool, Optional[str]]:
        """Проверяет, что запрос использует только разрешённые таблицы.
        
        Args:
            query: SQL-запрос.
            allowed_tables: Список разрешённых таблиц.
            
        Returns:
            Кортеж (is_valid, error_message).
        """
        # Извлекаем имена таблиц из запроса
        from_pattern = r"\bFROM\s+(\w+)"
        join_pattern = r"\b(?:JOIN|LEFT\s+JOIN|RIGHT\s+JOIN|INNER\s+JOIN|OUTER\s+JOIN)\s+(\w+)"
        
        tables = re.findall(from_pattern, query, re.IGNORECASE)
        tables.extend(re.findall(join_pattern, query, re.IGNORECASE))
        
        # Проверяем каждую таблицу
        for table in tables:
            if table.upper() not in [t.upper() for t in allowed_tables]:
                return False, f"Таблица '{table}' не разрешена"
        
        return True, None
