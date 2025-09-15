"""Configuration management for the political analyst database."""

from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""
    
    url: str = Field(default="postgresql://username:password@localhost:5432/political_analyst_db")
    test_url: str = Field(default="postgresql://username:password@localhost:5432/political_analyst_test_db")
    echo: bool = Field(default=False)
    
    class Config:
        env_prefix = "DATABASE_"


class RedisSettings(BaseSettings):
    """Redis configuration settings."""
    
    url: str = Field(default="redis://localhost:6379/0")
    
    class Config:
        env_prefix = "REDIS_"


class Neo4jSettings(BaseSettings):
    """Neo4j configuration settings."""
    
    uri: str = Field(default="bolt://localhost:7687")
    user: str = Field(default="neo4j")
    password: str = Field(default="password")
    
    class Config:
        env_prefix = "NEO4J_"


class OpenAISettings(BaseSettings):
    """OpenAI API configuration settings."""
    
    api_key: str = Field(default="")
    model: str = Field(default="gpt-3.5-turbo")
    
    class Config:
        env_prefix = "OPENAI_"


class TwitterSettings(BaseSettings):
    """Twitter API configuration settings."""
    
    api_key: str = Field(default="")
    api_secret: str = Field(default="")
    access_token: str = Field(default="")
    access_token_secret: str = Field(default="")
    bearer_token: str = Field(default="")
    
    class Config:
        env_prefix = "TWITTER_"


class CrawlingSettings(BaseSettings):
    """Web crawling configuration settings."""
    
    delay: float = Field(default=1.0)
    max_concurrent_requests: int = Field(default=10)
    user_agent: str = Field(default="PoliticalAnalystBot/1.0")
    timeout: int = Field(default=30)
    
    class Config:
        env_prefix = "CRAWL_"


class VectorSettings(BaseSettings):
    """Vector database configuration settings."""
    
    chroma_persist_directory: str = Field(default="./data/chroma")
    embedding_model: str = Field(default="all-MiniLM-L6-v2")
    collection_name: str = Field(default="political_documents")
    
    class Config:
        env_prefix = "VECTOR_"


class AppSettings(BaseSettings):
    """Main application configuration settings."""
    
    name: str = Field(default="Political Analyst Database")
    version: str = Field(default="0.1.0")
    debug: bool = Field(default=False)
    secret_key: str = Field(default="your_secret_key_here")
    log_level: str = Field(default="INFO")
    log_file: str = Field(default="logs/app.log")
    
    class Config:
        env_prefix = "APP_"


class Settings(BaseSettings):
    """Consolidated settings for the entire application."""
    
    database: DatabaseSettings = DatabaseSettings()
    redis: RedisSettings = RedisSettings()
    neo4j: Neo4jSettings = Neo4jSettings()
    openai: OpenAISettings = OpenAISettings()
    twitter: TwitterSettings = TwitterSettings()
    crawling: CrawlingSettings = CrawlingSettings()
    vector: VectorSettings = VectorSettings()
    app: AppSettings = AppSettings()
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()