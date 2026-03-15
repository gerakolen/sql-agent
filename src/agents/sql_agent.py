"""SQL-агент на основе LangGraph."""

from typing import Literal
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode

from src.config import Config
from src.database.connection import DatabaseConnection
from typing import Any


class SQLAgent:
    """SQL-агент для взаимодействия с базой данных через естественный язык."""
    
    def __init__(self, config: Config, db_connection: DatabaseConnection):
        """Инициализация SQL-агента.
        
        Args:
            config: Конфигурация приложения.
            db_connection: Подключение к базе данных.
        """
        self.config = config
        self.db_connection = db_connection
        
        # Создаём SQLDatabase из LangChain
        connection_string = db_connection.config.get_connection_string()
        self.db = SQLDatabase.from_uri(connection_string)
        
        # Инициализация LLM
        self.model = init_chat_model(
            config.llm.model,
            model_provider=config.llm.provider,
            api_key=config.llm.api_key,
            base_url=config.llm.base_url,
            temperature=config.llm.temperature
        )
        
        # Создаём toolkit и получаем инструменты
        self.toolkit = SQLDatabaseToolkit(db=self.db, llm=self.model)
        self.tools = self.toolkit.get_tools()
        
        # Получаем отдельные инструменты
        self.list_tables_tool = next(
            tool for tool in self.tools if tool.name == "sql_db_list_tables"
        )
        self.get_schema_tool = next(
            tool for tool in self.tools if tool.name == "sql_db_schema"
        )
        self.run_query_tool = next(
            tool for tool in self.tools if tool.name == "sql_db_query"
        )
        
        # Создаём узлы инструментов
        self.get_schema_node = ToolNode([self.get_schema_tool], name="get_schema")
        self.run_query_node = ToolNode([self.run_query_tool], name="run_query")
        
        # Создаём граф
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Строит граф агента."""
        
        # Системный промпт для генерации запросов
        generate_query_system_prompt = f"""You are an agent designed to interact with a SQL database.
Given an input question, create a syntactically correct {self.db.dialect} query to run,
then look at the results of the query and return the answer. Unless the user
specifies a specific number of examples they wish to obtain, always limit your
query to at most {self.config.agent.max_results} results.

You can order the results by a relevant column to return the most interesting
examples in the database. Never query for all the columns from a specific table,
only ask for the relevant columns given the question.

DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the database.
"""
        
        # Системный промпт для проверки запросов
        check_query_system_prompt = f"""You are a SQL expert with a strong attention to detail.
Double check the {self.db.dialect} query for common mistakes, including:
- Using NOT IN with NULL values
- Using UNION when UNION ALL should have been used
- Using BETWEEN for exclusive ranges
- Data type mismatch in predicates
- Properly quoting identifiers
- Using the correct number of arguments for functions
- Casting to the correct data type
- Using the proper columns for joins

If there are any of the above mistakes, rewrite the query. If there are no mistakes,
just reproduce the original query.

You will call the appropriate tool to execute the query after running this check.
"""
        
        # Узел для получения списка таблиц
        def list_tables(state: MessagesState) -> MessagesState:
            """Получает список таблиц из базы данных."""
            tool_call = {
                "name": "sql_db_list_tables",
                "args": {},
                "id": "list_tables_123",
                "type": "tool_call",
            }
            tool_call_message = AIMessage(content="", tool_calls=[tool_call])
            
            tool_message = self.list_tables_tool.invoke(tool_call)
            response = AIMessage(f"Available tables: {tool_message.content}")
            
            return {"messages": [tool_call_message, tool_message, response]}
        
        # Узел для вызова получения схемы
        def call_get_schema(state: MessagesState) -> MessagesState:
            """Вызывает инструмент для получения схемы."""
            llm_with_tools = self.model.bind_tools([self.get_schema_tool], tool_choice="any")
            response = llm_with_tools.invoke(state["messages"])
            return {"messages": [response]}
        
        # Узел для генерации запроса
        def generate_query(state: MessagesState) -> MessagesState:
            """Генерирует SQL-запрос на основе вопроса."""
            system_message = {
                "role": "system",
                "content": generate_query_system_prompt,
            }
            llm_with_tools = self.model.bind_tools([self.run_query_tool])
            response = llm_with_tools.invoke([system_message] + state["messages"])
            return {"messages": [response]}
        
        # Узел для проверки запроса
        def check_query(state: MessagesState) -> MessagesState:
            """Проверяет SQL-запрос на ошибки."""
            system_message = {
                "role": "system",
                "content": check_query_system_prompt,
            }
            
            # Генерируем искусственное сообщение пользователя для проверки
            tool_call = state["messages"][-1].tool_calls[0]
            user_message = {"role": "user", "content": tool_call["args"]["query"]}
            llm_with_tools = self.model.bind_tools([self.run_query_tool], tool_choice="any")
            response = llm_with_tools.invoke([system_message, user_message])
            response.id = state["messages"][-1].id
            
            return {"messages": [response]}
        
        # Функция для определения следующего шага
        def should_continue(state: MessagesState) -> str:
            """Определяет, нужно ли продолжать выполнение."""
            messages = state["messages"]
            last_message = messages[-1]
            if not last_message.tool_calls:
                return END
            else:
                return "run_query"
        
        # Создание графа
        builder = StateGraph(MessagesState)
        
        # Добавление узлов
        builder.add_node("list_tables", list_tables)
        builder.add_node("call_get_schema", call_get_schema)
        builder.add_node("get_schema", self.get_schema_node)
        builder.add_node("generate_query", generate_query)
        builder.add_node("run_query", self.run_query_node)
        
        # Добавление рёбер
        builder.add_edge(START, "list_tables")
        builder.add_edge("list_tables", "call_get_schema")
        builder.add_edge("call_get_schema", "get_schema")
        builder.add_edge("get_schema", "generate_query")
        builder.add_conditional_edges(
            "generate_query",
            should_continue,
            {
                END: END,
                "run_query": "run_query"
            }
        )
        builder.add_edge("run_query", "generate_query")
        
        return builder.compile()
    
    def query(self, question: str) -> dict:
        """Выполняет запрос к агенту.
        
        Args:
            question: Вопрос пользователя на естественном языке.
            
        Returns:
            Словарь с результатами выполнения.
        """
        try:
            result = self.graph.invoke(
                {"messages": [{"role": "user", "content": question}]},
                stream_mode="values"
            )
            
            # Извлекаем последнее сообщение
            last_message = result["messages"][-1]
            
            return {
                "success": True,
                "answer": last_message.content,
                "messages": result["messages"]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "answer": f"Произошла ошибка: {e}"
            }
    
    def query_with_stream(self, question: str, verbose: bool = False, show_tools: bool = False, show_sql: bool = False):
        """Выполняет запрос к агенту с потоковым выводом сообщений.
        
        Args:
            question: Вопрос пользователя на естественном языке.
            verbose: Показывать все сообщения.
            show_tools: Показывать сообщения инструментов.
            show_sql: Показывать SQL-запросы.
            
        Yields:
            Сообщения из выполнения графа.
        """
        try:
            for step in self.graph.stream(
                {"messages": [{"role": "user", "content": question}]},
                stream_mode="values"
            ):
                if "messages" in step and step["messages"]:
                    message = step["messages"][-1]
                    
                    # Фильтрация сообщений по флагам
                    if verbose:
                        yield message
                    elif show_tools and hasattr(message, 'tool_calls') and message.tool_calls:
                        yield message
                    elif show_sql and hasattr(message, 'tool_calls') and message.tool_calls:
                        # Показываем сообщения с tool_calls, которые содержат SQL-запросы
                        for tool_call in message.tool_calls:
                            if 'query' in tool_call.get('args', {}):
                                yield message
                                break
                    elif not show_tools and not show_sql:
                        # По умолчанию показываем только финальный ответ AI (без tool_calls)
                        if isinstance(message, AIMessage) and (not hasattr(message, 'tool_calls') or not message.tool_calls):
                            yield message
        except Exception as e:
            yield AIMessage(content=f"Произошла ошибка: {e}")
    
    def stream_query(self, question: str):
        """Выполняет запрос к агенту с потоковым выводом.
        
        Args:
            question: Вопрос пользователя на естественном языке.
            
        Yields:
            События выполнения графа.
        """
        for step in self.graph.stream(
            {"messages": [{"role": "user", "content": question}]},
            stream_mode="values"
        ):
            yield step
