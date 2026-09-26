"""Request/response models shared across API routes."""

from typing import Any, Literal

from pydantic import Field

from app.schemas.common import BurhanModel
from app.schemas.documents import PaperRecord


class HealthResponse(BurhanModel):
    status: Literal["ok"] = "ok"
    app: str
    version: str
    environment: str
    llm_provider: str
    llm_configured: bool
    graph_backend: str
    vector_backend: str


class ErrorDetail(BurhanModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BurhanModel):
    error: ErrorDetail


class UploadResult(BurhanModel):
    """Outcome for one file in a multi-file upload. Exactly one of `paper`/`error` is set."""

    file_name: str
    paper: PaperRecord | None = None
    duplicate: bool = False
    error: ErrorDetail | None = None


class UploadResponse(BurhanModel):
    results: list[UploadResult]
