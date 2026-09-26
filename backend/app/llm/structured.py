"""Schema-constrained generation: JSON mode + Pydantic validation + limited repair retries."""

import json
import logging
import re
from dataclasses import dataclass
from typing import Generic, TypeVar

from pydantic import BaseModel, ValidationError

from app.llm.base import ChatMessage, LLMClient, LLMOutputError

logger = logging.getLogger(__name__)

_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)
MAX_ERROR_CHARS = 1500

T = TypeVar("T", bound=BaseModel)


@dataclass(frozen=True)
class StructuredResult(Generic[T]):
    value: T
    model: str
    attempts: int


def extract_json(text: str) -> object:
    """Parse a JSON object from model output, tolerating code fences and surrounding prose."""
    cleaned = _FENCE.sub("", text.strip())
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start == -1 or end <= start:
            raise
        return json.loads(cleaned[start : end + 1])


def generate_structured(
    llm: LLMClient,
    messages: list[ChatMessage],
    schema: type[T],
    *,
    max_attempts: int = 3,
    max_tokens: int | None = None,
) -> StructuredResult[T]:
    """Call the LLM until its output validates against `schema`, feeding errors back."""
    conversation = list(messages)
    last_error = ""
    for attempt in range(1, max_attempts + 1):
        response = llm.complete(conversation, json_mode=True, max_tokens=max_tokens)
        try:
            value = schema.model_validate(extract_json(response.content))
            return StructuredResult(value=value, model=response.model, attempts=attempt)
        except (json.JSONDecodeError, ValidationError) as exc:
            last_error = str(exc)[:MAX_ERROR_CHARS]
            logger.warning(
                "Invalid %s output (attempt %d/%d): %s",
                schema.__name__,
                attempt,
                max_attempts,
                last_error.splitlines()[0] if last_error else "",
            )
            conversation += [
                ChatMessage("assistant", response.content[:4000]),
                ChatMessage(
                    "user",
                    "Your previous reply was not valid for the required JSON format.\n"
                    f"Error:\n{last_error}\n\n"
                    "Reply again with ONLY one corrected JSON object, no prose.",
                ),
            ]
    raise LLMOutputError(
        f"{schema.__name__} output still invalid after {max_attempts} attempts",
        details={"last_error": last_error},
    )
