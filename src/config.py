import os
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv

# Добавляем родительскую директорию в путь для импортов
sys.path.insert(0, str(Path(__file__).parent.parent))

load_dotenv()


@dataclass
class DatabaseConfig:
    """Конфигурация подключения к базе данных."""
    
    db_type: str = os.getenv("DB_TYPE", "sqlite")
    host: Optional[str] = os.getenv("DB_HOST", None)
    port: Optional[int] = int(os.getenv("DB_PORT", "5432")) if os.getenv("DB_PORT") else None
    database: str = os.getenv("DB_NAME", "sample.db")
    username: Optional[str] = os.getenv("DB_USER", None)
    password: Optional[str] = os.getenv("DB_PASSWORD", None)
    
    def get_connection_string(self) -> str:
        """Формирует строку подключения к базе данных."""
        if self.db_type == "postgresql":
            return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
        elif self.db_type == "sqlite":
            return f"sqlite:///{self.database}"
        else:
            raise ValueError(f"Неподдерживаемый тип базы данных: {self.db_type}")


@dataclass
class LLMConfig:
    """Конфигурация языковой модели."""
    
    provider: str = os.getenv("LLM_PROVIDER", "openai")
    model: str = os.getenv("LLM_MODEL", "glm-4.7")
    temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.0"))
    api_key: Optional[str] = os.getenv("OPENAI_API_KEY", None)
    base_url: Optional[str] = os.getenv("BASE_URL", None)
    
    def __post_init__(self):
        if self.provider == "openai" and not self.api_key:
            raise ValueError("OPENAI_API_KEY не установлен в переменных окружения")


@dataclass
class AgentConfig:
    """Конфигурация агента."""
    
    max_results: int = int(os.getenv("MAX_RESULTS", "100"))
    max_retries: int = int(os.getenv("MAX_RETRIES", "3"))
    enable_sql_validation: bool = os.getenv("ENABLE_SQL_VALIDATION", "true").lower() == "true"
    show_sql: bool = os.getenv("SHOW_SQL", "true").lower() == "true"
    language: str = os.getenv("LANGUAGE", "ru")


@dataclass
class Config:
    """Основная конфигурация приложения."""
    
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    agent: AgentConfig = field(default_factory=AgentConfig)
    
    @classmethod
    def from_env(cls) -> "Config":
        """Создаёт конфигурацию из переменных окружения."""
        return cls(
            database=DatabaseConfig(),
            llm=LLMConfig(),
            agent=AgentConfig()
        )
