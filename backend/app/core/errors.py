"""Domain errors and the handler that renders them as a consistent JSON shape."""

from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.schemas.api import ErrorDetail, ErrorResponse


class BurhanError(Exception):
    status_code = 500
    code = "internal_error"

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class NotFoundError(BurhanError):
    status_code = 404
    code = "not_found"


class InvalidInputError(BurhanError):
    status_code = 422
    code = "invalid_input"


class UnsupportedFileError(BurhanError):
    status_code = 415
    code = "unsupported_file"


class FileTooLargeError(BurhanError):
    status_code = 413
    code = "file_too_large"


class DocumentParsingError(BurhanError):
    """The file looked like a PDF but could not be parsed (corrupted, encrypted, no text)."""

    status_code = 422
    code = "unparseable_document"


class ProviderError(BurhanError):
    """An external dependency (LLM, Neo4j, Qdrant) failed."""

    status_code = 502
    code = "provider_error"


async def _handle_burhan_error(_: Request, exc: BurhanError) -> JSONResponse:
    body = ErrorResponse(error=ErrorDetail(code=exc.code, message=exc.message, details=exc.details))
    return JSONResponse(status_code=exc.status_code, content=body.model_dump())


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(BurhanError, _handle_burhan_error)
