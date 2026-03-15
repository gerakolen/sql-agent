"""Модуль форматирования результатов запросов."""

from typing import List, Dict, Any, Optional
import json


class ResultFormatter:
    """Класс для форматирования результатов SQL-запросов."""
    
    @staticmethod
    def format_as_table(results: List[Dict[str, Any]]) -> str:
        """Форматирует результаты в виде таблицы.
        
        Args:
            results: Список словарей с результатами запроса.
            
        Returns:
            Строковое представление таблицы.
        """
        if not results:
            return "Нет данных для отображения."
        
        # Получаем заголовки
        headers = list(results[0].keys())
        
        # Вычисляем ширину каждой колонки
        col_widths = {h: len(str(h)) for h in headers}
        for row in results:
            for h, v in row.items():
                col_widths[h] = max(col_widths[h], len(str(v)))
        
        # Формируем таблицу
        lines = []
        
        # Заголовок
        header_line = " | ".join(str(h).ljust(col_widths[h]) for h in headers)
        lines.append(header_line)
        
        # Разделитель
        separator = "-+-".join("-" * col_widths[h] for h in headers)
        lines.append(separator)
        
        # Данные
        for row in results:
            data_line = " | ".join(str(row[h]).ljust(col_widths[h]) for h in headers)
            lines.append(data_line)
        
        # Добавляем информацию о количестве строк
        lines.append(f"\nВсего строк: {len(results)}")
        
        return "\n".join(lines)
    
    @staticmethod
    def format_as_json(results: List[Dict[str, Any]], indent: int = 2) -> str:
        """Форматирует результаты в формате JSON.
        
        Args:
            results: Список словарей с результатами запроса.
            indent: Отступ для форматирования JSON.
            
        Returns:
            Строковое представление JSON.
        """
        return json.dumps(results, indent=indent, ensure_ascii=False, default=str)
    
    @staticmethod
    def format_as_markdown(results: List[Dict[str, Any]]) -> str:
        """Форматирует результаты в формате Markdown.
        
        Args:
            results: Список словарей с результатами запроса.
            
        Returns:
            Строковое представление Markdown таблицы.
        """
        if not results:
            return "Нет данных для отображения."
        
        headers = list(results[0].keys())
        
        lines = []
        
        # Заголовок
        lines.append("| " + " | ".join(headers) + " |")
        
        # Разделитель
        lines.append("| " + " | ".join("---" for _ in headers) + " |")
        
        # Данные
        for row in results:
            lines.append("| " + " | ".join(str(row[h]) for h in headers) + " |")
        
        return "\n".join(lines)
    
    @staticmethod
    def format_summary(results: List[Dict[str, Any]]) -> str:
        """Форматирует краткое описание результатов.
        
        Args:
            results: Список словарей с результатами запроса.
            
        Returns:
            Краткое описание результатов.
        """
        if not results:
            return "Запрос вернул пустой результат."
        
        count = len(results)
        columns = list(results[0].keys())
        
        summary = f"Запрос вернул {count} строк"
        if count == 1:
            summary += "у"
        elif count < 5:
            summary += "ы"
        summary += f" с {len(columns)} колонками: {', '.join(columns)}"
        
        return summary
    
    @staticmethod
    def format_error(error: str) -> str:
        """Форматирует сообщение об ошибке.
        
        Args:
            error: Текст ошибки.
            
        Returns:
            Форматированное сообщение об ошибке.
        """
        return f"❌ Ошибка: {error}"
    
    @staticmethod
    def format_sql_query(query: str) -> str:
        """Форматирует SQL-запрос для отображения.
        
        Args:
            query: SQL-запрос.
            
        Returns:
            Форматированный SQL-запрос.
        """
        return f"```sql\n{query}\n```"
    
    @staticmethod
    def format_answer(answer: str, sql_query: Optional[str] = None) -> str:
        """Форматирует полный ответ агента.
        
        Args:
            answer: Ответ агента.
            sql_query: SQL-запрос (опционально).
            
        Returns:
            Форматированный ответ.
        """
        lines = []
        
        if sql_query:
            lines.append("📊 SQL-запрос:")
            lines.append(ResultFormatter.format_sql_query(sql_query))
            lines.append("")
        
        lines.append("💬 Ответ:")
        lines.append(answer)
        
        return "\n".join(lines)
