"""Groq implementation of the LLM interface."""

import logging

import groq

from app.llm.base import ChatMessage, LLMClient, LLMProviderError, LLMResponse

logger = logging.getLogger(__name__)


class GroqClient(LLMClient):
    provider = "groq"

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        fallback_model: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
        timeout: float = 60.0,
        max_retries: int = 2,
        reasoning_effort: str | None = None,
        sdk_client: groq.Groq | None = None,
    ) -> None:
        # The SDK retries transient errors (429/5xx/connection) with backoff on its own.
        self._client = sdk_client or groq.Groq(
            api_key=api_key, timeout=timeout, max_retries=max_retries
        )
        self.model = model
        self.fallback_model = fallback_model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.reasoning_effort = reasoning_effort

    def complete(
        self,
        messages: list[ChatMessage],
        *,
        json_mode: bool = False,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        models = [self.model] + ([self.fallback_model] if self.fallback_model else [])
        last_error: Exception | None = None
        for model in models:
            try:
                return self._call(model, messages, json_mode, temperature, max_tokens)
            except groq.APIError as exc:
                last_error = exc
                logger.warning("Groq call failed with model %s: %s", model, exc)
        raise LLMProviderError(f"Groq request failed: {last_error}") from last_error

    def _call(
        self,
        model: str,
        messages: list[ChatMessage],
        json_mode: bool,
        temperature: float | None,
        max_tokens: int | None,
    ) -> LLMResponse:
        kwargs = {}
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        if self.reasoning_effort:
            kwargs["reasoning_effort"] = self.reasoning_effort
        resp = self._client.chat.completions.create(
            model=model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            temperature=self.temperature if temperature is None else temperature,
            max_tokens=max_tokens or self.max_tokens,
            **kwargs,
        )
        content = resp.choices[0].message.content or ""
        return LLMResponse(content=content, model=resp.model or model)
