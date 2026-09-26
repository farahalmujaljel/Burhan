from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    llm_base_url: str = "http://localhost:11434/v1"
    llm_model: str = "llama3.2:3b"

    database_url: str | None = None
    qdrant_url: str | None = "http://localhost:6333"
    qdrant_api_key: str | None = None
    neo4j_uri: str | None = "bolt://localhost:7687"
    neo4j_user: str | None = "neo4j"
    neo4j_password: str | None = "burhan-password"

    storage_dir: str = "storage"


settings = Settings()
