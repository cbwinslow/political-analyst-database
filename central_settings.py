from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Centralized application settings loaded from environment variables.
    """
    # Load from .env file if it exists
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    # PostgreSQL
    database_url: str

    # Neo4j
    neo4j_url: str = "bolt://neo4j:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str

    # AI Inference
    llm_service_url: str = "http://localai:8080"
    llm_model_name: str = "gpt-4-turbo"

# Create a single, importable instance of the settings
settings = Settings()
