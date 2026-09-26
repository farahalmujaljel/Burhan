import pymupdf
import pytest

from app.core.errors import (
    FileTooLargeError,
    InvalidInputError,
    NotFoundError,
    UnsupportedFileError,
)
from app.parsing.pymupdf_parser import TEXT_FLAGS, PyMuPDFParser, _clean_page_text
from app.schemas.documents import PaperStatus
from app.services.document_store import DocumentStore
from app.services.ingestion import IngestionService, validate_pdf_upload
from tests.pdf_factory import CORRUPTED_PDF, make_pdf

MB = 1024 * 1024


@pytest.fixture
def service(tmp_path) -> IngestionService:
    return IngestionService(
        DocumentStore(tmp_path / "uploads"),
        PyMuPDFParser(),
        chunk_size=300,
        chunk_overlap=50,
        max_upload_bytes=MB,
    )


# --- Upload validation --------------------------------------------------------


def test_validation_accepts_pdf_and_sanitizes_name():
    assert validate_pdf_upload("../../etc/paper.pdf", make_pdf(), "application/pdf", MB) == (
        "paper.pdf"
    )


@pytest.mark.parametrize(
    ("name", "data", "ctype", "error"),
    [
        ("notes.txt", b"%PDF-1.7 ...", "text/plain", UnsupportedFileError),
        ("paper.pdf", b"%PDF-1.7 ...", "image/png", UnsupportedFileError),
        ("paper.pdf", b"hello world", "application/pdf", UnsupportedFileError),
        ("paper.pdf", b"", "application/pdf", InvalidInputError),
        ("paper.pdf", b"%PDF-" + b"0" * MB, "application/pdf", FileTooLargeError),
    ],
    ids=["extension", "content-type", "magic-bytes", "empty", "too-large"],
)
def test_validation_rejects_bad_uploads(name, data, ctype, error):
    with pytest.raises(error):
        validate_pdf_upload(name, data, ctype, MB)


# --- Ingestion pipeline -------------------------------------------------------


def test_ingest_produces_traceable_parsed_document(service):
    data = make_pdf()
    record, duplicate = service.ingest("paper.pdf", data, "application/pdf")

    assert not duplicate
    assert record.status == PaperStatus.PARSED
    assert record.page_count == 3
    assert record.section_count == 9
    assert record.chunk_count and record.chunk_count > 0

    doc = service.store.get_document(record.paper_id)
    assert doc.paper_id == record.paper_id
    assert len(doc.chunks) == record.chunk_count

    # End-to-end provenance: every chunk is found verbatim on the PDF page(s) it claims.
    with pymupdf.open(stream=service.store.read_source(record.paper_id), filetype="pdf") as pdf:
        for chunk in doc.chunks:
            assert doc.text[chunk.char_start : chunk.char_end] == chunk.text
            span_text = "\n\n".join(
                _clean_page_text(pdf[p - 1].get_text("text", flags=TEXT_FLAGS))
                for p in range(chunk.page, chunk.page_end + 1)
            )
            assert chunk.text in span_text


def test_duplicate_upload_is_deduplicated(service):
    data = make_pdf()
    first, _ = service.ingest("a.pdf", data)
    second, duplicate = service.ingest("b.pdf", data)
    assert duplicate
    assert second.paper_id == first.paper_id
    assert len(service.store.list_records()) == 1


def test_corrupted_pdf_is_stored_as_failed(service):
    record, _ = service.ingest("broken.pdf", CORRUPTED_PDF)
    assert record.status == PaperStatus.FAILED
    assert record.error
    with pytest.raises(NotFoundError, match="not been parsed"):
        service.store.get_document(record.paper_id)


def test_truncated_pdf_never_crashes(service):
    data = make_pdf()
    record, _ = service.ingest("truncated.pdf", data[: len(data) // 2])
    assert record.status in {PaperStatus.PARSED, PaperStatus.FAILED}


def test_reprocess_updates_record(service):
    record, _ = service.ingest("paper.pdf", make_pdf())
    service.chunk_size, service.chunk_overlap = 1200, 200
    again = service.process(record.paper_id)
    assert again.status == PaperStatus.PARSED
    assert again.chunk_count < record.chunk_count
    assert service.store.get_record(record.paper_id).chunk_count == again.chunk_count


def test_store_persists_across_instances(service, tmp_path):
    record, _ = service.ingest("paper.pdf", make_pdf())
    fresh = DocumentStore(tmp_path / "uploads")
    assert fresh.get_record(record.paper_id) == record
    assert fresh.get_document(record.paper_id).chunks


@pytest.mark.parametrize("bad_id", ["../etc", "paper_000000000000", "paper_../../x", "x"])
def test_store_rejects_unknown_or_malicious_ids(service, bad_id):
    with pytest.raises(NotFoundError):
        service.store.get_record(bad_id)
