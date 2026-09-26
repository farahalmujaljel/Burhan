from app.core.config import Settings
from app.llm.base import LLMClient, LLMNotConfiguredError


def create_llm_client(settings: Settings) -> LLMClient:
    """Build the configured provider's client. Add new providers here."""
    if settings.llm_provider == "groq":
        if not settings.llm_configured:
            raise LLMNotConfiguredError("GROQ_API_KEY is not set; add it to .env to run extraction")
        from app.llm.groq_client import GroqClient

        return GroqClient(
            api_key=settings.groq_api_key.get_secret_value(),
            model=settings.llm_model,
            fallback_model=settings.llm_fallback_model,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_output_tokens,
            timeout=settings.llm_timeout_seconds,
            max_retries=settings.llm_http_retries,
            reasoning_effort=settings.llm_reasoning_effort,
        )
    raise LLMNotConfiguredError(f"Unsupported LLM provider '{settings.llm_provider}'")
