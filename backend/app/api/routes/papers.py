"""Paper upload, parsing, and extraction endpoints."""

from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, File, Query, Response, UploadFile

from app.api.deps import get_extraction, get_ingestion, get_settings
from app.core.config import Settings
from app.core.errors import BurhanError, InvalidInputError
from app.schemas.api import ErrorDetail, UploadResponse, UploadResult
from app.schemas.documents import PaperRecord, ParsedDocument
from app.schemas.extraction import PaperKnowledge
from app.services.extraction import ExtractionService
from app.services.ingestion import IngestionService

router = APIRouter(prefix="/papers", tags=["papers"])

Ingestion = Annotated[IngestionService, Depends(get_ingestion)]
Extraction = Annotated[ExtractionService, Depends(get_extraction)]


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


@router.post(
    "/{paper_id}/extract",
    response_model=PaperRecord,
    status_code=202,
    responses={200: {"description": "Extraction finished (wait=true)"}},
)
def extract_paper(
    paper_id: str,
    extraction: Extraction,
    background: BackgroundTasks,
    response: Response,
    wait: Annotated[bool, Query(description="Run synchronously and return when done")] = False,
) -> PaperRecord:
    """Extract evidence-backed scientific knowledge from a parsed paper using the LLM.

    By default runs in the background (202); poll `GET /papers/{paper_id}` for
    `extraction_status`, then read `GET /papers/{paper_id}/knowledge`.
    """
    record = extraction.start(paper_id)
    if wait:
        response.status_code = 200
        return extraction.run(paper_id)
    background.add_task(extraction.run, paper_id)
    return record


@router.get("/{paper_id}/knowledge", response_model=PaperKnowledge)
def get_knowledge(paper_id: str, extraction: Extraction) -> PaperKnowledge:
    """The stored extraction result: entities, relations, evidence, and run metadata."""
    return extraction.store.get_knowledge(paper_id)
