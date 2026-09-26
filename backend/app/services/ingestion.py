"""Ingestion pipeline: validate upload -> store -> parse -> detect sections -> chunk -> save.

Parsing failures never raise out of `process`: the record is marked FAILED with the reason,
so one corrupted file cannot break a multi-file upload.
"""

import hashlib
import logging
from datetime import UTC, datetime
from pathlib import PurePath

from app.core.errors import (
    DocumentParsingError,
    FileTooLargeError,
    InvalidInputError,
    UnsupportedFileError,
)
from app.parsing.base import DocumentParser
from app.parsing.chunker import chunk_document
from app.parsing.sectioner import detect_sections
from app.schemas.documents import PaperRecord, PaperStatus, ParsedDocument
from app.services.document_store import DocumentStore

logger = logging.getLogger(__name__)

PDF_MAGIC = b"%PDF-"
ALLOWED_CONTENT_TYPES = {"application/pdf", "application/x-pdf", "application/octet-stream", None}


def validate_pdf_upload(
    file_name: str, data: bytes, content_type: str | None, max_bytes: int
) -> str:
    """Check an upload looks like a PDF. Returns the sanitized file name."""
    name = PurePath(file_name or "upload.pdf").name or "upload.pdf"
    if not name.lower().endswith(".pdf"):
        raise UnsupportedFileError(f"'{name}' is not a .pdf file")
    if content_type and content_type.split(";")[0].strip().lower() not in ALLOWED_CONTENT_TYPES:
        raise UnsupportedFileError(f"'{name}' has unsupported content type '{content_type}'")
    if not data:
        raise InvalidInputError(f"'{name}' is empty")
    if len(data) > max_bytes:
        raise FileTooLargeError(
            f"'{name}' exceeds the {max_bytes // (1024 * 1024)} MB upload limit"
        )
    # PDF spec allows junk before the header; readers accept it within the first 1 KB.
    if PDF_MAGIC not in data[:1024]:
        raise UnsupportedFileError(f"'{name}' is not a valid PDF (missing %PDF header)")
    return name


class IngestionService:
    def __init__(
        self,
        store: DocumentStore,
        parser: DocumentParser,
        *,
        chunk_size: int,
        chunk_overlap: int,
        max_upload_bytes: int,
    ) -> None:
        self.store = store
        self.parser = parser
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.max_upload_bytes = max_upload_bytes

    def ingest(
        self, file_name: str, data: bytes, content_type: str | None = None
    ) -> tuple[PaperRecord, bool]:
        """Validate, store, and parse one upload. Returns (record, is_duplicate).

        Raises on invalid input (not stored). Parsing failures are captured on the record.
        """
        name = validate_pdf_upload(file_name, data, content_type, self.max_upload_bytes)
        sha256 = hashlib.sha256(data).hexdigest()
        record, created = self.store.create(file_name=name, data=data, sha256=sha256)
        if not created and record.status == PaperStatus.PARSED:
            logger.info("Duplicate upload %s matches %s", name, record.paper_id)
            return record, True
        return self.process(record.paper_id), not created

    def process(self, paper_id: str) -> PaperRecord:
        """(Re)parse a stored PDF and persist the ParsedDocument."""
        record = self.store.get_record(paper_id)
        try:
            doc = self._parse(record)
        except DocumentParsingError as exc:
            logger.warning("Parsing failed for %s: %s", paper_id, exc.message)
            self.store.delete_document(paper_id)
            record = record.model_copy(
                update={"status": PaperStatus.FAILED, "error": exc.message, "parsed_at": None}
            )
        else:
            self.store.save_document(doc)
            record = record.model_copy(
                update={
                    "status": PaperStatus.PARSED,
                    "error": None,
                    "title": doc.title,
                    "parser": doc.parser,
                    "page_count": doc.page_count,
                    "section_count": len(doc.sections),
                    "chunk_count": len(doc.chunks),
                    "parsed_at": datetime.now(UTC),
                }
            )
        self.store.save_record(record)
        return record

    def _parse(self, record: PaperRecord) -> ParsedDocument:
        doc = self.parser.parse(
            self.store.read_source(record.paper_id),
            paper_id=record.paper_id,
            file_name=record.file_name,
        )
        if not doc.sections:
            doc = doc.model_copy(update={"sections": detect_sections(doc)})
        chunks = chunk_document(doc, size=self.chunk_size, overlap=self.chunk_overlap)
        if not chunks:
            raise DocumentParsingError("No text chunks could be produced from this PDF")
        # Re-validate so offset/traceability invariants are enforced on the final document.
        return ParsedDocument.model_validate({**doc.model_dump(), "chunks": chunks})
