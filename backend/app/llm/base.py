"""Provider-agnostic LLM interface. Services depend on this, never on a vendor SDK."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal

from app.core.errors import BurhanError, ProviderError


@dataclass(frozen=True)
class ChatMessage:
    role: Literal["system", "user", "assistant"]
    content: str


@dataclass(frozen=True)
class LLMResponse:
    content: str
    model: str  # the model that actually answered (may be a fallback)


class LLMClient(ABC):
    provider: str

    @abstractmethod
    def complete(
        self,
        messages: list[ChatMessage],
        *,
        json_mode: bool = False,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        """Return the model's reply. Raise `LLMProviderError` on transport/API failure."""


class LLMProviderError(ProviderError):
    code = "llm_provider_error"


class LLMOutputError(ProviderError):
    """The model kept returning output that does not match the expected schema."""

    code = "llm_output_invalid"


class LLMNotConfiguredError(BurhanError):
    status_code = 503
    code = "llm_not_configured"
