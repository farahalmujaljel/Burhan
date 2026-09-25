from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    openai_api_key: str | None = None
    openai_model: str = "gpt-5"
    embedding_model: str = "text-embedding-3-large"

    database_url: str | None = None
    qdrant_url: str | None = "http://localhost:6333"
    qdrant_api_key: str | None = None
    neo4j_uri: str | None = "bolt://localhost:7687"
    neo4j_user: str | None = "neo4j"
    neo4j_password: str | None = "burhan-password"

    storage_dir: str = "storage"


settings = Settings()
