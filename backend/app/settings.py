from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    groq_api_key: str | None = None
    llm_base_url: str = "https://api.groq.com/openai/v1"
    llm_model: str = "openai/gpt-oss-120b"

    database_url: str | None = None
    qdrant_url: str | None = None
    qdrant_api_key: str | None = None
    neo4j_uri: str | None = None
    neo4j_user: str | None = "neo4j"
    neo4j_password: str | None = "burhan-password"

    storage_dir: str = "storage"


settings = Settings()
