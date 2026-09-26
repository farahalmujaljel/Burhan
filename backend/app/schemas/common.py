"""Shared base model and ID helpers for all Burhan schemas."""

from uuid import uuid4

from pydantic import BaseModel, ConfigDict


class BurhanModel(BaseModel):
    """Strict base: unknown fields are rejected so LLM output can't smuggle in extra data."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"
