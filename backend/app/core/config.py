"""Application settings, loaded from environment variables and the repo-root `.env`."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
    )

    # App
    app_name: str = "Burhan"
    app_version: str = "0.1.0"
    app_env: Literal["development", "test", "production"] = "development"
    log_level: str = "INFO"
    api_prefix: str = "/api"
    cors_origins: str = "http://localhost:3000"

    # LLM (provider-agnostic; Groq is the default)
    llm_provider: Literal["groq"] = "groq"
    groq_api_key: SecretStr | None = None
    llm_model: str = "openai/gpt-oss-120b"
    llm_fallback_model: str | None = "openai/gpt-oss-20b"
    # For reasoning models (gpt-oss): low keeps hidden reasoning tokens and latency down.
    llm_reasoning_effort: Literal["low", "medium", "high"] | None = "low"
    llm_temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    llm_timeout_seconds: float = Field(default=60.0, gt=0)
    # Repair retries when the model returns malformed/invalid JSON.
    llm_max_retries: int = Field(default=2, ge=0)
    # SDK retries for transient HTTP errors, including 429 rate limits (honours Retry-After).
    llm_http_retries: int = Field(default=6, ge=0)
    # Groq counts max_tokens toward the tokens-per-minute limit, so keep this modest.
    llm_max_output_tokens: int = Field(default=4096, gt=0)

    # Extraction
    extraction_window_chars: int = Field(default=8000, ge=1000)
    verification_batch_size: int = Field(default=12, gt=0)

    # Embeddings (always local; no embedding API is called)
    # model2vec runs everywhere (incl. Intel Macs); fastembed needs onnxruntime; hashing is
    # a no-download lexical fallback for tests/offline use.
    embedding_backend: Literal["model2vec", "fastembed", "hashing"] = "model2vec"
    embedding_model: str = "minishlab/potion-retrieval-32M"
    embedding_dim: int = Field(default=384, gt=0, description="Only used by the hashing backend")

    # Research Digital Twin
    research_domain: str = "General"

    # Knowledge graph
    graph_backend: Literal["memory", "neo4j"] = "memory"
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: SecretStr | None = None
    neo4j_database: str | None = None

    # Vector evidence store
    vector_backend: Literal["local", "qdrant"] = "local"
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: SecretStr | None = None
    qdrant_collection: str = "burhan_evidence"

    # Storage
    data_dir: Path = Path("data")
    max_upload_mb: int = Field(default=25, gt=0)
    max_files_per_upload: int = Field(default=20, gt=0)

    # Chunking (characters)
    chunk_size: int = Field(default=1200, ge=200)
    chunk_overlap: int = Field(default=200, ge=0)

    @model_validator(mode="after")
    def _resolve_and_check(self) -> "Settings":
        if not self.data_dir.is_absolute():
            self.data_dir = (REPO_ROOT / self.data_dir).resolve()
        if self.graph_backend == "neo4j" and not _secret(self.neo4j_password):
            raise ValueError("NEO4J_PASSWORD is required when GRAPH_BACKEND=neo4j")
        if self.chunk_overlap * 2 > self.chunk_size:
            raise ValueError("CHUNK_OVERLAP must be at most half of CHUNK_SIZE")
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    @property
    def uploads_dir(self) -> Path:
        return self.data_dir / "uploads"

    @property
    def papers_dir(self) -> Path:
        return self.data_dir / "papers"

    @property
    def demo_cache_dir(self) -> Path:
        return self.data_dir / "demo_cache"

    @property
    def twin_dir(self) -> Path:
        return self.data_dir / "twin"

    @property
    def qdrant_local_path(self) -> Path:
        return self.data_dir / "qdrant_local"

    @property
    def llm_configured(self) -> bool:
        return bool(_secret(self.groq_api_key))


def _secret(value: SecretStr | None) -> str:
    return value.get_secret_value() if value is not None else ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
