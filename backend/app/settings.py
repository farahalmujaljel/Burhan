from pathlib import Path

from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
GROQ_DEFAULT_MODEL = "openai/gpt-oss-120b"


class Settings(BaseSettings):
    # Resolve .env files by absolute path so the app behaves the same whether it is
    # started from the project root (backend.app.main) or from backend/ (app.main).
    # Later files take precedence; unknown keys (e.g. frontend vars) are ignored.
    model_config = SettingsConfigDict(
        env_file=(PROJECT_ROOT / ".env", BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


    llm_base_url: str = "https://api.groq.com/openai/v1"
    llm_model: str = "openai/gpt-oss-120b"
    llm_api_key: str | None = Field(default=None, validation_alias=AliasChoices("LLM_API_KEY", "GROQ_API_KEY"))
    # Paper text sent to the LLM per extraction request.
    llm_max_input_chars: int = 24000

    database_url: str | None = None
    qdrant_url: str | None = None
    qdrant_api_key: str | None = None
    neo4j_uri: str | None = None
    neo4j_user: str | None = "neo4j"
    neo4j_password: str | None = "burhan-password"

    storage_dir: str = "storage"

    @model_validator(mode="after")
    def _resolve_defaults(self) -> "Settings":
        # A Groq key with no explicit LLM endpoint means "use Groq" rather than local Ollama.
        if self.llm_api_key and "llm_base_url" not in self.model_fields_set:
            self.llm_base_url = GROQ_BASE_URL
            if "llm_model" not in self.model_fields_set:
                self.llm_model = GROQ_DEFAULT_MODEL
            # Groq's free tier caps requests at 8k tokens/minute; ~12k chars fits comfortably.
            if "llm_max_input_chars" not in self.model_fields_set:
                self.llm_max_input_chars = 12000
        # Relative storage paths are anchored to backend/ so existing runs are found
        # regardless of the working directory.
        storage = Path(self.storage_dir).expanduser()
        if not storage.is_absolute():
            storage = BACKEND_DIR / storage
        self.storage_dir = str(storage)
        return self


settings = Settings()
