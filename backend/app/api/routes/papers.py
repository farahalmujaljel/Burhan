"""Paper upload and parsing endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile

from app.api.deps import get_ingestion, get_settings
from app.core.config import Settings
from app.core.errors import BurhanError, InvalidInputError
from app.schemas.api import ErrorDetail, UploadResponse, UploadResult
from app.schemas.documents import PaperRecord, ParsedDocument
from app.services.ingestion import IngestionService

router = APIRouter(prefix="/papers", tags=["papers"])

Ingestion = Annotated[IngestionService, Depends(get_ingestion)]


@router.post("", response_model=UploadResponse)
def upload_papers(
    files: Annotated[list[UploadFile], File(description="One or more PDF files")],
    ingestion: Ingestion,
    settings: Annotated[Settings, Depends(get_settings)],
) -> UploadResponse:
    """Upload and parse PDFs. Each file gets its own result; one bad file never fails the batch."""
    if len(files) > settings.max_files_per_upload:
        raise InvalidInputError(
            f"At most {settings.max_files_per_upload} files per upload",
            details={"received": len(files)},
        )

    results: list[UploadResult] = []
    for upload in files:
        name = upload.filename or "upload.pdf"
        # Read one byte past the limit so oversized files are detected without reading them fully.
        data = upload.file.read(settings.max_upload_bytes + 1)
        try:
            record, duplicate = ingestion.ingest(name, data, upload.content_type)
            results.append(UploadResult(file_name=name, paper=record, duplicate=duplicate))
        except BurhanError as exc:
            error = ErrorDetail(code=exc.code, message=exc.message, details=exc.details)
            results.append(UploadResult(file_name=name, error=error))
    return UploadResponse(results=results)


@router.get("", response_model=list[PaperRecord])
def list_papers(ingestion: Ingestion) -> list[PaperRecord]:
    return ingestion.store.list_records()


@router.get("/{paper_id}", response_model=PaperRecord)
def get_paper(paper_id: str, ingestion: Ingestion) -> PaperRecord:
    return ingestion.store.get_record(paper_id)


@router.get("/{paper_id}/document", response_model=ParsedDocument)
def get_parsed_document(paper_id: str, ingestion: Ingestion) -> ParsedDocument:
    """Full parsed output: text, page spans, sections, and traceable chunks."""
    return ingestion.store.get_document(paper_id)


@router.post("/{paper_id}/process", response_model=PaperRecord)
def process_paper(paper_id: str, ingestion: Ingestion) -> PaperRecord:
    """Re-run parsing for a stored PDF (e.g. after changing chunking settings)."""
    return ingestion.process(paper_id)
