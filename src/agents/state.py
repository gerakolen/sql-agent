"""Модуль состояния для LangGraph."""

from typing import TypedDict, List, Dict, Any, Optional
from typing_extensions import Annotated
from langchain.messages import AnyMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """Состояние агента для LangGraph."""
    
    # Сообщения (используем add_messages для корректного обновления)
    messages: Annotated[list[AnyMessage], add_messages]
    
    # SQL-запрос
    sql_query: Optional[str]
    
    # Результаты запроса
    query_result: Optional[List[Dict[str, Any]]]
    
    # Ошибка
    error: Optional[str]
    
    # Счётчик попыток
    retry_count: int
